"""Evaluate retrieval (always) and generated answers (with GEMINI_API_KEY and/or ANTHROPIC_API_KEY) for the RAG feature (D30).

    python src/rag/eval_rag.py                  # development set (16 questions, used to revise the prompt)
    python src/rag/eval_rag.py --set holdout    # held-out set (34 questions with an answer key, A33)

Relevance: a passage is relevant to a question of data/reference/rag_eval.csv when it comes from a gold
document AND contains one of the expected keywords (binary relevance judgements, as in TREC-style evaluation).
Metrics, per configuration:
- recall@k (k = 1, 3, 5): a relevant passage is among the top k;
- MRR: mean of 1 / rank of the first relevant passage;
- nDCG@5 [N7]: discounted cumulative gain of the top 5, normalised by the best possible ordering.
Uncertainty: 95% percentile bootstrap intervals over questions (5,000 resamples) [N8], because 16 questions
give wide intervals. Comparison: a paired sign-flip randomization test on per-question reciprocal ranks,
two-sided, 10,000 draws.
Answers (optional, per provider with a key): share of answers citing a passage, share written in the language of
the question, and numeric grounding (numbers in the answer found in the cited passages), a simple proxy for
faithfulness [A2]. With both keys, the two providers answer the same questions and are compared with the paired test.
"""
from __future__ import annotations

import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))
import rag  # noqa: E402

KS = (1, 3, 5)
CONFIGS = [("bm25", True), ("embeddings", True), ("rrf", False), ("rrf", True), ("rrf+rerank", True)]
RNG = np.random.default_rng(20261014)
GEMINI_PAUSE = 13  # seconds between Gemini calls: the free tier allows about 5 requests per minute (A31)


def fold(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(ch) != "Mn")


def relevant_ids(gold_docs: set[str], keywords: list[str]) -> set[str]:
    c = rag.corpus()
    mask = c.doc_id.isin(gold_docs) & c.text.map(lambda t: any(fold(k) in fold(t) for k in keywords))
    return set(c.chunk_id[mask])


def ndcg(ranked: list[str], rel: set[str], k: int = 5) -> float:
    dcg = sum(1 / np.log2(i + 2) for i, c in enumerate(ranked[:k]) if c in rel)
    ideal = sum(1 / np.log2(i + 2) for i in range(min(len(rel), k)))
    return dcg / ideal if ideal else 0.0


def evaluate_retrieval(ev: pd.DataFrame, k_max: int = 10) -> pd.DataFrame:
    rows = []
    for method, titled in CONFIGS:
        name = f"{method}{'' if titled else ' (no title)'}"
        for r in ev.itertuples():
            rel = relevant_ids(set(r.gold_docs.split("|")), r.keywords.split("|"))
            ranked = rag.search(r.question, k_max, method, titled).chunk_id.tolist()
            rank = next((i + 1 for i, c in enumerate(ranked) if c in rel), None)
            rows.append({"config": name, "id": r.id, "lang": r.lang, "rank": rank, "rr": 1 / rank if rank else 0.0,
                         "ndcg@5": ndcg(ranked, rel), "n_relevant": len(rel), "top3": " ".join(ranked[:3])})
    return pd.DataFrame(rows)


def bootstrap_ci(x: np.ndarray, n: int = 5000) -> tuple[float, float]:
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def summarise(res: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    def agg(g):
        out = {f"recall@{k}": float((g["rank"] <= k).mean()) for k in KS}
        out["mrr"] = float(g.rr.mean())
        out["mrr_ci"] = "[{:.2f}; {:.2f}]".format(*bootstrap_ci(g.rr.to_numpy()))
        out["ndcg@5"] = float(g["ndcg@5"].mean())
        out["n"] = len(g)
        return pd.Series(out)
    return res.groupby(by, sort=False).apply(agg, include_groups=False)


def paired_test(a: np.ndarray, b: np.ndarray, n: int = 10000) -> float:
    """Two-sided sign-flip randomization test of mean(a - b) = 0 on paired per-question scores."""
    d = a - b
    obs = abs(d.mean())
    flips = RNG.choice([-1, 1], size=(n, len(d)))
    return float((np.abs((flips * d).mean(axis=1)) >= obs - 1e-12).mean())


def cited_ids(text: str) -> set[str]:
    """Passage ids cited as [R3-018] or grouped as [R4-003, R4-002] (both forms occur in model answers, A31)."""
    ids = (c.strip() for group in re.findall(r"\[([^\]]+)\]", text) for c in group.split(","))
    return {c for c in ids if re.fullmatch(r"[A-Z0-9-]+-\d{3}", c)}


ABSTAIN = re.compile(r"(passages?|sources?)\b.{0,40}\b(do|does) not (answer|contain|provide|specify|state|mention|say)"
                     r"|ne (répondent|contiennent|fournissent|précisent|disent|mentionnent|indiquent) pas", re.I)


def has_answer(text: str, terms: str) -> bool:
    """True when the answer contains one of the answer-key terms (accent- and case-insensitive; a number must not be
    part of a longer number). The key lists accepted forms in English and French, checked by hand against the sources."""
    t = fold(re.sub(r"\[[^\]]+\]", "", text)).replace("\u00a0", " ").replace("\u202f", " ")
    t = re.sub(r"(\d)\s*(%|pour cent|per cent|percent)", r"\1 %", t)  # 50 pour cent, 50% and 50 % are the same answer
    terms = "|".join(re.sub(r"(\d)\s*(%|pour cent|per cent|percent)", r"\1 %", fold(k)) for k in terms.split("|"))
    return any(re.search(rf"(?<![\d.,]){re.escape(fold(k))}(?![\d])", t) for k in terms.split("|"))


def evaluate_answers(ev: pd.DataFrame, name: str, k: int = 5) -> pd.DataFrame:
    rows = []
    for i, r in enumerate(ev.itertuples()):
        if name == "gemini" and i:
            time.sleep(GEMINI_PAUSE)
        passages = rag.search(r.question, k, rag.APP_SEARCH)  # the app's retrieval (D30, A33)
        text = rag.answer(r.question, passages, r.lang, name)
        cited = cited_ids(text)
        source = " ".join(passages[passages.chunk_id.isin(cited)].text)
        nums = re.findall(r"\d+(?:[.,]\d+)?", re.sub(r"\[[^\]]+\]", "", text))  # numbers outside the citations
        grounded = [x for x in nums if x in source or x.replace(",", ".") in source]
        rel = relevant_ids(set(r.gold_docs.split("|")), r.keywords.split("|"))
        failed = text in rag.FALLBACKS.values()  # generation error or refusal: scored apart, not as a correct-language answer
        rows.append({"provider": name, "id": r.id, "lang": r.lang, "answer": text, "failed": failed, "cites": len(cited) > 0,
                     # abstention although a relevant passage was given: the model, not retrieval, missed (A32)
                     "abstains": bool(ABSTAIN.search(text)) and not cited,
                     "relevant_given": bool(rel & set(passages.chunk_id)),
                     "lang_ok": rag.question_lang(re.sub(r"\[[^\]]+\]", "", text), "?") == r.lang,
                     "numbers": len(nums), "grounded": len(grounded),
                     "correct": has_answer(text, r.answer_terms) if "answer_terms" in ev else None})
    return pd.DataFrame(rows)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["dev", "holdout"], default="dev")
    split = parser.parse_args().set
    ev = pd.read_csv(ROOT / f"data/reference/{'rag_eval' if split == 'dev' else 'rag_eval_holdout'}.csv", dtype=str)
    tag = "" if split == "dev" else "_holdout"
    empty = [r.id for r in ev.itertuples() if not relevant_ids(set(r.gold_docs.split("|")), r.keywords.split("|"))]
    assert not empty, f"No relevant passage in the corpus for: {empty}"
    res = evaluate_retrieval(ev)
    out = ROOT / "data/processed" / f"rag_eval_retrieval{tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)
    overall = summarise(res, ["config"])
    overall.to_csv(ROOT / "data/processed" / f"rag_eval_summary{tag}.csv")
    print(overall.round(3))
    print(summarise(res, ["config", "lang"]).round(3))
    rr = res.pivot(index="id", columns="config", values="rr")
    for a, b in [("rrf", "bm25"), ("rrf", "rrf (no title)"), ("rrf+rerank", "rrf")]:
        print(f"paired test MRR {a} vs {b}: diff {rr[a].mean() - rr[b].mean():+.3f}, p = {paired_test(rr[a].to_numpy(), rr[b].to_numpy()):.3f}")
    from assistant import secret
    names = [n for n, key in (("gemini", "GEMINI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")) if secret(key)]
    if names:
        ans = pd.concat([evaluate_answers(ev, n) for n in names])
        ans.to_csv(ROOT / "data/processed" / f"rag_eval_answers{tag}.csv", index=False)
        for n, g in ans.groupby("provider", sort=False):
            ok = g[~g.failed]
            print(f"{n}: {len(ok)}/{len(g)} answers generated; among them, citing a passage {ok.cites.mean():.0%}; "
                  f"in the question's language {ok.lang_ok.mean():.0%}; numeric grounding {ok.grounded.sum()}/{ok.numbers.sum()} "
                  f"numbers ({ok.grounded.sum() / max(ok.numbers.sum(), 1):.0%}); abstentions {ok.abstains.sum()}, of which "
                  f"false (a relevant passage was given) {(ok.abstains & ok.relevant_given).sum()}")
            if ok.correct.notna().any():  # answer key (held-out set, A33)
                for lang, part in [("all", ok)] + list(ok.groupby("lang")):
                    lo, hi = bootstrap_ci(part.correct.astype(float).to_numpy())
                    print(f"  answer key met ({lang}): {int(part.correct.sum())}/{len(part)} = {part.correct.mean():.0%} [{lo:.0%}; {hi:.0%}]")
        if len(names) == 2:
            wide = ans.pivot(index="id", columns="provider", values="cites").astype(float)
            print(f"paired test citation rate gemini vs anthropic: p = {paired_test(wide.gemini.to_numpy(), wide.anthropic.to_numpy()):.3f}")
    else:
        print("Answer evaluation skipped (no GEMINI_API_KEY or ANTHROPIC_API_KEY).")


if __name__ == "__main__":
    main()
