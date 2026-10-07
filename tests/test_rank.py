from gapranker.matrix import Matrix
from gapranker.rank import rank

YEAR = (2015,)
BUNDLE = ["X", "W", "V"]

# Constructed case (9 countries, 36 pairs). Each country holds the slices listed:
#   a1-a3 lack X and W   a4-a5 lack X and V   d1-d2 lack V only   c1-c2 lack nothing
HAVE = {
    "a1": {"V"}, "a2": {"V"}, "a3": {"V"},
    "a4": {"W"}, "a5": {"W"},
    "d1": {"X", "W"}, "d2": {"X", "W"},
    "c1": {"X", "W", "V"}, "c2": {"X", "W", "V"},
}


def _matrix(have: dict[str, set[str]]) -> Matrix:
    m = Matrix(countries={c: c for c in have}, slices=BUNDLE, years=YEAR)
    for c, ss in have.items():
        for s in ss:
            m.present[(c, s, 2015)] = "C"
    return m


def test_raw_count_leader_differs_from_marginal_gain_leader() -> None:
    r = rank(_matrix(HAVE), BUNDLE)
    by = {s.slice_id: s for s in r.scores}
    # X is missing for the most countries and blocks the most pairs ...
    assert by["X"].raw_missing == 5 and by["V"].raw_missing == 4 and by["W"].raw_missing == 3
    assert by["X"].rows_blocked == 30
    # ... but never the only missing input, so fixing it alone unlocks nothing.
    assert by["X"].unlocks_now == 0 and by["W"].unlocks_now == 0
    assert by["V"].unlocks_now == 5  # d-d pair + d with c1, c2 (1 + 4)
    assert r.scores[0].slice_id == "V"
    assert max(r.scores, key=lambda s: s.raw_missing).slice_id == "X"  # naive pick differs


def test_greedy_recomputes_marginal_gain() -> None:
    r = rank(_matrix(HAVE), BUNDLE)
    assert r.comparable_now == 1  # only c1-c2
    assert [(g.slice_id, g.marginal_gain) for g in r.greedy] == [("V", 5), ("X", 9), ("W", 21)]
    assert r.greedy[-1].cumulative_comparable == r.total_pairs == 36


def test_universe_excludes_areas_with_no_data() -> None:
    have = {**HAVE, "ghost": set()}
    r = rank(_matrix(have), BUNDLE)
    assert "ghost" in r.excluded and "ghost" not in r.universe


def test_not_applicable_is_not_required() -> None:
    m = Matrix(countries={"a": "a", "b": "b"}, slices=["X"], years=YEAR)
    m.present[("a", "X", 2015)] = "C"
    m.present[("b", "Z", 2015)] = "C"  # b has other data, so it is in the universe
    assert rank(m, ["X"]).comparable_now == 0
    m.mark_not_applicable([("b", "X", 2015)])
    assert rank(m, ["X"]).comparable_now == 1
