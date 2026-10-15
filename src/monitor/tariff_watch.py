"""Tariff watch: does a tariffed CPI series leave the path forecast before the tariff? (D33)

    python src/monitor/tariff_watch.py              # 2026 watch from the frozen pre-tariff forecast
    python src/monitor/tariff_watch.py --backtest   # same rule replayed on the 2018 and 2025 episodes

The forecast made with data up to the month before a tariff (published model and conformal intervals, D23) is the
path prices would have followed without it. Each month after the tariff, every food CPI series is compared with that
path: above the 80% interval, above the 95% interval, within, or below. One series out of ten is expected above its
80% interval by chance (one side of an 80% interval), so the signal is the share of tariffed series above it compared
with the share of untaxed series above it, tested with Fisher's exact test (one-sided) [M6]. Intervals: conformal, calibrated on the 2019-2025 backtest [F4].

The 2026 forecast is frozen in data/reference/forecast_vintage_2026-08.csv (data to August 2026, tariffs in force on
8 September 2026): the monthly refresh replaces app/data/forecasts.csv, which would otherwise erase the counterfactual.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[2]
VINTAGE_2026 = ROOT / "data" / "reference" / "forecast_vintage_2026-08.csv"
EPISODES = {"CA2018": "2018-06", "CA2025": "2025-02", "CA2026": "2026-08"}  # last month before each tariff
ROLES = {"direct", "partial", "input", "over_quota_only"}


def tariffed(event_id: str) -> set[str]:
    """CPI series mapped to the episode's tariff lines (D18), whatever the exposure type."""
    m = pd.read_csv(ROOT / "data" / "reference" / "tariff_cpi_map.csv")
    return set(m[(m.event_id == event_id) & m.exposure.isin(ROLES)].cpi_product)


def status(actual: float, row: pd.Series) -> str:
    if actual > row.hi95:
        return "above 95%"
    if actual > row.hi80:
        return "above 80%"
    if actual < row.lo80:
        return "below 80%"
    return "within"


def watch(cpi: pd.DataFrame, forecast: pd.DataFrame, treated: set[str]) -> pd.DataFrame:
    """One row per (series, month) with an observed value: actual, forecast, gap in % and status."""
    df = forecast.merge(cpi[["series", "month", "value"]], on=["series", "month"], how="inner")
    if df.empty:
        return df.assign(gap_pct=[], status=[], tariffed=[])
    df["gap_pct"] = 100 * (df.value / df.forecast - 1)
    df["status"] = [status(a, r) for a, (_, r) in zip(df.value, df.iterrows())]
    df["tariffed"] = df.series.isin(treated)
    return df.sort_values(["month", "tariffed", "gap_pct"], ascending=[True, False, False]).reset_index(drop=True)


def summary(w: pd.DataFrame) -> pd.DataFrame:
    """Per month: share of tariffed and untaxed series above their 80% interval, and the one-sided Fisher p-value."""
    rows = []
    for month, g in w.groupby("month"):
        up = g.status.isin(["above 80%", "above 95%"])
        t, u = g[g.tariffed], g[~g.tariffed]
        a, b = int(up[g.tariffed].sum()), int(up[~g.tariffed].sum())
        p = fisher_exact([[a, len(t) - a], [b, len(u) - b]], alternative="greater")[1] if len(t) and len(u) else np.nan
        rows.append({"month": month, "h": int(g.h.iloc[0]), "n_tariffed": len(t), "tariffed_above": a,
                     "share_tariffed_above": a / len(t) if len(t) else np.nan, "n_untaxed": len(u), "untaxed_above": b,
                     "share_untaxed_above": b / len(u) if len(u) else np.nan, "p_value": p,
                     "mean_gap_tariffed": t.gap_pct.mean(), "mean_gap_untaxed": u.gap_pct.mean()})
    return pd.DataFrame(rows)


def cpi_long() -> pd.DataFrame:
    """National food CPI series from the app bundle (one base per series)."""
    return pd.read_csv(ROOT / "app" / "data" / "cpi_food.csv")[["series", "month", "value"]]


def backtest_forecast(cpi: pd.DataFrame, origin: str, series: list[str]) -> pd.DataFrame:
    """Re-run the published forecast (D23-D24) as if made at `origin`, with the published conformal quantiles."""
    sys.path.insert(0, str(ROOT / "src" / "forecast"))
    import models

    panel = cpi[cpi.series.isin(series)].pivot_table(index="month", columns="series", values="value", aggfunc="first")
    panel.index = pd.PeriodIndex(panel.index, freq="M")
    panel = panel.loc[:origin].dropna(axis=1, subset=[pd.Period(origin, "M")])
    q = pd.read_csv(ROOT / "app" / "data" / "conformal_quantiles.csv")
    return models.forecast_all(panel, "lightgbm", q)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backtest", action="store_true")
    args = parser.parse_args()
    pd.set_option("display.width", 200)
    cpi = cpi_long()
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    if args.backtest:
        series = sorted(pd.read_csv(VINTAGE_2026).series.unique())  # the 101 series of the published forecast
        for ev in ("CA2018", "CA2025"):
            fc = backtest_forecast(cpi, EPISODES[ev], series)
            w = watch(cpi, fc, tariffed(ev))
            w.assign(event_id=ev).to_csv(out / f"tariff_watch_backtest_{ev}.csv", index=False)
            s = summary(w)
            s.assign(event_id=ev).to_csv(out / f"tariff_watch_backtest_{ev}_summary.csv", index=False)
            print(f"\n{ev} (forecast from {EPISODES[ev]}):")
            print(s.round(3).to_string(index=False))
        return
    fc = pd.read_csv(VINTAGE_2026)
    w = watch(cpi, fc, tariffed("CA2026"))
    w.to_csv(out / "tariff_watch_2026.csv", index=False)
    if w.empty:
        print("No CPI month after August 2026 yet: the watch starts with the September 2026 release.")
        return
    print(summary(w).round(3).to_string(index=False))
    print(w[w.tariffed][["month", "series", "value", "forecast", "gap_pct", "status"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
