from __future__ import annotations

from pathlib import Path

import typer

from . import fetch as fetch_mod
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
