# Results in one page

*[Version française](../fr/resume.md)* · [Live app](https://canada-grocery-prices.streamlit.app/) · Data to August 2026 · Every number is traced in the [decision log](decision-log.md).

**Question.** How much do Canadian counter-tariffs raise grocery prices, how fast, and for how long?
**Approach.** Public data only (Statistics Canada, Bank of Canada, UN Comtrade, World Bank), methods chosen to be easy to explain, every choice sourced.

## The answer for households

While the 2025 counter-tariffs applied (March to August 2025), they cost an average household about **50 cents per 100 dollars of groceries** (plausible range 0 to 1.60 dollars), about 0.5 point of the 1.8% rise in grocery prices over those months. The app computes it for your own spending. (D26)

**Where it comes from.** In 2025, four categories carry 64% of that cost, three of them as upper bounds (bakery, condiments, beverages: their customs codes are broader than the taxed products). The 2026 tariffs cost about **11 cents per 100 dollars**, and only 2 cents of it is solid: cheese, the one product taxed as sold in stores. The rest falls on ingredients (bakery mixes, milk powders, whey), part of which goes to restaurants and manufacturers. (D33)

**Monitoring 2026.** The forecast made just before the September 2026 tariffs is frozen as the path prices would have followed without them, and each new month is compared with it. Replayed on 2018 and 2025, a tariff alarm built on this comparison detected nothing (tariffed and untaxed series left their forecast intervals equally often), so it is kept as an analysis tool rather than shown as an alert. (D33)

## Three findings

**1. Tariffed US goods are a small part of each grocery price index.**
In 2025, the median share of tariffed US goods in a tariffed CPI series was 9%. Even if the whole 25% tariff had been passed on, these series would have moved by about 3 points on average, close to what monthly public data can detect (about 5 points). This is why the effect is hard to see in the CPI, and why the Bank of Canada works with product-level data. (D20, D21)

**2. 2025: about 40% pass-through, consistent with the Bank of Canada.**
Comparing each tariffed series with a weighted mix of similar untaxed series, and removing world commodity prices, about 40% of the tariff reached shelf prices (95% interval −7% to 86%). The interval contains the Bank of Canada's estimate of about 25%. Coffee is excluded from this estimate: its rise came from world prices (arabica doubled), and it stayed high after the tariff was lifted. (D21, D22)

**3. 2026: the "dairy" tariffs mostly hit ingredients.**
The September 2026 list taxes milk powders and whey (50%) and cheese (25%). Fresh milk, butter, yogurt and ice cream are not on it. US cheese is about 2.4% of household spending on cheese, so even full pass-through would add at most 0.6 point to the cheese price index. (D06, D18)

## Forecasts

12-month forecasts for 101 food price series, tested on 2019–2025 as if made in the past. The published model beats a simple "same as last year" baseline at every horizon (MASE 1.28 vs 2.16), and its 80% and 95% intervals covered 85–87% and 96–97% of outcomes in 2023–2025. Food prices are forecast at +3.5% for 2026, just below the Food Price Report's +4% to +6%. (D23)

## Limits

- 2018 (10% surtax): no detectable effect; this neither confirms nor contradicts the Bank of Canada's 70% for food.
- A placebo test on dairy products partly failed: dairy prices follow their own regulated dynamics.
- Import exposure is measured at the 6-digit product level and at border value; it is an approximation.

## Work in progress

- **Document search (RAG):** removed from the app until it answers 80% of held-out questions correctly in each language (English 100%, French 56% today); next fix: translate French questions before the search. (D32)
- **AI assistant and LLM classification:** ready to run, waiting for an API key; the assistant is shown only once its accuracy is published. (D34)

## Skills shown

- **Causal inference:** synthetic control with permutation tests, difference-in-differences with a continuous treatment, placebo tests.
- **Forecasting:** seasonal baseline first, rolling-origin backtest, LightGBM, conformal prediction intervals checked for coverage.
- **NLP and retrieval:** TF-IDF, multilingual embeddings, rank fusion and BM25, scored against human labels with bootstrap intervals.
- **Data engineering and product:** public APIs (Statistics Canada, Bank of Canada, UN Comtrade, World Bank), one-command monthly refresh, SQL, CI tests, a deployed bilingual Streamlit app.

## What is in the repository

A monthly refresh (`python src/refresh.py`), eight notebooks, a bilingual app, SQL business queries, 30 automated tests run on every push, and a decision log (D01–D34).
