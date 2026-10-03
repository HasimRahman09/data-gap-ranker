from __future__ import annotations

from pathlib import Path

import typer

from . import fetch as fetch_mod
from .gate import catalog_check

app = typer.Typer(no_args_is_help=True, help="SDG data-gap ranker. Not an official UN product.")
CACHE = Path("data/cache")


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
