"""Synthetic control and event-study DiD for the tariff episodes (next step 4, D19).

Outcome: y_it = 100 * (ln P_it - ln P_i,t0), the cumulative log change in % since t0, the last month
before the tariff. Every series is 0 at t0, so the synthetic control matches trajectories, not levels.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from load_data import read_statcan  # noqa: E402

PRE_MONTHS = 60          # fit window before the tariff (D19); never below MIN_PRE_MONTHS = 36 (D17)
AFTER_MONTHS = 12        # persistence window after the tariff is lifted
COVID_START = pd.Period("2020-03", "M")  # the 2018 "after" window stops before the pandemic (D19)


@dataclass(frozen=True)
class Episode:
    event_id: str
    first_month: pd.Period   # first month with the tariff in force
    last_month: pd.Period    # last month with the tariff in force (at least part of the month)
    rate: float              # tariff rate on food lines

    @property
    def t0(self) -> pd.Period:
        return self.first_month - 1

    def windows(self, last_data: pd.Period) -> dict[str, tuple[pd.Period, pd.Period]]:
        after_end = min(self.last_month + AFTER_MONTHS, last_data)
        if self.first_month < COVID_START <= after_end:
            after_end = COVID_START - 1
        return {"pre": (self.t0 - PRE_MONTHS + 1, self.t0),
                "during": (self.first_month, self.last_month),
                "after": (self.last_month + 1, after_end)}


EPISODES = {
    # 2018: surtax 2018-07-01 to its repeal on 2019-05-19 (R10, R9); 10% on food lines
    "CA2018": Episode("CA2018", pd.Period("2018-07", "M"), pd.Period("2019-05", "M"), 0.10),
    # 2025: 2025-03-04 to 2025-08-31 for food lines (R7); 25%
    "CA2025": Episode("CA2025", pd.Period("2025-03", "M"), pd.Period("2025-08", "M"), 0.25),
}


def cpi_wide() -> pd.DataFrame:
    """National CPI, one column per product (each food product has a single index base)."""
    c = read_statcan("cpi_monthly", columns=["REF_DATE", "GEO", "Products and product groups", "UOM", "VALUE"])
    c = c[(c.GEO == "Canada") & (c.UOM != "1992=100")]
    return c.pivot_table(index="REF_DATE", columns="product", values="VALUE", aggfunc="first").sort_index()


def outcome(wide: pd.DataFrame, ep: Episode, products: list[str], spec: str = "main") -> pd.DataFrame:
    """Outcome in % (100 * log), from the start of the pre window to the end of the after window.

    spec="t0":   100 * (ln P_t - ln P_t0), the raw cumulative change since the last pre-tariff month.
    spec="main": seasonality removed, then centred on the pre-window mean (D19):
                 seasonal factors are the average deviation of ln P from its centred 12-month moving
                 average, by calendar month, estimated on the pre window only (no post data used);
                 centring on the pre mean plays the role of a unit fixed effect [M4] and avoids
                 anchoring every series on one noisy month.
    """
    w = ep.windows(wide.index.max())
    sub = np.log(wide.loc[w["pre"][0]: w["after"][1], products])
    if spec == "t0":
        return 100 * (sub - sub.loc[ep.t0])
    pre = sub.loc[w["pre"][0]: w["pre"][1]]
    ma = pre.rolling(12, center=True).mean().rolling(2).mean().shift(-1)  # centred 2x12 moving average
    dev = (pre - ma).groupby(pre.index.month).mean()
    dev = dev - dev.mean()
    seasonal = dev.reindex(sub.index.month).set_axis(sub.index)
    adj = sub - seasonal
    return 100 * (adj - adj.loc[w["pre"][0]: w["pre"][1]].mean())


def finest(products: list[str], parent: dict[str, str]) -> list[str]:
    """Drop a series when one of its descendants is also in the list (no parent-child overlap in the pool)."""
    s = set(products)

    def has_desc(p):
        return any(p in _chain(q, parent) for q in s if q != p)

    return [p for p in products if not has_desc(p)]


def _chain(p, parent):
    out, cur = [], parent.get(p)
    while cur is not None and cur in parent:
        out.append(cur)
        cur = parent[cur]
    if cur is not None:
        out.append(cur)
    return out


def sc_weights(y_pre: np.ndarray, X_pre: np.ndarray) -> np.ndarray:
    """Abadie-type weights: w >= 0, sum(w) = 1, minimising the pre-period squared error [M1, M2]."""
    n = X_pre.shape[1]
    obj = lambda w: np.sum((y_pre - X_pre @ w) ** 2)
    grad = lambda w: -2 * X_pre.T @ (y_pre - X_pre @ w)
    res = minimize(obj, np.full(n, 1 / n), jac=grad, method="SLSQP", bounds=[(0, 1)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 500, "ftol": 1e-10})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def fit_one(Y: pd.DataFrame, treated: str, donors: list[str], ep: Episode) -> dict:
    """Synthetic control for one series; returns the gap path and window summaries."""
    w_ = ep.windows(Y.index.max())
    pre = Y.loc[w_["pre"][0]: w_["pre"][1]]
    d = [x for x in donors if x != treated and Y[x].notna().all()]
    w = sc_weights(pre[treated].to_numpy(), pre[d].to_numpy())
    synth = Y[d].to_numpy() @ w
    gap = pd.Series(Y[treated].to_numpy() - synth, index=Y.index)

    def win(k):
        a, b = w_[k]
        return gap.loc[a:b]

    rmspe = lambda g: float(np.sqrt(np.mean(g ** 2))) if len(g) else np.nan
    return {
        "series": treated, "gap": gap, "weights": pd.Series(w, index=d).sort_values(ascending=False),
        "pre_rmspe": rmspe(win("pre")), "during_rmspe": rmspe(win("during")),
        "effect_during": float(win("during").mean()), "effect_end": float(win("during").iloc[-1]),
        "effect_after": float(win("after").mean()) if len(win("after")) else np.nan,
    }


def run_episode(wide: pd.DataFrame, ep: Episode, treated: list[str], donors: list[str],
                placebos: list[str] | None = None, spec: str = "main",
                Y: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    """SC for each treated (and placebo) series; in-space permutation p-values from the donors [M1].

    p-value = share of donor placebo runs whose during/pre RMSPE ratio is >= the treated one (treated included).
    A precomputed outcome `Y` (e.g. commodity-adjusted, D22) replaces the one built from `wide`.
    """
    placebos = placebos or []
    cols = list(dict.fromkeys(treated + placebos + donors))
    Y = (outcome(wide, ep, cols, spec) if Y is None else Y[[c for c in cols if c in Y]]).dropna(axis=1)
    donors = [d for d in donors if d in Y]
    runs = {s: fit_one(Y, s, donors, ep) for s in treated + placebos if s in Y}
    perm = {d: fit_one(Y, d, donors, ep) for d in donors}
    ratio = lambda r: r["during_rmspe"] / r["pre_rmspe"]
    perm_ratios = np.array([ratio(r) for r in perm.values()])

    rows = []
    for s, r in runs.items():
        rows.append({
            "event_id": ep.event_id, "spec": spec, "series": s, "group": "placebo" if s in placebos else "treated",
            "effect_during": r["effect_during"], "effect_end": r["effect_end"], "effect_after": r["effect_after"],
            "pre_rmspe": r["pre_rmspe"], "ratio": ratio(r),
            "p_value": (1 + np.sum(perm_ratios >= ratio(r))) / (1 + len(perm_ratios)),
            "rho_during": r["effect_during"] / (100 * ep.rate),
            "n_donors": len(r["weights"]), "top_donors": "; ".join(f"{k} ({v:.2f})" for k, v in r["weights"].head(3).items()),
        })
    return pd.DataFrame(rows), {"runs": runs, "perm": perm, "Y": Y}


def event_study(Y: pd.DataFrame, treated: list[str], donors: list[str], ep: Episode) -> pd.DataFrame:
    """Event-study DiD with series and month fixed effects, SE clustered by series [M3].

    One treatment date per episode (no staggered adoption), so two-way fixed effects are valid here.
    Relative month -1 (= t0) is the reference.
    """
    import statsmodels.formula.api as smf

    long = Y[[c for c in treated + donors if c in Y]].stack().rename("y").reset_index()
    long.columns = ["month", "series", "y"]
    long["treated"] = long.series.isin(treated).astype(int)
    long["rel"] = [(m - ep.first_month).n for m in long.month]
    long["rel_c"] = long.rel.clip(lower=-12)  # bin all months before -12
    long["month"] = long.month.astype(str)
    dummies = []
    for k in sorted(long.rel_c.unique()):
        if k == -1:
            continue
        name = f"d_{'m' if k < 0 else 'p'}{abs(k)}"
        long[name] = ((long.rel_c == k) & (long.treated == 1)).astype(int)
        dummies.append((k, name))
    f = "y ~ " + " + ".join(n for _, n in dummies) + " + C(series) + C(month)"
    m = smf.ols(f, data=long).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(long.series)[0]})
    ci = m.conf_int()
    return pd.DataFrame([{"rel_month": k, "coef": m.params[n], "lo": ci.loc[n, 0], "hi": ci.loc[n, 1], "p": m.pvalues[n]}
                         for k, n in dummies])


def did_2x2(Y: pd.DataFrame, treated: list[str], donors: list[str], ep: Episode) -> dict:
    """Average DiD over the tariff months vs the pre window, with series-clustered SE [M3]."""
    import statsmodels.formula.api as smf

    w = ep.windows(Y.index.max())
    sub = Y[[c for c in treated + donors if c in Y]]
    long = sub.stack().rename("y").reset_index()
    long.columns = ["month", "series", "y"]
    long = long[(long.month >= w["pre"][0]) & (long.month <= w["during"][1])]
    long["post"] = (long.month >= ep.first_month).astype(int)
    long["treated"] = long.series.isin(treated).astype(int)
    long["month"] = long.month.astype(str)
    m = smf.ols("y ~ treated:post + C(series) + C(month)", data=long).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(long.series)[0]})
    lo, hi = m.conf_int().loc["treated:post"]
    return {"event_id": ep.event_id, "did": m.params["treated:post"], "lo": lo, "hi": hi, "p": m.pvalues["treated:post"],
            "n_treated": len(set(treated) & set(sub)), "n_controls": len(set(donors) & set(sub))}
