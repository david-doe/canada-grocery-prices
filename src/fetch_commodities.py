"""Download monthly world commodity prices from the World Bank "Pink Sheet" (D22).

Usage:
    python src/fetch_commodities.py

Output: data/raw/commodity_prices_monthly.csv (month, commodity, usd), not committed.
The workbook URL changes when the World Bank opens a new yearly folder: if the download fails, take the
current "CMO-Historical-Data-Monthly.xlsx" link from the Pink Sheet page and update WB_URL.
"""
from __future__ import annotations

import io

import pandas as pd
import requests

from load_data import RAW, ROOT

WB_URL = ("https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/"
          "related/CMO-Historical-Data-Monthly.xlsx")
COMMODITIES = ["Cocoa", "Coffee, Arabica", "Tea, avg 3 auctions", "Groundnuts", "Rapeseed oil",
               "Rice, Thai 5%", "Wheat, US HRW", "Orange", "Sugar, world"]
TIMEOUT = 120


def main() -> None:
    resp = requests.get(WB_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT)
    resp.raise_for_status()
    raw = pd.read_excel(io.BytesIO(resp.content), sheet_name="Monthly Prices", header=None)
    updated = str(raw.iloc[3, 0])
    names = [str(n).strip() for n in raw.iloc[4]]
    data = raw.iloc[6:].copy()
    data.columns = ["month"] + names[1:]
    missing = [c for c in COMMODITIES if c not in data.columns]
    assert not missing, f"Commodities not found in the workbook: {missing}"
    long = data[["month"] + COMMODITIES].melt(id_vars="month", var_name="commodity", value_name="usd")
    long["usd"] = pd.to_numeric(long.usd, errors="coerce")
    long = long.dropna()
    long["month"] = long.month.str.replace("M", "-")
    out = RAW / "commodity_prices_monthly.csv"
    long.to_csv(out, index=False)
    print(f"[worldbank] {updated} -> {out.relative_to(ROOT)} ({long.month.min()} to {long.month.max()}, {len(COMMODITIES)} series)")


if __name__ == "__main__":
    main()
