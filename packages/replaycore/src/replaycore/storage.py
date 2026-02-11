from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import Artifact, Delivery, Finding, Run, Scenario


class ReplayStorage:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(".replaylab/replaylab.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scenarios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                seed INTEGER NOT NULL,
                target_url TEXT NOT NULL,
                chaos_profile TEXT NOT NULL,
                expected_invariants TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                seed INTEGER NOT NULL,
                config_snapshot TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                headers_json TEXT NOT NULL,
                attempt_no INTEGER NOT NULL,
                scheduled_at TEXT NOT NULL,
                sent_at TEXT,
                result_status INTEGER,
                latency_ms INTEGER
            );
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                details_json TEXT NOT NULL,
                suggested_fix TEXT NOT NULL,
                evidence_links TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                content_json TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def _j(self, value: Any) -> str:
        return json.dumps(value, sort_keys=True)

    def create_scenario(self, scenario: Scenario) -> Scenario:
        self.conn.execute(
            "INSERT INTO scenarios VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                scenario.id,
                scenario.name,
                scenario.description,
                scenario.seed,
                scenario.target_url,
                self._j(scenario.chaos_profile),
                self._j(scenario.expected_invariants),
                scenario.created_at,
            ),
        )
        self.conn.commit()
        return scenario

    def update_scenario(self, scenario_id: str, payload: dict[str, Any]) -> Scenario | None:
        current = self.get_scenario(scenario_id)
        if not current:
            return None
        merged = {
            "id": current.id,
            "name": payload.get("name", current.name),
            "description": payload.get("description", current.description),
            "seed": payload.get("seed", current.seed),
            "target_url": payload.get("target_url", current.target_url),
            "chaos_profile": payload.get("chaos_profile", current.chaos_profile),
            "expected_invariants": payload.get("expected_invariants", current.expected_invariants),
            "created_at": current.created_at,
        }
        self.conn.execute(
            "UPDATE scenarios SET name=?, description=?, seed=?, target_url=?, chaos_profile=?, expected_invariants=? WHERE id=?",
            (
                merged["name"],
                merged["description"],
                merged["seed"],
                merged["target_url"],
                self._j(merged["chaos_profile"]),
                self._j(merged["expected_invariants"]),
                scenario_id,
            ),
        )
        self.conn.commit()
        return Scenario(**merged)

    def list_scenarios(self) -> list[Scenario]:
        rows = self.conn.execute("SELECT * FROM scenarios ORDER BY created_at DESC").fetchall()
        return [self._scenario(r) for r in rows]

    def get_scenario(self, scenario_id: str) -> Scenario | None:
        row = self.conn.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,)).fetchone()
        return self._scenario(row) if row else None

    def delete_scenario(self, scenario_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM scenarios WHERE id=?", (scenario_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def create_run(self, run: Run) -> Run:
        self.conn.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run.id, run.scenario_id, run.status, run.started_at, run.finished_at, run.seed, self._j(run.config_snapshot)),
        )
        self.conn.commit()
        return run

    def update_run(self, run_id: str, *, status: str, finished_at: str | None = None) -> None:
        self.conn.execute("UPDATE runs SET status=?, finished_at=? WHERE id=?", (status, finished_at, run_id))
        self.conn.commit()

    def list_runs(self, scenario_id: str | None = None) -> list[Run]:
        if scenario_id:
            rows = self.conn.execute("SELECT * FROM runs WHERE scenario_id=? ORDER BY started_at DESC", (scenario_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM runs ORDER BY started_at DESC").fetchall()
        return [self._run(r) for r in rows]

    def get_run(self, run_id: str) -> Run | None:
        row = self.conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return self._run(row) if row else None

    def create_delivery(self, delivery: Delivery) -> Delivery:
        self.conn.execute(
            "INSERT INTO deliveries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                delivery.id,
                delivery.run_id,
                delivery.event_type,
                self._j(delivery.payload_json),
                self._j(delivery.headers_json),
                delivery.attempt_no,
                delivery.scheduled_at,
                delivery.sent_at,
                delivery.result_status,
                delivery.latency_ms,
            ),
        )
        self.conn.commit()
        return delivery

    def list_deliveries(self, run_id: str) -> list[Delivery]:
        rows = self.conn.execute(
            "SELECT * FROM deliveries WHERE run_id=? ORDER BY scheduled_at, attempt_no", (run_id,)
        ).fetchall()
        return [self._delivery(r) for r in rows]

    def create_finding(self, finding: Finding) -> Finding:
        self.conn.execute(
            "INSERT INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                finding.id,
                finding.run_id,
                finding.severity,
                finding.category,
                finding.summary,
                self._j(finding.details_json),
                finding.suggested_fix,
                self._j(finding.evidence_links),
            ),
        )
        self.conn.commit()
        return finding

    def list_findings(self, run_id: str) -> list[Finding]:
        rows = self.conn.execute("SELECT * FROM findings WHERE run_id=?", (run_id,)).fetchall()
        return [self._finding(r) for r in rows]

    def create_artifact(self, artifact: Artifact) -> Artifact:
        self.conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?)",
            (artifact.id, artifact.run_id, artifact.kind, self._j(artifact.content_json)),
        )
        self.conn.commit()
        return artifact

    def list_artifacts(self, run_id: str) -> list[Artifact]:
        rows = self.conn.execute("SELECT * FROM artifacts WHERE run_id=?", (run_id,)).fetchall()
        return [self._artifact(r) for r in rows]

    def _scenario(self, row: sqlite3.Row) -> Scenario:
        return Scenario(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            seed=row["seed"],
            target_url=row["target_url"],
            chaos_profile=json.loads(row["chaos_profile"]),
            expected_invariants=json.loads(row["expected_invariants"]),
            created_at=row["created_at"],
        )

    def _run(self, row: sqlite3.Row) -> Run:
        return Run(
            id=row["id"],
            scenario_id=row["scenario_id"],
            status=row["status"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            seed=row["seed"],
            config_snapshot=json.loads(row["config_snapshot"]),
        )

    def _delivery(self, row: sqlite3.Row) -> Delivery:
        return Delivery(
            id=row["id"],
            run_id=row["run_id"],
            event_type=row["event_type"],
            payload_json=json.loads(row["payload_json"]),
            headers_json=json.loads(row["headers_json"]),
            attempt_no=row["attempt_no"],
            scheduled_at=row["scheduled_at"],
            sent_at=row["sent_at"],
            result_status=row["result_status"],
            latency_ms=row["latency_ms"],
        )

    def _finding(self, row: sqlite3.Row) -> Finding:
        return Finding(
            id=row["id"],
            run_id=row["run_id"],
            severity=row["severity"],
            category=row["category"],
            summary=row["summary"],
            details_json=json.loads(row["details_json"]),
            suggested_fix=row["suggested_fix"],
            evidence_links=json.loads(row["evidence_links"]),
        )

    def _artifact(self, row: sqlite3.Row) -> Artifact:
        return Artifact(
            id=row["id"],
            run_id=row["run_id"],
            kind=row["kind"],
            content_json=json.loads(row["content_json"]),
        )
