"""Cached fetch. Transport is injectable so tests and CI never touch the network."""

from __future__ import annotations

import time
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from . import ledger

BASE = "https://unstats.un.org/sdgapi/v1/sdg"
Transport = Callable[[str], bytes]

# Metadata lists only; observation data is a separate, separately approved step.
SNAPSHOT_REQUESTS: list[tuple[str, dict[str, str]]] = [
    (f"{BASE}/Goal/List", {"includechildren": "true"}),
    (f"{BASE}/GeoArea/List", {}),
    (f"{BASE}/Series/List", {}),
]


def http_get(url: str) -> bytes:  # pragma: no cover - live network
    req = urllib.request.Request(url, headers={"User-Agent": "data-gap-ranker/0.0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data: bytes = resp.read()
    return data


def fetch(
    url: str,
    params: dict[str, str],
    cache_dir: Path,
    transport: Transport = http_get,
    delay_s: float = 0.0,
) -> ledger.LedgerEntry:
    """Return the ledger entry for a query, fetching only if it is not already cached."""
    qid = ledger.query_id(url, params)
    cached = cache_dir / f"{qid}.json"
    ledger_path = cache_dir / "ledger.jsonl"
    for entry in ledger.read(ledger_path):
        if entry.query_id == qid and cached.exists():
            return entry
    full = url + ("?" + urlencode(params) if params else "")
    if delay_s:
        time.sleep(delay_s)
    body = transport(full)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(body)
    entry = ledger.LedgerEntry(
        query_id=qid,
        url=url,
        params=params,
        retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
        sha256=ledger.checksum(body),
        path=cached.name,
    )
    ledger.append(ledger_path, entry)
    return entry
