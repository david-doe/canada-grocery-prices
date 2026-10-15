"""Optional AI assistant: answers in the user's own words, only from this app's verified facts (D28).

How it works, in one sentence: one call to Claude with a fixed set of facts built from app/data/ and the
verified FAQ, and the instruction to answer only from those facts, cite the decision numbers, and say so
when the answer is not in them. It is enabled only when an ANTHROPIC_API_KEY is configured (Streamlit
secrets or environment); otherwise the app keeps the fixed-answer FAQ. Its accuracy is measured on a
bilingual question set (data/reference/assistant_eval.csv, src/eval_assistant.py).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
MODEL = "claude-opus-5-5"
MAX_QUESTION_CHARS = 500

SYSTEM_RULES = """You are the assistant of a public dashboard on Canadian grocery prices and counter-tariffs, \
written by David Doe, a data science student at the University of Lille.

Rules:
- Answer ONLY from the FACTS below. Do not use outside knowledge, even if you think you know the answer.
- If the facts do not contain the answer, say so plainly in one sentence and suggest a tab of the dashboard \
or a related question the facts can answer. Never guess a number.
- Answer in the language of the question (English or French). Use 2 to 6 short sentences, plain words, no jargon, \
no emojis, no headings.
- When you use a number, keep its uncertainty (range or interval) if the facts give one.
- End with the decision numbers you relied on, in parentheses, for example (D21, D22).
- These are statistical estimates for an average household, not advice."""


def secret(name: str) -> str | None:
    """A setting from the Streamlit secrets (Community Cloud: app settings > Secrets), else the environment."""
    try:
        import streamlit as st
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name)


def api_key() -> str | None:
    return secret("ANTHROPIC_API_KEY")


def build_facts() -> str:
    """A compact, deterministic text of everything the assistant may use (sorted, no timestamps: cache-friendly)."""
    from faq import FAQ

    notes = json.loads((DATA / "monthly_notes.json").read_text(encoding="utf-8"))
    cost = pd.read_csv(DATA / "tariff_cost.csv").set_index("event_id")
    ptc = pd.read_csv(DATA / "pass_through_commodity.csv")
    sc = pd.read_csv(DATA / "sc_results.csv")
    lookup = pd.read_csv(DATA / "tariff_lookup.csv")
    prov = pd.read_csv(DATA / "province_food.csv")
    fc = pd.read_csv(DATA / "forecasts.csv")
    cpi = pd.read_csv(DATA / "cpi_food.csv")

    lines = ["## Latest data", json.dumps(notes, ensure_ascii=False, sort_keys=True)]
    c25, c26 = cost.loc["CA2025"], cost.loc["CA2026"]
    lines += ["## Household cost (D26)",
              f"2025 tariffs (March 4 to August 31, 2025): cost per 100 dollars of groceries = 100 x {c25.rate:.2f} x pass-through "
              f"{c25.pt_central:.2f} (range {c25.pt_low:.2f}-{c25.pt_high:.2f}) x share of food spending on tariffed US goods "
              f"{c25.share_central:.3f} (range {c25.share_low:.3f}-{c25.share_high:.3f}) = "
              f"{100 * c25.rate * c25.pt_central * c25.share_central:.2f} dollars (range {100 * c25.rate * c25.pt_low * c25.share_low:.2f}-"
              f"{100 * c25.rate * c25.pt_high * c25.share_high:.2f}).",
              f"2026 tariffs (from September 8, 2026, scenarios only, no measured data yet): import-weighted rate {c26.rate:.2f}, "
              f"share of food spending {c26.share_central:.4f}, pass-through scenarios 0.25 / 0.60 / 0.70."]
    lines += ["## Pass-through estimates (D21, D22)"] + [
        f"{r.event_id} | {r.sample} | {r.outcome} | pass-through {r.pass_through:.2f} [95% CI {r.lo:.2f}; {r.hi:.2f}] p={r.p:.2f}"
        for r in ptc.sort_values(["event_id", "sample", "outcome"]).itertuples()]
    lines += ["## Synthetic-control effect per series during the tariff months, in % (D19, D20)"] + [
        f"{r.event_id} | {r.group} | {r.series} | {r.effect_during:+.1f}% | p={r.p_value:.2f}"
        for r in sc.sort_values(["event_id", "group", "series"]).itertuples()]
    lines += ["## Products on the tariff lists, mapped to CPI series (D18)"] + [
        f"{r.event_id} ({r.start} to {r.end if isinstance(r.end, str) else 'in force'}) | rate {r.rate} | {r.exposure} | "
        f"{r.series} / {r.series_fr} | {r.note_en}" for r in lookup.itertuples()]
    last = prov.month.max()
    lines += [f"## Store-food CPI, 12-month change by province, {last} (D13)"] + [
        f"{r.geo}: {r.yoy:+.1f}%" for r in prov[prov.month == last].sort_values("geo").itertuples()]
    key = ["Food", "Food purchased from stores", "Food purchased from restaurants", "Cheese", "Fresh milk", "Butter",
           "Eggs", "Fresh or frozen beef", "Fresh or frozen chicken", "Fresh vegetables", "Fresh fruit",
           "Roasted or ground coffee (2013=100)", "Bakery products", "Fruit juices"]
    lines.append("## 12-month forecasts with 80% intervals (D23)")
    for s in key:
        f, h = fc[fc.series == s], cpi[cpi.series == s]
        if len(f) and len(h):
            last_v, f12 = h.value.iloc[-1], f.iloc[-1]
            lines.append(f"{s}: {100 * (f12.forecast / last_v - 1):+.1f}% by {f12.month} "
                         f"(80% interval {100 * (f12.lo80 / last_v - 1):+.1f}% to {100 * (f12.hi80 / last_v - 1):+.1f}%); "
                         f"last 12 months {100 * (h.value.iloc[-1] / h.value.iloc[-13] - 1):+.1f}%")
    lines.append("## Verified answers (FAQ)")
    for it in FAQ:
        lines.append(f"Q: {it['q']['en']} | A: {it['a']['en']} | Source: {it['source']}")
    lines += ["## Context (D01, D02)",
              "Counter-tariff episodes: 2018 (10% surtax on some US food, July 1, 2018 to May 19, 2019), 2025 (25% on a broad range "
              "of US goods from March 4, 2025; food lines lifted on September 1, 2025), 2026 (from September 8, 2026, in response to a "
              "50% US tariff on C$27.6 billion of Canadian goods: cheese 25%, milk powders, whey, honey, molasses and bakery mixes 50%).",
              "Bank of Canada: about 25% pass-through in 2025, temporary (R1, R2); about 70% for food in 2018, persistent (R3); "
              "two thirds of the effect runs through input costs (R4). Canada's Food Price Report 2026: food prices +4% to +6% in 2026 (R5).",
              "This project: a transparent public-data monitor; it replicates the Bank of Canada orders of magnitude only roughly, "
              "because public monthly CPI series mix taxed and untaxed products (D20)."]
    return "\n".join(lines)


def ask(question: str, facts: str, lang: str = "en") -> tuple[str, dict]:
    """One answer. Returns (text, info) where info carries the stop reason and token usage for monitoring."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key(), max_retries=2, timeout=60.0)
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=2000,  # answers are 2-6 sentences
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},  # chat route; Claude Opus 5.5 defaults to medium
            system=[{"type": "text", "text": SYSTEM_RULES + "\n\nFACTS\n" + facts,
                     "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
            messages=[{"role": "user", "content": question[:MAX_QUESTION_CHARS]}],
        )
    except anthropic.RateLimitError:
        return ("The assistant is busy, please try again in a minute." if lang == "en"
                else "L'assistant est occupé, réessayez dans une minute."), {"error": "rate_limit"}
    except anthropic.APIStatusError as e:
        return ("The assistant is unavailable right now; the verified answers below still work." if lang == "en"
                else "L'assistant est indisponible pour le moment ; les réponses vérifiées ci-dessous restent disponibles."), {"error": f"status_{e.status_code}"}
    except anthropic.APIConnectionError:
        return ("The assistant could not be reached." if lang == "en" else "L'assistant n'a pas pu être joint."), {"error": "connection"}

    info = {"stop_reason": response.stop_reason, "input_tokens": response.usage.input_tokens,
            "cache_read": getattr(response.usage, "cache_read_input_tokens", 0), "output_tokens": response.usage.output_tokens}
    if response.stop_reason == "refusal":
        return ("This question cannot be answered here." if lang == "en" else "Cette question ne peut pas être traitée ici."), info
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    return text, info
