# Canadian Grocery Prices and Counter-Tariffs

*[Version française](README.fr.md)*

A transparent, public-data monitor of how Canadian counter-tariffs reach grocery prices: what was taxed, how much of it reached shelf prices, and where food prices are heading. Bilingual (EN/FR), updated monthly, every choice sourced.

**Live app: [https://canada-grocery-prices.streamlit.app/](https://canada-grocery-prices.streamlit.app/)** · **Results in one page: [docs/en/summary.md](docs/en/summary.md)**

## Key findings (data to August 2026)

1. **What it cost households**: about 50 cents per 100 dollars of groceries while the 2025 counter-tariffs applied (plausible range 0 to 1.60 dollars), about 0.5 point of the 1.8% rise in grocery prices over those months.
2. **Tariffed US goods are a small part of each grocery price index** (median 9% in 2025). Even full pass-through would move these indexes by about 3 points, close to the detection limit of monthly public data.
3. **2025 counter-tariffs: about 40% pass-through** (95% interval −7% to 86%) once world commodity prices are removed, consistent with the Bank of Canada's estimate of about 25%. The 2025 coffee surge came from world prices, not the tariff.
4. **2026 "dairy" tariffs mostly hit ingredients** (milk powders, whey). Fresh milk and butter are not on the list; the 25% tariff on cheese can add at most 0.6 point to the cheese price index.
5. **Forecasts**: food prices +3.5% in 2026 (Food Price Report: +4% to +6%), with intervals that covered 85–97% of past outcomes.

## Methods, in one sentence each

| Question | Method | Where |
|---|---|---|
| What was taxed? | Official tariff lists mapped to CPI series, with a confidence level per mapping | notebook 02, D18 |
| Did prices rise because of the tariff? | Compare each taxed series with a weighted mix of similar untaxed series (synthetic control), then before/after differences | notebooks 03–04, D19–D21 |
| Was it the tariff or world prices? | Remove the part explained by world commodity prices | notebook 05, D22 |
| Where are prices heading? | Simple and machine-learning forecasts, tested on 2019–2025, with intervals checked on past data | notebook 06, D23 |
| Can a new tariff list be mapped automatically? | NLP: TF-IDF, multilingual embeddings and rank fusion propose CPI series for each customs line, scored against the hand-made mapping | notebook 07, D29 |
| What do the official documents say? (in development, not in the app yet) | RAG: BM25, embeddings, rank fusion and cross-encoder re-ranking over 765 official passages, evaluated with recall@k, MRR, nDCG and a held-out answer key (79%, French questions weaker) | notebook 08, D30, D32 |
| Which categories drive the cost? | SQL on a DuckDB warehouse (CTEs, window functions) | `sql/`, D31 |

## App

Online at [https://canada-grocery-prices.streamlit.app/](https://canada-grocery-prices.streamlit.app/). A bilingual dashboard, light or dark, that starts with the context (what happened, why it matters, what this project adds), then shows what the tariffs cost a household (enter your own grocery spending), whether a product was taxed, food inflation by province, forecasts with intervals, the tariff effects, a monthly note written automatically from the latest data, shareable links and a summary image, and a question tab built on verified answers. An optional AI assistant answers in your own words, only from the dashboard's verified facts (enabled with an API key; its bilingual evaluation set is ready and will be run once a key is available, D34).

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/refresh.py        # download the latest data, rebuild roles, forecasts and app data
python src/fetch_trade.py    # UN Comtrade imports (needed for notebook 04)
python src/sql/warehouse.py  # SQL warehouse and business queries
pytest -q                    # 22 checks (also run by GitHub Actions on every push)
```

Notebooks `01` to `06` in `notebooks/` run in order and keep their outputs.

## Repository

```
src/                 data download, CPI catalogue, tariff roles, refresh
src/causal/          synthetic control, DiD, exposure, commodity adjustment
src/forecast/        forecasting models, backtest, conformal intervals
app/                 Streamlit app and its small data bundle
data/reference/      hand-curated, versioned files (tariff lists, mappings)
notebooks/           01 coverage, 02 mapping, 03 replication, 04 pass-through, 05 world prices, 06 forecasts, 07 NLP, 08 RAG
src/nlp/, src/rag/   tariff-line classification, document corpus and retrieval evaluation
sql/                 business questions in SQL (DuckDB)
docs/                decision log, references, one-page summary (EN and FR)
tests/               automated checks
```

## Future work

- **AI assistant and LLM classification** (D28, D29, D34): code and question sets are ready; they run with one command once an Anthropic API key is available, and the assistant appears in the app only after its accuracy is published.
- **Document search (RAG)** (D30, D32): removed from the app until the held-out answer key reaches 80% in each language (now English 100%, French 56%). Next fix: translate French questions before the search, then measure on a new, untouched question set.
- **Methods**: conformal intervals by group of series (Mondrian), synthetic difference-in-differences, 8-digit trade data.

## Traceability

Every design choice is justified in the [decision log](docs/en/decision-log.md) (D01–D34) and backed by the [references](docs/references.md), all checked online.

## Data

All public: Statistics Canada (CPI 18-10-0004-01, average prices 18-10-0245-01, basket weights 18-10-0007-01, household spending 36-10-0225-01), Bank of Canada (USD/CAD), UN Comtrade (imports by product), World Bank (commodity prices). Tariff lists: Finance Canada and the Canada Gazette.

## Author

David Doe, data science student, University of Lille.
