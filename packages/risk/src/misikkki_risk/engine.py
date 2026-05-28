from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from misikkki_core.models import OrderIntent, Side, parse_decimal, utc_now


@dataclass(frozen=True)
class RiskPolicy:
    max_order_notional: Decimal = Decimal("1000")
    max_position_notional: Decimal = Decimal("2500")
    max_daily_loss: Decimal = Decimal("250")
    max_open_orders: int = 3
    allowed_symbols: tuple[str, ...] = ("BTC/USDT",)
    allowed_order_types: tuple[str, ...] = ("market", "limit")
    cooldown_after_loss_seconds: int = 300
    market_data_max_age_seconds: int = 60
    max_slippage_bps: Decimal = Decimal("50")
    allow_short: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_order_notional", parse_decimal(self.max_order_notional))
        object.__setattr__(self, "max_position_notional", parse_decimal(self.max_position_notional))
        object.__setattr__(self, "max_daily_loss", parse_decimal(self.max_daily_loss))
        object.__setattr__(self, "max_slippage_bps", parse_decimal(self.max_slippage_bps))


@dataclass
class RiskState:
    positions: dict[str, Decimal] = field(default_factory=dict)
    avg_prices: dict[str, Decimal] = field(default_factory=dict)
    daily_realized_pnl: Decimal = Decimal("0")
    open_orders: int = 0
    last_loss_at: datetime | None = None
    kill_switch_active: bool = False
    kill_switch_reason: str | None = None


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    rule_id: str
    reason: str


class RiskEngine:
    def __init__(self, policy: RiskPolicy | None = None) -> None:
        self.policy = policy or RiskPolicy()

    def evaluate(
        self,
        intent: OrderIntent,
        *,
        market_price: Decimal,
        state: RiskState,
        now: datetime | None = None,
        market_data_ts: datetime | None = None,
    ) -> RiskDecision:
        now = now or utc_now()
        market_price = parse_decimal(market_price)

        if state.kill_switch_active:
            return RiskDecision(
                False,
                "kill_switch",
                f"Kill switch is active: {state.kill_switch_reason or 'no reason recorded'}",
            )

        if intent.symbol not in self.policy.allowed_symbols:
            return RiskDecision(False, "allowed_symbols", f"{intent.symbol} is not allowed")

        if intent.order_type.value not in self.policy.allowed_order_types:
            return RiskDecision(False, "allowed_order_types", f"{intent.order_type.value} orders are not allowed")

        if intent.qty <= 0:
            return RiskDecision(False, "positive_quantity", "Order quantity must be positive")

        if market_data_ts is None:
            return RiskDecision(
                False,
                "market_data_required",
                "Market data timestamp is required for freshness validation",
            )

        age = now - market_data_ts
        if age < timedelta(0) or age > timedelta(seconds=self.policy.market_data_max_age_seconds):
            return RiskDecision(False, "market_data_freshness", f"Market data is stale by {age.total_seconds():.0f}s")

        order_notional = intent.notional(market_price)
        if order_notional > self.policy.max_order_notional:
            return RiskDecision(
                False,
                "max_order_notional",
                f"Order notional {order_notional} exceeds {self.policy.max_order_notional}",
            )

        if state.open_orders >= self.policy.max_open_orders:
            return RiskDecision(False, "max_open_orders", "Open order limit reached")

        if state.daily_realized_pnl <= -self.policy.max_daily_loss:
            return RiskDecision(
                False,
                "max_daily_loss",
                f"Daily loss {state.daily_realized_pnl} breaches {self.policy.max_daily_loss}",
            )

        if state.last_loss_at is not None:
            cooldown = timedelta(seconds=self.policy.cooldown_after_loss_seconds)
            if now - state.last_loss_at < cooldown:
                return RiskDecision(False, "cooldown_after_loss", "Loss cooldown is still active")

        current_qty = state.positions.get(intent.symbol, Decimal("0"))
        next_qty = current_qty + intent.qty if intent.side == Side.BUY else current_qty - intent.qty
        if not self.policy.allow_short and next_qty < 0:
            return RiskDecision(False, "no_short_selling", "Paper MVP does not allow short positions")

        next_position_notional = abs(next_qty * market_price)
        if next_position_notional > self.policy.max_position_notional:
            return RiskDecision(
                False,
                "max_position_notional",
                f"Position notional {next_position_notional} exceeds {self.policy.max_position_notional}",
            )

        if intent.limit_price is not None:
            slippage_bps = abs((intent.limit_price - market_price) / market_price) * Decimal("10000")
            if slippage_bps > self.policy.max_slippage_bps:
                return RiskDecision(
                    False,
                    "max_slippage",
                    f"Limit price differs from reference by {slippage_bps:.2f} bps",
                )

        return RiskDecision(True, "allowed", "Order intent passed all MVP risk controls")
