from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from misikkki_connectors.contract import BrokerResult
from misikkki_core.models import Order, OrderIntent, OrderStatus


@dataclass
class FakeSandboxExchange:
    base_url: str = "https://sandbox.example.local/api"
    orders: dict[str, Order] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert_sandbox_endpoint(self.base_url)

    def submit_order(self, intent: OrderIntent, *, market_price: Decimal) -> BrokerResult:
        existing = self.orders.get(intent.client_order_id)
        if existing is not None:
            return BrokerResult(order=existing)

        order = Order(
            session_id=intent.session_id,
            client_order_id=intent.client_order_id,
            symbol=intent.symbol,
            side=intent.side,
            order_type=intent.order_type,
            qty=intent.qty,
            limit_price=intent.limit_price,
            filled_price=market_price,
            status=OrderStatus.FILLED,
            exchange_order_id=f"fake:{intent.client_order_id}",
            created_at=intent.created_at,
            updated_at=intent.created_at,
        )
        self.orders[intent.client_order_id] = order
        return BrokerResult(order=order)

    def cancel_all(self, session_id: str, *, reason: str) -> list[Order]:
        cancelled: list[Order] = []
        for order in self.orders.values():
            if order.session_id == session_id and order.status == OrderStatus.NEW:
                cancelled.append(
                    Order(
                        session_id=order.session_id,
                        client_order_id=order.client_order_id,
                        symbol=order.symbol,
                        side=order.side,
                        order_type=order.order_type,
                        qty=order.qty,
                        limit_price=order.limit_price,
                        filled_price=order.filled_price,
                        exchange_order_id=order.exchange_order_id,
                        status=OrderStatus.CANCELLED,
                        created_at=order.created_at,
                        updated_at=order.updated_at,
                    )
                )
        return cancelled


def assert_sandbox_endpoint(base_url: str) -> None:
    lowered = base_url.lower()
    if "sandbox" not in lowered and "testnet" not in lowered:
        raise ValueError(f"Refusing non-sandbox exchange endpoint: {base_url}")
