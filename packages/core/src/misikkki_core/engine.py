from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from uuid import uuid4

from misikkki_audit import AppendOnlyAuditLog
from misikkki_backtest import load_candles
from misikkki_connectors.factory import create_broker
from misikkki_core.models import OrderIntent, OrderType, SessionMode, utc_now
from misikkki_core.strategy import MovingAverageCrossoverStrategy
from misikkki_risk import RiskEngine, RiskPolicy
from misikkki_risk.kill_switch import activate_kill_switch
from misikkki_storage import SQLiteRepository


@dataclass(frozen=True)
class PaperDemoConfig:
    sample_path: Path | Traversable
    database_path: Path
    audit_log_path: Path
    max_bars: int | None = None
    policy: RiskPolicy = RiskPolicy()


@dataclass(frozen=True)
class PaperDemoResult:
    session_id: str
    database_path: Path
    audit_log_path: Path
    summary: dict[str, object]


def default_sample_path() -> Path | Traversable:
    cwd_candidate = Path.cwd() / "sample_data" / "btc_usdt_1m.csv"
    if cwd_candidate.exists():
        return cwd_candidate
    return files("misikkki_data").joinpath("sample_data", "btc_usdt_1m.csv")


def default_runtime_dir() -> Path:
    override = os.environ.get("MISIKKKI_RUNTIME_DIR")
    if override:
        return Path(override)

    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        base_dir = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base_dir / "MisikkkiBot" / "runtime"

    return Path.cwd() / ".misikkki"


def default_config() -> PaperDemoConfig:
    runtime_dir = default_runtime_dir()
    return PaperDemoConfig(
        sample_path=default_sample_path(),
        database_path=runtime_dir / "demo.sqlite",
        audit_log_path=runtime_dir / "audit.jsonl",
    )


def _stable_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def run_paper_demo(config: PaperDemoConfig | None = None) -> PaperDemoResult:
    config = config or default_config()
    candles = load_candles(config.sample_path)
    if config.max_bars is not None:
        candles = candles[: config.max_bars]
    if not candles:
        raise ValueError("No candles available for paper demo")

    session_id = str(uuid4())
    strategy = MovingAverageCrossoverStrategy(symbol=candles[0].symbol)
    risk_engine = RiskEngine(config.policy)
    broker = create_broker("paper")
    repository = SQLiteRepository(config.database_path)
    repository.apply_migrations()
    audit = AppendOnlyAuditLog(config.audit_log_path)

    started_at = candles[0].ts
    strategy_params = strategy.parameters()
    policy_payload = {
        "max_order_notional": str(config.policy.max_order_notional),
        "max_position_notional": str(config.policy.max_position_notional),
        "max_daily_loss": str(config.policy.max_daily_loss),
        "max_open_orders": config.policy.max_open_orders,
        "allowed_symbols": list(config.policy.allowed_symbols),
        "allowed_order_types": list(config.policy.allowed_order_types),
        "market_data_max_age_seconds": config.policy.market_data_max_age_seconds,
        "max_slippage_bps": str(config.policy.max_slippage_bps),
    }
    config_hash = _stable_hash({"strategy": strategy_params, "policy": policy_payload})

    repository.create_session(
        session_id=session_id,
        mode=SessionMode.PAPER.value,
        strategy_id=strategy.strategy_id,
        started_at=started_at,
        status="running",
        config_hash=config_hash,
    )
    repository.record_strategy_version(
        strategy_id=strategy.strategy_id,
        name="Moving Average Crossover",
        source_kind="declarative_template",
        source_hash=_stable_hash(strategy_params),
        params=strategy_params,
        created_at=started_at,
    )
    _record(repository, audit, session_id, "session_started", {"mode": "paper", "config_hash": config_hash}, ts=started_at)
    _record(repository, audit, session_id, "strategy_parameters", strategy_params, ts=started_at)
    _record(repository, audit, session_id, "risk_policy", policy_payload, ts=started_at)

    signal_count = 0
    last_ts = started_at
    for candle in candles:
        last_ts = candle.ts
        repository.record_market_bar(candle)
        signal = strategy.on_candle(candle)
        if signal is None:
            continue

        signal_count += 1
        client_order_id = f"{session_id[:8]}-{signal_count:04d}"
        intent = OrderIntent(
            session_id=session_id,
            client_order_id=client_order_id,
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            side=signal.side,
            order_type=OrderType.MARKET,
            qty=strategy.qty,
            limit_price=None,
            reason=signal.reason,
            created_at=candle.ts,
        )
        _record(
            repository,
            audit,
            session_id,
            "strategy_signal",
            {
                "client_order_id": client_order_id,
                "symbol": signal.symbol,
                "side": signal.side.value,
                "reason": signal.reason,
                "observed_price": str(signal.observed_price),
            },
            ts=candle.ts,
        )
        broker_state = broker.state_for(session_id) if hasattr(broker, "state_for") else broker.state
        decision = risk_engine.evaluate(
            intent,
            market_price=candle.close,
            state=broker_state,
            now=candle.ts,
            market_data_ts=candle.ts,
        )
        repository.record_risk_decision(session_id=session_id, order_id=client_order_id, decision=decision, ts=candle.ts)
        _record(
            repository,
            audit,
            session_id,
            "risk_decision",
            {
                "client_order_id": client_order_id,
                "allowed": decision.allowed,
                "rule_id": decision.rule_id,
                "reason": decision.reason,
            },
            ts=candle.ts,
        )

        if not decision.allowed:
            _record(
                repository,
                audit,
                session_id,
                "order_blocked",
                {"client_order_id": client_order_id, "rule_id": decision.rule_id, "reason": decision.reason},
                ts=candle.ts,
            )
            continue

        result = broker.submit_order(intent, market_price=candle.close)
        repository.record_order(result.order)
        for position in broker.positions(session_id=session_id):
            repository.upsert_position(position)
        _record(
            repository,
            audit,
            session_id,
            "paper_order_filled",
            {
                "client_order_id": result.order.client_order_id,
                "side": result.order.side.value,
                "qty": str(result.order.qty),
                "filled_price": str(result.order.filled_price),
                "realized_pnl": str(result.realized_pnl),
            },
            ts=candle.ts,
        )

    repository.stop_session(session_id=session_id, stopped_at=last_ts, status="stopped")
    _record(repository, audit, session_id, "session_stopped", {"reason": "sample_replay_complete"}, ts=last_ts)
    return PaperDemoResult(
        session_id=session_id,
        database_path=config.database_path,
        audit_log_path=config.audit_log_path,
        summary=repository.session_summary(session_id),
    )


def trigger_demo_kill_switch(result: PaperDemoResult, reason: str = "operator_requested") -> dict[str, str]:
    repository = SQLiteRepository(result.database_path)
    audit = AppendOnlyAuditLog(result.audit_log_path)
    broker = create_broker("paper")
    payload = activate_kill_switch(broker.state, reason)
    event = audit.append(result.session_id, "kill_switch_activated", payload)
    repository.record_audit_event(event)
    return payload


def _record(
    repository: SQLiteRepository,
    audit: AppendOnlyAuditLog,
    session_id: str,
    event_type: str,
    payload: dict[str, object],
    *,
    ts,
) -> None:
    event = audit.append(session_id, event_type, payload, ts=ts)
    repository.record_audit_event(event)
