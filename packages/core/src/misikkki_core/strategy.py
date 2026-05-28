from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal

from misikkki_core.models import Candle, OrderType, Side, StrategySignal, parse_decimal


@dataclass
class MovingAverageCrossoverStrategy:
    """Inspectable moving-average crossover strategy template."""

    symbol: str = "BTC/USDT"
    short_window: int = 2
    long_window: int = 3
    qty: Decimal = Decimal("0.05")
    order_type: OrderType = OrderType.MARKET
    strategy_id: str = "moving_average_crossover:v1"
    _closes: deque[Decimal] = field(default_factory=deque, init=False)
    _last_state: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Moving average windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        self.qty = parse_decimal(self.qty)

    def parameters(self) -> dict[str, str | int]:
        return {
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "short_window": self.short_window,
            "long_window": self.long_window,
            "qty": str(self.qty),
            "order_type": self.order_type.value,
        }

    def on_candle(self, candle: Candle) -> StrategySignal | None:
        if candle.symbol != self.symbol:
            return None

        self._closes.append(candle.close)
        if len(self._closes) > self.long_window:
            self._closes.popleft()
        if len(self._closes) < self.long_window:
            return None

        closes = list(self._closes)
        short_ma = sum(closes[-self.short_window:]) / Decimal(self.short_window)
        long_ma = sum(closes) / Decimal(self.long_window)

        if short_ma > long_ma:
            state = "above"
        elif short_ma < long_ma:
            state = "below"
        else:
            state = "flat"

        if state == self._last_state or state == "flat":
            self._last_state = state
            return None

        previous = self._last_state or "initial"
        self._last_state = state
        side = Side.BUY if state == "above" else Side.SELL
        return StrategySignal(
            symbol=candle.symbol,
            side=side,
            observed_price=candle.close,
            candle_ts=candle.ts,
            strategy_id=self.strategy_id,
            reason=(
                f"short_ma({self.short_window}) crossed {state} "
                f"long_ma({self.long_window}); previous_state={previous}"
            ),
        )
