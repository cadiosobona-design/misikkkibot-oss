CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  mode TEXT NOT NULL,
  strategy_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  stopped_at TEXT,
  status TEXT NOT NULL,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_versions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  params_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  ts TEXT NOT NULL,
  payload_json_redacted TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_audit_events_session_ts ON audit_events(session_id, ts);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  client_order_id TEXT NOT NULL UNIQUE,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  type TEXT NOT NULL,
  qty TEXT NOT NULL,
  limit_price TEXT,
  status TEXT NOT NULL,
  exchange_order_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_orders_session_status ON orders(session_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_symbol_created_at ON orders(symbol, created_at);

CREATE TABLE IF NOT EXISTS positions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  qty TEXT NOT NULL,
  avg_price TEXT NOT NULL,
  realized_pnl TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(session_id, symbol),
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS market_bars (
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  ts TEXT NOT NULL,
  open TEXT NOT NULL,
  high TEXT NOT NULL,
  low TEXT NOT NULL,
  close TEXT NOT NULL,
  volume TEXT NOT NULL,
  UNIQUE(symbol, timeframe, ts)
);

CREATE TABLE IF NOT EXISTS risk_decisions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  order_id TEXT,
  allowed INTEGER NOT NULL,
  rule_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  ts TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_risk_decisions_session_ts ON risk_decisions(session_id, ts);
