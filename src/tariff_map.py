"""Treated / control roles of food CPI series for each tariff episode (next step 3, D18).

Inputs (versioned, hand-curated from official lists):
  data/reference/tariff_hs6_food.csv  food HS6 subheadings on each list (R7, R10)
  data/reference/tariff_cpi_map.csv   which CPI series those products fall in, with an exposure type

Exposure types (D18):
  direct           tariffed retail products are a main part of the series, at a binding rate
  over_quota_only  only over-access lines were tariffed, on top of MFN rates of about 240-300% (S9)
  partial          tariffed products are a small or uncertain part of the series
  input            tariffed goods are ingredients of the series (indirect effect, R4)
A series inherits the exposure of its nearest mapped ancestor. An unmapped series with a mapped
descendant "contains" exposed products.

A control for one episode must not be exposed to another episode that falls inside its estimation
window [start - MIN_PRE_MONTHS, start of the next episode). In practice the 2026 window (from 2023-09)
contains the 2025 episode, so series exposed in 2025 are not 2026 controls. Placebo (over-quota-only)
exposure does not disqualify a control: its expected effect is near zero (D18).
"""
from __future__ import annotations

import pandas as pd

from cpi_catalog import MIN_PRE_MONTHS, ROOT, TARIFF_EVENTS, build_catalog

REF = ROOT / "data" / "reference"
HS6_FILE = REF / "tariff_hs6_food.csv"
MAP_FILE = REF / "tariff_cpi_map.csv"

ROLE = {
    "direct": "treated",
    "over_quota_only": "placebo",
    "partial": "excluded_partial",
    "input": "excluded_input",
    "contains": "excluded_aggregate",
    None: "control",
}
OUT_OF_SCOPE_ROOT = "Food purchased from restaurants"


def read_map() -> pd.DataFrame:
    return pd.read_csv(MAP_FILE, dtype=str)


def validate(cat: pd.DataFrame, tmap: pd.DataFrame) -> None:
    """Fail loudly if the map names an unknown CPI series or an HS6 code absent from that episode's list."""
    unknown = set(tmap.cpi_product) - set(cat["product"])
    assert not unknown, f"Unknown CPI series in {MAP_FILE.name}: {sorted(unknown)}"
    hs6 = pd.read_csv(HS6_FILE, dtype=str)
    listed = set(zip(hs6.event_id, hs6.hs6))
    missing = [(r.event_id, h, r.cpi_product) for r in tmap.itertuples() for h in r.hs6.split(";")
               if (r.event_id, h) not in listed]
    assert not missing, f"HS6 codes not on the episode's list: {missing}"
    dup = tmap.duplicated(["event_id", "cpi_product"])
    assert not dup.any(), f"Duplicate rows: {tmap[dup].values.tolist()}"


def _ancestors(cat: pd.DataFrame) -> dict[str, list[str]]:
    parent = dict(zip(cat["product"], cat["parent"]))
    out = {}
    for p in cat["product"]:
        chain, cur = [], parent.get(p)
        while cur in parent:
            chain.append(cur)
            cur = parent[cur]
        out[p] = chain
    return out


def roles(cat: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (episode, CPI food series): exposure, role and whether the series is usable (D17)."""
    cat = build_catalog() if cat is None else cat
    tmap = read_map()
    validate(cat, tmap)
    anc = _ancestors(cat)
    events = pd.read_csv(TARIFF_EVENTS, parse_dates=["start_date"]).sort_values("start_date")

    def exposure_of(ev: str) -> dict[str, tuple[str | None, str | None]]:
        mapped = dict(zip(*tmap.loc[tmap.event_id == ev, ["cpi_product", "exposure"]].T.values))
        has_exposed_child = {a for p in mapped for a in anc[p]}
        out = {}
        for p in cat["product"]:
            if p in mapped:
                out[p] = (mapped[p], p)
                continue
            inherited = next((a for a in anc[p] if a in mapped), None)
            out[p] = (mapped[inherited], inherited) if inherited else (("contains", None) if p in has_exposed_child else (None, None))
        return out

    exp = {ev: exposure_of(ev) for ev in events.event_id}
    starts = list(events.start_date.dt.to_period("M"))
    windows = {ev: (s - MIN_PRE_MONTHS, starts[i + 1] if i + 1 < len(starts) else None)
               for i, (ev, s) in enumerate(zip(events.event_id, starts))}

    rows = []
    for ev in events.event_id:
        lo, hi = windows[ev]
        others = [o for o, s in zip(events.event_id, starts) if o != ev and s >= lo and (hi is None or s < hi)]
        for r in cat.itertuples():
            p = r.product
            exposure, via = exp[ev][p]
            role = "out_of_scope" if (p == OUT_OF_SCOPE_ROOT or OUT_OF_SCOPE_ROOT in anc[p]) else ROLE[exposure]
            hit = [o for o in others if exp[o][p][0] in ("direct", "partial", "input", "contains")]
            if role == "control" and hit:
                role = "excluded_other_episode"
            rows.append({
                "event_id": ev, "product": p, "product_fr": r.product_fr, "depth": r.depth, "is_leaf": r.is_leaf,
                "exposure": exposure, "mapped_via": via, "role": role,
                "exposed_in_other_episode": ";".join(hit),
                "pre_months": getattr(r, f"{ev}_pre"), "post_months": getattr(r, f"{ev}_post"),
                "usable": bool(getattr(r, f"{ev}_pre_ok")) and getattr(r, f"{ev}_post") > 0,
                "pre_ok": bool(getattr(r, f"{ev}_pre_ok")),
            })
    return pd.DataFrame(rows)
