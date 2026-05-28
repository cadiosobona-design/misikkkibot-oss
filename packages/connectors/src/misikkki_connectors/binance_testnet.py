from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from misikkki_connectors.fake_exchange import assert_sandbox_endpoint
from misikkki_core.models import OrderIntent
from misikkki_security.permissions import assert_no_withdrawal_permissions


@dataclass(frozen=True)
class BinanceSpotTestnetConfig:
    api_key_label: str
    permissions: tuple[str, ...]
    base_url: str = "https://testnet.binance.vision/api"

    def __post_init__(self) -> None:
        assert_sandbox_endpoint(self.base_url)
        assert_no_withdrawal_permissions(self.permissions)


class BinanceSpotTestnetAdapter:
    """Guarded testnet request planner.

    The MVP does not perform network I/O by default. This adapter documents and
    validates the sandbox boundary so future connector work can add signed HTTP
    execution without changing core trading behavior.
    """

    def __init__(self, config: BinanceSpotTestnetConfig) -> None:
        self.config = config

    def build_order_payload(self, intent: OrderIntent, *, market_price: Decimal) -> dict[str, str]:
        return {
            "symbol": intent.symbol.replace("/", ""),
            "side": intent.side.value.upper(),
            "type": intent.order_type.value.upper(),
            "quantity": str(intent.qty),
            "newClientOrderId": intent.client_order_id,
            "testnetBaseUrl": self.config.base_url,
            "referencePrice": str(market_price),
        }
