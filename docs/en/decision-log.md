# Decision log

Every project decision is backed by a source (see `docs/references.md`).
Format: **Decision** → **Rationale** → **Alternatives rejected**.
Status: [decided] or [to confirm] with data.

---

## D01 — Topic: food inflation in Canada and the effect of counter-tariffs [decided]
**Decision.** Measure and forecast the effect of Canadian counter-tariffs on grocery prices, with a bilingual assistant to query the results.

**Rationale.**
- It affects every household: *Canada's Food Price Report 2026* forecasts food prices up 4–6%, or up to $994 more for a family of four [R5].
- It is current: new counter-tariffs have applied since September 8, 2026 to C$27.6B of US imports, including dairy (50%) and cheeses (25%) [R7, R8]. Their effect on groceries is debated [R6].
- The Bank of Canada published three studies on the topic in 2025–2026 [R1–R4], a sign that the question matters to Canadian economic institutions.

**Alternatives rejected.** Sales forecasting on the Walmart M5 dataset (2016 US data, heavily used, unrelated to current events); housing prices (saturated topic); wildfire risk (geospatial data too heavy for a solo project).

## D02 — Positioning relative to the Bank of Canada studies [decided]
**Decision.** Do not claim to discover the effect of the 2025 tariffs. The project (1) **replicates** the published orders of magnitude with **fully public data**, (2) **focuses on food**, a category for which R1/R2 publish no separate rate, and (3) **extends the analysis to the September 2026 tariffs**, which have not been studied yet.

**Rationale.**
- R1/R2 use daily online prices from 7 retailers (private data) and give no grocery-specific pass-through rate.
- R3 uses CPI microdata, which are not public.
- Replicating a result with open data is a recognised scientific practice, and monitoring a shock as it unfolds adds something new.

**Repositioning (2026-10-14, after D20–D23).** The replication can only be *compatible* with the Bank of Canada estimates (D20–D22): public monthly sub-indices are too aggregated to confirm or reject them. The project's contribution is therefore stated as **a transparent, public-data monitor**: what each tariff list actually taxes (D18), how much of it can reach shelf prices given import exposure (D21), whether world prices explain a price move (D22), and monthly forecasts (D23), all reproducible with one command (D25). The 2026 extension is reduced to exposure and scenarios: the direct effect on cheese is at most 0.6 point (D06).

## D03 — Data for causal measurement: CPI sub-indices (18-10-0004-01) [decided]
**Decision.** Measure the tariff effect with monthly CPI sub-indices (for example "cheese", "fresh milk", "coffee"), not with average prices.

**Rationale.** Statistics Canada states that the average price table "does not measure pure price change" and recommends the CPI for measuring inflation [S3]. The CPI adjusts for quality and package-size changes.

## D04 — Data for the dashboard: average prices (18-10-0245-01) [decided]
**Decision.** Use average prices in dollars (for example "4 L of milk") only for the public interface and the assistant, and **handle the January 2024 break**, when more grocers were added to the sample.

**Rationale.** Dollar prices speak to the public more than indices do. Statistics Canada however flags product rotation and asks for caution on changes around January 2024 [S3]. We therefore add a break indicator and draw no causal conclusion from this table.

## D05 — Main causal method: synthetic control, product by product [decided]
**Decision.** For each tariffed sub-index, build a "twin" from the untariffed sub-indices that tracked it most closely before the shock [M1, M2]. The estimated effect is the gap between the actual price and this twin. Robustness is checked with **difference-in-differences** [M3] and **synthetic DiD** [M4].

**Rationale.**
- This is the method the Bank of Canada used for the 2018 episode [R3]. Difference-in-differences is the method of R2.
- The tariff episodes start on different dates (2018, 2025, 2026). Callaway and Sant'Anna [M3] handle this staggered-treatment case correctly.
- Tariff start and end dates come from official sources [R1, R7, R9] (file `data/reference/tariff_events.csv`).

**To check with the data.** Are CPI sub-indices detailed enough to isolate the tariffed products? If not, we weight by exposure to US imports.

**Finding (2026-10-14, notebook 01).** The food subtree has 129 series. For the September 2026 dairy and cheese tariffs, granularity is sufficient: *Fresh milk*, *Butter*, *Cheese*, *Ice cream and related products* and *Other dairy products* exist nationally and by province since 1949–1985, and finer national series exist since 2013 (*Whole milk*, *Low-fat milk*, *Cheddar*, *Mozzarella*, *Processed*, *Unripened or fresh cheese*). Granularity for the 2018 and 2025 lists will be checked when mapping them (next step 3). Status stays [to confirm] until then.

**Conclusion (2026-10-14, notebook 02).** Granularity is sufficient for all three episodes once tariff lines are mapped to CPI series (D18): 10 treated series usable for 2018, 22 for 2025 and 5 for 2026. Series where tariffed goods are only a small part or only an ingredient are excluded rather than weighted by import exposure (see D18).

## D06 — Pass-through priors: scenarios bounded by the literature [decided]
**Decision.** For the 2026 tariffs, produce three scenarios rather than a single forecast:
- **low**, about 25% pass-through and a temporary effect (2025 episode [R1, R2]);
- **central**, about 60%;
- **high**, about 70% for food, with a persistent effect (2018 episode [R3]).

**Rationale.** Two recent Canadian studies reach very different results. The US literature shows near-complete pass-through to border prices but partial pass-through in stores [L1–L3]. R4 shows that two thirds of the effect runs through input costs. Data from the coming months will show which scenario reality is closer to.

**Hypothesis to test.** Supply management limits US dairy imports. The 50% tariff could therefore have little effect on retail milk prices, acting mostly through ingredients (powders, whey) [R6].

**2026 cheese, computed (notebook 06, D23).** US cheese imports in 2025 were about US$132 million (24% of cheese imports), against about C$7.7 billion of household spending on cheese: exposure s = 0.024. At 100% pass-through, the 25% tariff would add only **0.6 points** to the cheese CPI; the three scenarios add 0.15 to 0.4 points, well inside the forecast's 80% interval (about ±4 points). The tariff matters for importers and for cheese made with US ingredients, but its direct effect on the cheese CPI will be too small to detect.

## D07 — Control variable: the CAD/USD exchange rate [decided]
**Decision.** Add the Bank of Canada daily USD/CAD rate, aggregated by month, as a control variable in the causal and forecasting models.

**Rationale.** The price of an imported product depends on the exchange rate as much as on the tariff. Omitting the exchange rate would wrongly attribute its effect to the tariffs.

## D08 — Forecasting: start from a baseline and validate on a rolling origin [decided]
**Decision.** Compare (1) a seasonal naive baseline, (2) per-series ETS and ARIMA models [F1] and (3) a global LightGBM model trained on all series. Evaluation uses **rolling-origin validation** with MASE and sMAPE.

**Rationale.**
- Every method must beat a simple benchmark [F1].
- In the M5 competition, global tree-based models (LightGBM) dominated on related retail series [F2].
- Random cross-validation leaks the future into training, a classic mistake [F3].

## D09 — Uncertainty: conformal prediction intervals [decided]
**Decision.** Pair each forecast with 80% and 95% intervals obtained by conformal prediction, then check their actual coverage.

**Rationale.** Conformal prediction guarantees coverage without assuming an error distribution [F4]. For decision-making, a range is more honest and more useful than a single number.

## D10 — External benchmark: the Food Price Report [to confirm]
**Decision.** Compare our annual forecasts by category with those of the Food Price Report (+4–6% for 2026; exact 2025 forecast figure to be taken from the 2025 report) [R5].

**Rationale.** It is Canada's reference forecast, and it is published. The report states that its 2025 forecast was broadly right but underestimated meat [R5]. This gives a concrete comparison that anyone can understand.

**Comparison done (notebook 06).** Our forecast of the *Food* CPI for 2026 (annual average, 8 observed months and 4 forecast months) is **+3.5%** vs 2025, just below the report's +4% to +6% range [R5].

## D11 — The assistant: tool-using RAG, evaluated on a test set [decided]
**Decision.** A bilingual assistant that (1) queries the tables and models through tools (SQL, forecasts), (2) cites its sources [A1], (3) declines to answer outside its scope. It is evaluated on a **bilingual question set with verified answers**, using faithfulness and relevance metrics inspired by RAGAS [A2].

**Rationale.** In companies, reliability is the main barrier to AI assistants. Measuring that reliability, rather than assuming it, sets the project apart from a simple demo.

**Update (D24).** For the first public version, the assistant is a fixed set of verified answers; the LLM version is postponed.

## D12 — Bilingualism [decided]
**Decision.** Deliver the whole project in English and French (README, app, assistant).

**Rationale.**
- English and French are Canada's two official languages, and Statistics Canada publishes every table in both [S1, S2] (the `--lang` option of `src/fetch_data.py`).



## D13 — Geographic level: Canada, then provinces, Ontario first [decided]
**Decision.** Start the analysis at the national level, then break it down by province, starting with Ontario.

**Rationale.** The Food Price Report forecasts an above-average increase for Ontario [R5]. Provincial data availability is still to be confirmed.

**Confirmed with the data (2026-10-14, notebook 01).** 32 of the 129 food series are published by province: the ten provinces plus Whitehorse and Yellowknife (no food series for Iqaluit), since 1978-09 for most and 1985-01 for the rest. Ontario is always included. These 32 are all aggregates (base 2002=100), for example *Fresh milk*, *Butter*, *Cheese*, *Fresh vegetables*. Detailed series (bases 2013, 2023 and 2024) are national only. Provincial analysis is therefore done on aggregates; product-level analysis is national.

## D14 — Known limitations (to be detailed in the report) [decided]
- Monthly aggregated data are less precise than the daily product-level prices of R1/R2.
- Actual exposure to US imports by product is only approximated.
- Indirect effects run through inputs [R4] and substitution [R3].
- Other shocks happen at the same time (weather, beef prices [R5], fuel tax [R6]).
- **Statistical power (D20).** With national monthly CPI sub-indices, the smallest average effect the design detects is about 3.6 points for 2018 and 5.3 points for 2025, larger than what the Bank of Canada estimates imply for broad CPI series.

## D15 — USD/CAD before 2017: splice the legacy noon rate [decided]
**Decision.** Extend the exchange rate series back to 2007-05-01 with the Bank of Canada legacy noon rate (series IEXE0101), and use the current daily average rate (FXUSDCAD) from its first day, 2017-01-03. A `source` column records the series of each row.

**Rationale.**
- FXUSDCAD starts on 2017-01-03. That leaves only 18 months before the July 2018 tariffs, too short a pre-period to use the exchange rate as a control (D07) in a synthetic control [M2].
- The Bank of Canada replaced the noon rate with a daily average rate on 1 March 2017, published both in parallel until 28 April 2017, and stopped the noon rate after that date [S5, S6].
- Measured on our data, over the 82 days where both series exist (2017-01-03 to 2017-04-28): the daily gap averages −0.01% (standard deviation 0.12%), and the monthly means differ by less than 0.03%. Since D07 uses monthly averages, the splice creates no visible break.

**Alternatives rejected.** Keeping only FXUSDCAD (pre-period too short for 2018); using the noon rate alone (stopped in 2017); rescaling one series to the other (the measured gap is too small to justify it).

## D16 — One source of numbers: EN tables; FR tables only for labels [decided]
**Decision.** All computations read the English StatCan files. French files are used only for French labels (geography, product), joined on the StatCan series id `VECTOR`. Loading goes through `src/load_data.py`.

**Rationale.**
- Statistics Canada publishes each table in both languages [S1, S2] (D12). Checked on 2026-10-14: the EN and FR files of both tables have the same rows (1,152,913 and 141,432), the same `VECTOR` ids and the same values, with 0 differences.
- The file formats differ: "," separator in EN, ";" in FR, translated column names, UTF-8 BOM in both. One source avoids parsing the same numbers twice and the risk of divergent results between the two languages.

**Alternatives rejected.** Running the analysis twice, once per language (twice the work and a risk of divergence); translating labels by hand (StatCan's official French labels already exist).

## D17 — Which series can be used for each tariff episode [decided]
**Decision.** A CPI series is used for an episode only if it has **at least 36 months of data before the first tariff month** and at least one month after it. Series that start too late are replaced by their parent aggregate. The rule is coded in `src/cpi_catalog.py` (`MIN_PRE_MONTHS`).

**Rationale.**
- A synthetic control is credible only if it reproduces the treated series over a long pre-treatment period; with a short pre-period, a good fit can be obtained by chance [M2].
- Food CPI series are strongly seasonal (fresh produce in particular). Three full yearly cycles is the minimum we accept to separate seasonality from trend [F1].
- Applied to the data (notebook 01): 106 series qualify for 2018 and 101 for 2025. Excluded for 2025: the 15 meat cuts (base 2024-04, only 11 months before) and the 8 fresh produce series (base 2023-04, 23 months before); 5 series discontinued in 2021-05 have no data after March 2025. For 2026, 114 series have enough history, but **no post-tariff data exist yet**: the last published month is August 2026, and the September 2026 CPI is released on October 19, 2026 [S7].

**Consequences.** The 2026 analysis can start only once several post-tariff months are published (September data on Oct. 19, October data on Nov. 16, November data on Dec. 14, 2026 [S7]). Until then, work on 2018 and 2025 (next steps 3 and 4).

**Alternatives rejected.** 24 months (would admit the 15 meat cuts into the 2026 episode with only 29 months, about two cycles, of history); 48 or 60 months (would drop the 8 fresh produce series, 41 months of history, from the 2026 episode without changing anything for 2018 or 2025).

## D18 — Treated, placebo and control series for each tariff episode [decided]
**Decision.** Map each food tariff line of the official lists to the CPI series where the product is priced, then give every CPI food series one role per episode:
- **treated**: tariffed retail products are a main part of the series, at a binding rate (exposure `direct`);
- **placebo**: only over-quota imports were tariffed (exposure `over_quota_only`); used as a falsification test;
- **excluded**: tariffed goods are a small or uncertain part of the series (`partial`), only an ingredient (`input`), the series is an aggregate containing exposed series, or it was exposed in another episode inside the estimation window;
- **control**: everything else bought in stores. Restaurant food is out of scope.

Files: `data/reference/tariff_hs6_food.csv` (lists at HS 6-digit level), `data/reference/tariff_cpi_map.csv` (mapping with confidence level and EN/FR notes), `src/tariff_map.py`, notebook 02.

**Rationale.**
- Only the official texts say what was taxed. Food lines (HS chapters 01–24): **2018**, 25 lines in 18 subheadings at 10% [R10], unchanged by the April 2019 amendment, which removed boats only [R11], and repealed on 2019-05-19 [R9]; **2025**, 407 lines in 183 subheadings at 25% [R7], all lifted on 2025-09-01 (the list in force from that date has no food line [R7]); **2026**, 66 lines in 15 subheadings [R7]: cheese at 25%; milk powders, whey, honey, molasses and bakery mixes at 50%. Alcohol, tobacco, live animals and feed are outside the food CPI (120 lines in 2025, 1 in 2018).
- Supply-managed products have tariff-rate quotas. US imports within the quota enter duty-free; imports above it already pay about 241% (milk), 298.5% (butter) or 245.5% (cheese) [S9]. In 2025, milk, butter, cheese, shell eggs and ice cream were tariffed **only above the quota**, so the extra 25% should change nothing. Treating these series as placebos tests the method: a "significant" effect on them would reveal a flaw [M2].
- Series exposed only partly or through inputs would dilute the effect if treated and contaminate the controls if used as donors; both break the no-interference assumption of synthetic control and difference-in-differences [M2, M3]. The input channel is real [R4], so these series are kept out of both groups.
- The 2026 estimation window (36 months before, D17) starts in 2023-09 and contains the 2025 episode: 50 series exposed in 2025 are therefore not 2026 controls.
- **Finding for 2026.** The 50% "dairy" tariff hits milk powders and whey, which are ingredients. Fresh milk, butter, yogurt and ice cream are not on the list. Only cheese is directly tariffed. This supports the D06 hypothesis that the retail effect on dairy runs mostly through inputs [R6].
- Result (series with enough history and post-tariff data): 2018, 10 treated and 71 controls; 2025, 22 treated, 11 placebos and 28 controls; 2026, 5 treated (cheese and its 4 sub-series, waiting for post-tariff data, D17) and 39 controls.

**Assumptions checked (2026-10-14).**
- *Yogurt is priced in Other dairy products*: **confirmed by elimination.** Yogurt is a CPI representative product [S11]; *Dairy products* has exactly five sub-series (fresh milk, butter, cheese, ice cream, other dairy products) and yogurt is none of the first four. StatCan does not publish the content of each series, so this is the strongest check available. *Other dairy products* had about 3 representative products in the 2014 basket [S10]: the 2018 effect on it is diluted, so step 4 reports results with and without it.
- *Honey is priced in Sugar and syrup*: **not verifiable** (in 2014 the series had a single representative product [S10]; honey is a representative product today [S11], class not published). **No role depends on it**: in 2025 the series is treated through sugar and maple syrup; in 2026 it stays excluded because molasses is an input. Confidence lowered to `low` for 2026.

**Alternatives rejected.** Weighting each series by its share of US imports: more precise, but it needs a concordance between HS codes and CPI series that is not public; kept as a possible robustness check. Treating all 2025 dairy as treated: ignores the quota structure and would bias the 2025 estimate towards zero.

## D19 — Estimation design for the 2018 and 2025 replications [decided]
**Decision.**
- **Outcome**: 100 × log CPI, seasonality removed (calendar-month factors estimated on the pre window only) and centred on the pre-window mean. Results are in % (log points).
- **Windows**: 60 months before the tariff to fit (≥ 36, D17); *during* = months with the tariff in force (2018-07 to 2019-05; 2025-03 to 2025-08); *after* = up to 12 months after removal, stopped before March 2020 for 2018 (pandemic).
- **Synthetic control** per treated series: weights ≥ 0 summing to 1, fitted on the pre window [M1, M2]. Donors = D18 controls at the finest level, so that a series and its parent are never both in the pool (52 donors for 2018, 22 for 2025).
- **Inference**: in-space permutation, i.e. the same estimator run on each donor; p-value = rank of the post/pre RMSPE ratio [M1].
- **Robustness**: 2×2 and event-study difference-in-differences with series and month fixed effects, standard errors clustered by series. Each episode has a single start date, so two-way fixed effects are not exposed to the staggered-timing bias [M3].
- **Reading**: `rho` = effect ÷ tariff rate = pass-through × share of tariffed US goods in the series. It is not a pass-through rate on its own.

**Rationale.** The specification was chosen on pre-period fit, a criterion fixed before looking at effects [M2]. Removing seasonality and centring on the pre mean (which acts like a unit fixed effect [M4]) lowers the median pre-period RMSPE of treated series from 1.32 to 1.07 points (2018) and from 2.87 to 2.11 points (2025), compared with anchoring every series on the last pre-tariff month. Both specifications are kept in notebook 03.

**Alternatives rejected.** Anchoring on the last pre-tariff month (worse fit, a single noisy month drives every path); a shorter pre window (D17); synthetic DiD [M4] as the main estimator (kept for later: with 22 donors in 2025, the gain is small next to the D20 power issue).

## D20 — Replication results for 2018 and 2025: no effect detectable with public CPI sub-indices [decided]
**Findings (notebook 03, specification D19).**

| | 2018 (10% surtax) | 2025 (25% counter-tariffs) |
|---|---|---|
| Synthetic control, mean effect during the tariff | −1.8% (0 of 10 series with p < 0.10) | +1.1%, median −0.2% (2 of 22 with p < 0.10) |
| DiD, average effect during the tariff [95% CI] | −1.9 [−4.4; +0.7] | +2.1 [−1.6; +5.8] |
| Minimum detectable effect (80% power) | 3.6 points | 5.3 points |
| Placebo series (over-quota dairy and eggs) | — | −2.4% mean; DiD −2.0 [−4.9; +0.9] |

- **2018.** No price increase is detectable in the treated series; the event study even shows them slightly below controls in months 1 to 5 (two months with p < 0.05). Dropping *Other dairy products* (broad series, D18) changes nothing (−1.8 [−4.5; +0.9]).
- **2025.** The positive mean comes from coffee (+18.2%, p = 0.04) and confectionery (+3.9%, p = 0.09). Both moved during sharp rises in world coffee and cocoa prices, which Canadian donor series cannot reproduce. Without them, the DiD falls to +1.0 [−2.3; +4.3]. With high-confidence mappings only, it is +4.0 [−0.1; +8.0]. The event study shows treated series already 1 to 2 points above controls in the 10 months before the tariff, so the parallel-trends assumption is doubtful.
- **Falsification.** The placebo series, which should show zero, are on average 2.4% below their synthetic controls (cheese p = 0.04). Dairy prices follow their own regulated dynamics, which non-dairy donors do not capture. Individual p-values near 0.05 are therefore not reliable evidence here; with 22 tests, about one false positive at 5% is expected anyway.

**Comparison with the literature (D02).** R3 finds about 70% pass-through for food in 2018. A 10% surtax with 70% pass-through moves a broad CPI series by more than our upper bound (+0.7%) only if US tariffed goods are more than about 10% of that series. R1/R2 find about 25% pass-through in 2025. Our 2025 `rho` (0.04 for synthetic control, 0.08 for DiD, upper bound 0.23) is compatible with 25% × the US share. **We neither confirm nor contradict the Bank of Canada estimates. Public monthly sub-indices are too aggregated to detect effects of that size.** This is a result in its own right, and it explains why R1/R2/R3 rely on product-level or micro data.

**Consequences.**
1. Pass-through cannot be reported without exposure weights. Next: estimate the US share of each CPI series from Statistics Canada trade data (imports by HS code) and domestic supply, then convert effects into pass-through rates.
2. Control for world commodity prices (coffee, cocoa, oranges) before reading 2025 coffee and confectionery as tariff effects.
3. For 2026, the cheese series are the strongest case (25% on all lines, within and over quota). Precision will stay limited: report minimum detectable effects next to every estimate.

**Alternatives rejected.** Reporting only the significant series (coffee) as evidence of pass-through: multiple testing, a global price confounder and a failed placebo argue against it.

## D21 — Pass-through from exposure-weighted effects [decided]
**Decision.** Convert effects into pass-through rates comparable with the Bank of Canada [R1–R3]:
- **Exposure** of each treated series `s` = US imports of its tariffed HS6 subheadings (UN Comtrade [S12], year before the tariff: 2017 or 2024, converted at the annual USD/CAD rate) ÷ household spending on the series (CPI basket weight [S13] ÷ weight of food from stores × HFCE on food and non-alcoholic beverages [S14], same year). Over-quota-only subheadings are left out (D18).
- **Main estimate**: DiD with a continuous treatment, dose = 100 × tariff × `s` (0 for controls), series and month fixed effects, SE clustered by series [M3, M5]. The coefficient is the pass-through rate.
- Code: `src/fetch_trade.py`, `src/causal/exposure.py`; results: notebook 04.

**Rationale.**
- An effect on a broad CPI series mixes pass-through with the share of tariffed US goods in that series; only the ratio is comparable with R1–R3.
- Exposure is low: median `s` = 0.12 in 2018 and 0.09 in 2025. At full pass-through, the expected average effect is only 1.4 points (2018) and 3.0 points (2025), below the minimum detectable effects of D20 (3.6 and 5.3 points). This explains why D20 found nothing.

**Results.**

| | Pass-through [95% CI] |
|---|---|
| 2018, all 10 treated series | −0.96 [−2.45; +0.54] |
| 2018, own basket weight only (6) | −0.16 [−1.05; +0.73] |
| 2025, all 22 treated series | +0.83 [−0.11; +1.78] |
| 2025, without coffee and confectionery (20) | +0.35 [−0.12; +0.81] |
| 2025, own basket weight only (17) | +0.27 [−0.19; +0.73] |

- **2025**: every variant contains the ~25% of R1/R2. The estimate above 80% with all series is driven by coffee and confectionery (world price shocks, D20).
- **2018**: the main estimate excludes R3's 70% at the 5% level, but the variant with series that have their own basket weight does not. A negative pass-through has no economic meaning; it signals domestic dynamics the controls miss. **No conclusion against R3 is drawn.**

**Known biases.** Imports are at border value, while spending is at retail value (understates `s`); imports also go to restaurants and processors (overstates `s`). Five HS6 codes are broader than the tariffed 8-digit lines (`hs6_broader`, `s` is then an upper bound); eight detailed series use a parent's basket weight (understates `s`). Basket weights are rounded to 0.01%, which is coarse for small series.

**Alternatives rejected.** Statistics Canada 8- or 10-digit trade data by country would remove the broader-code bias, but they are not available through an open API; UN Comtrade at 6 digits is public and reproducible. Using the share of US imports in total imports: it ignores domestic production, which dominates many food series.

## D22 — Controlling for world commodity prices [decided]
**Decision.** For the 12 treated series tied to a world commodity (`data/reference/commodity_map.csv`: coffee, cocoa, oranges, sugar, rapeseed oil, rice, wheat, tea, groundnuts), remove the world-price component before estimating effects:
- world prices: World Bank Pink Sheet, monthly [S15], converted to CAD (D15);
- elasticities on **12-month log changes**, lags 0–11 months in four blocks, estimated on all months before the tariff since 2005;
- the implied component is removed from the series, then the synthetic control (D19) and the pass-through DiD (D21) are run again. Code: `src/fetch_commodities.py`, `src/causal/commodity.py`; results: notebook 05.

**Rationale.** Canada takes world prices as given, so they are not affected by Canadian tariffs and can be removed without biasing the tariff effect. Twelve-month changes remove seasonality and spurious level trends; the long window gives several commodity cycles.

**Results.**
- Elasticities are plausible: coffee 0.16, wheat → flour 0.19, wheat → pasta 0.24, sugar 0.27, rapeseed oil → margarine 0.15.
- **Coffee 2025**: world arabica in CAD roughly doubled between mid-2024 and early 2025. It explains 7.1 of the 18.2-point gap; the adjusted gap (11.2 points, p = 0.04) still exceeds the 7.1 points that a full pass-through of the tariff would produce (D21), and it stays high **after** the tariff was lifted (14.5 points over Sept. 2025–Aug. 2026). A tariff effect would fade when the tariff ends; this one does not. The coffee rise is therefore read as a world-price effect that the 0–17-month lag structure does not fully capture, **not** as tariff pass-through.
- **Pass-through 2025**: all series, adjusted, 0.69 [0.01; 1.38] (lags 0–11) and 0.62 [0.03; 1.20] (lags 0–17). These are the only estimates significant at 5%, and they rest on coffee. **Preferred estimate: without coffee and confectionery, commodity-adjusted: 0.39 [−0.07; 0.86]** (0.44 [−0.05; 0.93] with lags 0–17). It contains the ~25% of R1/R2 and rules out pass-through above about 90%.
- **2018**: unchanged, −0.94 [−2.44; +0.56].

**Rule used for the preferred estimate (stated before reporting it).** A series is treated as confounded when its commodity-adjusted effect exceeds the effect expected at 100% pass-through and persists after the tariff is lifted. Only coffee meets both conditions; confectionery is removed with it because cocoa had its own record shock in 2024–2025 and its adjusted elasticity is near zero (R² 0.02), so the adjustment cannot be trusted there.

**Alternatives rejected.** A first version regressed the synthetic-control gap on commodity prices over the 60-month pre window only. It was unstable: the oranges correction moved the effect by 16 points, and the coffee elasticity came out at 0.04 because the window holds too little commodity variation. Comparing with US CPI for the same products: the US imposed its own tariffs on coffee-producing countries in 2025, so it is not a clean control.

## D23 — Forecast results and intervals [decided]
**Decision.** Publish 12-month forecasts for the 101 national food CPI series that start by 2014 and reach the last month, with the model chosen by D24, and split-conformal 80% and 95% intervals by horizon. Code: `src/forecast/models.py`; results: notebook 06.

**Results (rolling origin, 27 origins from 2019-01 to 2025-08, horizons 1–12) [F3].**

| Model | MASE | sMAPE (%) |
|---|---|---|
| LightGBM, global | 1.28 | 3.2 |
| ETS, per series | 1.37 | 3.4 |
| Seasonal naive (baseline) | 2.16 | 5.2 |

- Both models beat the baseline at every horizon [F1, F2]. ETS is best at 1 month (MASE 0.61 vs 0.65); LightGBM is better from 3 months on. ETS is 6% above LightGBM overall, beyond the 5% margin of D24, so LightGBM is published.
- Conformal intervals calibrated on 2019–2022 origins cover 85–87% (80% target) and 96–97% (95% target) of the 2023–2025 outcomes: slightly conservative, as expected after the 2022 inflation surge [F4].
- MASE is above 1 at long horizons because the scale is the in-sample one-year-ahead naive error; the 2021–2023 inflation surge makes all models miss at 12 months.

**Alternatives rejected.** A single train/test split (one period would decide everything, F3); intervals from model residuals (they assume a distribution and were not checked).

## D24 — Explainable methods and a sober presentation [decided]
**Decision.**
- **Forecasts**: the published forecast uses the simplest model whose mean MASE is within 5% of the best one, in the order seasonal naive, ETS, LightGBM. LightGBM stays in the backtest as a benchmark.
- **Assistant**: a question tab built on a fixed set of verified bilingual answers (`app/faq.py`), each citing its decision and source, matched by shared keywords. No language model.
- **Presentation**: no emojis anywhere (app, README, logs); status markers are words ([decided], [to confirm], verified, to check). Minimal charts using the same five colours.
- **App data**: a small derived bundle in `app/data/` (built by `src/build_app_data.py`), so the app runs without the raw files.

**Rationale.**
- The project is a portfolio piece: every method has to be explained to a non-specialist in a few sentences. When accuracy is close, the simpler forecast is preferred, which is standard practice [F1].
- A fixed-answer assistant cannot invent numbers; its behaviour is fully predictable and testable. This keeps the reliability goal of D11 without a model to monitor.
- A sober style keeps attention on the results and reads as professional.

**Alternatives rejected.** An LLM assistant with tools (D11): more flexible, but it needs an API key, monitoring and an evaluation set before it can be trusted; kept for a later version. Always publishing the most accurate model: the gain over ETS has to be large enough to justify a harder explanation.

## D25 — Monthly refresh, automated checks, and dropping the detailed 2026 cheese study [decided]
**Decision.**
- **Monthly refresh**: one command, `python src/refresh.py`, run after each CPI release (calendar [S7]): download, catalogue and roles, published forecast with the notebook 06 conformal quantiles, cheese scenarios, app data. Historical causal estimates are not recomputed.
- **Automated checks**: 12 tests in `tests/` (official line counts, mapping validity, estimator behaviour on known inputs, conformal quantile, app data, no emojis), run with `pytest -q` without the raw data.
- **References**: every DOI was resolved on doi.org and its Crossref title, first author and year compared with `docs/references.md` (all match); arXiv and web references opened. Only the publication year of S10 remains to check.
- **2026 cheese**: no dedicated causal study (former step 4c). The monthly refresh keeps the cheese series and scenarios up to date.

**Rationale.**
- A monitor is only useful if it is updated; one command keeps the update explainable and reproducible.
- With an exposure of 0.024, full pass-through adds at most 0.6 point to the cheese CPI (D06), against a minimum detectable effect of several points (D20): a dedicated study would report "not detectable" by construction.
- Tests catch silent errors: the first run found a FAQ keyword ("4l") too short to ever match.

**Alternatives rejected.** A scheduled cloud job (needs a public repository and secrets; possible later). Recomputing all causal estimates each month: they cover closed episodes and would not change.

## D26 — Public features: household cost, product lookup, provinces, light and dark theme [decided]
**Decision.** Make the app answer the questions a non-specialist asks, with the same explainable methods:
- **What it costs me**: cost = monthly grocery spending × tariff rate × share passed on × share of food spending on tariffed US goods. For 2025: rate 25%, share passed on 39% (range 0–86%, D22), share of spending 5.3% (range 2.6–7.5%): about **0.52 dollar per 100 dollars of groceries** while the tariffs applied, i.e. about 0.5 point of the 1.8% rise in grocery prices between February and August 2025. For 2026: import-weighted rate 43%, share of spending 0.4%, pass-through scenarios 25–70% (D06).
- **Is it taxed?**: a search over the official lists mapped to CPI series (D18), in English and French, accent-insensitive.
- **Provinces**: 12-month change of the store-food CPI for the ten provinces, Whitehorse and Yellowknife (D13).
- **Latest-data banner**, **plain-language method**, **downloads** and a **citation**; author shown as David Doe, data science student, University of Lille.
- **Light and dark theme** chosen in the sidebar; the same five colours, stepped for each background.

**Rationale.**
- The share of spending is the ratio of US imports of tariffed food lines (UN Comtrade [S12]) to household spending on food and non-alcoholic beverages (2024, [S14]). Central value: lines mapped to the treated CPI series (D21); low: exact 6-digit codes only; high: every tariffed food line, including ingredients. The range is shown, never a single number alone.
- It is an average-household estimate: border values understate retail values, and a basket heavy in US products costs more. Both caveats are written next to the result.
- Tables are rendered as plain HTML so they follow the chosen theme.

**Alternatives rejected.** A cost estimate by product basket chosen by the user (needs product-level US shares that are not public); a map of provinces (a sorted bar chart compares values more precisely).

## D27 — Context, monthly note, shareable views and basket detail [decided]
**Decision.**
- **Context section first**: the situation (2018, 2025 and 2026 episodes, food prices), the problem (households cannot see what tariffs cost them; official estimates rely on non-public data), and what the project does, each fact tied to R1–R10.
- **Monthly note**: a paragraph filled automatically from the latest release (12-month change and its direction, restaurants, three largest increases and decreases among detailed series, provincial range, forecast). No text is written by hand or by a model.
- **Shareable views**: every section, language, theme, product search and grocery amount is kept in the address (`?section=cost&lang=fr&bill=1500`), and a 1200 × 630 summary image is generated in both languages.
- **Basket detail (2025)**: the ten tariffed categories with the most US imports plus "other tariffed products", each with its own share of US goods (D21); a user can change the amounts.

**Rationale.** A non-specialist needs to understand why the question matters before reading results; a dated note gives a reason to come back; links and images make the work easy to share; the basket detail answers "and if I buy a lot of coffee?" with the same one-line method. The basket at average-household amounts gives 5.15 dollars per month for 1,000 dollars, consistent with the aggregate 5.20 (D26), and a test checks the two stay within 10%.

**Alternatives rejected.** A text written by a model for the monthly note (not reproducible, risk of invented numbers); social-network preview tags (not configurable on Streamlit Community Cloud; the image is offered for download instead).

## D28 — Optional AI assistant grounded in the dashboard's facts, with an evaluation set [decided, evaluation is future work (D34)]
**Decision.** Add an assistant that answers questions in the user's own words with one call to Claude (`claude-opus-5-5`, low effort, server-side refusal fallback), given only a fixed text of the dashboard's verified facts (latest data, costs, pass-through, effects per series, tariff lists, provinces, forecasts, the verified FAQ, context). It must answer only from those facts, keep ranges, cite decision numbers, and say so when the facts do not cover a question. It is enabled only when an `ANTHROPIC_API_KEY` is set in the Streamlit secrets; otherwise the fixed-answer FAQ stays the only mode. Limits: 500 characters per question, 10 questions per visit.

**Evaluation.** 20 bilingual questions (`data/reference/assistant_eval.csv`): 16 with required facts, 4 out of scope that must be declined without a number. `python src/eval_assistant.py` grades each answer by required keywords (accent-insensitive) and writes the results. **Not run yet: it needs an API key.** The assistant should only be presented as reliable once this accuracy is published.

**Rationale.** This completes D11 without giving up D24: the model never sees the internet or raw data, only facts already verified and shown in the app, so its answers can be checked against the dashboard. The facts text is deterministic (no timestamps, sorted), so the about 5,000-token prefix is cached and each question costs little.

**Alternatives rejected.** Tools that query the data freely (more flexible, harder to verify); an always-on assistant without a key check (cost and abuse risk).

## D29 — NLP: ranking CPI series for each tariff line [decided, LLM step is future work (D34)]
**Decision.** Pre-map every new tariff list to CPI series with text methods, scored against the hand-made mapping of D18 (ground truth: 151 food HS6 subheadings, 135 with a CPI series, 123 candidate series). Customs descriptions come from the UN Comtrade HS nomenclature. Methods, from simplest to most advanced: TF-IDF with word and character n-grams [N10]; multilingual sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2) [N2, N3]; their combination (standardised-score average fixed in advance, and Reciprocal Rank Fusion [N4]); then, with an API key, Claude picks one series among the 5 candidates through a JSON schema that only allows those candidates or "none". Code: `src/nlp/hs_cpi_classifier.py`; results: notebook 07.

**Results** (strict = exact series; 95% bootstrap intervals [N8]):

| Method | Top-1 | Recall@5 | MRR |
|---|---|---|---|
| TF-IDF | 39% [31; 48] | 73% [65; 80] | 0.54 |
| Embeddings | 36% [27; 44] | 72% [64; 79] | 0.51 |
| Hybrid (fixed weights) | 38% [30; 46] | **81% [74; 87]** | 0.55 |
| RRF | **44% [36; 53]** | 79% [71; 85] | **0.58** |

- The hybrid shortlist beats TF-IDF on recall@5 (exact McNemar test [N9], p = 0.007); embeddings alone do not (p = 1.0). With the lenient metric (parent or child accepted), embeddings put the right family in the top 5 for 96% of lines: they find the right branch but not the right level.
- Error analysis: 32 of 84 top-1 errors are level errors (for example *Herbs and spices* for its parent *Condiments, spices and vinegars*), fixed in one click by a reviewer. The 52 others need domain knowledge the models lack: *Gallus domesticus* is chicken; milk powders and yogurt belong to *Other dairy products*; rapeseed oil is canola. This is what the LLM step is for; it is coded but **not yet measured** (no API key).
- Use: a reviewer checks 5 proposals instead of 123 series; the best weight found in the sensitivity table is not used, to avoid tuning on the test lines.

**Alternatives rejected.** Training a supervised classifier (135 labelled lines are too few, and new lists bring new products); asking the LLM to choose among all 123 series without a shortlist (longer prompts, harder to audit).

## D31 — SQL warehouse, continuous integration and the tools data teams use [decided]
**Decision.**
- **SQL**: a DuckDB warehouse (`src/sql/warehouse.py`) with dimension and fact tables (series, CPI, forecasts, provinces, tariff lines, mapping, exposure) and five business questions answered in plain SQL files (`sql/*.sql`): CTEs, joins, window functions (LAG, RANK, running sums), conditional aggregation, QUALIFY.
- **Continuous integration**: GitHub Actions runs the test suite on every push (`.github/workflows/tests.yml`, light `requirements-ci.txt`).
- **Industry vocabulary mapped to this project**: hybrid search (BM25 + vectors + RRF), cross-encoder re-ranking, embeddings, structured outputs, RAG evaluation, prompt caching, conformal prediction, backtesting, causal inference, A/B-style placebo and permutation tests.

**Rationale.** SQL, automated tests and reproducible pipelines are asked for in most data job postings; showing them on the project's own data is more convincing than a separate exercise. The queries also produced findings: four tariffed categories carry two thirds of the 2025 cost (bakery, condiments, beverages, confectionery), and the forecasts expect a return towards average after the steepest moves (bacon, oranges, pasta).

**Known limitation found by SQL.** The conformal intervals have the same relative width for every series at a given horizon (14.1% at 12 months for 80%), because they are calibrated on all series together (D23). Series-specific (Mondrian) conformal prediction would fix this; noted as a next step.

**Alternatives rejected.** A cloud warehouse (cost and accounts for a portfolio project); LangChain or LlamaIndex for retrieval (convenient, but implementing BM25, RRF and the evaluation directly shows the mechanics; the same pieces exist in those libraries).

## D30 — RAG: retrieval over official documents, with cited answers [decided, paused in the app since D32]
**Decision.** A document-search feature that retrieves passages from official sources and, with an API key, writes a short answer citing them [A1]. Corpus: 765 passages of about 1,000 characters (150-character overlap) from Bank of Canada studies R1–R4 (reuse allowed with attribution), Canada Gazette orders R9–R11 and Statistics Canada documents S3, S10 (Open Government Licence – Canada), and the project's decision logs and summaries; commercial sources are excluded. Each passage is indexed with its document title in front (contextual header). Code: `src/rag/build_corpus.py`, `app/rag.py`, `src/rag/eval_rag.py`; results: notebook 08.

**Evaluation** (16 questions, 10 English and 6 French, binary relevance = gold document + expected keyword; 95% bootstrap intervals [N8]):

| Configuration | Recall@1 | Recall@5 | MRR [95% CI] | nDCG@5 [N7] |
|---|---|---|---|---|
| BM25 [N1] | 56% | 69% | 0.64 [0.43; 0.85] | 0.47 |
| Multilingual embeddings [N2, N3] | 50% | **94%** | 0.65 [0.46; 0.83] | 0.43 |
| RRF of both [N4], without titles | 50% | 63% | 0.57 [0.34; 0.78] | 0.33 |
| RRF of both, with titles | 56% | 81% | 0.63 [0.43; 0.84] | 0.46 |
| RRF + cross-encoder re-ranking [N5, N6] | **75%** | **94%** | **0.81 [0.62; 0.95]** | **0.68** |

- Re-ranking is best on every metric and fixes French questions (recall@1 83% vs 33% for RRF), but its gain over RRF is not significant with 16 questions (paired randomization test, p = 0.12): a larger question set is needed to prove it.
- RRF fails on French questions because BM25 cannot match French words in English documents and pulls the fusion down; embeddings and the cross-encoder are cross-lingual.
- **Choice for the app**: the cross-encoder needs several gigabytes of memory, too much for the hosted app. The app shows 5 passages, so recall@5 is the relevant metric; among light methods, embeddings are best on it (94%) and work in French. This choice was made after seeing the results; it is stated here for that reason.
- **Generated answers** are coded (passages only, a [chunk_id] after each supported sentence) and will be scored on citation rate and numeric grounding (numbers in the answer found in the cited passages, a simple proxy for faithfulness [A2]) once an API key is available.

**Alternatives rejected.** Putting all documents in the prompt (over 500,000 characters: retrieval is needed here, unlike the small fact set of D28); a hosted vector database (765 passages fit in a 1 MB matrix).

**Update (A29): passage start and answer language.** (1) The 150-character overlap was cut at a fixed character count, so 81% of the passages began in the middle of a word and the app showed truncated sentence starts. The chunker now starts the overlap at a sentence start (else a word start); for the current corpus, which cannot be rebuilt offline, the app and the answer prompt drop the repeated leading fragment (`clean_start`, at most 160 characters, so only overlap text is removed). Retrieval is unchanged: indexing still uses the stored passages, so the evaluation above stands (BM25 re-run: same figures). (2) 91% of the passages are in English (only the project's own French logs and summary are in French). The answer language is now detected from the question (16 of 16 evaluation questions correctly detected) instead of taken from the app language, and the prompt names the target language explicitly, because a generic "answer in the language of the question" instruction competes with a mostly English context [A1, N3]. The app tells the user that sources are mostly in English and that quoted passages stay in their original language.

**Update (A30): answer provider.** The hosted app had no API key, so it wrote no answer and showed only English passages. Answers can now be written by Gemini (Google AI Studio free tier) or Claude, chosen by the `RAG_PROVIDER` secret or by whichever key is set (Gemini first). Reasons: a public demo at zero cost that actually answers; Claude kept as a second provider so that the choice rests on a measured comparison rather than a preference. The free tier lets Google use submitted questions to improve its products and has low rate limits [A3]: the questions are public and about public documents, the app says so under each Gemini answer, and any failure falls back to the passages. The answer evaluation now uses the app's retrieval (embeddings), adds the share of answers written in the language of the question, and compares the providers on the same questions with the paired test.

**Update (A31): measured answers with Gemini.** Run of `src/rag/eval_rag.py` on 15 October 2026 with the 16 questions, Gemini only (no Claude key). The default model `gemini-flash-latest` (then Gemini 3.8 Flash) answered 7 of 16 questions: the free tier allows 20 requests per day per model and about 5 per minute, and the other calls failed with quota (429) or overload (503) errors. A second run with `gemini-flash-lite-latest` (separate quota, set through the `GEMINI_MODEL` secret) answered all 16: 10/16 answers cite a passage (62%), 16/16 are written in the language of the question (100%: 10 English, 6 French), and 12 of the 16 numbers written outside citations appear in the cited passages (75%). The 6 answers without a citation are all abstentions ("the passages do not answer"), and in 5 of them a relevant passage was in the top 5 retrieved (ranks 1 to 4): the model is too cautious rather than misled by retrieval. Three measurement and robustness fixes came with the run: grouped citations such as [R4-003, R4-002] are now counted, failed generations are reported apart instead of counting as correct-language answers, and Gemini calls are retried briefly on 429 and 503 and paced in the evaluation. Implications: 16 questions remain too few for any significance test (step 2: enlarge the set); 20 requests per day make Flash unusable for a public app and for a larger evaluation, so Flash-Lite or a paid tier is needed; false abstentions should become a tracked metric.

**Update (A32): Flash-Lite by default, less cautious answers.** Two corrections follow A31. (1) The app's default model becomes `gemini-flash-lite-latest`: Flash allows 20 free requests a day, which a public app and a larger evaluation exceed at once, while Flash-Lite answered all 16 questions on the same day; a paid tier would cost money for a portfolio demo, and the `GEMINI_MODEL` secret still overrides the default. (2) The prompt now asks the model to answer with what the passages state even when they cover only part of the question, to say what is missing, and to abstain only when no passage is relevant: in A31, 5 of the 6 abstentions had a relevant passage in hand. The evaluation now counts abstentions and false abstentions (abstention while a relevant passage was given), detected by a phrase pattern in English and French that matched exactly the 6 abstentions of A31. Results on the 16 questions, same day, Flash-Lite: answers citing a passage 10/16 to 16/16, abstentions 6 to 0 (false abstentions 5 to 0), numeric grounding 12/16 to 19/20 numbers, language 16/16 in both runs. A manual reading of the new answers is less flattering than the citation rate: 10 answer the question correctly, 3 partly (Q04 repeal date, Q10 the rule but not its reason, Q11 world price shocks without arabica) and 3 do not answer it while citing a side passage (Q01, Q13; Q15 where no relevant passage was retrieved). The citation rate therefore no longer measures whether the question is answered; step 2 adds a hand-checked answer key. Two known limits: answers now sometimes add a needless sentence on what the passages do not cover (Q05, Q06, Q11), and the prompt was revised after reading answers to these same 16 questions, so the gain must be confirmed on new questions (step 2) before it is taken as general.

**Update (A33): held-out questions with an answer key.** The 16 questions were used to revise the prompt in A32, so 34 new questions (18 English, 16 French; `data/reference/rag_eval_holdout.csv`) were written from the sources with an answer key: the accepted forms of the expected answer (a number, date or phrase), checked by hand against the passages (for French questions on English sources, the key holds the French translation). An answer meets the key when it contains one of these forms (`has_answer()`, written-out percents accepted). Results with Flash-Lite and the app's retrieval at the time (embeddings): key met 19/34 (56%); 19 questions received a relevant passage, 18 of them were answered correctly; 15 did not, and only 1 of those was. Retrieval, not generation, was the bottleneck. On the held-out set the embeddings ranked worst (MRR 0.44 [0.30; 0.59], recall@5 56%) and BM25 better (MRR 0.63, recall@5 82%); over the 50 questions of both sets BM25 leads embeddings (MRR 0.63 vs 0.51, recall@5 0.78 vs 0.68, paired test p = 0.10). The cross-encoder is best (MRR 0.87 on the held-out set, p < 0.001 against RRF) but needs 2.4 GB of memory and about 11 seconds per question on 4 CPUs, too heavy for the hosted app. The app's retrieval therefore becomes BM25, which also needs no model download. Re-run with BM25: key met 27/34 (79% [65%; 91%]), English 18/18, French 9/16; 28 questions received a relevant passage and 27 of them were answered correctly; numeric grounding 59/63 (94%). The remaining gap is French questions on English sources, which keywords do not match: translating the query before the search (roadmap step 4) is the next fix. Choosing BM25 used the held-out set, so it is no longer untouched for retrieval; a third set is needed before the next comparison.

## D32 — Pause the document search (RAG) in the app; focus on the operational and business side [decided]
**Decision.** The document search with written answers (RAG, D30) is removed from the hosted app (first replaced by an "in development" notice in A34, then removed entirely in A35); the code, tests and evaluation stay in the repository, and the section comes back with the `RAG` secret set to `on`. The verified answers (fixed questions and answers with their source, no AI, D24) stay as they are. Work on the RAG continues offline (evaluation sets, retrieval, translation of French questions) and will be presented as work in progress until it meets a quality bar fixed in advance. The project's next priority is its operational use and the business need it answers: measuring what tariffs cost households and which grocery categories they hit.

**Rationale.** The owner judged the answers not convincing enough for a public demo, and the measurements agree: before A33 the answer key was met for 56% of new questions, and even after switching to BM25 French questions reach only 56% (English 100%). A feature that is right about half the time for half of the users damages the credibility of the rest of the project, whose results are verified (D24). Keeping the code, tests and evaluation (D30, A31 to A33) preserves the work and shows the method; a measured threshold avoids switching it back on by impression.

**Condition to switch it back on.** Answer key met for at least 80% of the held-out questions in each language, on a set not used to tune the system, with retrieval light enough for the hosted app.

**Alternatives rejected.** Keeping the RAG online with a warning (users would still read unreliable answers); keeping the passage search without written answers (a partial feature would still be shown, and French questions would still find weak passages); deleting the feature (the evaluation work is part of the portfolio and the next fixes are known).

## D33 — Operational side: freeze the pre-tariff 2026 forecast, no automatic tariff alarm, cost by category [decided]
**Decision.**
- **Frozen counterfactual.** The forecast made with data to August 2026, the month before the 2026 tariffs (8 September 2026, D18), is saved in `data/reference/forecast_vintage_2026-08.csv`. The monthly refresh (D25) replaces `forecasts.csv` and would otherwise erase the path prices would have followed without the tariffs; the cheese scenarios (D06) now start from this frozen forecast.
- **No automatic tariff alarm in the app.** A watch rule was built (`src/monitor/tariff_watch.py`): each month, a series above its 80% conformal interval [F4] is flagged, and tariffed series are compared with untaxed ones (Fisher's exact test, one-sided [M6]). Replayed on the two past episodes with the published model, it detects nothing: 2018, 4% of tariffed series flagged against 7% of untaxed ones; 2025, 14% against 15%; no month with p < 0.05. The only strong 2025 signal, coffee (18% above its forecast), comes from world prices (D22). The rule therefore stays an analysis tool and is not shown as an alert.
- **Cost by category in the app.** The "What it costs me" section shows, for the user's bill, where the 2025 cost comes from: the same one-line method applied to each category of the basket (D27), sorted, with upper-bound categories hatched.

**Rationale.** The business need is to tell a household, a retailer or an analyst what the tariffs cost and where. The backtest confirms the project's main finding (D20, D21): a tariff effect on a CPI series (about 3 points at most) is below what monthly public data can detect (about 5 points), and the 2026 cheese effect is at most 0.6 point (D06). An alarm that almost never rings, and rings for the wrong reason when world prices move, would mislead. The category view answers the practical question with numbers already verified: four categories carry 64% of the central cost, three of them as upper bounds (bakery, condiments, beverages: their customs codes are broader than the taxed products).

**Alternatives rejected.** Showing the alarm with its limits written next to it (it would mostly display "nothing visible" or a false signal); per-series alarms without untaxed comparison (coffee would read as a tariff effect); recomputing the counterfactual each month (it would absorb the tariff).

**Update (A38): 2026 cost by category.** The same view now covers the 2026 tariffs, from the 2025 US imports of the 15 tariffed lines (UN Comtrade, D21) over 2024 household food spending, the denominator of the published total (D26); the groups add up to it exactly. For a $1,000 monthly bill, central scenario: bakery mixes and doughs $0.64, milk powders and whey $0.25, cheese $0.17, honey and molasses $0.04, total $1.10 against $5.20 for 2025. Cheese is the only product taxed as sold in stores (16% of the cost); the three other groups are ingredients (D18) and are shown as upper bounds, since part of their imports goes to restaurants and food manufacturers. So the solid part of the 2026 household cost is about $0.17 a month per $1,000 of groceries, consistent with the cheese effect of at most 0.6 point (D06).

## D34 — Steps that need a paid API key are documented as future work [decided]
**Decision.** The two steps that need an Anthropic API key are not run in this version and are presented as future work in the README, the one-page summary and the project notes: the accuracy of the optional AI assistant (D28, 20 bilingual questions, `python src/eval_assistant.py`) and the LLM step of the tariff-line classifier (D29, Claude picks one of the 5 candidate series). The code, question sets and scoring are ready, so each step is one command once a key exists. Without a key the hosted app does not show the assistant (D28), so no unmeasured AI answer reaches users; the verified answers stay the question tab's only mode.

**Rationale.** A paid key is a recurring cost for a student project, and the parts of the project that answer its question (tracker, causal estimate, forecasts, household cost) do not depend on it. The rule of D24 and D32 applies: the app shows only what has been verified, and an AI feature is shown only once its accuracy is published. Stating the pending steps openly is more credible than a claim without a number; the README previously said the assistant's accuracy was "measured", which was not yet true, and is corrected.

**Alternatives rejected.** Scoring the assistant with the free Gemini key already used for the RAG (D30): the prompt and the cached facts prefix are built for Claude, so the score would describe a different assistant from the one that would be deployed; showing the assistant without its evaluation (contrary to D28).
