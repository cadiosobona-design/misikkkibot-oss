from __future__ import annotations

import csv
from pathlib import Path

from misikkki_core.models import Candle


def load_candles(path: str | Path) -> list[Candle]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return [Candle.from_mapping(row) for row in csv.DictReader(handle)]
