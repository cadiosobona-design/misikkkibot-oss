from decimal import Decimal

import pytest

from misikkki_connectors import LiveTradingUnavailable, PaperBroker, create_broker
from misikkki_connectors.binance_testnet import BinanceSpotTestnetAdapter, BinanceSpotTestnetConfig
from misikkki_connectors.fake_exchange import FakeSandboxExchange
from misikkki_core.models import OrderIntent, OrderType, Side, utc_now


def _intent(**overrides):
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
        "created_at": utc_now(),
    }
    values.update(overrides)
    return OrderIntent(**values)


def test_fake_sandbox_exchange_contract_runs_without_credentials():
    exchange = FakeSandboxExchange()

    result = exchange.submit_order(_intent(), market_price=Decimal("100"))

    assert result.order.status.value == "filled"
    assert result.order.exchange_order_id == "fake:order-1"


def test_fake_sandbox_exchange_is_idempotent_by_client_order_id():
    exchange = FakeSandboxExchange()
    intent = _intent()

    first = exchange.submit_order(intent, market_price=Decimal("100"))
    duplicate = exchange.submit_order(intent, market_price=Decimal("200"))

    assert duplicate == first
    assert len(exchange.orders) == 1
    assert exchange.orders["order-1"].filled_price == Decimal("100")


def test_paper_broker_is_idempotent_by_client_order_id_before_position_mutation():
    broker = PaperBroker()
    intent = _intent()

    first = broker.submit_order(intent, market_price=Decimal("100"))
    duplicate = broker.submit_order(intent, market_price=Decimal("200"))
    position = broker.position(intent.session_id, intent.symbol)

    assert duplicate == first
    assert position.qty == Decimal("0.1")
    assert position.avg_price == Decimal("100")
    assert broker.state.positions[intent.symbol] == Decimal("0.1")


def test_paper_broker_positions_are_isolated_by_session():
    broker = PaperBroker()
    symbol = "BTC/USDT"

    broker.submit_order(_intent(session_id="session-1", client_order_id="s1-order"), market_price=Decimal("100"))
    session_2_before = broker.position("session-2", symbol)
    broker.submit_order(
        _intent(session_id="session-2", client_order_id="s2-order", qty=Decimal("0.2")),
        market_price=Decimal("200"),
    )

    session_1_position = broker.position("session-1", symbol)
    session_2_position = broker.position("session-2", symbol)

    assert session_2_before.qty == Decimal("0")
    assert session_1_position.qty == Decimal("0.1")
    assert session_1_position.avg_price == Decimal("100")
    assert session_2_position.qty == Decimal("0.2")
    assert session_2_position.avg_price == Decimal("200")
    assert broker.state_for("session-1").positions[symbol] == Decimal("0.1")
    assert broker.state_for("session-2").positions[symbol] == Decimal("0.2")


def test_fake_exchange_refuses_live_endpoint():
    with pytest.raises(ValueError):
        FakeSandboxExchange(base_url="https://api.exchange.example/v1")


def test_live_broker_is_unavailable_in_mvp():
    with pytest.raises(LiveTradingUnavailable):
        create_broker("live")


def test_binance_testnet_adapter_rejects_withdrawal_posture():
    with pytest.raises(ValueError):
        BinanceSpotTestnetConfig(api_key_label="demo", permissions=("read", "withdraw"))


def test_binance_testnet_adapter_plans_testnet_order_payload():
    config = BinanceSpotTestnetConfig(api_key_label="demo", permissions=("read", "trade"))
    payload = BinanceSpotTestnetAdapter(config).build_order_payload(_intent(), market_price=Decimal("100"))

    assert payload["testnetBaseUrl"] == "https://testnet.binance.vision/api"
    assert payload["newClientOrderId"] == "order-1"
