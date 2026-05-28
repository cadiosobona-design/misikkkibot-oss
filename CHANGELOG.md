# Changelog

## 0.1.0 - 2026-05-28

Initial MisikkkiBot OSS MVP source release candidate.

### Included

- Clean-room, source-first, local-first crypto strategy workstation MVP.
- Paper-trading default path with bundled sample OHLCV data and no credentials.
- Inspectable moving-average crossover strategy example.
- Risk controls for allowed symbols, allowed order types, max order notional, max position notional, max daily loss, max open orders, stale market data, slippage, cooldown after loss, bounded replay, and kill switch.
- SQLite persistence for sessions, orders, positions, market bars, risk decisions, strategy versions, and audit events.
- Append-only JSONL audit log with redacted payloads.
- Fake sandbox connector contract tests and a guarded Binance Spot Testnet request planner.
- Standard-library desktop launcher with CI-safe headless smoke mode.
- Apache-2.0 license posture with NOTICE, clean-room, threat-model, license-review, exchange-connector, and live-trading-gate documentation.

### Fixed

- No-subcommand `misikkki` invocation now uses paper-demo defaults instead of raising an argparse namespace error.

### Not Included

- Live-money trading.
- Withdrawal or transfer-capable API key posture.
- Proprietary binary execution, decompilation, copied implementation, or hidden binary parity claims.
- Profitability claims or financial advice.

### Known Limitations

- The MVP is paper/sandbox only; sandbox request planning does not submit live exchange orders by default.
- Desktop UI depth is intentionally MVP-level; source-run workflows are the primary release surface.
- Live trading requires a separate CEO gate, security review, QA pass, and release approval before any implementation or distribution.
- This is a source release candidate; binary packaging and installer-specific dependency notices are intentionally deferred.
