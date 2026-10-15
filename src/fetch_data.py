"""Download the public raw data used by the project.

Sources (see docs/en/decision-log.md, D03, D04, D07):
  - Statistics Canada, table 18-10-0004-01: Consumer Price Index, monthly, not seasonally adjusted
  - Statistics Canada, table 18-10-0245-01: Monthly average retail prices for selected products
  - Statistics Canada, table 18-10-0007-01: Basket weights of the CPI (exposure weights, D21)
  - Statistics Canada, table 36-10-0225-01: Detailed household final consumption expenditure, annual (D21)
  - Bank of Canada Valet API: USD/CAD daily exchange rate (series FXUSDCAD, from 2017-01-03),
    extended back to 2007-05-01 with the legacy noon rate (series IEXE0101), see D15

Usage:
    python src/fetch_data.py            # English tables
    python src/fetch_data.py --lang fr  # French tables (same data, French labels)

Files are written to data/raw/ and are not committed (see .gitignore).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

STATCAN_WDS = "https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{pid}/{lang}"
STATCAN_TABLES = {
    "18100004": "cpi_monthly",               # Consumer Price Index, monthly, not seasonally adjusted
    "18100245": "avg_retail_prices_monthly",  # Monthly average retail prices for selected products
    "18100007": "cpi_basket_weights",         # Basket weights of the CPI (D21)
    "36100225": "hfce_annual",                # Household final consumption expenditure, annual (D21)
}
BOC_VALET = "https://www.bankofcanada.ca/valet/observations/{series}/json"
BOC_SERIES = "FXUSDCAD"        # daily average rate, current methodology
BOC_LEGACY_SERIES = "IEXE0101"  # noon rate, discontinued after 2017-04-28
TIMEOUT = 120


def fetch_statcan_table(pid: str, name: str, lang: str) -> Path:
    """Resolve the full-table zip URL through the WDS API, then download and extract the CSV."""
    meta = requests.get(STATCAN_WDS.format(pid=pid, lang=lang), timeout=TIMEOUT)
    meta.raise_for_status()
    payload = meta.json()
    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"StatCan WDS error for {pid}: {payload}")
    zip_url = payload["object"]

    resp = requests.get(zip_url, timeout=TIMEOUT)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        data_csv = next(n for n in zf.namelist() if n.startswith(pid) and "MetaData" not in n)
        meta_csv = next((n for n in zf.namelist() if "MetaData" in n), None)
        out = RAW / f"{name}_{lang}.csv"
        out.write_bytes(zf.read(data_csv))
        if meta_csv:
            (RAW / f"{name}_{lang}_metadata.csv").write_bytes(zf.read(meta_csv))
    print(f"[statcan] {pid} -> {out.name} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


def _valet_series(series: str, start: str) -> pd.DataFrame:
    resp = requests.get(BOC_VALET.format(series=series), params={"start_date": start}, timeout=TIMEOUT)
    resp.raise_for_status()
    obs = resp.json()["observations"]
    # Skip days without a value (holidays can appear with an empty observation)
    return pd.DataFrame(
        {"date": [o["d"] for o in obs if o.get(series)],
         "usdcad": [float(o[series]["v"]) for o in obs if o.get(series)]}
    )


def fetch_usdcad(start: str = "2007-05-01") -> Path:
    """Daily USD/CAD rate from the Bank of Canada Valet API, saved as a tidy CSV.

    FXUSDCAD starts on 2017-01-03. Earlier days come from the legacy noon rate IEXE0101.
    On their overlap (2017-01-03 to 2017-04-28) the monthly means differ by less than 0.03% (D15).
    The `source` column records which series each row comes from.
    """
    current = _valet_series(BOC_SERIES, start).assign(source=BOC_SERIES)
    legacy = _valet_series(BOC_LEGACY_SERIES, start).assign(source=BOC_LEGACY_SERIES)
    legacy = legacy[legacy.date < current.date.min()]
    df = pd.concat([legacy, current], ignore_index=True).sort_values("date")
    out = RAW / "usdcad_daily.csv"
    df.to_csv(out, index=False)
    print(f"[boc] {BOC_LEGACY_SERIES}+{BOC_SERIES} -> {out.name} "
          f"({len(df)} rows, {df.date.min()} to {df.date.max()}, legacy rows: {len(legacy)})")
    return out


def write_manifest(files: list[Path], lang: str) -> Path:
    """Record each run per language without erasing the other language's entry."""
    path = RAW / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {}
    manifest.pop("files", None)  # drop the old flat format
    manifest.pop("lang", None)
    manifest.pop("downloaded_on", None)
    manifest[lang] = {
        "downloaded_on": date.today().isoformat(),
        "files": {
            f.name: {"bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
            for f in files
        },
    }
    path.write_text(json.dumps(manifest, indent=2))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=["en", "fr"], default="en")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    files = [fetch_statcan_table(pid, name, args.lang) for pid, name in STATCAN_TABLES.items()]
    files.append(fetch_usdcad())

    write_manifest(files, args.lang)
    print("Done. Manifest written to data/raw/manifest.json")


if __name__ == "__main__":
    main()
