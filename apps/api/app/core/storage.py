from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_FILE = Path(__file__).resolve().parents[3] / "replaylab.sqlite3"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scenarios (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  version INTEGER NOT NULL,
  config_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  status TEXT NOT NULL,
  seed INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  baseline_run_id TEXT,
  summary_json TEXT NOT NULL,
  FOREIGN KEY(scenario_id) REFERENCES scenarios(id)
);

CREATE TABLE IF NOT EXISTS api_calls (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  service TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_json TEXT NOT NULL,
  response_json TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  idempotency_key TEXT,
  correlation_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  latency_ms INTEGER NOT NULL,
  cache_hit INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT NOT NULL,
  target_url TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  delivered_at TEXT NOT NULL,
  http_status INTEGER NOT NULL,
  outcome TEXT NOT NULL,
  ordering_index INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS object_states (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  state_json TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS diff_reports (
  id TEXT PRIMARY KEY,
  run_id_a TEXT NOT NULL,
  run_id_b TEXT NOT NULL,
  status TEXT NOT NULL,
  diff_json TEXT NOT NULL,
  diagnosis_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_cache (
  cache_key TEXT PRIMARY KEY,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_scenario ON runs(scenario_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_run ON webhook_deliveries(run_id);
CREATE INDEX IF NOT EXISTS idx_apicalls_run ON api_calls(run_id);
"""


def to_json(data: object) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def from_json(raw: str) -> object:
    return json.loads(raw)


class Storage:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_FILE

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
