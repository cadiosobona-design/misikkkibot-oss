import sqlite3
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from misikkki_connectors import PaperBroker
from misikkki_core.models import OrderIntent, OrderType, SessionMode, Side, utc_now
from misikkki_storage import OrderReconciliationError, SQLiteRepository


def test_schema_creates_required_indexes(tmp_path: Path):
    db_path = tmp_path / "demo.sqlite"
    SQLiteRepository(db_path).apply_migrations()

    with sqlite3.connect(db_path) as connection:
        index_names = {
            row[1]
            for row in connection.execute(
                "SELECT type, name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert "idx_audit_events_session_ts" in index_names
    assert "idx_orders_session_status" in index_names
    assert "idx_orders_symbol_created_at" in index_names
    assert "idx_risk_decisions_session_ts" in index_names


def test_record_order_is_idempotent_for_broker_retry(tmp_path: Path):
    repo = SQLiteRepository(tmp_path / "demo.sqlite")
    repo.apply_migrations()
    now = utc_now()
    repo.create_session(
        session_id="session-1",
        mode=SessionMode.PAPER.value,
        strategy_id="strategy-1",
        started_at=now,
        status="running",
        config_hash="test",
    )
    broker = PaperBroker()
    intent = OrderIntent(
        session_id="session-1",
        client_order_id="retry-1",
        strategy_id="strategy-1",
        symbol="BTC/USDT",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=Decimal("0.1"),
        limit_price=None,
        reason="test retry",
        created_at=now,
    )

    first = broker.submit_order(intent, market_price=Decimal("100"))
    duplicate = broker.submit_order(intent, market_price=Decimal("200"))
    repo.record_order(first.order)
    repo.record_order(duplicate.order)

    assert repo.session_summary("session-1")["orders"] == 1


def test_record_order_conflicting_duplicate_requires_reconciliation(tmp_path: Path):
    repo = SQLiteRepository(tmp_path / "demo.sqlite")
    repo.apply_migrations()
    now = utc_now()
    repo.create_session(
        session_id="session-1",
        mode=SessionMode.PAPER.value,
        strategy_id="strategy-1",
        started_at=now,
        status="running",
        config_hash="test",
    )
    broker = PaperBroker()
    intent = OrderIntent(
        session_id="session-1",
        client_order_id="retry-1",
        strategy_id="strategy-1",
        symbol="BTC/USDT",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        qty=Decimal("0.1"),
        limit_price=None,
        reason="test retry",
        created_at=now,
    )
    result = broker.submit_order(intent, market_price=Decimal("100"))
    repo.record_order(result.order)

    with pytest.raises(OrderReconciliationError, match="qty"):
        repo.record_order(replace(result.order, qty=Decimal("0.2")))
