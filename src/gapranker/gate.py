"""catalog-check: verify the cached snapshot against the ledger (exit 0 / 1 / 2)."""

from __future__ import annotations

import json
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
    # Every ledger entry, including data pages, must match its checksum.
    for entry in entries:
        path = cache_dir / entry.path
        if not path.exists():
            return UNEVALUABLE, [f"cached file missing: {entry.path}"]
        if ledger.checksum(path.read_bytes()) != entry.sha256:
            problems.append(f"checksum mismatch: {entry.path}")
    # Every series seen in the ledger must have all pages 1..totalPages.
    pages: dict[str, set[int]] = {}
    totals: dict[str, int] = {}
    for entry in entries:
        code = entry.params.get("seriesCode")
        if code is None or not (cache_dir / entry.path).exists():
            continue
        body = json.loads((cache_dir / entry.path).read_text(encoding="utf-8"))
        pages.setdefault(code, set()).add(int(entry.params["page"]))
        totals[code] = int(body["totalPages"])
    for code, total in sorted(totals.items()):
        if pages[code] != set(range(1, total + 1)):
            problems.append(f"incomplete series {code}: pages {sorted(pages[code])} of {total}")
    return (BLOCKED, problems) if problems else (PASS, ["snapshot and data match ledger"])
