# Threat Model

## Assets

- User exchange API credentials.
- Local strategy configuration.
- Order, fill, and position history.
- Audit logs and exported reports.
- Runtime control over order submission.

## MVP Trust Boundaries

- Desktop UI can start paper sessions and request a kill switch, but it does not call exchange clients directly.
- Strategy templates are declarative and cannot access credentials, files, or network clients.
- Risk evaluation is mandatory before broker submission.
- Paper broker is the default and requires no credentials.
- Sandbox adapters are separated behind connector interfaces and explicit endpoint checks.

## Primary Risks And Controls

| Risk | MVP control |
| --- | --- |
| Live-money trading is accidentally enabled | No live broker implementation; factory raises `LiveTradingUnavailable`. |
| Withdrawal-capable API keys are accepted | Permission validator rejects withdraw or transfer posture. |
| Strategy bypasses risk controls | Order intent must pass `RiskEngine.evaluate` before broker submission. |
| Duplicate orders after timeout | Connector contract records unknown submission state and reconciles by client order id before retry. |
| Secrets leak into logs | Secret-typed values and secret-like keys are redacted before audit persistence. |
| Stale market data authorizes an order | Risk policy blocks data older than the configured freshness window. |
| User needs emergency stop | Kill switch blocks new order intents and appends an audit event. |

## Non-Goals In MVP

- No arbitrary user Python strategy runner.
- No LLM-generated executable strategy path.
- No cloud account, remote control plane, or telemetry.
- No custodial wallet features.
- No live trading release path before explicit CEO review.
