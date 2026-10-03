from pathlib import Path

from gapranker import gate
from gapranker.fetch import SNAPSHOT_REQUESTS, fetch


def _fill(cache: Path) -> int:
    calls = 0

    def transport(url: str) -> bytes:
        nonlocal calls
        calls += 1
        return b'{"ok": true}'

    for url, params in SNAPSHOT_REQUESTS:
        fetch(url, params, cache, transport)
    return calls


def test_gate_unevaluable_without_snapshot(tmp_path: Path) -> None:
    assert gate.catalog_check(tmp_path)[0] == gate.UNEVALUABLE


def test_gate_passes_then_blocks_on_tamper(tmp_path: Path) -> None:
    _fill(tmp_path)
    assert gate.catalog_check(tmp_path)[0] == gate.PASS
    next(tmp_path.glob("*.json")).write_bytes(b"tampered")
    assert gate.catalog_check(tmp_path)[0] == gate.BLOCKED


def test_second_fetch_hits_cache(tmp_path: Path) -> None:
    assert _fill(tmp_path) == len(SNAPSHOT_REQUESTS)
    assert _fill(tmp_path) == 0
