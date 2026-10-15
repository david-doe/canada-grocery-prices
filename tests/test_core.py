"""Fast checks that run without the raw data (only versioned files and synthetic inputs).

    pytest -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "causal"), str(ROOT / "src" / "forecast"), str(ROOT / "app")]


# ---------------- reference files (D18, D22)

def test_tariff_line_counts_match_official_lists():
    hs6 = pd.read_csv(ROOT / "data/reference/tariff_hs6_food.csv", dtype=str)
    counts = hs6.assign(n=hs6.n_lines.astype(int)).groupby("event_id").n.sum().to_dict()
    assert counts == {"CA2018": 25, "CA2025": 407, "CA2026": 66}


def test_every_mapped_hs6_is_on_its_episode_list():
    hs6 = pd.read_csv(ROOT / "data/reference/tariff_hs6_food.csv", dtype=str)
    listed = set(zip(hs6.event_id, hs6.hs6))
    tmap = pd.read_csv(ROOT / "data/reference/tariff_cpi_map.csv", dtype=str)
    missing = [(r.event_id, h) for r in tmap.itertuples() for h in r.hs6.split(";") if (r.event_id, h) not in listed]
    assert not missing


def test_mapping_values_are_valid():
    tmap = pd.read_csv(ROOT / "data/reference/tariff_cpi_map.csv", dtype=str)
    assert set(tmap.exposure) <= {"direct", "partial", "input", "over_quota_only"}
    assert set(tmap.confidence) <= {"high", "medium", "low"}
    assert not tmap.duplicated(["event_id", "cpi_product"]).any()
    assert tmap.note_fr.notna().all() and tmap.note_en.notna().all()


def test_tariff_events_dates():
    ev = pd.read_csv(ROOT / "data/reference/tariff_events.csv")
    row = ev.set_index("event_id")
    assert row.loc["CA2018", "end_date"] == "2019-05-19"   # repeal registered and in force (R9)
    assert row.loc["CA2026", "start_date"] == "2026-09-08"


# ---------------- methods

def test_synthetic_control_weights_recover_a_known_mix():
    import synth
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 4)).cumsum(axis=0)
    y = X @ np.array([0.6, 0.4, 0.0, 0.0])
    w = synth.sc_weights(y, X)
    assert w.min() >= 0 and abs(w.sum() - 1) < 1e-8
    assert np.allclose(w, [0.6, 0.4, 0.0, 0.0], atol=0.02)


def test_finest_drops_parents_when_a_child_is_present():
    import synth
    parent = {"Cheese": "Dairy products", "Cheddar": "Cheese", "Dairy products": "Food"}
    assert synth.finest(["Dairy products", "Cheese", "Cheddar", "Eggs"], parent) == ["Cheddar", "Eggs"]


def test_episode_windows_stop_before_covid():
    import synth
    w = synth.EPISODES["CA2018"].windows(pd.Period("2026-08", "M"))
    assert w["pre"] == (pd.Period("2013-07", "M"), pd.Period("2018-06", "M"))
    assert w["after"][1] == pd.Period("2020-02", "M")


def test_conformal_quantile_has_finite_sample_correction():
    import models
    bt = pd.DataFrame({"model": "m", "h": 1, "log_err": np.linspace(-1, 1, 19)})
    q = models.conformal_quantiles(bt).iloc[0]
    # n = 19: the 80% quantile is the ceil(20 * 0.8) = 16th smallest |error|
    e = np.sort(np.abs(np.linspace(-1, 1, 19)))
    assert q.q80 == pytest.approx(e[15])


def test_seasonal_naive_repeats_last_year():
    import models
    idx = pd.period_range("2020-01", "2022-12", freq="M")
    y = pd.Series(np.arange(len(idx), dtype=float), index=idx)
    f = models.seasonal_naive(y, pd.Period("2022-12", "M"))
    assert list(f) == list(y.loc["2022-01":"2022-12"])


# ---------------- app and style (D24)

def test_faq_answers_are_bilingual_and_sourced():
    from faq import FAQ
    for item in FAQ:
        assert item["q"]["en"] and item["q"]["fr"] and item["a"]["en"] and item["a"]["fr"] and item["source"]
        assert all(len(k) >= 4 for k in item["keywords"])


def test_app_data_bundle_is_present_and_small():
    files = list((ROOT / "app/data").glob("*.csv"))
    assert {f.name for f in files} >= {"cpi_food.csv", "forecasts.csv", "sc_results.csv", "pass_through_commodity.csv"}
    assert sum(f.stat().st_size for f in files) < 10e6


def test_no_emojis_in_deliverables():
    emoji = re.compile(r"[\U0001F300-\U0001FAFF☀-➿⭐]")
    paths = [*ROOT.glob("*.md"), *ROOT.glob("docs/**/*.md"), *ROOT.glob("app/*.py"), *ROOT.glob("src/**/*.py")]
    offenders = [str(p.relative_to(ROOT)) for p in paths if emoji.search(p.read_text(encoding="utf-8"))]
    assert not offenders


# ---------------- public features (D26)

def test_tariff_cost_inputs_are_coherent():
    cost = pd.read_csv(ROOT / "app/data/tariff_cost.csv").set_index("event_id")
    c25 = cost.loc["CA2025"]
    assert 0 < c25.share_low <= c25.share_central <= c25.share_high < 0.2
    assert 0 <= c25.pt_low <= c25.pt_central <= c25.pt_high <= 1
    # about 50 cents per 100 dollars of groceries in 2025 (D26)
    assert 0.3 < 100 * c25.rate * c25.pt_central * c25.share_central < 0.8


def test_product_lookup_finds_products_in_both_languages():
    import unicodedata
    lookup = pd.read_csv(ROOT / "app/data/tariff_lookup.csv")
    fold = lambda s: "".join(ch for ch in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(ch) != "Mn")
    text = lookup.apply(lambda r: fold(" ".join(map(str, [r.series, r.series_fr, r.note_en, r.note_fr]))), axis=1)
    for word, events in [("orange", {"CA2018", "CA2025"}), ("fromage", {"CA2026"}), ("coffee", {"CA2018", "CA2025"})]:
        assert events <= set(lookup[text.str.contains(word)].event_id)


# ---------------- context, monthly note, sharing, assistant (D27, D28)

def test_monthly_note_is_complete():
    import json
    n = json.loads((ROOT / "app/data/monthly_notes.json").read_text(encoding="utf-8"))
    assert {"month", "stores_yoy", "stores_yoy_prev", "top_up", "top_down", "province_high", "province_low", "forecast_12m"} <= set(n)
    assert len(n["top_up"]) == 3 and all(i["en"] and i["fr"] for i in n["top_up"] + n["top_down"])
    assert (ROOT / "app/data/share_card_en.png").exists() and (ROOT / "app/data/share_card_fr.png").exists()


def test_basket_matches_the_aggregate_cost():
    b = pd.read_csv(ROOT / "app/data/basket_2025.csv")
    cost = pd.read_csv(ROOT / "app/data/tariff_cost.csv").set_index("event_id").loc["CA2025"]
    basket_share = (b.spend_share * b.exposure).sum()           # tariffed US goods per dollar of food spending
    assert abs(basket_share - cost.share_central) / cost.share_central < 0.10


def test_basket_2026_adds_up_to_the_published_cost():
    b = pd.read_csv(ROOT / "app/data/basket_2026.csv")
    cost = pd.read_csv(ROOT / "app/data/tariff_cost.csv").set_index("event_id").loc["CA2026"]
    assert abs(b.share.sum() - cost.share_central) < 1e-9                      # same lines, same denominator
    assert abs((b.share * b.rate).sum() - cost.share_central * cost.rate) < 1e-9  # same import-weighted rate
    assert list(b.group[~b.upper_bound]) == ["Cheese"]                         # the only product taxed as sold


def test_assistant_facts_are_deterministic_and_contain_key_numbers():
    import assistant
    f1, f2 = assistant.build_facts(), assistant.build_facts()
    assert f1 == f2                                              # stable prefix: prompt caching works
    for needle in ["0.52", "0.39", "D26", "Whitehorse", "cheese", "R1, R2"]:
        assert needle in f1
    assert 10_000 < len(f1) < 60_000


def test_eval_grading_rules():
    import eval_assistant as ev
    assert ev.grade("About 0,52 $ per 100 dollars (D26).", "0.52|0,52;D26", False)
    assert not ev.grade("About 52 dollars.", "0.52|0,52;D26", False)
    assert ev.grade("Les faits de ce tableau de bord ne couvrent pas cette question.", "", True)
    assert not ev.grade("It will be 70,000 dollars.", "", True)


# ---------------- SQL warehouse, retrieval and NLP building blocks (D29-D31)

def test_sql_queries_run_and_answer():
    sys.path.insert(0, str(ROOT / "src" / "sql"))
    import warehouse
    res = warehouse.run_queries(warehouse.build(":memory:"))
    assert len(res) >= 5 and all(len(df) > 0 for df in res.values())
    prov = res["02_province_ranking"]
    assert prov.rank_highest.min() == 1 and "Canada" not in set(prov.geo)


def test_bm25_and_rrf_on_toy_examples():
    import rag
    bm = rag.BM25([["cheese", "tariff"], ["milk", "powder"], ["cheese", "cheese", "price"]])
    s = bm.scores(["cheese"])
    assert s[1] == 0 and s[0] > 0 and s[2] > 0
    fused = rag.rrf(np.array([3.0, 2.0, 1.0]), np.array([1.0, 3.0, 2.0]))
    assert fused.argmax() == 1          # 2nd and 1st beats 1st and 3rd


def test_passages_do_not_start_mid_word():
    import rag
    sys.path.insert(0, str(ROOT / "src" / "rag"))
    import build_corpus as B
    assert rag.clean_start("ement of the index. The price rose.") == "The price rose."
    assert rag.clean_start("gning a product to a code") == "... a product to a code"
    assert rag.clean_start("The CPI is a fixed basket.") == "The CPI is a fixed basket."
    shown = rag.corpus().text.map(rag.clean_start)
    assert not shown.str.match(r"^[a-z]").any()          # was 81% of the passages before A29
    text = "\n\n".join(f"Paragraph {i} says that prices rose by {i} percent in that month. It ended." for i in range(60))
    parts = B.chunks(text)
    assert len(parts) > 3 and all(re.match(r"^[A-Z]", c) for c in parts)


def test_answer_follows_the_language_of_the_question():
    import rag
    ev = pd.read_csv(ROOT / "data/reference/rag_eval.csv", dtype=str)
    assert all(rag.question_lang(q, "xx") == lang for q, lang in zip(ev.question, ev.lang))
    assert rag.question_lang("Quel est l'effet des tarifs ?", "en") == "fr"
    passages = rag.corpus().head(2)
    system, user = rag.prompt("Pourquoi le fromage a-t-il augmenté ?", passages, "fr")
    assert "Write the whole answer in French" in system and user.endswith("Answer in French.")


def test_answer_provider_choice_and_fallbacks(monkeypatch):
    import rag
    for name in ("RAG_PROVIDER", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert rag.provider() is None
    monkeypatch.delenv("RAG", raising=False)
    assert not rag.enabled()                              # RAG paused by default (D32)
    monkeypatch.setenv("RAG", "on")
    assert rag.enabled()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert rag.provider() == "anthropic"
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert rag.provider() == "gemini"                     # free tier first
    monkeypatch.setenv("RAG_PROVIDER", "anthropic")
    assert rag.provider() == "anthropic"
    passages = rag.corpus().head(2)
    monkeypatch.setattr(rag, "generate", lambda system, user, name: ("", "error"))
    assert rag.answer("Quel est l'effet des tarifs ?", passages, "en").startswith("La réponse n'a pas pu")
    monkeypatch.setattr(rag, "generate", lambda system, user, name: ("Texte [R1-000].", "ok"))
    assert rag.answer("Quel est l'effet des tarifs ?", passages, "en") == "Texte [R1-000]."


def test_gemini_request_shape(monkeypatch):
    import types as pytypes
    import rag
    seen = {}

    class Models:
        def generate_content(self, model, contents, config):
            seen.update(model=model, contents=contents, config=config)
            return pytypes.SimpleNamespace(text=" Réponse [R1-000]. ", prompt_feedback=None)

    class Client:
        def __init__(self, api_key, http_options=None):
            seen.update(key=api_key, http=http_options)
            self.models = Models()

    genai = pytypes.ModuleType("google.genai")
    genai.Client = Client
    genai.types = pytypes.SimpleNamespace(GenerateContentConfig=lambda **kw: kw, HttpOptions=lambda **kw: kw,
                                          HttpRetryOptions=lambda **kw: kw)
    google = pytypes.ModuleType("google")
    google.genai = genai
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", genai.types)
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert rag.generate("SYS", "USER", "gemini") == ("Réponse [R1-000].", "ok")
    assert seen["key"] == "g" and seen["model"] == rag.GEMINI_MODEL and seen["contents"] == "USER"
    assert seen["config"]["system_instruction"] == "SYS"
    assert set(seen["http"]["retry_options"]["http_status_codes"]) == {429, 503}  # free-tier quota and overload


def test_ndcg_and_bootstrap():
    sys.path.insert(0, str(ROOT / "src" / "rag"))
    import eval_rag
    assert eval_rag.ndcg(["a", "b", "c"], {"a"}) == pytest.approx(1.0)
    assert eval_rag.ndcg(["x", "a"], {"a"}) == pytest.approx(1 / np.log2(3))
    lo, hi = eval_rag.bootstrap_ci(np.array([0.0, 1.0] * 20))
    assert lo < 0.5 < hi


def test_gold_labels_for_classification():
    sys.path.insert(0, str(ROOT / "src" / "nlp"))
    import hs_cpi_classifier as H
    if not (ROOT / "data/raw/hs_reference.json").exists():
        pytest.skip("HS nomenclature not downloaded")
    g = H.gold_table()
    assert len(g) == 151 and (g.gold != "none").sum() == 135


def test_answer_scoring_helpers():
    sys.path.insert(0, str(ROOT / "src" / "rag"))
    import eval_rag
    assert eval_rag.cited_ids("A [R4-003, R4-002]. B [S3-001].") == {"R4-003", "R4-002", "S3-001"}  # grouped form (A31)
    assert eval_rag.cited_ids("No citation [note].") == set()
    assert eval_rag.ABSTAIN.search("The provided passages do not contain information about this.")  # A32
    assert eval_rag.ABSTAIN.search("Les passages fournis ne disent pas quand la surtaxe a été abrogée.")
    assert not eval_rag.ABSTAIN.search("The surtax rate was 10% [R10-001].")


def test_answer_key_matching():
    sys.path.insert(0, str(ROOT / "src" / "rag"))
    import eval_rag
    assert eval_rag.has_answer("Prices rose about 6% [R1-003].", "6%|6 %")
    assert eval_rag.has_answer("Une hausse d'environ 3,5 % est prévue.", "3,5|3.5")
    assert not eval_rag.has_answer("The rate was 16% in 2025.", "6%")      # 6% inside 16% is not the answer
    assert not eval_rag.has_answer("See [R1-025].", "25")                   # citations are ignored
    assert eval_rag.has_answer("Le 1er juillet 2018.", "1er juillet 2018")
    ev = pd.read_csv(ROOT / "data/reference/rag_eval_holdout.csv", dtype=str)
    assert ev.id.is_unique and set(ev.lang) == {"en", "fr"} and ev.answer_terms.notna().all()
    assert eval_rag.has_answer("Un taux de 50 pour cent [SUM-FR-003].", "50 %|50%")   # A33: percent written out


def test_tariff_watch_rule():
    sys.path.insert(0, str(ROOT / "src" / "monitor"))
    import tariff_watch as tw
    fc = pd.DataFrame({"series": ["A", "B", "C"], "month": "2026-09", "h": 1, "forecast": 100.0,
                       "lo80": 97.0, "hi80": 103.0, "lo95": 95.0, "hi95": 105.0})
    cpi = pd.DataFrame({"series": ["A", "B", "C"], "month": "2026-09", "value": [106.0, 104.0, 100.0]})
    w = tw.watch(cpi, fc, {"A"})
    assert dict(zip(w.series, w.status)) == {"A": "above 95%", "B": "above 80%", "C": "within"}
    s = tw.summary(w).iloc[0]
    assert s.tariffed_above == 1 and s.untaxed_above == 1 and 0 < s.p_value <= 1
    assert tw.watch(cpi.assign(month="2026-08"), fc, {"A"}).empty           # no month after the vintage yet
    assert "Cheese" in tw.tariffed("CA2026")
    v = pd.read_csv(ROOT / "data/reference/forecast_vintage_2026-08.csv")
    assert v.month.min() == "2026-09" and v.series.nunique() == 101           # frozen before the 2026 tariffs (D33)
