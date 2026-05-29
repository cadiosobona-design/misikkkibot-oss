from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from misikkki_core.models import Candle


def load_candles(path: str | Path | Any) -> list[Candle]:
    readable = path if hasattr(path, "open") else Path(path)
    with readable.open("r", encoding="utf-8", newline="") as handle:
        return [Candle.from_mapping(row) for row in csv.DictReader(handle)]
