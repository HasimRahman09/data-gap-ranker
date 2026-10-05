"""Cached fetch. Transport is injectable so tests and CI never touch the network."""

from __future__ import annotations

import json
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
    (f"{BASE}/GeoArea/Tree", {}),  # separates aggregates from countries
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


PAGE_SIZE = 1000


def fetch_series_pages(
    series_code: str,
    cache_dir: Path,
    transport: Transport = http_get,
    delay_s: float = 0.0,
) -> list[ledger.LedgerEntry]:
    """Fetch every page of one series; fail loudly if the API echoes a different page."""
    url = f"{BASE}/Series/Data"
    entries: list[ledger.LedgerEntry] = []
    page, total_pages = 1, 1
    while page <= total_pages:
        params = {"seriesCode": series_code, "pageSize": str(PAGE_SIZE), "page": str(page)}
        entry = fetch(url, params, cache_dir, transport, delay_s)
        body = json.loads((cache_dir / entry.path).read_text(encoding="utf-8"))
        if body["pageNumber"] != page:
            raise ValueError(f"{series_code}: asked for page {page}, got {body['pageNumber']}")
        total_pages = int(body["totalPages"])
        entries.append(entry)
        page += 1
    return entries
