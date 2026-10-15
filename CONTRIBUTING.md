# Contributing — Canadian Grocery Prices & Tariffs

## Project in one paragraph
Portfolio project by David Doe (data science student, University of Lille; MSc SIAD). Question: how much do Canadian counter-tariffs raise grocery prices, how fast, and for how long? Four parts: (1) price tracker, (2) causal estimate of tariff pass-through, (3) 6–12 month forecasts with conformal intervals, (4) bilingual EN/FR assistant with measured accuracy. Deployed app at the end.

## Working rules
- **Every decision must be justified by a source.** Add or update an entry in BOTH `docs/fr/journal-decisions.md` and `docs/en/decision-log.md` (same D-number, same content), and cite references from `docs/references.md` (R/S/L/M/F/A/C ids). New sources go in `docs/references.md` in APA 7 marked `verified` (checked online) or `to check` (DOI to double-check). No emojis in any deliverable: sober, minimalist style (D24).
- **Bilingual deliverables.** README, app text, assistant and reports exist in English and French. English is primary for code, comments and commit messages.
- **Positioning (D02).** Do not present the 2025 tariff effect as a discovery: the Bank of Canada already measured it (≈25% pass-through, temporary: R1/R2; 2018 food ≈70%, persistent: R3). Our value = public-data replication + food focus + the September 2026 tariffs.
- **Causal work uses CPI sub-indices (table 18-10-0004-01)**, never the average-price table 18-10-0245-01, which StatCan says does not measure pure price change (D03). Average prices are for the dashboard only, with a January 2024 break flag (D04).
- **Forecast evaluation:** seasonal naive baseline first, rolling-origin validation only, MASE/sMAPE (D08). No random CV on time series.
- Raw data stays out of git (`data/raw/` is ignored). Tariff dates live in `data/reference/tariff_events.csv`.

## Layout
```
src/fetch_data.py              download StatCan tables + Bank of Canada USD/CAD (spliced, D15)
src/load_data.py               read raw files (EN "," / FR ";"), EN/FR labels by VECTOR (D16)
src/cpi_catalog.py             food CPI hierarchy, coverage, usability per episode (D17)
src/tariff_map.py              treated / placebo / control role of each CPI series per episode (D18)
src/causal/synth.py            synthetic control, permutation p-values, 2x2 and event-study DiD (D19)
src/causal/exposure.py         US import exposure per series, continuous-treatment DiD = pass-through (D21)
src/fetch_trade.py             UN Comtrade imports by HS6 (US, world) -> data/raw/comtrade_imports.csv
src/fetch_commodities.py       World Bank Pink Sheet monthly prices -> data/raw/commodity_prices_monthly.csv
src/causal/commodity.py        world-price adjustment of commodity-linked series (D22)
src/forecast/models.py         seasonal naive, ETS, LightGBM, backtest, conformal intervals (D23)
src/refresh.py                 monthly one-command update (D25)
src/build_app_data.py          small data bundle for the app (D24)
src/monitor/tariff_watch.py    2026 tariff watch from the frozen pre-tariff forecast, backtest on 2018/2025 (D33)
app/                           bilingual Streamlit app, verified-answer FAQ (D24)
tests/                         pytest checks (D25)
notebooks/01_cpi_food_coverage.ipynb   step 2 results
notebooks/02_tariff_cpi_mapping.ipynb  step 3 results
notebooks/03_replication_2018_2025.ipynb  step 4 results (D20)
notebooks/04_pass_through_exposure.ipynb  step 4a results (D21)
notebooks/05_commodity_prices.ipynb       step 4b results (D22)
notebooks/06_forecasts.ipynb              step 5 results (D23)
data/reference/                hand-curated, versioned reference files
data/raw/, data/processed/     generated, not committed
docs/fr/journal-decisions.md   decision log (FR)
docs/en/decision-log.md        decision log (EN)
docs/references.md             bibliography (annex)
```


## Commands
```bash
pip install -r requirements.txt
python src/fetch_data.py            # EN tables -> data/raw/
python src/fetch_data.py --lang fr  # FR tables
python src/fetch_trade.py           # UN Comtrade imports (D21)
python src/fetch_commodities.py     # World Bank commodity prices (D22)
```

## Status (2026-10-14)
Done: D01–D34 (NLP classification D29, RAG D30 paused by D32, SQL and CI D31). Data, catalogue, tariff mapping, 2018/2025 replication, pass-through with exposure, world-price control, forecasts with conformal intervals, bilingual app, monthly refresh, tests, verified references, one-page summary.

Positioning (D02 update): a transparent public-data monitor, not a new estimate. Headline: 2025 pass-through ~40% [−7%; 86%] once world prices are removed (consistent with the Bank of Canada ~25%); coffee is a world-price story; 2026 "dairy" tariffs hit ingredients, cheese at most +0.6 point; forecasts Food +3.5% in 2026.

Never overwrite `data/reference/forecast_vintage_2026-08.csv`: it is the pre-tariff 2026 counterfactual (D33).

Monthly routine: after each CPI release, `python src/refresh.py`, then `pytest -q`, then commit `app/data/` and `git push` (the deployed app reads `app/data/` from GitHub).

## Next steps
1. ~~Deploy the app~~: online at https://canada-grocery-prices.streamlit.app/ (Streamlit Community Cloud, main file `app/streamlit_app.py`, redeploys on each push).
2. Future work (D34): run the assistant evaluation once an ANTHROPIC_API_KEY is available (`python src/eval_assistant.py`), publish its accuracy in D28, then add the key to the Streamlit secrets.
3. Future work (D34), with an API key: run the LLM step of `src/nlp/hs_cpi_classifier.py` and publish it in D29. The RAG is removed from the app (D32, A35; secret `RAG`=on shows it again) until the held-out answer key reaches 80% per language; it is at 79% (EN 100%, FR 56%, A33). Next RAG fix: translate French queries before BM25.
4. A third RAG question set (the held-out set of A33 was used to pick BM25), Mondrian conformal intervals (D31), synthetic DiD (M4), 8-digit trade data.
