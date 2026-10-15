"""Remove the world-commodity-price component from treated CPI series (next step 4b, D22).

For a treated series i linked to a commodity c (data/reference/commodity_map.csv):
1. Elasticities are estimated on 12-month log changes, over all months before the tariff since 2005-01:
       D12 ln P_i,t = a + sum_k b_k * D12 xk_t + e_t
   where xk_t = mean of ln(world price of c in CAD) over lag block k (0-2, 3-5, 6-8, 9-11 months).
   12-month changes remove seasonality and spurious level trends, and the long window gives the
   commodity cycles enough variation (a 60-month window did not, see D22).
2. The commodity component in levels, comp_t = 100 * sum_k b_k * (xk_t - mean of xk over the SC pre window),
   is subtracted from the series before the synthetic control is fitted again.
Canada is a price taker on these world markets, so the commodity price is not affected by Canadian tariffs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from load_data import RAW, ROOT, read_usdcad_monthly  # noqa: E402

LAG_BLOCKS = [(0, 2), (3, 5), (6, 8), (9, 11)]
LONG_LAG_BLOCKS = LAG_BLOCKS + [(12, 14), (15, 17)]  # sensitivity: slower retail adjustment
ESTIMATION_START = pd.Period("2005-01", "M")


def commodity_map() -> dict[str, str]:
    m = pd.read_csv(ROOT / "data" / "reference" / "commodity_map.csv")
    return dict(zip(m.cpi_product, m.commodity))


def world_prices_cad() -> pd.DataFrame:
    """ln(price in CAD), one column per commodity, monthly PeriodIndex (from 2007-05, start of USD/CAD)."""
    p = pd.read_csv(RAW / "commodity_prices_monthly.csv")
    p["month"] = pd.PeriodIndex(p.month, freq="M")
    wide = p.pivot(index="month", columns="commodity", values="usd")
    fx = read_usdcad_monthly().set_index("REF_DATE").usdcad
    wide = wide.loc[wide.index.isin(fx.index)]
    return np.log(wide.mul(fx.reindex(wide.index), axis=0))


def lag_blocks(x: pd.Series, blocks=LAG_BLOCKS) -> pd.DataFrame:
    return pd.DataFrame({f"lag{a}_{b}": pd.concat([x.shift(j) for j in range(a, b + 1)], axis=1).mean(axis=1)
                         for a, b in blocks})


def elasticities(log_cpi: pd.Series, log_price: pd.Series, t0: pd.Period, blocks=LAG_BLOCKS) -> dict:
    """OLS of 12-month changes of the CPI series on 12-month changes of the lag blocks, months <= t0."""
    X = lag_blocks(log_price, blocks)
    d = pd.concat([log_cpi.diff(12).rename("y"), X.diff(12)], axis=1).loc[ESTIMATION_START: t0].dropna()
    A = np.column_stack([np.ones(len(d)), d[X.columns].to_numpy()])
    beta, *_ = np.linalg.lstsq(A, d.y.to_numpy(), rcond=None)
    resid = d.y.to_numpy() - A @ beta
    r2 = 1 - resid @ resid / np.sum((d.y - d.y.mean()) ** 2)
    return {"b": pd.Series(beta[1:], index=X.columns), "r2": float(r2), "n_obs": len(d),
            "start": str(d.index.min()), "elasticity": float(beta[1:].sum())}


def adjust(wide: pd.DataFrame, Y: pd.DataFrame, ep, treated: list[str], blocks=LAG_BLOCKS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Commodity-adjusted outcome for mapped treated series; returns (table of elasticities, adjusted Y)."""
    cmap = commodity_map()
    prices = world_prices_cad()
    w = ep.windows(Y.index.max())
    Yadj = Y.copy()
    rows = []
    for s in treated:
        if s not in cmap or s not in Y:
            continue
        est = elasticities(np.log(wide[s]), prices[cmap[s]], ep.t0, blocks)
        X = lag_blocks(prices[cmap[s]], blocks).reindex(Y.index)
        Xc = X - X.loc[w["pre"][0]: w["pre"][1]].mean()
        comp = 100 * (Xc @ est["b"])
        Yadj[s] = Y[s] - comp
        rows.append({"event_id": ep.event_id, "series": s, "commodity": cmap[s], "elasticity": est["elasticity"],
                     "r2": est["r2"], "n_obs": est["n_obs"], "estimated_from": est["start"],
                     "commodity_part_during": float(comp.loc[w["during"][0]: w["during"][1]].mean()),
                     "commodity_part_after": float(comp.loc[w["after"][0]: w["after"][1]].mean())})
    return pd.DataFrame(rows), Yadj
