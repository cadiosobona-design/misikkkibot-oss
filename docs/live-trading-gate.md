# Live Trading Gate

Live-money auto-trading is not implemented in this MVP.

Before any live trading path exists, a separate CEO review must approve:

- Product scope and user-facing risk language.
- Security review of credential handling and permission introspection.
- Connector review for duplicate-order, retry, rate-limit, and reconciliation behavior.
- QA evidence for risk controls, kill switch, stale-data handling, and audit export.
- Release notes that identify the feature as live-money capable.

Implementation requirements for a future gate:

- Live broker code lives behind a separate interface and is unavailable by default.
- Users must pass a no-withdrawal permission check or explicit non-introspectable-key acknowledgement.
- Every order intent must still pass risk evaluation.
- Emergency stop must cancel open orders where supported and block new intents.

Until that review happens, `create_broker("live")` raises `LiveTradingUnavailable`.
