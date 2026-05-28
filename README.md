# MisikkkiBot OSS

Clean-room, local-first crypto strategy workstation MVP.

This repository is source-first and paper-first. It does not execute, decompile, or reproduce hidden behavior from any proprietary executable. The default workflow runs a bundled sample market replay with no exchange credentials.

## What Is Included

- Paper-trading demo with deterministic fills from bundled OHLCV sample data.
- Inspectable moving-average crossover strategy example.
- Risk controls for allowed symbols, allowed order types, max order notional, max position notional, max daily loss, max open orders, market-data freshness, slippage, cooldown after loss, bounded replay stop condition, and kill switch.
- Append-only JSONL audit log plus SQLite tables for sessions, strategy versions, orders, positions, risk decisions, audit events, and market bars.
- Fake sandbox connector contract tests that require no credentials.
- Guarded Binance Spot Testnet adapter configuration that refuses live endpoints and withdrawal-capable permissions.
- A small desktop launcher built with the Python standard-library Tk toolkit, plus a headless mode for CI and servers.

## Quick Start

Requirements:

- Python 3.12+
- uv 0.11+

```powershell
uv sync
uv run pytest
uv run misikkki paper-demo
uv run misikkki paper-demo --max-bars 6
uv run misikkki-desktop --headless
```

The paper demo writes local runtime files under `.misikkki/` by default:

- `.misikkki/demo.sqlite`
- `.misikkki/audit.jsonl`

These files are generated artifacts and are not needed to inspect the source.

## Run The Desktop Launcher

```powershell
uv run misikkki-desktop
```

If the environment has no GUI display, use the headless path:

```powershell
uv run misikkki-desktop --headless
```

The launcher exposes the first-run paper demo and a visible kill-switch control. Trading behavior remains in the testable core packages; the UI does not call exchange clients directly.

## Inspect Strategy Parameters

```powershell
uv run misikkki inspect-strategy
```

The MVP intentionally supports declarative strategy templates only. It does not execute arbitrary user Python strategy code.

## Safety Posture

- Paper trading is the default and needs no credentials.
- Live-money trading is unavailable in MVP. `create_broker("live")` raises `LiveTradingUnavailable`.
- Withdrawal or transfer permission posture is rejected by the connector/security boundary.
- Every order intent receives an auditable risk decision before paper submission.
- The kill switch blocks new order intents and writes an audit event.

This project makes no profitability claims and is not financial advice.

## Repository Layout

```text
apps/desktop/src/misikkki_desktop/
packages/audit/src/misikkki_audit/
packages/backtest/src/misikkki_backtest/
packages/connectors/src/misikkki_connectors/
packages/core/src/misikkki_core/
packages/risk/src/misikkki_risk/
packages/security/src/misikkki_security/
packages/storage/src/misikkki_storage/
sample_data/
tests/
```

## Clean-Room Notes

See `docs/clean-room.md` for provenance and allowed evidence. The binary named in the parent product issue was not executed, decompiled, copied, or used as an implementation source.
