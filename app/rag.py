"""Retrieval-augmented answers over official documents and the project's decision logs (D30).

How it works:
1. Retrieve: the question is compared with 765 passages (about 1,000 characters each), each indexed with its
   document title in front (a contextual header, so a passage keeps track of what it belongs to), by
   - BM25 [N1]: a probabilistic keyword score that rewards rare shared words, saturates repeated words and
     normalises for passage length;
   - multilingual sentence embeddings [N2, N3] (fastembed, local ONNX model, no API): meaning-based,
     works across French and English;
   - Reciprocal Rank Fusion [N4]: each method votes 1 / (60 + rank) for every passage; votes are added.
     It needs no score calibration, which is why it is the standard way to combine rankers;
   - optional re-ranking [N5, N6] (evaluation only): a multilingual cross-encoder reads the question and each of the
     top 20 passages together and re-orders them. More accurate, but too heavy for the hosted app.
2. Answer (optional, needs GEMINI_API_KEY or ANTHROPIC_API_KEY): a language model (Gemini or Claude, see
   provider()) writes a short answer from the top passages only,
   citing each passage it uses as [chunk_id], in the language of the question (detected, not the app's
   language): most passages are English, so the instruction names the target language explicitly (A29).
   Without a key, the app shows the passages themselves.
Passages of the current corpus were cut with a raw 150-character overlap, so most of them start in the middle
of a word; clean_start() trims that repeated fragment for display and for the answer prompt (A29).
The corpus is built by src/rag/build_corpus.py; retrieval quality is measured by src/rag/eval_rag.py.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
STOP = set("the of and a an in to for on by with is are was were be as at from that this it or its their which de la le les des du et en un une pour par sur au aux est sont dans que qui".split())


RRF_K = 60
SENTENCE_START = re.compile(r"(?<=[.!?;:])\s+(?=[\"'«(\[]?[A-Z0-9À-Ý])")
FR_WORDS = set("le la les des du de un une est sont quel quelle quels quelles comment pourquoi combien quand ou "
               "que qui quoi sur pour dans avec par aux au ce cette ces il elle ont a été prix droits banque "
               "taxe taxes douane fromage lait donnees donnée données utilise utilisé utilisées".split())
EN_WORDS = set("the a an of is are was were what which how why when where who did does do has have on for in with "
               "by to from price prices tariff tariffs bank data cheese milk use used".split())
LANG_NAME = {"en": "English", "fr": "French"}
CLAUDE_MODEL = "claude-opus-5-5"
GEMINI_MODEL = "gemini-flash-lite-latest"  # Flash-Lite: Flash allows only 20 free requests a day (A32); GEMINI_MODEL secret overrides
RERANK_MODEL = "BAAI/bge-reranker-v2-m3-int8"
# Retrieval used by the app and by the answer evaluation. BM25 since A33: on the 50 questions of both sets it ranks
# better than embeddings (MRR 0.63 vs 0.51, recall@5 0.78 vs 0.68, p = 0.10) and needs no model; the cross-encoder is
# best (MRR 0.85) but takes 2.4 GB of memory and about 11 s per question, too heavy for the hosted app.
APP_SEARCH = "bm25"


def tokens(text: str) -> list[str]:
    t = "".join(ch for ch in unicodedata.normalize("NFD", str(text).lower()) if unicodedata.category(ch) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP and len(w) > 1]


def clean_start(text: str, window: int = 160) -> str:
    """Drop the leading word or sentence fragment repeated from the previous passage (overlap cut mid-word).

    A passage that starts with a lowercase letter or punctuation begins inside a sentence: it is moved forward
    to the first sentence start within `window` characters (the overlap is 150, so only repeated text is dropped),
    else to the next word and marked with an ellipsis. Passages that start cleanly are returned unchanged."""
    text = str(text).strip()
    if not text or not (text[0].islower() or text[0] in ",;:.)]-–/"):
        return text
    m = SENTENCE_START.search(text[:window])
    if m:
        return text[m.end():]
    space = text.find(" ")
    return "... " + text[space + 1:] if 0 <= space < window else text


def question_lang(question: str, default: str = "en") -> str:
    """'fr' or 'en' from French accents and common words; the app's language breaks ties."""
    folded = str(question).lower()
    words = re.findall(r"[a-zà-ÿ']+", folded)
    fr = sum(w in FR_WORDS for w in words) + 2 * len(re.findall(r"[éèêàùâîôûç]", folded)) \
        + sum(w.startswith(("l'", "d'", "qu'")) for w in words)
    en = sum(w in EN_WORDS for w in words)
    return "fr" if fr > en else "en" if en > fr else default


@lru_cache(maxsize=1)
def corpus() -> pd.DataFrame:
    return pd.read_csv(DATA / "rag_chunks.csv")


def index_texts(titled: bool = True) -> list[str]:
    c = corpus()
    return [f"{t}. {x}" for t, x in zip(c.title, c.text)] if titled else c.text.tolist()


class BM25:
    """Okapi BM25 (k1 = 1.5, b = 0.75)."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = self.len.mean()
        df = Counter(w for d in docs for w in set(d))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}
        self.tf = [Counter(d) for d in docs]

    def scores(self, query: list[str]) -> np.ndarray:
        s = np.zeros(len(self.docs))
        for w in set(query):
            idf = self.idf.get(w)
            if idf is None:
                continue
            f = np.array([tf.get(w, 0) for tf in self.tf], dtype=float)
            s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len / self.avg))
        return s


@lru_cache(maxsize=2)
def bm25(titled: bool = True) -> BM25:
    return BM25([tokens(t) for t in index_texts(titled)])


@lru_cache(maxsize=1)
def embedder():
    from fastembed import TextEmbedding
    return TextEmbedding(EMBED_MODEL)


def embed(texts: list[str]) -> np.ndarray:
    v = np.array(list(embedder().embed(texts)), dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


@lru_cache(maxsize=2)
def chunk_vectors(titled: bool = True) -> np.ndarray:
    path = DATA / ("rag_embeddings.npy" if titled else "rag_embeddings_untitled.npy")
    if path.exists():
        return np.load(path)
    v = embed(index_texts(titled))
    np.save(path, v)
    return v


def rrf(*rankings: np.ndarray, k: int = RRF_K) -> np.ndarray:
    """Reciprocal Rank Fusion [N4]: score(d) = sum over rankers of 1 / (k + rank of d)."""
    total = np.zeros(len(rankings[0]))
    for scores in rankings:
        ranks = np.empty(len(scores))
        ranks[np.argsort(-scores)] = np.arange(1, len(scores) + 1)
        total += 1.0 / (k + ranks)
    return total


@lru_cache(maxsize=1)
def reranker():
    from fastembed.rerank.cross_encoder import TextCrossEncoder
    return TextCrossEncoder(RERANK_MODEL)


def search(query: str, k: int = 5, method: str = "rrf", titled: bool = True) -> pd.DataFrame:
    """method: bm25 | embeddings | rrf | rrf+rerank (the last one re-orders the top 20 with a cross-encoder)."""
    s_bm25 = bm25(titled).scores(tokens(query))
    if method == "bm25":
        score = s_bm25
    else:
        s_emb = chunk_vectors(titled) @ embed([query])[0]
        score = s_emb if method == "embeddings" else rrf(s_bm25, s_emb)
    top = np.argsort(-score)[: (20 if method == "rrf+rerank" else k)]
    out = corpus().iloc[top].assign(score=score[top])
    if method == "rrf+rerank":
        texts = [index_texts(titled)[i] for i in top]
        out = out.assign(score=list(reranker().rerank(query, texts))).sort_values("score", ascending=False).head(k)
    return out


def prompt(question: str, passages: pd.DataFrame, lang: str) -> tuple[str, str]:
    """System and user messages for answer(); lang is the language the answer must be written in."""
    target = LANG_NAME[lang]
    context = "\n\n".join(f"[{r.chunk_id}] ({r.title})\n{clean_start(r.text)}" for r in passages.itertuples())
    system = ("You answer questions about Canadian counter-tariffs and grocery prices using ONLY the numbered passages given. "
              "Cite every passage you use as [chunk_id] right after the sentence it supports. Answer with what the passages "
              "state even when they cover only part of the question, and say what is missing. Only when no passage is "
              "relevant, say in one sentence that the passages do not answer the question. Answer in 2 to 6 short sentences, plain words, no emojis. "
              f"Write the whole answer in {target}, the language of the question, even when the passages are in another "
              "language: translate what you use and keep the [chunk_id] citations unchanged.")
    user = f"PASSAGES\n\n{context}\n\nQUESTION\n{question[:500]}\n\nAnswer in {target}."
    return system, user


def enabled() -> bool:
    """The document search with written answers (RAG) is paused in the app (D32): on held-out questions the answer key
    was met only about half the time, mostly because retrieval missed the right passage. The RAG secret set to "on"
    turns it back on; the evaluation (src/rag/eval_rag.py) does not depend on it."""
    from assistant import secret

    return (secret("RAG") or "").strip().lower() == "on"


def provider() -> str | None:
    """Which model writes the answers: the RAG_PROVIDER secret ("gemini" or "anthropic") if set, else the first
    provider with a key (Gemini first: free tier for the public app), else None (passages only)."""
    from assistant import secret

    keys = {"gemini": secret("GEMINI_API_KEY"), "anthropic": secret("ANTHROPIC_API_KEY")}
    chosen = (secret("RAG_PROVIDER") or "").strip().lower()
    if chosen in keys:
        return chosen if keys[chosen] else None
    return next((name for name, key in keys.items() if key), None)


def generate(system: str, user: str, name: str) -> tuple[str, str]:
    """(text, status) from one provider; status is ok, refusal or error. No exception reaches the app."""
    from assistant import secret

    try:
        if name == "gemini":
            from google import genai
            from google.genai import types

            # Free tier: demand spikes (503) and per-minute quota (429) are frequent, so retry briefly (A31); a spent
            # daily quota still fails after about 6 s and the app shows the passages
            retry = types.HttpRetryOptions(attempts=3, initial_delay=2.0, max_delay=8.0, http_status_codes=[429, 503])
            client = genai.Client(api_key=secret("GEMINI_API_KEY"), http_options=types.HttpOptions(retry_options=retry))
            r = client.models.generate_content(
                model=secret("GEMINI_MODEL") or GEMINI_MODEL, contents=user,
                config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=2000, temperature=0.2))
            text = (r.text or "").strip()
            blocked = r.prompt_feedback is not None and r.prompt_feedback.block_reason is not None
            return (text, "ok") if text else ("", "refusal" if blocked else "error")
        import anthropic

        client = anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY"), max_retries=2, timeout=60.0)
        r = client.beta.messages.create(
            model=CLAUDE_MODEL, max_tokens=2000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low"}, system=system, messages=[{"role": "user", "content": user}])
        if r.stop_reason == "refusal":
            return "", "refusal"
        return "".join(b.text for b in r.content if b.type == "text").strip(), "ok"
    except Exception:  # network, quota, invalid key or model name: the app falls back to the passages
        return "", "error"


FALLBACKS = {
    ("refusal", "en"): "This question cannot be answered here.",
    ("refusal", "fr"): "Cette question ne peut pas être traitée ici.",
    ("error", "en"): "The answer could not be generated; the passages below are the sources.",
    ("error", "fr"): "La réponse n'a pas pu être générée ; les passages ci-dessous sont les sources.",
}


def answer(question: str, passages: pd.DataFrame, lang: str = "en", name: str | None = None) -> str:
    """Short answer from the passages only, with [chunk_id] citations (needs a provider key).

    lang is the app's language; the answer follows the language of the question when it can be detected.
    name forces a provider (used by the evaluation to compare them)."""
    lang = question_lang(question, lang)
    system, user = prompt(question, passages, lang)
    text, status = generate(system, user, name or provider() or "anthropic")
    if status in ("refusal", "error"):
        return FALLBACKS[(status, lang if lang in ("en", "fr") else "en")]
    return text
