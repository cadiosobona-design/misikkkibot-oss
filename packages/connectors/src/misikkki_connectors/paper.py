from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from misikkki_connectors.contract import BrokerResult
from misikkki_core.models import Order, OrderIntent, OrderStatus, Position, Side, utc_now
from misikkki_risk.engine import RiskState


@dataclass
class PaperBroker:
    """Deterministic no-credential broker for paper sessions."""

    state: RiskState = field(default_factory=RiskState)
    _states: dict[str, RiskState] = field(default_factory=dict)
    _positions: dict[tuple[str, str], Position] = field(default_factory=dict)
    _submitted_results: dict[str, BrokerResult] = field(default_factory=dict)

    def state_for(self, session_id: str) -> RiskState:
        state = self._states.setdefault(session_id, RiskState())
        self.state = state
        return state

    def submit_order(self, intent: OrderIntent, *, market_price: Decimal) -> BrokerResult:
        existing = self._submitted_results.get(intent.client_order_id)
        if existing is not None:
            return existing

        state = self.state_for(intent.session_id)
        position_key = (intent.session_id, intent.symbol)
        current = self._positions.get(
            position_key,
            Position(
                session_id=intent.session_id,
                symbol=intent.symbol,
                qty=Decimal("0"),
                avg_price=Decimal("0"),
                realized_pnl=Decimal("0"),
                updated_at=intent.created_at,
            ),
        )

        realized = Decimal("0")
        if intent.side == Side.BUY:
            next_qty = current.qty + intent.qty
            next_avg = ((current.qty * current.avg_price) + (intent.qty * market_price)) / next_qty
        else:
            next_qty = current.qty - intent.qty
            realized = (market_price - current.avg_price) * intent.qty
            next_avg = Decimal("0") if next_qty == 0 else current.avg_price

        next_position = Position(
            session_id=intent.session_id,
            symbol=intent.symbol,
            qty=next_qty,
            avg_price=next_avg,
            realized_pnl=current.realized_pnl + realized,
            updated_at=intent.created_at,
        )
        self._positions[position_key] = next_position
        state.positions[intent.symbol] = next_position.qty
        state.avg_prices[intent.symbol] = next_position.avg_price
        state.daily_realized_pnl += realized
        if realized < 0:
            state.last_loss_at = intent.created_at

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
            exchange_order_id=f"paper:{intent.client_order_id}",
            created_at=intent.created_at,
            updated_at=intent.created_at,
        )
        result = BrokerResult(order=order, realized_pnl=realized)
        self._submitted_results[intent.client_order_id] = result
        return result

    def cancel_all(self, session_id: str, *, reason: str) -> list[Order]:
        return []

    def position(self, session_id: str, symbol: str) -> Position:
        return self._positions.get(
            (session_id, symbol),
            Position(
                session_id=session_id,
                symbol=symbol,
                qty=Decimal("0"),
                avg_price=Decimal("0"),
                realized_pnl=Decimal("0"),
                updated_at=next(iter(self._positions.values())).updated_at if self._positions else utc_now(),
            ),
        )

    def positions(self, session_id: str | None = None) -> list[Position]:
        if session_id is None:
            return list(self._positions.values())
        return [position for key, position in self._positions.items() if key[0] == session_id]
