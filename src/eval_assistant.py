"""Measure the accuracy of the optional AI assistant on a fixed bilingual question set (D28).

    ANTHROPIC_API_KEY=... python src/eval_assistant.py

Grading is deliberately simple and explainable:
- answerable questions pass when every required group in `must_include` is found in the answer
  (groups separated by ";", alternatives by "|", case- and accent-insensitive);
- out-of-scope questions (`expect_decline`) pass when the answer says the facts do not cover it
  and gives no number.
Each run calls the API once per question (20 calls, about 5,000 cached input tokens each).
Results: data/processed/assistant_eval_results.csv and a summary printed by language.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import assistant as A  # noqa: E402

DECLINE_CUES = ["not in", "do not contain", "don't contain", "doesn't cover", "does not cover", "cannot answer", "can't answer",
                "no information", "not cover", "outside", "pas dans", "ne contiennent pas", "ne couvrent pas", "ne permet pas",
                "pas d'information", "hors du champ", "ne peux pas", "ne sais pas", "don't know", "do not know"]


def fold(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(ch) != "Mn")


def grade(answer: str, must_include: str, expect_decline: bool) -> bool:
    a = fold(answer)
    if expect_decline:
        return any(fold(c) in a for c in DECLINE_CUES) and not re.search(r"\d+[.,]?\d*\s?(\$|%|dollars?)", a)
    groups = [g for g in str(must_include).split(";") if g and g != "nan"]
    return all(any(fold(alt) in a for alt in g.split("|")) for g in groups)


def main() -> None:
    if not A.api_key():
        sys.exit("Set ANTHROPIC_API_KEY to run the evaluation.")
    ev = pd.read_csv(ROOT / "data/reference/assistant_eval.csv", dtype=str, keep_default_na=False)
    facts = A.build_facts()
    rows = []
    for r in ev.itertuples():
        answer, info = A.ask(r.question, facts, r.lang)
        ok = grade(answer, r.must_include, r.expect_decline == "True")
        rows.append({"id": r.id, "lang": r.lang, "pass": ok, "answer": answer, **info})
        print(f"{r.id} {'PASS' if ok else 'FAIL'}")
    res = pd.DataFrame(rows)
    out = ROOT / "data/processed/assistant_eval_results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, index=False)
    print(res.groupby("lang")["pass"].agg(["mean", "count"]).round(2))
    print(f"Overall accuracy: {res['pass'].mean():.0%} on {len(res)} questions -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
