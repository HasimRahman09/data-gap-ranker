"""catalog-check: verify the cached snapshot against the ledger (exit 0 / 1 / 2)."""

from __future__ import annotations

from pathlib import Path

from . import ledger
from .fetch import SNAPSHOT_REQUESTS

PASS, BLOCKED, UNEVALUABLE = 0, 1, 2


def catalog_check(cache_dir: Path) -> tuple[int, list[str]]:
    entries = ledger.read(cache_dir / "ledger.jsonl")
    if not entries:
        return UNEVALUABLE, ["no ledger: snapshot has not been fetched"]
    by_id = {e.query_id: e for e in entries}
    problems: list[str] = []
    for url, params in SNAPSHOT_REQUESTS:
        entry = by_id.get(ledger.query_id(url, params))
        if entry is None:
            return UNEVALUABLE, [f"missing from ledger: {url}"]
        path = cache_dir / entry.path
        if not path.exists():
            return UNEVALUABLE, [f"cached file missing: {entry.path}"]
        if ledger.checksum(path.read_bytes()) != entry.sha256:
            problems.append(f"checksum mismatch: {entry.path}")
    return (BLOCKED, problems) if problems else (PASS, ["snapshot matches ledger"])
