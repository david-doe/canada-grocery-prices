"""A small analytical warehouse in DuckDB, with SQL answers to business questions (D31).

    python src/sql/warehouse.py            # build data/processed/grocery.duckdb and run every query in sql/

Tables (star-like layout, all from versioned or app data, so the warehouse builds without raw downloads):
- dim_series      CPI food series with EN/FR labels and parent (hierarchy)
- fact_cpi        monthly CPI value per national series since 2010
- fact_forecast   12-month forecasts with conformal intervals
- fact_province   12-month change of store-food prices by province
- dim_tariff_line food HS6 subheadings on each tariff list, with access type and rate
- map_tariff_cpi  hand-made mapping HS6 -> CPI series with exposure type (D18)
- fact_exposure   US import exposure per treated series (D21)
Queries live in sql/*.sql, one business question per file, so they can be read and reviewed like code.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
APP, REF, SQL = ROOT / "app" / "data", ROOT / "data" / "reference", ROOT / "sql"
DB = ROOT / "data" / "processed" / "grocery.duckdb"


def build(path: Path | str = DB) -> duckdb.DuckDBPyConnection:
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
    con = duckdb.connect(str(path))
    tm = pd.read_csv(REF / "tariff_cpi_map.csv", dtype=str)
    long_map = tm.assign(hs6=tm.hs6.str.split(";")).explode("hs6")[["event_id", "hs6", "cpi_product", "exposure", "confidence"]]
    tables = {
        "dim_series": pd.read_csv(APP / "series_labels.csv"),
        "fact_cpi": pd.read_csv(APP / "cpi_food.csv"),
        "fact_forecast": pd.read_csv(APP / "forecasts.csv"),
        "fact_province": pd.read_csv(APP / "province_food.csv"),
        "dim_tariff_line": pd.read_csv(REF / "tariff_hs6_food.csv", dtype=str),
        "map_tariff_cpi": long_map,
        "fact_exposure": pd.read_csv(APP / "exposure.csv"),
    }
    for name, df in tables.items():
        con.register("tmp", df)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM tmp")
        con.unregister("tmp")
    return con


def run_queries(con: duckdb.DuckDBPyConnection) -> dict[str, pd.DataFrame]:
    return {f.stem: con.execute(f.read_text(encoding="utf-8")).df() for f in sorted(SQL.glob("*.sql"))}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    con = build()
    for name, df in run_queries(con).items():
        print(f"\n== {name} ({len(df)} rows)")
        print(df.head(12).to_string(index=False))
    print(f"\nWarehouse: {DB.relative_to(ROOT)}")
