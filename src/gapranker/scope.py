"""Which SDG 3 series are in scope. Derived from the cached Series/List snapshot."""

from __future__ import annotations

import json
from pathlib import Path

# Official development assistance flows describe donors, not country health outcomes.
EXCLUDED_ODA = {"DC_TOF_HLTHNT", "DC_TOF_HLTHL"}
# Absolute counts that duplicate a rate series for the same quantity; keeping both would
# make one gap look like two.
EXCLUDED_COUNT_DUPLICATES = {"SH_DYN_IMRTN", "SH_DYN_NMRTN", "SH_DYN_MORTN", "SH_STA_TRAFN"}


def sdg3_series(series_list_path: Path) -> list[str]:
    rows = json.loads(series_list_path.read_text(encoding="utf-8"))
    codes = {r["code"] for r in rows if "3" in r["goal"]}
    return sorted(codes - EXCLUDED_ODA - EXCLUDED_COUNT_DUPLICATES)
