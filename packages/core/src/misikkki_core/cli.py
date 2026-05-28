from __future__ import annotations

import argparse
from pathlib import Path

from misikkki_connectors import LiveTradingUnavailable, create_broker
from misikkki_core.engine import PaperDemoConfig, default_config, run_paper_demo
from misikkki_core.strategy import MovingAverageCrossoverStrategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="misikkki", description="MisikkkiBot OSS clean-room MVP")
    subcommands = parser.add_subparsers(dest="command")

    paper_demo = subcommands.add_parser("paper-demo", help="Run the no-credential paper-trading demo")
    paper_demo.add_argument("--data", type=Path, default=None, help="CSV OHLCV data path")
    paper_demo.add_argument("--database", type=Path, default=None, help="SQLite output path")
    paper_demo.add_argument("--audit-log", type=Path, default=None, help="Append-only JSONL audit path")
    paper_demo.add_argument("--max-bars", type=int, default=None, help="Replay only the first N bars")

    subcommands.add_parser("inspect-strategy", help="Print the built-in strategy template parameters")
    subcommands.add_parser("verify-no-live", help="Verify that live trading is unavailable")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "paper-demo"

    if command == "paper-demo":
        defaults = default_config()
        config = PaperDemoConfig(
            sample_path=args.data or defaults.sample_path,
            database_path=args.database or defaults.database_path,
            audit_log_path=args.audit_log or defaults.audit_log_path,
            max_bars=args.max_bars,
        )
        result = run_paper_demo(config)
        print("MisikkkiBot OSS paper demo complete")
        print(f"session_id={result.session_id}")
        print(f"orders={result.summary['orders']}")
        print(f"risk_decisions={result.summary['risk_decisions']}")
        print(f"blocked_orders={result.summary['blocked_orders']}")
        print(f"database={result.database_path}")
        print(f"audit_log={result.audit_log_path}")
        return 0

    if command == "inspect-strategy":
        strategy = MovingAverageCrossoverStrategy()
        for key, value in strategy.parameters().items():
            print(f"{key}={value}")
        return 0

    if command == "verify-no-live":
        try:
            create_broker("live")
        except LiveTradingUnavailable as exc:
            print(str(exc))
            return 0
        raise RuntimeError("Live broker unexpectedly available")

    parser.error(f"Unknown command: {command}")
    return 2
