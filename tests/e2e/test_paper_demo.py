import json
import sqlite3
from pathlib import Path

from misikkki_core.engine import PaperDemoConfig, run_paper_demo, trigger_demo_kill_switch


def test_paper_demo_runs_without_credentials_and_records_audit(tmp_path: Path):
    result = run_paper_demo(
        PaperDemoConfig(
            sample_path=Path("sample_data/btc_usdt_1m.csv"),
            database_path=tmp_path / "demo.sqlite",
            audit_log_path=tmp_path / "audit.jsonl",
        )
    )

    assert result.summary["orders"] >= 1
    assert result.summary["risk_decisions"] >= result.summary["orders"]
    assert result.audit_log_path.exists()
    assert result.database_path.exists()

    events = [json.loads(line) for line in result.audit_log_path.read_text(encoding="utf-8").splitlines()]
    event_types = {event["event_type"] for event in events}
    assert {"session_started", "strategy_signal", "risk_decision", "paper_order_filled", "session_stopped"} <= event_types
    assert all("api_key" not in json.dumps(event).lower() for event in events)

    with sqlite3.connect(result.database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert {"sessions", "orders", "positions", "risk_decisions", "audit_events", "market_bars"} <= tables


def test_kill_switch_audit_event_is_persisted(tmp_path: Path):
    result = run_paper_demo(
        PaperDemoConfig(
            sample_path=Path("sample_data/btc_usdt_1m.csv"),
            database_path=tmp_path / "demo.sqlite",
            audit_log_path=tmp_path / "audit.jsonl",
        )
    )

    payload = trigger_demo_kill_switch(result, "test operator stop")

    assert payload["event"] == "kill_switch_activated"
    assert "kill_switch_activated" in result.audit_log_path.read_text(encoding="utf-8")
