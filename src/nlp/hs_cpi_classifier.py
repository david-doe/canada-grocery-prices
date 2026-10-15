"""Classify tariff lines (HS 6-digit) into food CPI series: TF-IDF, embeddings, then an LLM (D29).

Why: the mapping of each new tariff list to CPI series (D18) is done by hand. This module ranks the CPI
series for each customs description, so that a new list can be pre-mapped in minutes and a human only
reviews the doubtful lines. The hand-made mapping of D18 is the ground truth.

Steps, from simplest to most advanced:
1. TF-IDF baseline: word and character n-gram similarity between the customs description and the CPI
   series name (English and French labels, with the parent series for context).
2. Multilingual sentence embeddings (local model, no API): cosine similarity in a semantic space.
3. Hybrid: average of the standardised TF-IDF and embedding scores (equal weights, fixed in advance), and
   Reciprocal Rank Fusion [N4], the standard rank-based combination, reported alongside.
4. LLM (optional, needs ANTHROPIC_API_KEY): Claude picks one series among the 5 hybrid candidates,
   or "none", through a JSON schema whose allowed values are those candidates, so it cannot invent a series.
Metrics: top-1 accuracy, recall@5 and mean reciprocal rank, strict and lenient (a parent or child of the
right series counts as correct), on HS lines that have a gold series.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "data" / "reference"
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
HS_URL = "https://comtradeapi.un.org/files/v1/app/reference/HS.json"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "claude-opus-5-5"
PRIORITY = {"direct": 0, "over_quota_only": 1, "partial": 2, "input": 3}
OUT_OF_SCOPE = ("01", "23", "24")  # live animals, feed, tobacco; alcohol (22.03-22.08) handled below


# ---------------------------------------------------------------- data

def hs_reference() -> pd.DataFrame:
    """UN Comtrade HS nomenclature (code, description, parent); downloaded once to data/raw/."""
    path = RAW / "hs_reference.json"
    if not path.exists():
        import requests
        r = requests.get(HS_URL, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    d = json.loads(path.read_text(encoding="utf-8-sig"))["results"]
    df = pd.DataFrame(d)[["id", "text", "parent"]]
    df["text"] = df.text.str.split(" - ", n=1).str[-1]
    return df.set_index("id")


def gold_table() -> pd.DataFrame:
    """One row per food HS6 subheading on any tariff list, with the hand-mapped CPI series (D18)."""
    hs = pd.read_csv(REF / "tariff_hs6_food.csv", dtype=str)
    hs = hs[~hs.chapter.isin(OUT_OF_SCOPE) & ~hs.hs6.str[:4].between("2203", "2208")]
    tmap = pd.read_csv(REF / "tariff_cpi_map.csv", dtype=str)
    links = [(r.event_id, h, r.cpi_product, r.exposure) for r in tmap.itertuples() for h in r.hs6.split(";")]
    links = pd.DataFrame(links, columns=["event_id", "hs6", "series", "exposure"])
    ref = hs_reference()
    rows = []
    for code, g in hs.groupby("hs6"):
        l = links[links.hs6 == code].assign(p=lambda d: d.exposure.map(PRIORITY)).sort_values("p")
        key = code.replace(".", "")
        rows.append({"hs6": code, "description": ref.text.get(key, ""), "heading": ref.text.get(key[:4], ""),
                     "events": ";".join(sorted(g.event_id.unique())),
                     "gold": l.series.iloc[0] if len(l) else "none",
                     "gold_exposure": l.exposure.iloc[0] if len(l) else "",
                     "gold_set": ";".join(sorted(set(l.series))) if len(l) else "none"})
    return pd.DataFrame(rows)


def cpi_candidates() -> pd.DataFrame:
    """Food CPI series bought in stores, with a text made of EN and FR labels and the parent series."""
    cat = pd.read_csv(PROC / "cpi_food_catalog.csv")
    restaurants = "Food purchased from restaurants"
    cat = cat[(cat["product"] != restaurants) & (cat.parent != restaurants) & (cat.depth >= 2)]
    clean = lambda s: str(s).split(" (2")[0]
    cat["text"] = [f"{clean(p)}. {clean(f)}. Category: {clean(par)}" for p, f, par in zip(cat["product"], cat.product_fr, cat.parent)]
    return cat[["product", "product_fr", "parent", "depth", "text"]].reset_index(drop=True)


def query_text(g: pd.DataFrame) -> list[str]:
    return [f"{d}. Heading: {h}" for d, h in zip(g.description, g.heading)]


# ---------------------------------------------------------------- rankers

def rank_tfidf(queries: list[str], cands: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import FeatureUnion

    vec = FeatureUnion([("w", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
                        ("c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True))])
    vec.fit(cands + queries)
    Q, C = vec.transform(queries), vec.transform(cands)
    Q = Q.multiply(1 / np.sqrt(Q.multiply(Q).sum(axis=1)))
    C = C.multiply(1 / np.sqrt(C.multiply(C).sum(axis=1)))
    return np.asarray((Q @ C.T).todense())


def rank_embeddings(queries: list[str], cands: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    q = model.encode(queries, normalize_embeddings=True, batch_size=32)
    c = model.encode(cands, normalize_embeddings=True, batch_size=32)
    return q @ c.T


def rank_hybrid(tfidf: np.ndarray, emb: np.ndarray, w_tfidf: float = 0.5) -> np.ndarray:
    """Lexical + semantic: average of row-standardised scores. Equal weights, fixed before looking at results."""
    z = lambda m: (m - m.mean(axis=1, keepdims=True)) / m.std(axis=1, keepdims=True)
    return w_tfidf * z(tfidf) + (1 - w_tfidf) * z(emb)


def rank_rrf(*scores: np.ndarray, k: int = 60) -> np.ndarray:
    """Reciprocal Rank Fusion [N4], row by row: sum of 1 / (k + rank)."""
    total = np.zeros_like(scores[0], dtype=float)
    for sc in scores:
        ranks = np.argsort(np.argsort(-sc, axis=1), axis=1) + 1
        total += 1.0 / (k + ranks)
    return total


# ---------------------------------------------------------------- statistics

def bootstrap_ci(hits: np.ndarray, n: int = 5000, seed: int = 20261014) -> tuple[float, float]:
    """95% percentile bootstrap interval of a proportion over lines [N8]."""
    rng = np.random.default_rng(seed)
    m = hits[rng.integers(0, len(hits), size=(n, len(hits)))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def mcnemar_exact(a: np.ndarray, b: np.ndarray) -> float:
    """Exact McNemar test [N9] on paired successes: two-sided binomial test on the discordant pairs."""
    from scipy.stats import binomtest
    b01, b10 = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return 1.0 if b01 + b10 == 0 else float(binomtest(b01, b01 + b10, 0.5).pvalue)


# ---------------------------------------------------------------- LLM step (optional)

def llm_choose(description: str, heading: str, candidates: list[str]) -> dict:
    """Claude picks one candidate or 'none' and an exposure type; the JSON schema restricts the choice."""
    import anthropic

    client = anthropic.Anthropic(max_retries=2, timeout=60.0)
    schema = {"type": "object", "additionalProperties": False, "required": ["series", "exposure", "reason"],
              "properties": {"series": {"type": "string", "enum": candidates + ["none"]},
                             "exposure": {"type": "string", "enum": ["direct", "partial", "input", "none"]},
                             "reason": {"type": "string"}}}
    prompt = (f"A Canadian counter-tariff applies to this customs subheading:\n{description}\n(heading: {heading})\n\n"
              "Which Statistics Canada consumer price index (CPI) series prices this product for households? "
              "Choose one of the candidate series, or 'none' if the product is not a consumer food sold in stores. "
              "Exposure: 'direct' if the product is a main retail item of that series, 'partial' if it is a small or "
              "uncertain part, 'input' if it is mainly an ingredient. Reason in one short sentence.\n\nCandidates:\n- "
              + "\n- ".join(candidates))
    response = client.beta.messages.create(
        model=LLM_MODEL, max_tokens=2000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}])
    if response.stop_reason == "refusal":
        return {"series": "none", "exposure": "none", "reason": "refused"}
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ---------------------------------------------------------------- evaluation

def lineage_ok(pred: str, gold: str, parent: dict) -> bool:
    """Lenient match: same series, or direct parent/child (one level apart)."""
    return pred == gold or parent.get(pred) == gold or parent.get(gold) == pred


def evaluate(scores: np.ndarray, gold: pd.DataFrame, cands: pd.DataFrame, k: int = 5) -> tuple[dict, pd.DataFrame]:
    names = cands["product"].tolist()
    parent = dict(zip(cands["product"], cands.parent))
    order = np.argsort(-scores, axis=1)
    rows = []
    for i, r in enumerate(gold.itertuples()):
        ranked = [names[j] for j in order[i]]
        golds = set(r.gold_set.split(";"))
        strict_rank = next((n + 1 for n, s in enumerate(ranked) if s in golds), None)
        lenient_rank = next((n + 1 for n, s in enumerate(ranked) if any(lineage_ok(s, g, parent) for g in golds)), None)
        rows.append({"hs6": r.hs6, "gold": r.gold, "top1": ranked[0], "top5": " | ".join(ranked[:k]),
                     "rank_strict": strict_rank, "rank_lenient": lenient_rank})
    res = pd.DataFrame(rows)
    m = {"n": len(res),
         "top1_strict": float((res.rank_strict == 1).mean()), "top1_lenient": float((res.rank_lenient == 1).mean()),
         f"recall@{k}_strict": float((res.rank_strict <= k).mean()), f"recall@{k}_lenient": float((res.rank_lenient <= k).mean()),
         "mrr_strict": float((1 / res.rank_strict.fillna(np.inf)).mean())}
    return m, res


def run(use_llm: bool | None = None) -> dict:
    gold = gold_table()
    labelled = gold[gold.gold != "none"].reset_index(drop=True)
    cands = cpi_candidates()
    q, c = query_text(labelled), cands.text.tolist()
    scores = {"tfidf": rank_tfidf(q, c), "embeddings": rank_embeddings(q, c)}
    scores["hybrid"] = rank_hybrid(scores["tfidf"], scores["embeddings"])
    scores["rrf"] = rank_rrf(scores["tfidf"], scores["embeddings"])
    out = {name: evaluate(sc, labelled, cands) for name, sc in scores.items()}
    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY")) if use_llm is None else use_llm
    if use_llm:
        res = out["hybrid"][1].copy()  # the LLM chooses among the 5 hybrid candidates
        parent = dict(zip(cands["product"], cands.parent))
        picks = [llm_choose(r.description, r.heading, t5.split(" | "))
                 for r, t5 in zip(labelled.itertuples(), res.top5)]
        res["llm"] = [p["series"] for p in picks]
        res["llm_exposure"] = [p["exposure"] for p in picks]
        golds = [set(s.split(";")) for s in labelled.gold_set]
        out["llm"] = ({"n": len(res), "top1_strict": float(np.mean([p in g for p, g in zip(res.llm, golds)])),
                       "top1_lenient": float(np.mean([any(lineage_ok(p, x, parent) for x in g) for p, g in zip(res.llm, golds)]))}, res)
    return {"gold": gold, "labelled": labelled, "candidates": cands, "scores": scores, "results": out}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = run()
    for k, (m, _) in r["results"].items():
        print(k, {a: round(b, 3) if isinstance(b, float) else b for a, b in m.items()})
