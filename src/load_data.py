"""Load the raw files written by fetch_data.py into tidy DataFrames.

StatCan full-table CSVs differ by language (checked on 2026-10-14, see D16):
  - EN files use "," as separator, FR files use ";". Both start with a UTF-8 BOM.
  - Column names are translated (REF_DATE / PÉRIODE DE RÉFÉRENCE, VECTOR / VECTEUR, ...).
  - Values are identical: same rows, same VECTOR ids, same VALUE.
Numbers therefore come from the EN tables; FR tables only supply labels, joined on VECTOR.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

SEP = {"en": ",", "fr": ";"}
FR_TO_EN = {
    "PÉRIODE DE RÉFÉRENCE": "REF_DATE",
    "GÉO": "GEO",
    "Produits et groupes de produits": "Products and product groups",
    "Produits": "Products",
    "UNITÉ DE MESURE": "UOM",
    "VECTEUR": "VECTOR",
    "VALEUR": "VALUE",
    "STATUS": "STATUS",
    "SYMBOLE": "SYMBOL",
    "TERMINÉ": "TERMINATED",
}
PRODUCT_COL = {"cpi_monthly": "Products and product groups", "avg_retail_prices_monthly": "Products"}


def read_statcan(name: str, lang: str = "en", columns: list[str] | None = None) -> pd.DataFrame:
    """Read a StatCan table with English column names, whatever the file language.

    `columns` uses English names. REF_DATE is parsed to a monthly Period.
    """
    df = pd.read_csv(RAW / f"{name}_{lang}.csv", sep=SEP[lang], encoding="utf-8-sig", low_memory=False)
    if lang == "fr":
        df = df.rename(columns=FR_TO_EN)
    df = df.rename(columns={PRODUCT_COL[name]: "product"})
    if columns:
        df = df[[("product" if c == PRODUCT_COL[name] else c) for c in columns]]
    if "REF_DATE" in df:
        df["REF_DATE"] = pd.PeriodIndex(df["REF_DATE"], freq="M")
    return df


def read_labels(name: str) -> pd.DataFrame:
    """One row per VECTOR with English and French GEO and product labels."""
    cols = ["VECTOR", "GEO", "product"]
    en = read_statcan(name, "en").drop_duplicates("VECTOR")[cols]
    fr = read_statcan(name, "fr").drop_duplicates("VECTOR")[cols]
    return en.merge(fr, on="VECTOR", suffixes=("_en", "_fr"))


def read_usdcad_monthly() -> pd.DataFrame:
    """Monthly average USD/CAD (D07), from the spliced daily series (D15)."""
    df = pd.read_csv(RAW / "usdcad_daily.csv", parse_dates=["date"])
    out = df.groupby(df.date.dt.to_period("M")).agg(usdcad=("usdcad", "mean"), source=("source", "last"))
    out.index.name = "REF_DATE"
    return out.reset_index()
