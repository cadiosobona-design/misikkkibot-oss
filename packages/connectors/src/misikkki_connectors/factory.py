from __future__ import annotations

from misikkki_connectors.contract import LiveTradingUnavailable
from misikkki_connectors.fake_exchange import FakeSandboxExchange
from misikkki_connectors.paper import PaperBroker


def create_broker(mode: str):
    normalized = mode.lower().strip()
    if normalized == "paper":
        return PaperBroker()
    if normalized in {"sandbox", "testnet"}:
        return FakeSandboxExchange()
    if normalized == "live":
        raise LiveTradingUnavailable("Live trading is not implemented in the MVP and requires a later CEO gate")
    raise ValueError(f"Unknown broker mode: {mode}")
