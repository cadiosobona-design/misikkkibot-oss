from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import uuid4

from misikkki_audit.log import AuditEvent
from misikkki_core.models import Candle, Order, Position
from misikkki_risk.engine import RiskDecision
from misikkki_security.redaction import redact_payload


class OrderReconciliationError(RuntimeError):
    pass


class SQLiteRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def apply_migrations(self) -> None:
        with self.connect() as connection:
            for script in _migration_scripts():
                connection.executescript(script)

    def create_session(
        self,
        *,
        session_id: str,
        mode: str,
        strategy_id: str,
        started_at: datetime,
        status: str,
        config_hash: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions(id, mode, strategy_id, started_at, status, config_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, mode, strategy_id, started_at.isoformat(), status, config_hash),
            )

    def stop_session(self, *, session_id: str, stopped_at: datetime, status: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE sessions SET stopped_at = ?, status = ? WHERE id = ?",
                (stopped_at.isoformat(), status, session_id),
            )

    def record_strategy_version(
        self,
        *,
        strategy_id: str,
        name: str,
        source_kind: str,
        source_hash: str,
        params: dict[str, Any],
        created_at: datetime,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO strategy_versions(
                  id, name, source_kind, source_hash, params_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    strategy_id,
                    name,
                    source_kind,
                    source_hash,
                    json.dumps(redact_payload(params), sort_keys=True),
                    created_at.isoformat(),
                ),
            )

    def record_market_bar(self, candle: Candle) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO market_bars(
                  symbol, timeframe, ts, open, high, low, close, volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candle.symbol,
                    candle.timeframe,
                    candle.ts.isoformat(),
                    str(candle.open),
                    str(candle.high),
                    str(candle.low),
                    str(candle.close),
                    str(candle.volume),
                ),
            )

    def record_audit_event(self, event: AuditEvent) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events(id, session_id, event_type, ts, payload_json_redacted)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.session_id,
                    event.event_type,
                    event.ts.isoformat(),
                    json.dumps(event.payload, sort_keys=True),
                ),
            )

    def record_order(self, order: Order) -> None:
        expected = self._order_record(order)
        with self.connect() as connection:
            existing = self._order_by_client_order_id(connection, order.client_order_id)
            if existing is not None:
                self._ensure_order_matches(existing, expected, order.client_order_id)
                return

            try:
                connection.execute(
                    """
                    INSERT INTO orders(
                      id, session_id, client_order_id, symbol, side, type, qty, limit_price,
                      status, exchange_order_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid4()),
                        expected["session_id"],
                        expected["client_order_id"],
                        expected["symbol"],
                        expected["side"],
                        expected["type"],
                        expected["qty"],
                        expected["limit_price"],
                        expected["status"],
                        expected["exchange_order_id"],
                        expected["created_at"],
                        expected["updated_at"],
                    ),
                )
            except sqlite3.IntegrityError:
                existing = self._order_by_client_order_id(connection, order.client_order_id)
                if existing is None:
                    raise
                self._ensure_order_matches(existing, expected, order.client_order_id)

    def _order_by_client_order_id(self, connection: sqlite3.Connection, client_order_id: str) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT session_id, client_order_id, symbol, side, type, qty, limit_price,
                   status, exchange_order_id, created_at, updated_at
            FROM orders
            WHERE client_order_id = ?
            """,
            (client_order_id,),
        ).fetchone()

    def _order_record(self, order: Order) -> dict[str, str | None]:
        return {
            "session_id": order.session_id,
            "client_order_id": order.client_order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "type": order.order_type.value,
            "qty": str(order.qty),
            "limit_price": str(order.limit_price) if order.limit_price is not None else None,
            "status": order.status.value,
            "exchange_order_id": order.exchange_order_id,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

    def _ensure_order_matches(
        self,
        existing: sqlite3.Row,
        expected: dict[str, str | None],
        client_order_id: str,
    ) -> None:
        mismatches = [column for column, value in expected.items() if existing[column] != value]
        if mismatches:
            raise OrderReconciliationError(
                f"Conflicting order record for client_order_id {client_order_id}: {', '.join(mismatches)}"
            )

    def upsert_position(self, position: Position) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO positions(id, session_id, symbol, qty, avg_price, realized_pnl, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, symbol) DO UPDATE SET
                  qty = excluded.qty,
                  avg_price = excluded.avg_price,
                  realized_pnl = excluded.realized_pnl,
                  updated_at = excluded.updated_at
                """,
                (
                    str(uuid4()),
                    position.session_id,
                    position.symbol,
                    str(position.qty),
                    str(position.avg_price),
                    str(position.realized_pnl),
                    position.updated_at.isoformat(),
                ),
            )

    def record_risk_decision(
        self,
        *,
        session_id: str,
        order_id: str,
        decision: RiskDecision,
        ts: datetime,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO risk_decisions(id, session_id, order_id, allowed, rule_id, reason, ts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    session_id,
                    order_id,
                    1 if decision.allowed else 0,
                    decision.rule_id,
                    decision.reason,
                    ts.isoformat(),
                ),
            )

    def recent_events(self, session_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, ts, payload_json_redacted
                FROM audit_events
                WHERE session_id = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [
            {
                "event_type": row["event_type"],
                "ts": row["ts"],
                "payload": json.loads(row["payload_json_redacted"]),
            }
            for row in rows
        ]

    def session_summary(self, session_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            session = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            order_count = connection.execute(
                "SELECT COUNT(*) AS count FROM orders WHERE session_id = ?",
                (session_id,),
            ).fetchone()["count"]
            blocked_count = connection.execute(
                "SELECT COUNT(*) AS count FROM risk_decisions WHERE session_id = ? AND allowed = 0",
                (session_id,),
            ).fetchone()["count"]
            risk_count = connection.execute(
                "SELECT COUNT(*) AS count FROM risk_decisions WHERE session_id = ?",
                (session_id,),
            ).fetchone()["count"]
        return {
            "session_id": session_id,
            "status": session["status"] if session else "missing",
            "orders": order_count,
            "risk_decisions": risk_count,
            "blocked_orders": blocked_count,
        }


def _migration_scripts() -> list[str]:
    migrations = files("misikkki_storage").joinpath("migrations")
    return [
        migration.read_text(encoding="utf-8")
        for migration in sorted(migrations.iterdir(), key=lambda item: item.name)
        if migration.name.endswith(".sql")
    ]
