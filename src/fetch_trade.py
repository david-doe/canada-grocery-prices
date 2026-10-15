"""Download Canadian imports by HS 6-digit subheading from the UN Comtrade public API (D21).

For each tariff episode, imports in the calendar year before the tariff (2017 for CA2018, 2024 for CA2025)
of every food HS6 subheading on that episode's list (data/reference/tariff_hs6_food.csv), from the
United States (partner 842) and from the world (partner 0). Values are in US dollars as reported to
UN Comtrade (Canada reports imports at customs value).

Usage:
    python src/fetch_trade.py

Output: data/raw/comtrade_imports.csv (not committed). The public preview endpoint needs no key and
returns at most 500 records per call, so one call is made per episode and partner.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

from load_data import RAW, ROOT

COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REPORTER_CANADA = 124
PARTNERS = {842: "United States", 0: "World"}
IMPORT_YEAR = {"CA2018": 2017, "CA2025": 2024, "CA2026": 2025}
TIMEOUT = 120


def fetch(event_id: str, codes: list[str], partner: int) -> pd.DataFrame:
    params = {"reporterCode": REPORTER_CANADA, "period": IMPORT_YEAR[event_id], "partnerCode": partner,
              "cmdCode": ",".join(codes), "flowCode": "M"}
    resp = requests.get(COMTRADE, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        return pd.DataFrame(columns=["event_id", "year", "partner", "hs6", "value_usd"])
    return pd.DataFrame({"event_id": event_id, "year": df.refYear, "partner": PARTNERS[partner],
                         "hs6": df.cmdCode.str[:4] + "." + df.cmdCode.str[4:], "value_usd": df.primaryValue})


def main() -> None:
    hs6 = pd.read_csv(ROOT / "data" / "reference" / "tariff_hs6_food.csv", dtype=str)
    frames = []
    for ev, codes in hs6.groupby("event_id").hs6:
        if ev not in IMPORT_YEAR:
            continue
        clean = sorted({c.replace(".", "") for c in codes})
        for partner in PARTNERS:
            # 183 codes for CA2025 stay well under the 500-record limit of the preview endpoint
            df = fetch(ev, clean, partner)
            print(f"[comtrade] {ev} {IMPORT_YEAR[ev]} {PARTNERS[partner]}: {len(df)} of {len(clean)} subheadings")
            frames.append(df)
            time.sleep(2)  # be gentle with the public endpoint
    out = RAW / "comtrade_imports.csv"
    pd.concat(frames, ignore_index=True).to_csv(out, index=False)
    print(f"Done -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
