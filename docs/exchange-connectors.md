# Exchange Connectors

## MVP Connector Scope

1. Paper broker: default first-run mode, no credentials, deterministic fills.
2. CSV replay: bundled or user-provided OHLCV data.
3. Fake sandbox exchange: CI-safe contract tests with no network or credentials.
4. Binance Spot Testnet adapter configuration: guarded testnet-only request planning, not used by default demos.

## Connector Rules

- CI must not require real exchange credentials.
- Any sandbox connector must assert a sandbox or testnet endpoint before order submission.
- Client order ids must be deterministic enough for reconciliation.
- Order creation timeouts must move to unknown submission state; retry must reconcile by client order id first.
- Live exchange endpoints are unavailable in MVP.

## Binance Spot Testnet Notes

The adapter default base URL is `https://testnet.binance.vision/api`.

The adapter refuses URLs that do not contain `testnet` or `sandbox`, and it refuses withdrawal or transfer permissions. Real network submission is intentionally not part of the default paper demo or CI path.
