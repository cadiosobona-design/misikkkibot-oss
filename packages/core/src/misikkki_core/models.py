from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    NEW = "new"
    FILLED = "filled"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    UNKNOWN_SUBMISSION_STATE = "unknown_submission_state"


class SessionMode(StrEnum):
    PAPER = "paper"
    SANDBOX = "sandbox"


def parse_decimal(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Candle:
    ts: datetime
    symbol: str
    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @classmethod
    def from_mapping(cls, row: dict[str, str]) -> "Candle":
        return cls(
            ts=parse_ts(row["ts"]),
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            open=parse_decimal(row["open"]),
            high=parse_decimal(row["high"]),
            low=parse_decimal(row["low"]),
            close=parse_decimal(row["close"]),
            volume=parse_decimal(row["volume"]),
        )


@dataclass(frozen=True)
class StrategySignal:
    symbol: str
    side: Side
    reason: str
    observed_price: Decimal
    candle_ts: datetime
    strategy_id: str


@dataclass(frozen=True)
class OrderIntent:
    session_id: str
    client_order_id: str
    strategy_id: str
    symbol: str
    side: Side
    order_type: OrderType
    qty: Decimal
    limit_price: Decimal | None
    reason: str
    created_at: datetime

    def notional(self, market_price: Decimal) -> Decimal:
        return abs(self.qty * market_price)


@dataclass(frozen=True)
class Order:
    session_id: str
    client_order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    qty: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    limit_price: Decimal | None = None
    filled_price: Decimal | None = None
    exchange_order_id: str | None = None


@dataclass(frozen=True)
class Position:
    session_id: str
    symbol: str
    qty: Decimal
    avg_price: Decimal
    realized_pnl: Decimal
    updated_at: datetime
