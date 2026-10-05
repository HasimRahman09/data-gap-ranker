import random

import pytest

from gapranker.matrix import Matrix, State


def _m() -> Matrix:
    m = Matrix(countries={"1": "A", "2": "B"}, slices=["S"], years=(2015, 2016))
    m.present[("1", "S", 2015)] = "C"
    return m


def test_states() -> None:
    m = _m()
    assert m.state(("1", "S", 2015)) is State.PRESENT
    assert m.state(("1", "S", 2016)) is State.MISSING
    assert m.counts() == {State.PRESENT: 1, State.MISSING: 3, State.NOT_APPLICABLE: 0}


def test_present_cell_cannot_become_not_applicable() -> None:
    with pytest.raises(ValueError):
        _m().mark_not_applicable([("1", "S", 2015)])


def test_missing_and_not_applicable_never_convert() -> None:
    rng = random.Random(0)
    for _ in range(200):
        m = Matrix(countries={str(i): "x" for i in range(5)}, slices=["S", "T"], years=(2015, 2016))
        cells = list(m.cells())
        present = set(rng.sample(cells, 8))
        m.present.update(dict.fromkeys(present, "C"))
        na = set(rng.sample([c for c in cells if c not in present], 5))
        m.mark_not_applicable(na)
        for c in cells:
            expect = State.MISSING
            if c in present:
                expect = State.PRESENT
            elif c in na:
                expect = State.NOT_APPLICABLE
            assert m.state(c) is expect
