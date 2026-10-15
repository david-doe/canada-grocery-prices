"""12-month forecasts of food CPI series with a rolling-origin backtest and conformal intervals (step 5, D23).

Models (D08): seasonal naive (baseline), per-series damped ETS on log prices, and a global LightGBM
model trained on all series at once (direct multi-horizon: target = ln P_t+h - ln P_t).
Evaluation (D08): rolling origins only, MASE (scaled by the in-sample seasonal naive MAE) and sMAPE.
Intervals (D09): split conformal on log errors |ln(actual / forecast)| by model and horizon,
calibrated on early origins and checked on later ones.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from load_data import read_statcan  # noqa: E402

H = 12
ETS_WINDOW = 120         # months used to fit each ETS model
GBM_TRAIN_START = pd.Period("2000-01", "M")
LEVELS = (0.80, 0.95)


def food_panel(min_start: str = "2014-01") -> pd.DataFrame:
    """National food CPI series (store food and restaurants) that start by `min_start` and reach the last month."""
    cat = pd.read_csv(Path(__file__).resolve().parents[2] / "data" / "processed" / "cpi_food_catalog.csv")
    c = read_statcan("cpi_monthly", columns=["REF_DATE", "GEO", "Products and product groups", "UOM", "VALUE"])
    c = c[(c.GEO == "Canada") & c["product"].isin(cat["product"]) & (c.UOM != "1992=100")]
    wide = c.pivot_table(index="REF_DATE", columns="product", values="VALUE", aggfunc="first").sort_index()
    last = wide.index.max()
    keep = [p for p in wide if wide[p].first_valid_index() <= pd.Period(min_start, "M")
            and wide[p].last_valid_index() == last]
    return wide[keep]


# ---------- models: each returns a (H,) array of forecast levels for months origin+1 .. origin+H ----------

def seasonal_naive(y: pd.Series, origin: pd.Period) -> np.ndarray:
    hist = y.loc[:origin]
    return np.array([hist.iloc[-12 + (h - 1) % 12] for h in range(1, H + 1)])


def ets(y: pd.Series, origin: pd.Period) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    hist = np.log(y.loc[:origin].dropna().iloc[-ETS_WINDOW:])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(hist.to_numpy(), trend="add", damped_trend=True, seasonal="add",
                                   seasonal_periods=12, initialization_method="estimated").fit()
    return np.exp(fit.forecast(H))


def _features(logp: pd.DataFrame) -> pd.DataFrame:
    """One row per (series, month t): last 12 monthly log changes, 12-month change, series id."""
    d = logp.diff()
    feats = {f"r{k}": d.shift(k) for k in range(12)}
    feats["yoy"] = logp - logp.shift(12)
    rows = []
    for name, f in feats.items():
        rows.append(f.stack().rename(name))
    X = pd.concat(rows, axis=1)
    X.index.names = ["month", "series"]
    return X


def gbm_fit_predict(panel: pd.DataFrame, origin: pd.Period) -> dict[str, np.ndarray]:
    """Global LightGBM, direct strategy: one model with horizon h as a feature."""
    import lightgbm as lgb

    logp = np.log(panel.loc[GBM_TRAIN_START:origin])
    X = _features(logp).dropna()
    series_codes = {s: i for i, s in enumerate(panel.columns)}
    train = []
    for h in range(1, H + 1):
        target = (logp.shift(-h) - logp).stack().rename("y")
        target.index.names = ["month", "series"]
        df = X.join(target, how="inner").dropna()
        df = df[df.index.get_level_values("month") <= origin - h]
        df = df.assign(h=h, target_month=[(m + h).month for m in df.index.get_level_values("month")])
        train.append(df)
    train = pd.concat(train)
    train["sid"] = train.index.get_level_values("series").map(series_codes)
    cols = [c for c in train.columns if c != "y"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=0)
        model.fit(train[cols], train.y, categorical_feature=["sid"])
    last = X.xs(origin, level="month")
    out = {}
    for s in panel.columns:
        if s not in last.index:
            continue
        base = last.loc[[s]].assign(sid=series_codes[s])
        rows = pd.concat([base.assign(h=h, target_month=(origin + h).month) for h in range(1, H + 1)])
        out[s] = np.exp(np.log(panel.loc[origin, s]) + model.predict(rows[cols]))
    return out


# ---------- backtest ----------

def backtest(panel: pd.DataFrame, origins: list[pd.Period]) -> pd.DataFrame:
    """Rolling-origin forecasts for all models; one row per (origin, series, model, h)."""
    rows = []
    for o in origins:
        gbm = gbm_fit_predict(panel, o)
        for s in panel.columns:
            y = panel[s].dropna()
            if y.index.min() > o - 60:
                continue
            actual = y.reindex([o + h for h in range(1, H + 1)]).to_numpy()
            scale = np.mean(np.abs(y.loc[:o].diff(12).dropna()))
            for model, f in [("seasonal_naive", seasonal_naive(y, o)), ("ets", ets(y, o)), ("lightgbm", gbm.get(s))]:
                if f is None:
                    continue
                for h in range(1, H + 1):
                    rows.append({"origin": o, "series": s, "model": model, "h": h, "forecast": f[h - 1],
                                 "actual": actual[h - 1], "scale": scale})
    df = pd.DataFrame(rows).dropna(subset=["actual"])
    df["abs_err"] = (df.actual - df.forecast).abs()
    df["mase"] = df.abs_err / df.scale
    df["smape"] = 200 * df.abs_err / (df.actual.abs() + df.forecast.abs())
    df["log_err"] = np.log(df.actual / df.forecast)
    return df


def conformal_quantiles(bt: pd.DataFrame) -> pd.DataFrame:
    """Split-conformal quantiles of |log error| by model and horizon (finite-sample corrected) [F4]."""
    out = []
    for (m, h), g in bt.groupby(["model", "h"]):
        e = np.sort(g.log_err.abs().to_numpy())
        n = len(e)
        row = {"model": m, "h": h, "n_cal": n}
        for lv in LEVELS:
            k = min(int(np.ceil((n + 1) * lv)), n) - 1
            row[f"q{int(lv * 100)}"] = e[k]
        out.append(row)
    return pd.DataFrame(out)


def coverage(bt_test: pd.DataFrame, q: pd.DataFrame) -> pd.DataFrame:
    d = bt_test.merge(q, on=["model", "h"])
    return d.groupby("model").apply(lambda g: pd.Series({
        f"coverage_{int(lv * 100)}": float((g.log_err.abs() <= g[f"q{int(lv * 100)}"]).mean()) for lv in LEVELS}),
        include_groups=False)


def forecast_all(panel: pd.DataFrame, model: str, q: pd.DataFrame) -> pd.DataFrame:
    """Final 12-month forecasts from the last month, with conformal intervals."""
    o = panel.index.max()
    gbm = gbm_fit_predict(panel, o) if model == "lightgbm" else {}
    qm = q[q.model == model].set_index("h")
    rows = []
    for s in panel.columns:
        y = panel[s].dropna()
        f = {"seasonal_naive": lambda: seasonal_naive(y, o), "ets": lambda: ets(y, o), "lightgbm": lambda: gbm.get(s)}[model]()
        if f is None:
            continue
        for h in range(1, H + 1):
            r = {"series": s, "month": str(o + h), "h": h, "forecast": f[h - 1], "model": model}
            for lv in LEVELS:
                qq = qm.loc[h, f"q{int(lv * 100)}"]
                r[f"lo{int(lv * 100)}"], r[f"hi{int(lv * 100)}"] = f[h - 1] * np.exp(-qq), f[h - 1] * np.exp(qq)
            rows.append(r)
    return pd.DataFrame(rows)
