"""Query ledger: every fetched response is recorded with URL, params, time and checksum."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode


@dataclass(frozen=True)
class LedgerEntry:
    query_id: str
    url: str
    params: dict[str, str]
    retrieved_at: str
    sha256: str
    path: str


def query_id(url: str, params: dict[str, str]) -> str:
    key = url + "?" + urlencode(sorted(params.items()))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def checksum(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def append(ledger_path: Path, entry: LedgerEntry) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read(ledger_path: Path) -> list[LedgerEntry]:
    if not ledger_path.exists():
        return []
    with ledger_path.open(encoding="utf-8") as fh:
        return [LedgerEntry(**json.loads(line)) for line in fh if line.strip()]
