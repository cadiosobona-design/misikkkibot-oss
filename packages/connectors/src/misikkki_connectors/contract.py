from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from misikkki_core.models import Order, OrderIntent


class BrokerUnavailableError(RuntimeError):
    pass


class LiveTradingUnavailable(BrokerUnavailableError):
    pass


@dataclass(frozen=True)
class BrokerResult:
    order: Order
    realized_pnl: Decimal = Decimal("0")


class Broker(Protocol):
    def submit_order(self, intent: OrderIntent, *, market_price: Decimal) -> BrokerResult:
        ...

    def cancel_all(self, session_id: str, *, reason: str) -> list[Order]:
        ...
