from pathlib import Path

import pytest

from gapranker.matrix import Matrix, State
from gapranker.rules import apply_malaria_free


def _setup(tmp_path: Path, rows: str) -> tuple[Matrix, Path]:
    p = tmp_path / "r.csv"
    p.write_text("who_name,certified_year\n" + rows)
    countries = {"1": "Aland", "2": "Bland"}
    m = Matrix(countries=countries, slices=["SH_STA_MALR"], years=(2015, 2016, 2017))
    return m, p


def test_applies_from_certification_year_and_skips_reported(tmp_path: Path) -> None:
    m, p = _setup(tmp_path, "Aland,2016\n")
    m.present[("1", "SH_STA_MALR", 2017)] = "C"  # reported after certification: keep PRESENT
    assert apply_malaria_free(m, p) == 1
    assert m.state(("1", "SH_STA_MALR", 2015)) is State.MISSING  # before certification
    assert m.state(("1", "SH_STA_MALR", 2016)) is State.NOT_APPLICABLE
    assert m.state(("1", "SH_STA_MALR", 2017)) is State.PRESENT
    assert m.state(("2", "SH_STA_MALR", 2016)) is State.MISSING  # not in the rule


def test_unknown_name_fails_loudly(tmp_path: Path) -> None:
    m, p = _setup(tmp_path, "Nowhere,2016\n")
    with pytest.raises(ValueError):
        apply_malaria_free(m, p)
