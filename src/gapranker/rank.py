"""Rank missing slices by the country comparisons they would unlock.

A *comparison* is an unordered pair of countries over a bundle of slices. It is COMPARABLE
only when every required slice has a value for both countries in the reference window.
Obtaining a slice is assumed to fill it for every country in the universe (optimistic upper
bound: it says what the gap is worth, not what any agency can deliver).

Three numbers per slice, never to be conflated:
- ``unlocks_now``: pairs where this slice is the ONLY missing input.
- ``rows_blocked``: pairs where this slice is merely AMONG the missing inputs.
- ``raw_missing``: country-slice gaps for this slice (what a naive ranking uses).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .matrix import Matrix, State


@dataclass(frozen=True)
class SliceScore:
    slice_id: str
    unlocks_now: int
    rows_blocked: int
    raw_missing: int


@dataclass(frozen=True)
class GreedyStep:
    slice_id: str
    marginal_gain: int
    cumulative_comparable: int


@dataclass(frozen=True)
class Ranking:
    universe: list[str]
    excluded: list[str]
    bundle: list[str]
    total_pairs: int
    comparable_now: int
    scores: list[SliceScore]  # sorted by unlocks_now, then rows_blocked (ties: slice id)
    greedy: list[GreedyStep]


def universe(matrix: Matrix) -> tuple[list[str], list[str]]:
    """Countries with at least one PRESENT cell for any slice in the window; and the rest."""
    with_data = {c for (c, _s, y) in matrix.present if y in matrix.years}
    inside = sorted(c for c in matrix.countries if c in with_data)
    outside = sorted(c for c in matrix.countries if c not in with_data)
    return inside, outside


def missing_masks(
    matrix: Matrix, countries: list[str], bundle: list[str], min_years: int = 1
) -> dict[str, int]:
    """Per country, a bitmask of bundle slices that are required but not covered.

    A slice is covered when PRESENT in at least ``min_years`` window years. It is not
    required of a country whose every window cell is NOT_APPLICABLE.
    """
    masks: dict[str, int] = {}
    for c in countries:
        mask = 0
        for i, s in enumerate(bundle):
            states = [matrix.state((c, s, y)) for y in matrix.years]
            if sum(st is State.PRESENT for st in states) >= min_years:
                continue
            if all(st is State.NOT_APPLICABLE for st in states):
                continue
            mask |= 1 << i
        masks[c] = mask
    return masks


def _popcount_bits(mask: int) -> list[int]:
    return [i for i in range(mask.bit_length()) if mask >> i & 1]


def rank(matrix: Matrix, bundle: list[str], min_years: int = 1) -> Ranking:
    countries, excluded = universe(matrix)
    masks = missing_masks(matrix, countries, bundle, min_years)
    pair_masks = [masks[a] | masks[b] for a, b in combinations(countries, 2)]
    comparable_now = sum(1 for m in pair_masks if m == 0)

    scores: list[SliceScore] = []
    for i, s in enumerate(bundle):
        bit = 1 << i
        scores.append(
            SliceScore(
                slice_id=s,
                unlocks_now=sum(1 for m in pair_masks if m == bit),
                rows_blocked=sum(1 for m in pair_masks if m & bit),
                raw_missing=sum(1 for c in countries if masks[c] & bit),
            )
        )
    scores.sort(key=lambda x: (-x.unlocks_now, -x.rows_blocked, x.slice_id))

    greedy: list[GreedyStep] = []
    fixed = 0  # bitmask of slices already "obtained"
    remaining = set(range(len(bundle)))
    comparable = comparable_now
    while remaining:
        best_i, best_gain = -1, -1
        for i in sorted(remaining, key=lambda k: bundle[k]):
            trial = fixed | (1 << i)
            gain = sum(1 for m in pair_masks if m & ~trial == 0) - comparable
            if gain > best_gain:
                best_i, best_gain = i, gain
        fixed |= 1 << best_i
        remaining.discard(best_i)
        comparable += best_gain
        greedy.append(GreedyStep(bundle[best_i], best_gain, comparable))
    return Ranking(
        universe=countries,
        excluded=excluded,
        bundle=bundle,
        total_pairs=len(pair_masks),
        comparable_now=comparable_now,
        scores=scores,
        greedy=greedy,
    )
