from datetime import timedelta
from decimal import Decimal

from misikkki_core.models import OrderIntent, OrderType, Side, utc_now
from misikkki_risk import RiskEngine, RiskPolicy, RiskState, activate_kill_switch


def _intent(**overrides):
    now = overrides.pop("created_at", utc_now())
    values = {
        "session_id": "session-1",
        "client_order_id": "order-1",
        "strategy_id": "strategy-1",
        "symbol": "BTC/USDT",
        "side": Side.BUY,
        "order_type": OrderType.MARKET,
        "qty": Decimal("0.1"),
        "limit_price": None,
        "reason": "test",
        "created_at": now,
    }
    values.update(overrides)
    return OrderIntent(**values)


def _evaluate(engine, intent=None, *, state=None, market_price=Decimal("100"), now=None, market_data_ts=None):
    now = now or utc_now()
    return engine.evaluate(
        intent or _intent(created_at=now),
        market_price=market_price,
        state=state or RiskState(),
        now=now,
        market_data_ts=now if market_data_ts is None else market_data_ts,
    )


def test_kill_switch_blocks_new_order_intents():
    state = RiskState()
    activate_kill_switch(state, "operator stop")

    decision = _evaluate(RiskEngine(), state=state)

    assert not decision.allowed
    assert decision.rule_id == "kill_switch"


def test_max_position_size_blocks_oversized_position():
    engine = RiskEngine(RiskPolicy(max_position_notional=Decimal("5")))

    decision = _evaluate(engine, _intent(qty=Decimal("0.1")))

    assert not decision.allowed
    assert decision.rule_id == "max_position_notional"


def test_max_daily_loss_blocks_after_loss_limit():
    engine = RiskEngine(RiskPolicy(max_daily_loss=Decimal("10")))
    state = RiskState(daily_realized_pnl=Decimal("-10"))

    decision = _evaluate(engine, state=state)

    assert not decision.allowed
    assert decision.rule_id == "max_daily_loss"


def test_open_order_limit_blocks_new_order():
    engine = RiskEngine(RiskPolicy(max_open_orders=1))
    state = RiskState(open_orders=1)

    decision = _evaluate(engine, state=state)

    assert not decision.allowed
    assert decision.rule_id == "max_open_orders"


def test_stale_market_data_blocks_order():
    now = utc_now()
    engine = RiskEngine(RiskPolicy(market_data_max_age_seconds=5))

    decision = _evaluate(engine, now=now, market_data_ts=now - timedelta(seconds=10))

    assert not decision.allowed
    assert decision.rule_id == "market_data_freshness"


def test_missing_market_data_timestamp_blocks_order():
    decision = RiskEngine(RiskPolicy(market_data_max_age_seconds=5)).evaluate(
        _intent(),
        market_price=Decimal("100"),
        state=RiskState(),
        now=utc_now(),
        market_data_ts=None,
    )

    assert not decision.allowed
    assert decision.rule_id == "market_data_required"


def test_slippage_limit_blocks_far_limit_order():
    engine = RiskEngine(RiskPolicy(max_slippage_bps=Decimal("10")))

    decision = _evaluate(
        engine,
        _intent(order_type=OrderType.LIMIT, limit_price=Decimal("105")),
        market_price=Decimal("100"),
    )

    assert not decision.allowed
    assert decision.rule_id == "max_slippage"


def test_no_short_selling_blocks_sell_without_position():
    decision = _evaluate(
        RiskEngine(),
        _intent(side=Side.SELL),
        market_price=Decimal("100"),
    )

    assert not decision.allowed
    assert decision.rule_id == "no_short_selling"
