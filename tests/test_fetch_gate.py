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


def test_gate_blocks_incomplete_series(tmp_path: Path) -> None:
    import json

    from gapranker.fetch import fetch_series_pages

    _fill(tmp_path)

    def transport(url: str) -> bytes:
        page = int(url.split("page=")[1].split("&")[0])
        return json.dumps({"pageNumber": page, "totalPages": 2, "data": []}).encode()

    entries = fetch_series_pages("X", tmp_path, transport)
    assert gate.catalog_check(tmp_path)[0] == gate.PASS
    (tmp_path / entries[1].path).unlink()
    assert gate.catalog_check(tmp_path)[0] == gate.UNEVALUABLE
