"""Three-state cell matrix: PRESENT / MISSING / NOT_APPLICABLE per country x slice x year.

A *slice* is the headline view of a series. Rows that break a series down by a dimension
(sex, age, ...) are ignored when the series also reports that dimension's total, so a partial
breakdown never hides a gap. When a series has no total for a dimension, each value of that
dimension is its own slice (e.g. health-worker density per occupation).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from . import ledger

YEARS = range(2015, 2025)
# Every row in the cached SDG 3 data has Reporting Type "G"; it carries no breakdown.
IGNORED_DIMENSIONS = {"Reporting Type"}
TOTAL_SDMX = "_T"


class State(Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


Cell = tuple[str, str, int]  # (geo_area_code, slice_id, year)


def load_countries(tree_path: Path) -> dict[str, str]:
    """Areas the source's own tree labels "Country", keyed by code (names are the source's)."""
    out: dict[str, str] = {}

    def walk(node: dict[str, Any]) -> None:
        if node.get("type") == "Country":
            out[str(node["geoAreaCode"])] = str(node["geoAreaName"])
        for child in node.get("children") or []:
            walk(child)

    for root in json.loads(tree_path.read_text(encoding="utf-8")):
        walk(root)
    return out


@dataclass
class Matrix:
    countries: dict[str, str]
    slices: list[str]
    years: tuple[int, ...] = tuple(YEARS)
    present: dict[Cell, str] = field(default_factory=dict)  # cell -> Nature flag
    not_applicable: set[Cell] = field(default_factory=set)

    def state(self, cell: Cell) -> State:
        if cell in self.present:
            return State.PRESENT
        if cell in self.not_applicable:
            return State.NOT_APPLICABLE
        return State.MISSING

    def cells(self) -> Iterator[Cell]:
        for c in self.countries:
            for s in self.slices:
                for y in self.years:
                    yield (c, s, y)

    def mark_not_applicable(self, cells: Iterable[Cell]) -> None:
        """Only an explicit, cited rule may call a cell not applicable; never a present one."""
        for cell in cells:
            if cell in self.present:
                raise ValueError(f"cell has a value, cannot be NOT_APPLICABLE: {cell}")
            self.not_applicable.add(cell)

    def counts(self) -> dict[State, int]:
        out = dict.fromkeys(State, 0)
        for cell in self.cells():
            out[self.state(cell)] += 1
        return out


def _total_codes(page: dict[str, Any]) -> dict[str, set[str]]:
    return {
        d["id"]: {c["code"] for c in d["codes"] if c.get("sdmx") == TOTAL_SDMX}
        for d in page.get("dimensions", [])
    }


def build(cache_dir: Path, series: list[str], countries: dict[str, str]) -> Matrix:
    """Build the matrix from cached pages listed in the ledger. No network."""
    entries = [e for e in ledger.read(cache_dir / "ledger.jsonl") if "seriesCode" in e.params]
    rows_by_series: dict[str, list[dict[str, Any]]] = {s: [] for s in series}
    totals: dict[str, dict[str, set[str]]] = {s: {} for s in series}
    for e in entries:
        code = e.params["seriesCode"]
        if code not in rows_by_series:
            continue
        page = json.loads((cache_dir / e.path).read_text(encoding="utf-8"))
        rows_by_series[code].extend(page["data"])
        for dim, codes in _total_codes(page).items():
            totals[code].setdefault(dim, set()).update(codes)

    slices: set[str] = set()
    present: dict[Cell, str] = {}
    for code, rows in rows_by_series.items():
        # A dimension "has a total" only if the series actually reports one.
        observed_total = {
            dim
            for r in rows
            for dim, v in r["dimensions"].items()
            if v in totals[code].get(dim, set())
        }
        for r in rows:
            area, year = str(r["geoAreaCode"]), int(r["timePeriodStart"])
            if area not in countries or year not in YEARS:
                continue
            parts: list[str] = []
            headline = True
            for dim, v in sorted(r["dimensions"].items()):
                if dim in IGNORED_DIMENSIONS or v in totals[code].get(dim, set()):
                    continue
                if dim in observed_total:
                    headline = False  # a breakdown of a dimension whose total is reported
                    break
                parts.append(f"{dim}={v}")
            if not headline:
                continue
            slice_id = code + ("|" + "|".join(parts) if parts else "")
            slices.add(slice_id)
            present[(area, slice_id, year)] = str(r["attributes"].get("Nature", ""))
    return Matrix(countries=countries, slices=sorted(slices), present=present)
