"""Catalogue of food CPI sub-indices (table 18-10-0004-01): hierarchy, coverage, eligibility.

Used by notebooks/01_cpi_food_coverage.ipynb (next step 2 in CONTRIBUTING.md) and, later, to pick
treated and control series for each tariff episode (D05, D17).
"""
from __future__ import annotations

import io

import pandas as pd

from load_data import RAW, ROOT, read_statcan

TARIFF_EVENTS = ROOT / "data" / "reference" / "tariff_events.csv"
MIN_PRE_MONTHS = 36  # D17: at least three full seasonal cycles before a tariff starts


def read_members(lang: str = "en") -> pd.DataFrame:
    """Member table of the StatCan metadata file (geographies and products, with parents)."""
    text = (RAW / f"cpi_monthly_{lang}_metadata.csv").read_text(encoding="utf-8-sig")
    header = '"Member Name"' if lang == "en" else '"Nom du membre"'
    block = next(b.strip() for b in text.split("\n\n") if header in b.strip().split("\n", 1)[0])
    sep = "," if lang == "en" else ";"
    df = pd.read_csv(io.StringIO(block), dtype=str, sep=sep)
    df.columns = ["dim", "name", "code", "member_id", "parent_id", "terminated", "notes", "definition"][: len(df.columns)]
    return df


def food_tree(members: pd.DataFrame) -> pd.DataFrame:
    """Depth-first list of the 'Food' subtree: one row per product with its depth and parent name."""
    prod = members[members.dim == "2"]
    name = dict(zip(prod.member_id, prod.name))
    children = prod.groupby("parent_id").member_id.apply(list).to_dict()
    root = prod.loc[prod.name == "Food", "member_id"].iloc[0]

    rows, stack = [], [(root, 0)]
    while stack:
        node, depth = stack.pop()
        parent = prod.loc[prod.member_id == node, "parent_id"].iloc[0]
        rows.append({"member_id": node, "product": name[node], "depth": depth,
                     "parent": name.get(parent), "is_leaf": node not in children})
        stack.extend((c, depth + 1) for c in reversed(children.get(node, [])))
    return pd.DataFrame(rows)


def coverage(cpi: pd.DataFrame, products: list[str]) -> pd.DataFrame:
    """Start, end, length, base period and number of geographies for each product.

    A product has one index base (UOM) except 'All-items'; the national series defines start/end.
    """
    sub = cpi[cpi["product"].isin(products) & (cpi.UOM != "1992=100")]
    nat = (sub[sub.GEO == "Canada"].groupby("product")
           .agg(base=("UOM", "first"), start=("REF_DATE", "min"), end=("REF_DATE", "max"), n_months=("VALUE", "count")))
    geo = sub.groupby("product").GEO.agg(n_geo="nunique",
                                         has_ontario=lambda g: "Ontario" in set(g))
    return nat.join(geo)


def episode_eligibility(cov: pd.DataFrame, events: pd.DataFrame, min_pre: int = MIN_PRE_MONTHS) -> pd.DataFrame:
    """For each product and tariff episode (D17):
    - `_pre`: months of data before the first tariff month;
    - `_post`: months of data from the first tariff month to the last published month;
    - `_pre_ok`: enough history to build a synthetic control (pre >= min_pre).
    A series can be used for an episode once `_pre_ok` is true and `_post` > 0.
    """
    out = cov[[]].copy()
    for ev in events.itertuples():
        start = pd.Period(ev.start_date, freq="M")
        pre = cov.start.apply(lambda s: max((start - s).n, 0))
        post = cov.end.apply(lambda e: max((e - start).n + 1, 0))
        out[f"{ev.event_id}_pre"] = pre
        out[f"{ev.event_id}_post"] = post
        out[f"{ev.event_id}_pre_ok"] = pre >= min_pre
    return out


def build_catalog() -> pd.DataFrame:
    """Food tree + coverage + per-episode eligibility + French labels, one row per product."""
    tree = food_tree(read_members("en"))
    cpi = read_statcan("cpi_monthly", columns=["REF_DATE", "GEO", "Products and product groups", "UOM", "VALUE"])
    cov = coverage(cpi, tree["product"].tolist())
    events = pd.read_csv(TARIFF_EVENTS)
    elig = episode_eligibility(cov, events)
    fr = read_members("fr")
    fr_names = dict(zip(fr.loc[fr.dim == "2", "member_id"], fr.loc[fr.dim == "2", "name"]))
    cat = tree.join(cov, on="product").join(elig, on="product")
    cat.insert(2, "product_fr", cat.member_id.map(fr_names))
    return cat
