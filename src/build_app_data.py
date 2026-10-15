"""Build the small, versioned data bundle read by the Streamlit app (app/data/, D24).

Raw files stay out of git (CONTRIBUTING.md); the app only needs derived tables of a few hundred KB.
Run after the notebooks: python src/build_app_data.py
"""
from __future__ import annotations

import json
import shutil

import numpy as np
import pandas as pd

from load_data import ROOT, read_labels, read_statcan

OUT = ROOT / "app" / "data"
PROC = ROOT / "data" / "processed"
START = "2010-01"
BREAK = "2024-01"  # average retail prices: more grocers added to the sample (D04, S3)


FOOD_LINES_OUT = ("01", "23", "24")  # live animals, animal feed, tobacco: not in the food CPI (D18)


def _us_food_imports(event_id: str, year: int) -> pd.DataFrame:
    """US imports (M CAD) of the tariffed food HS6 lines of an episode, with their tariff rate (D21)."""
    import sys
    sys.path.insert(0, str(ROOT / "src" / "causal"))
    import exposure as E

    hs6 = pd.read_csv(ROOT / "data/reference/tariff_hs6_food.csv", dtype=str)
    hs6 = hs6[(hs6.event_id == event_id) & (hs6.access != "O") & ~hs6.chapter.isin(FOOD_LINES_OUT)
              & ~hs6.hs6.str[:4].between("2203", "2208")]
    trade = pd.read_csv(ROOT / "data/raw/comtrade_imports.csv", dtype={"hs6": str})
    us = trade[(trade.event_id == event_id) & (trade.partner == "United States")].set_index("hs6").value_usd
    out = hs6[["hs6", "rate"]].copy()
    out["us_mcad"] = out.hs6.map(us).fillna(0) * E.usdcad_annual()[year] / 1e6
    out["rate"] = out.rate.str.rstrip("%").astype(float) / 100
    return out


def tariff_cost_table(cat: pd.DataFrame) -> pd.DataFrame:
    """Share of household food spending exposed to each tariff, and the pass-through to apply (D26).

    Cost per dollar of groceries = tariff rate x pass-through x share of spending on tariffed US goods.
    Share: US imports of tariffed food lines / household spending on food and non-alcoholic beverages (2024).
      central = lines mapped to the treated CPI series (D21); low = exact 6-digit codes only;
      high = every tariffed food line, including ingredients.
    """
    import sys
    sys.path.insert(0, str(ROOT / "src" / "causal"))
    import exposure as E

    food = E.hfce_food(2024)
    expo = pd.read_csv(PROC / "exposure.csv")
    x25 = expo[expo.event_id == "CA2025"]
    ptc = pd.read_csv(PROC / "pass_through_commodity.csv")
    pref = ptc[(ptc.event_id == "CA2025") & (ptc["sample"] == "without coffee and confectionery")
               & (ptc.outcome == "commodity-adjusted (lags 0-11)")].iloc[0]
    all25 = _us_food_imports("CA2025", 2024)
    all26 = _us_food_imports("CA2026", 2025)
    rate26 = float((all26.us_mcad * all26.rate).sum() / all26.us_mcad.sum())
    rows = [
        {"event_id": "CA2025", "months": 6, "rate": 0.25,
         "share_central": x25.us_imports_mcad.sum() / food,
         "share_low": x25[x25.hs6_broader.fillna("") == ""].us_imports_mcad.sum() / food,
         "share_high": all25.us_mcad.sum() / food,
         "pt_central": pref.pass_through, "pt_low": max(pref.lo, 0.0), "pt_high": pref.hi,
         "pt_source": "measured (D22)"},
        {"event_id": "CA2026", "months": 12, "rate": rate26,
         "share_central": all26.us_mcad.sum() / food, "share_low": all26.us_mcad.sum() / food,
         "share_high": all26.us_mcad.sum() / food,
         "pt_central": 0.60, "pt_low": 0.25, "pt_high": 0.70, "pt_source": "scenarios (D06)"},
    ]
    return pd.DataFrame(rows)


def lookup_table() -> pd.DataFrame:
    """Searchable list: which products were tariffed, when, at what rate, in which CPI series (D18)."""
    tmap = pd.read_csv(ROOT / "data/reference/tariff_cpi_map.csv", dtype=str)
    hs6 = pd.read_csv(ROOT / "data/reference/tariff_hs6_food.csv", dtype=str)
    rate = hs6.groupby("event_id").apply(lambda g: dict(zip(g.hs6, g.rate)), include_groups=False).to_dict()
    lab = pd.read_csv(PROC / "cpi_food_catalog.csv").set_index("product").product_fr
    ev = pd.read_csv(ROOT / "data/reference/tariff_events.csv").set_index("event_id")
    rows = []
    for r in tmap.itertuples():
        rates = sorted({rate[r.event_id].get(h, "") for h in r.hs6.split(";")} - {""})
        rows.append({"event_id": r.event_id, "start": ev.loc[r.event_id, "start_date"],
                     "end": ev.loc[r.event_id, "end_date"] if pd.notna(ev.loc[r.event_id, "end_date"]) else "",
                     "series": r.cpi_product, "series_fr": lab.get(r.cpi_product, r.cpi_product),
                     "exposure": r.exposure, "rate": " / ".join(rates), "note_en": r.note_en, "note_fr": r.note_fr})
    return pd.DataFrame(rows)


def province_table() -> pd.DataFrame:
    """Year-over-year change of the Food CPI by province (D13), monthly since 2019."""
    c = read_statcan("cpi_monthly", columns=["REF_DATE", "GEO", "Products and product groups", "UOM", "VALUE"])
    c = c[(c["product"] == "Food purchased from stores") & (c.UOM == "2002=100")]
    w = c.pivot_table(index="REF_DATE", columns="GEO", values="VALUE").sort_index()
    yoy = (100 * (w / w.shift(12) - 1)).loc["2019-01":]
    out = yoy.stack().rename("yoy").reset_index().rename(columns={"REF_DATE": "month", "GEO": "geo"})
    out["month"] = out.month.astype(str)
    return out


def basket_table() -> pd.DataFrame:
    """2025 tariffed CPI series: average-household share of food spending and exposure s (D21, D27).

    The ten series with the most US imports are listed; the rest is pooled in "Other tariffed products".
    Untaxed food spending is left out (exposure 0).
    """
    import sys
    sys.path.insert(0, str(ROOT / "src" / "causal"))
    import exposure as E

    food = E.hfce_food(2024)
    x = pd.read_csv(PROC / "exposure.csv")
    x = x[x.event_id == "CA2025"].sort_values("us_imports_mcad", ascending=False)
    lab = pd.read_csv(PROC / "cpi_food_catalog.csv").set_index("product").product_fr
    top, rest = x.head(10), x.iloc[10:]
    rows = [{"series": r.series, "series_fr": lab.get(r.series, r.series), "spend_share": r.spending_musd_cad / food,
             "exposure": min(r.exposure_s, 1.0), "upper_bound": bool(r.hs6_broader) if isinstance(r.hs6_broader, str) else False}
            for r in top.itertuples()]
    rows.append({"series": "Other tariffed products", "series_fr": "Autres produits taxés",
                 "spend_share": rest.spending_musd_cad.sum() / food,
                 "exposure": rest.us_imports_mcad.sum() / rest.spending_musd_cad.sum(), "upper_bound": False})
    return pd.DataFrame(rows)


# 2026 tariff lines grouped by what households buy (D18 mapping, D33): only cheese is taxed as sold in stores
GROUPS_2026 = [
    ("0406", "Cheese", "Fromage", False),
    ("1901.20", "Bakery mixes and doughs (bread, cakes, cookies)", "Mélanges et pâtes de boulangerie (pain, gâteaux, biscuits)", True),
    ("0402;0404", "Milk powders and whey (yogurt, ice cream)", "Poudres de lait et lactosérum (yogourt, crème glacée)", True),
    ("0409;1703", "Honey and molasses", "Miel et mélasse", True),
]


def basket_2026_table() -> pd.DataFrame:
    """2026 tariffed food lines by group: share of household food spending and rate (D26, D33).

    Same denominator as tariff_cost_table, so the groups add up to the published 2026 share. Ingredients are
    upper bounds: part of their imports goes to restaurants and industry, not to grocery shelves.
    """
    import sys
    sys.path.insert(0, str(ROOT / "src" / "causal"))
    import exposure as E

    food = E.hfce_food(2024)
    imp = _us_food_imports("CA2026", 2025)
    rows = []
    for prefixes, en, fr, upper in GROUPS_2026:
        g = imp[imp.hs6.str.startswith(tuple(prefixes.split(";")))]
        rows.append({"group": en, "group_fr": fr, "hs6": ";".join(g.hs6), "us_mcad": g.us_mcad.sum(),
                     "share": g.us_mcad.sum() / food, "rate": float((g.us_mcad * g.rate).sum() / g.us_mcad.sum()),
                     "upper_bound": upper})
    out = pd.DataFrame(rows)
    assert len(set(";".join(out.hs6).split(";"))) == len(imp), "every 2026 line belongs to one group"
    return out


def monthly_notes() -> dict:
    """Facts for the automatic 'this month' paragraph (D27): computed, never written by hand."""
    cat = pd.read_csv(PROC / "cpi_food_catalog.csv")
    lab = cat.set_index("product").product_fr.to_dict()
    c = pd.read_csv(OUT / "cpi_food.csv")
    w = c.pivot_table(index="month", columns="series", values="value").sort_index()
    last, prev = w.index[-1], w.index[-2]
    yoy = 100 * (w.iloc[-1] / w.iloc[-13] - 1)
    yoy_prev = 100 * (w.iloc[-2] / w.iloc[-14] - 1)
    leaves = set(cat.loc[cat.is_leaf, "product"])
    detail = yoy[[s for s in yoy.index if s in leaves]].dropna()
    prov = pd.read_csv(OUT / "province_food.csv")
    pl = prov[(prov.month == prov.month.max()) & (prov.geo != "Canada")].sort_values("yoy")
    fc = pd.read_csv(PROC / "forecasts.csv")
    f = fc[fc.series == "Food purchased from stores"]
    stores = w["Food purchased from stores"]
    item = lambda s: {"en": s.replace(" (2013=100)", "").replace(" (202304=100)", "").replace(" (202404=100)", ""),
                      "fr": lab.get(s, s).replace(" (2013=100)", "").replace(" (202304=100)", "").replace(" (202404=100)", ""),
                      "yoy": round(float(detail[s]), 1)}
    return {
        "month": last, "previous_month": prev,
        "stores_yoy": round(float(yoy["Food purchased from stores"]), 1),
        "stores_yoy_prev": round(float(yoy_prev["Food purchased from stores"]), 1),
        "food_yoy": round(float(yoy["Food"]), 1),
        "restaurants_yoy": round(float(yoy["Food purchased from restaurants"]), 1),
        "top_up": [item(s) for s in detail.sort_values(ascending=False).index[:3]],
        "top_down": [item(s) for s in detail.sort_values().index[:3]],
        "province_high": {"geo": pl.geo.iloc[-1], "yoy": round(float(pl.yoy.iloc[-1]), 1)},
        "province_low": {"geo": pl.geo.iloc[0], "yoy": round(float(pl.yoy.iloc[0]), 1)},
        "forecast_12m": round(float(100 * (f.forecast.iloc[-1] / stores.iloc[-1] - 1)), 1),
        "forecast_month": f.month.iloc[-1],
    }


def share_cards(notes: dict) -> None:
    """1200 x 630 summary images (EN, FR) for sharing on LinkedIn or by e-mail (D27). Sober, no emojis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cost = pd.read_csv(OUT / "tariff_cost.csv").set_index("event_id").loc["CA2025"]
    per100 = 100 * cost.rate * cost.pt_central * cost.share_central
    ptc = pd.read_csv(PROC / "pass_through_commodity.csv")
    pref = ptc[(ptc.event_id == "CA2025") & (ptc["sample"] == "without coffee and confectionery")
               & (ptc.outcome == "commodity-adjusted (lags 0-11)")].iloc[0]
    texts = {
        "en": {"title": "What Canada's counter-tariffs cost at the grocery store",
               "k": [(f"${per100:.2f}", "per $100 of groceries\nwhile the 2025 tariffs applied"),
                     (f"{100 * pref.pass_through:.0f}%", "of the 2025 tariff\nreached shelf prices"),
                     (f"{notes['stores_yoy']:+.1f}%", f"grocery prices over 12 months\n(to {notes['month']})")],
               "foot": "Public data, every number sourced  ·  David Doe, data science student, University of Lille"},
        "fr": {"title": "Ce que les contre-tarifs canadiens coûtent à l'épicerie",
               "k": [(f"{per100:.2f} $".replace(".", ","), "par 100 $ d'épicerie pendant\nles tarifs de 2025"),
                     (f"{100 * pref.pass_through:.0f} %", "du tarif de 2025\nrépercuté en magasin"),
                     (f"{notes['stores_yoy']:+.1f} %".replace(".", ","), f"prix en magasin sur 12 mois\n(jusqu'à {notes['month']})")],
               "foot": "Données publiques, chaque chiffre sourcé  ·  David Doe, étudiant en data science, Université de Lille"},
    }
    for lang, tx in texts.items():
        fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor="#fcfcfb")
        fig.text(0.06, 0.80, tx["title"], fontsize=25, fontweight="bold", color="#0b0b0b")
        for i, (v, l) in enumerate(tx["k"]):
            x = 0.06 + i * 0.31
            fig.add_artist(plt.Line2D([x, x + 0.26], [0.64, 0.64], color="#2a78d6", lw=3, transform=fig.transFigure))
            fig.text(x, 0.50, v, fontsize=46, fontweight="bold", color="#0b0b0b")
            fig.text(x, 0.44, l, fontsize=15, color="#52514e", va="top", linespacing=1.4)
        fig.text(0.06, 0.08, "canada-grocery-prices.streamlit.app", fontsize=17, color="#2a78d6")
        fig.text(0.06, 0.03, tx["foot"], fontsize=11, color="#52514e")
        fig.savefig(OUT / f"share_card_{lang}.png", facecolor=fig.get_facecolor())
        plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cat = pd.read_csv(PROC / "cpi_food_catalog.csv")

    # 1. National food CPI series, monthly, with EN/FR labels and hierarchy
    c = read_statcan("cpi_monthly", columns=["REF_DATE", "GEO", "Products and product groups", "UOM", "VALUE"])
    c = c[(c.GEO == "Canada") & c["product"].isin(cat["product"]) & (c.UOM != "1992=100") & (c.REF_DATE >= START)]
    c = c.rename(columns={"REF_DATE": "month", "product": "series", "VALUE": "value", "UOM": "base"})
    c["month"] = c.month.astype(str)
    c[["month", "series", "base", "value"]].to_csv(OUT / "cpi_food.csv", index=False)
    cat[["product", "product_fr", "parent", "depth"]].rename(columns={"product": "series", "product_fr": "series_fr"}) \
        .to_csv(OUT / "series_labels.csv", index=False)

    # 2. Average retail prices (dashboard only, D04), with the January 2024 break flag
    a = read_statcan("avg_retail_prices_monthly", columns=["REF_DATE", "GEO", "Products", "VECTOR", "VALUE"])
    a = a[a.GEO == "Canada"].rename(columns={"REF_DATE": "month", "product": "item", "VALUE": "price"})
    lab = read_labels("avg_retail_prices_monthly").set_index("VECTOR").product_fr
    a["item_fr"] = a.VECTOR.map(lab)
    a["after_2024_break"] = a.month >= pd.Period(BREAK, "M")
    a["month"] = a.month.astype(str)
    a[["month", "item", "item_fr", "price", "after_2024_break"]].to_csv(OUT / "avg_prices.csv", index=False)

    # 3. Results tables produced by the notebooks
    for name in ["forecasts.csv", "scenarios_cheese.csv", "sc_results.csv", "pass_through.csv",
                 "pass_through_commodity.csv", "exposure.csv", "conformal_quantiles.csv"]:
        shutil.copy(PROC / name, OUT / name)
    bt = pd.read_csv(PROC / "backtest.csv")
    bt.groupby(["model", "h"])[["mase", "smape"]].mean().reset_index().to_csv(OUT / "backtest_summary.csv", index=False)

    tariff_cost_table(cat).to_csv(OUT / "tariff_cost.csv", index=False)
    lookup_table().to_csv(OUT / "tariff_lookup.csv", index=False)
    province_table().to_csv(OUT / "province_food.csv", index=False)
    basket_table().to_csv(OUT / "basket_2025.csv", index=False)
    basket_2026_table().to_csv(OUT / "basket_2026.csv", index=False)
    notes = monthly_notes()
    (OUT / "monthly_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    share_cards(notes)

    size = sum(f.stat().st_size for f in OUT.iterdir()) / 1e6
    print(f"app/data: {len(list(OUT.iterdir()))} files, {size:.1f} MB")


if __name__ == "__main__":
    main()
