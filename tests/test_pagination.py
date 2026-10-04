import json
from pathlib import Path

import pytest

from gapranker.fetch import fetch_series_pages
from gapranker.scope import sdg3_series


def _transport(total_pages: int, echo_wrong: bool = False):  # type: ignore[no-untyped-def]
    def t(url: str) -> bytes:
        page = int(url.split("page=")[1].split("&")[0]) if "page=" in url else 1
        shown = 1 if echo_wrong else page
        return json.dumps({"pageNumber": shown, "totalPages": total_pages, "data": []}).encode()

    return t


def test_all_pages_fetched(tmp_path: Path) -> None:
    assert len(fetch_series_pages("X", tmp_path, _transport(3))) == 3


def test_wrong_page_echo_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        fetch_series_pages("X", tmp_path, _transport(3, echo_wrong=True))


def test_scope_excludes_oda_and_duplicates(tmp_path: Path) -> None:
    p = tmp_path / "s.json"
    rows = [{"code": c, "goal": ["3"]} for c in ["SH_STA_MORT", "DC_TOF_HLTHL", "SH_DYN_IMRTN"]]
    rows.append({"code": "OTHER", "goal": ["4"]})
    p.write_text(json.dumps(rows))
    assert sdg3_series(p) == ["SH_STA_MORT"]
