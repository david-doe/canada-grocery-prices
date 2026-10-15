"""Exposure of each treated CPI series to the tariff, and pass-through estimates (next step 4a, D21).

Exposure s_i = value of US imports of the tariffed HS6 subheadings mapped to series i (D18), in the
year before the tariff, divided by household spending on series i in that year:

    spending_i = (CPI basket weight_i / weight of "Food purchased from stores") x HFCE "Food and non-alcoholic beverages"

using the basket and HFCE of the same year as the imports (2017 for CA2018, 2024 for CA2025).
The expected price change at 100% pass-through is then tau x s_i, and

    pass-through = observed effect / (tau x s_i).

Known biases, both documented in D21: imports are at border value (retail value is higher, so s is
understated) and include goods sold to restaurants and processors (so s is overstated). HS6 codes are
broader than some tariffed 8-digit lines (flagged as `hs6_broader`, s is then an upper bound).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from load_data import RAW, ROOT  # noqa: E402

YEAR = {"CA2018": 2017, "CA2025": 2024}
RATE = {"CA2018": 0.10, "CA2025": 0.25}
STORES = "Food purchased from stores"
HFCE_FOOD = "Food and non-alcoholic beverages"

# Detailed CPI series (base 2013) have no basket weight of their own: use the closest published class
WEIGHT_PROXY = {
    "Roasted or ground coffee (2013=100)": "Roasted or ground coffee",
    "Dry or fresh pasta (2013=100)": "Pasta products",
    "Fermented or pickled vegetables (2013=100)": "Condiments, spices and vinegars",
    "Sauces, condiments and dips (2013=100)": "Condiments, spices and vinegars",
    "Jam, jelly and other preserves (2013=100)": "Other preserved fruit and fruit preparations",
    "Frozen fruit (2013=100)": "Other preserved fruit and fruit preparations",
    "Nut butter (2013=100)": "All other food preparations",
    "Shrimps and prawns (2013=100)": "Seafood and other marine products",
}
# HS6 subheadings of which only some Canadian 8-digit lines were tariffed (from the official lists, R7, R10)
HS6_BROADER = {
    ("CA2018", "1905.90"): "pizza, quiche, pastries and cakes only (1905.90.51)",
    ("CA2018", "2007.99"): "strawberry jam only (2007.99.10)",
    ("CA2025", "1905.90"): "pizza, quiche, pastries and cakes only (1905.90.51)",
    ("CA2025", "2103.90"): "mayonnaise and salad dressing only (2103.90.10)",
    ("CA2025", "2202.99"): "milk-based beverages only (2202.99.31/33/39)",
}


def usdcad_annual() -> pd.Series:
    d = pd.read_csv(RAW / "usdcad_daily.csv", parse_dates=["date"])
    return d.groupby(d.date.dt.year).usdcad.mean()


def basket_weights(year: int) -> pd.Series:
    w = pd.read_csv(RAW / "cpi_basket_weights_en.csv", encoding="utf-8-sig", low_memory=False)
    w = w[(w.GEO == "Canada") & (w.REF_DATE == year)
          & (w["Price period of weight"] == "Weight at basket reference period prices")
          & (w["Geographic distribution of weight"] == "Distribution to selected geographies")]
    return w.set_index("Products and product groups").VALUE


def hfce_food(year: int) -> float:
    """Household spending on food and non-alcoholic beverages, millions of current dollars."""
    h = pd.read_csv(RAW / "hfce_annual_en.csv", encoding="utf-8-sig", low_memory=False)
    h = h[(h.GEO == "Canada") & (h.Prices == "Current prices") & (h.Estimates == HFCE_FOOD) & (h.REF_DATE == year)]
    return float(h.VALUE.iloc[0])


def exposure(roles: pd.DataFrame) -> pd.DataFrame:
    """One row per (episode, directly treated series): spending, US imports, exposure s and flags."""
    tmap = pd.read_csv(ROOT / "data" / "reference" / "tariff_cpi_map.csv", dtype=str)
    hs6 = pd.read_csv(ROOT / "data" / "reference" / "tariff_hs6_food.csv", dtype=str)
    trade = pd.read_csv(RAW / "comtrade_imports.csv", dtype={"hs6": str})
    cat = pd.read_csv(ROOT / "data" / "processed" / "cpi_food_catalog.csv")
    parent = dict(zip(cat["product"], cat["parent"]))
    fx = usdcad_annual()
    rows = []
    for ev, year in YEAR.items():
        w = basket_weights(year)
        food_spend = hfce_food(year)
        access = hs6[hs6.event_id == ev].set_index("hs6").access
        us = trade[(trade.event_id == ev) & (trade.partner == "United States")].set_index("hs6").value_usd
        world = trade[(trade.event_id == ev) & (trade.partner == "World")].set_index("hs6").value_usd
        treated = roles[(roles.event_id == ev) & (roles.role == "treated") & roles.usable]
        for r in treated.itertuples():
            m = tmap[(tmap.event_id == ev) & (tmap.cpi_product == r.mapped_via)].iloc[0]
            # over-access-only subheadings are left out: imports above the quota are negligible (D18)
            codes = [c for c in m.hs6.split(";") if access.get(c) != "O"]
            wname = WEIGHT_PROXY.get(r.product, r.product)
            node = r.product
            while pd.isna(w.get(wname, np.nan)) and node in parent:  # class absent from that basket year
                node = parent[node]
                wname = node
            spend = w.get(wname, np.nan) / w[STORES] * food_spend
            us_cad = us.reindex(codes).fillna(0).sum() * fx[year] / 1e6
            rows.append({
                "event_id": ev, "series": r.product, "weight_class": wname, "weight_from_proxy": wname != r.product,
                "spending_musd_cad": spend, "us_imports_mcad": us_cad,
                "us_share_of_imports": us.reindex(codes).sum() / world.reindex(codes).sum() if world.reindex(codes).sum() else np.nan,
                "exposure_s": us_cad / spend, "rate": RATE[ev],
                "expected_effect_full_pt": 100 * RATE[ev] * us_cad / spend,
                "hs6_used": ";".join(codes),
                "hs6_broader": "; ".join(HS6_BROADER[(ev, c)] for c in codes if (ev, c) in HS6_BROADER),
            })
    out = pd.DataFrame(rows)
    out["exposure_s_capped"] = out.exposure_s.clip(upper=1.0)
    return out


def intensity_did(Y: pd.DataFrame, exp: pd.DataFrame, donors: list[str], first_month: pd.Period,
                  last_month: pd.Period, pre_start: pd.Period) -> dict:
    """DiD with continuous treatment: y_it = a_i + g_t + beta * D_i * post_t, D_i = 100 * tau * s_i (0 for donors).

    beta is a pass-through rate: the share of the full-pass-through price change that shows up in the CPI.
    Identification needs stronger assumptions than binary DiD [M5]; SE clustered by series.
    """
    import statsmodels.formula.api as smf

    assert exp.exposure_s.notna().all(), f"Missing exposure: {exp[exp.exposure_s.isna()].series.tolist()}"
    dose = dict(zip(exp.series, 100 * exp.rate * exp.exposure_s_capped))
    cols = [c for c in list(dose) + donors if c in Y]
    long = Y[cols].stack().rename("y").reset_index()
    long.columns = ["month", "series", "y"]
    long = long[(long.month >= pre_start) & (long.month <= last_month)]
    long["dose_post"] = long.series.map(dose).fillna(0) * (long.month >= first_month)
    long["month"] = long.month.astype(str)
    m = smf.ols("y ~ dose_post + C(series) + C(month)", data=long).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(long.series)[0]})
    lo, hi = m.conf_int().loc["dose_post"]
    return {"pass_through": m.params["dose_post"], "lo": lo, "hi": hi, "p": m.pvalues["dose_post"],
            "n_treated": len(set(dose) & set(cols)), "n_donors": len(set(donors) & set(cols))}
