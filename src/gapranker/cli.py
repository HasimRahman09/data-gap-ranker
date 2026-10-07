from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from . import fetch as fetch_mod
from . import ledger, matrix
from . import rank as rank_mod
from .gate import catalog_check
from .scope import sdg3_series

app = typer.Typer(no_args_is_help=True, help="SDG data-gap ranker. Not an official UN product.")
CACHE = Path("data/cache")
SERIES_LIST = CACHE / "059a83a91aef1bb4.json"  # Series/List snapshot (see ledger)


@app.command()
def fetch(commit: bool = typer.Option(False, "--commit", help="Perform the downloads.")) -> None:
    """Fetch the metadata snapshot. Dry-run by default: lists the requests, downloads nothing."""
    for url, params in fetch_mod.SNAPSHOT_REQUESTS:
        typer.echo(f"{'GET' if commit else 'would GET'} {url} {params or ''}")
        if commit:
            fetch_mod.fetch(url, params, CACHE, delay_s=1.0)


@app.command("catalog-check")
def catalog_check_cmd() -> None:
    """Gate: 0 pass / 1 blocked / 2 could not evaluate."""
    code, messages = catalog_check(CACHE)
    for m in messages:
        typer.echo(m)
    raise typer.Exit(code)


@app.command("fetch-data")
def fetch_data(commit: bool = typer.Option(False, "--commit", help="Download.")) -> None:
    """Fetch observation data for in-scope SDG 3 series. Dry-run by default."""
    series = sdg3_series(SERIES_LIST)
    typer.echo(f"{len(series)} series in scope; at least {len(series)} requests (pageSize 1000).")
    for code in series:
        if not commit:
            typer.echo(f"would fetch {code}")
            continue
        entries = fetch_mod.fetch_series_pages(code, CACHE, delay_s=1.0)
        typer.echo(f"{code}: {len(entries)} page(s)")


# Illustrative bundle only. Not an official or composite measure; pass --slice to choose your own.
EXAMPLE_BUNDLE = [
    "SH_STA_MORT|Sex=FEMALE",
    "SH_DYN_MORT|Age=<5Y",
    "SH_TBS_INCD",
    "SH_HIV_INCD",
    "SH_STA_MALR",
    "SH_ACS_DTP3",
    "SH_MED_DEN|Type of occupation=PHYS",
]


@app.command()
def rank(
    slice_: Annotated[
        list[str] | None, typer.Option("--slice", help="Slice id; repeat. Default: example.")
    ] = None,
    min_years: Annotated[int, typer.Option(help="Window years a value is needed in.")] = 1,
) -> None:
    """Rank missing slices by comparisons unlocked. Exit 2 if the cache fails the gate."""
    code, messages = catalog_check(CACHE)
    if code != 0:
        for m in messages:
            typer.echo(m)
        raise typer.Exit(code)
    from .fetch import BASE

    tree = CACHE / f"{ledger.query_id(BASE + '/GeoArea/Tree', {})}.json"
    mat = matrix.build(CACHE, sdg3_series(SERIES_LIST), matrix.load_countries(tree))
    bundle = list(slice_ or EXAMPLE_BUNDLE)
    unknown = [s for s in bundle if s not in mat.slices]
    if unknown:
        typer.echo(f"unknown slice(s): {unknown}")
        raise typer.Exit(2)
    r = rank_mod.rank(mat, bundle, min_years)
    typer.echo("Source: UN Statistics Division, SDG Global Database. Not an official UN product.")
    typer.echo(f"Window 2015-2024; value needed in >= {min_years} year(s); {len(bundle)} slices.")
    typer.echo(f"Universe: {len(r.universe)} areas with SDG 3 data ({len(r.excluded)} excluded).")
    typer.echo(f"Comparable now: {r.comparable_now} of {r.total_pairs} pairs.")
    typer.echo("\nunlocks_now = only missing input | rows_blocked = among missing | raw = gaps")
    for s in r.scores:
        typer.echo(f"{s.unlocks_now:6d} {s.rows_blocked:7d} {s.raw_missing:4d}  {s.slice_id}")
    typer.echo("\nGreedy (marginal gain recomputed after each pick):")
    for g in r.greedy:
        typer.echo(f"+{g.marginal_gain:6d} -> {g.cumulative_comparable:6d}  {g.slice_id}")
