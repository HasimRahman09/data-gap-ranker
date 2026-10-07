"""Cited NOT_APPLICABLE rules. Each rule file in rules/ names its source and applies one slice."""

from __future__ import annotations

import csv
from pathlib import Path

from .matrix import Cell, Matrix

RULES_DIR = Path("rules")
MALARIA_SLICE = "SH_STA_MALR"


def malaria_free_cells(matrix: Matrix, csv_path: Path) -> list[Cell]:
    """Cells of the malaria slice that WHO-certified malaria-free areas cannot report.

    A cell is not applicable from the certification year onward, unless a value is reported.
    Names are matched exactly against the snapshot's source-labelled countries; an unmatched
    name raises, so a stale or misspelt rule never silently does nothing.
    """
    codes: dict[str, list[str]] = {}
    for code, name in matrix.countries.items():
        codes.setdefault(name, []).append(code)
    cells: list[Cell] = []
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            matches = codes.get(row["who_name"], [])
            if len(matches) != 1:
                raise ValueError(f"rule name not uniquely in snapshot: {row['who_name']!r}")
            start = int(row["certified_year"])
            for year in matrix.years:
                cell = (matches[0], MALARIA_SLICE, year)
                if year >= start and cell not in matrix.present:
                    cells.append(cell)
    return cells


def apply_malaria_free(matrix: Matrix, csv_path: Path = RULES_DIR / "malaria_free.csv") -> int:
    cells = malaria_free_cells(matrix, csv_path)
    matrix.mark_not_applicable(cells)
    return len(cells)
