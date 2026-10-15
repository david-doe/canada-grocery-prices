"""Monthly refresh after each CPI release: one command, same steps every month (D25).

    python src/refresh.py

1. Download the latest public data (StatCan EN and FR tables, Bank of Canada, World Bank).
2. Rebuild the food CPI catalogue and the treatment roles (D17, D18).
3. Re-run the published forecast (model chosen by D24, conformal quantiles from the notebook 06 backtest).
4. Recompute the cheese scenarios on the forecast frozen before the 2026 tariffs (D06, D33).
5. Rebuild the app data bundle (app/data/).
The 2018 and 2025 causal estimates are historical and are not recomputed.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
sys.path[:0] = [str(SRC), str(SRC / "forecast")]
from cpi_catalog import build_catalog  # noqa: E402
from load_data import ROOT  # noqa: E402

PROC = ROOT / "data" / "processed"
PUBLISHED_MODEL = "lightgbm"      # D23-D24: simplest model within 5% of the best MASE
CHEESE_EXPOSURE = 0.024           # D06: US share of cheese spending (2025 imports, notebook 06)
CHEESE_TARIFF = 0.25
SCENARIOS = {"low (25%, temporary)": (0.25, True), "central (60%)": (0.60, False), "high (70%, persistent)": (0.70, False)}


def run(*args: str) -> None:
    print(">", " ".join(args))
    subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


def cheese_scenarios(fc: pd.DataFrame) -> pd.DataFrame:
    base = fc[fc.series == "Cheese"].copy()
    months = pd.PeriodIndex(base.month, freq="M")
    k = np.array([(m - pd.Period("2026-09", "M")).n for m in months])
    full = CHEESE_TARIFF * CHEESE_EXPOSURE
    out = base[["month", "forecast", "lo80", "hi80", "lo95", "hi95"]].copy()
    for name, (pt, temporary) in SCENARIOS.items():
        eff = pt * full * (np.clip(1 - k / 12, 0, None) if temporary else (k >= 0).astype(float))
        out[name] = base.forecast.to_numpy() * (1 + eff)
    return out


def main() -> None:
    run("src/fetch_data.py")
    run("src/fetch_data.py", "--lang", "fr")
    run("src/fetch_commodities.py")

    build_catalog().to_csv(PROC / "cpi_food_catalog.csv", index=False)
    import tariff_map
    tariff_map.roles().to_csv(PROC / "treatment_roles.csv", index=False)

    import models
    panel = models.food_panel()
    q = pd.read_csv(PROC / "conformal_quantiles.csv")
    fc = models.forecast_all(panel, PUBLISHED_MODEL, q)
    fc.to_csv(PROC / "forecasts.csv", index=False)
    # The cheese scenarios start from the forecast frozen before the 2026 tariffs (D33): a forecast re-run on months
    # after September 2026 would already contain the tariff it is meant to be compared with.
    cheese_scenarios(pd.read_csv(ROOT / "data" / "reference" / "forecast_vintage_2026-08.csv")).to_csv(
        PROC / "scenarios_cheese.csv", index=False)

    run("src/build_app_data.py")
    print(f"Refresh done: last CPI month {panel.index.max()}, forecasts to {fc.month.max()}.")


if __name__ == "__main__":
    main()
