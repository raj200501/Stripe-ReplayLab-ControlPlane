from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from .schema import (
    ApiCallRecord,
    DiffReportRecord,
    ObjectStateRecord,
    RunRecord,
    ScenarioRecord,
    WebhookDeliveryRecord,
    new_id,
    utc_now,
)
from .storage import Storage, from_json, to_json


class ReplayRepository:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def create_scenario(
        self,
        name: str,
        description: str,
        version: int,
        config_json: dict[str, Any],
    ) -> ScenarioRecord:
        record = ScenarioRecord(
            id=new_id("scn"),
            name=name,
            description=description,
            version=version,
            config_json=config_json,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO scenarios(
                    id,name,description,version,config_json,created_at,updated_at,deleted
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.name,
                    record.description,
                    record.version,
                    to_json(record.config_json),
                    record.created_at,
                    record.updated_at,
                    record.deleted,
                ),
            )
        return record

    def list_scenarios(self) -> list[ScenarioRecord]:
        with self.storage.tx() as conn:
            rows = conn.execute(
                "SELECT * FROM scenarios WHERE deleted = 0 ORDER BY created_at DESC"
            ).fetchall()
        return [
            ScenarioRecord(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                version=row["version"],
                config_json=from_json(row["config_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                deleted=row["deleted"],
            )
            for row in rows
        ]

    def get_scenario(self, scenario_id: str) -> ScenarioRecord | None:
        with self.storage.tx() as conn:
            row = conn.execute(
                "SELECT * FROM scenarios WHERE id = ? AND deleted = 0", (scenario_id,)
            ).fetchone()
        if row is None:
            return None
        return ScenarioRecord(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            version=row["version"],
            config_json=from_json(row["config_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            deleted=row["deleted"],
        )

    def create_run(
        self, scenario_id: str, seed: int, baseline_run_id: str | None = None
    ) -> RunRecord:
        record = RunRecord(
            id=new_id("run"),
            scenario_id=scenario_id,
            status="running",
            seed=seed,
            started_at=utc_now(),
            finished_at=None,
            baseline_run_id=baseline_run_id,
            summary_json={"api_calls": 0, "webhooks": 0, "states": 0},
        )
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO runs(
                    id,scenario_id,status,seed,started_at,finished_at,baseline_run_id,summary_json
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.scenario_id,
                    record.status,
                    record.seed,
                    record.started_at,
                    record.finished_at,
                    record.baseline_run_id,
                    to_json(record.summary_json),
                ),
            )
        return record

    def finish_run(self, run_id: str, status: str, summary_json: dict[str, Any]) -> None:
        with self.storage.tx() as conn:
            conn.execute(
                "UPDATE runs SET status = ?, finished_at = ?, summary_json = ? WHERE id = ?",
                (status, utc_now(), to_json(summary_json), run_id),
            )

    def get_run(self, run_id: str) -> RunRecord | None:
        with self.storage.tx() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return RunRecord(
            id=row["id"],
            scenario_id=row["scenario_id"],
            status=row["status"],
            seed=row["seed"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            baseline_run_id=row["baseline_run_id"],
            summary_json=from_json(row["summary_json"]),
        )

    def save_api_call(self, record: ApiCallRecord) -> None:
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO api_calls(
                    id,run_id,service,method,path,request_json,response_json,status_code,
                idempotency_key,correlation_id,started_at,ended_at,latency_ms,cache_hit)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.run_id,
                    record.service,
                    record.method,
                    record.path,
                    to_json(record.request_json),
                    to_json(record.response_json),
                    record.status_code,
                    record.idempotency_key,
                    record.correlation_id,
                    record.started_at,
                    record.ended_at,
                    record.latency_ms,
                    record.cache_hit,
                ),
            )

    def save_webhook_delivery(self, record: WebhookDeliveryRecord) -> None:
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO webhook_deliveries(
                    id,run_id,event_type,event_id,target_url,attempt,delivered_at,
                http_status,outcome,ordering_index,payload_json,correlation_id)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.run_id,
                    record.event_type,
                    record.event_id,
                    record.target_url,
                    record.attempt,
                    record.delivered_at,
                    record.http_status,
                    record.outcome,
                    record.ordering_index,
                    to_json(record.payload_json),
                    record.correlation_id,
                ),
            )

    def save_object_state(self, record: ObjectStateRecord) -> None:
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO object_states(id,run_id,object_type,object_id,state_json,recorded_at)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.run_id,
                    record.object_type,
                    record.object_id,
                    to_json(record.state_json),
                    record.recorded_at,
                ),
            )

    def list_api_calls(self, run_id: str) -> list[ApiCallRecord]:
        with self.storage.tx() as conn:
            rows = conn.execute("SELECT * FROM api_calls WHERE run_id = ?", (run_id,)).fetchall()
        out: list[ApiCallRecord] = []
        for row in rows:
            out.append(
                ApiCallRecord(
                    id=row["id"],
                    run_id=row["run_id"],
                    service=row["service"],
                    method=row["method"],
                    path=row["path"],
                    request_json=from_json(row["request_json"]),
                    response_json=from_json(row["response_json"]),
                    status_code=row["status_code"],
                    idempotency_key=row["idempotency_key"],
                    correlation_id=row["correlation_id"],
                    started_at=row["started_at"],
                    ended_at=row["ended_at"],
                    latency_ms=row["latency_ms"],
                    cache_hit=row["cache_hit"],
                )
            )
        return out

    def list_webhooks(self, run_id: str) -> list[WebhookDeliveryRecord]:
        with self.storage.tx() as conn:
            rows = conn.execute(
                "SELECT * FROM webhook_deliveries WHERE run_id = ? ORDER BY ordering_index",
                (run_id,),
            ).fetchall()
        return [
            WebhookDeliveryRecord(
                id=row["id"],
                run_id=row["run_id"],
                event_type=row["event_type"],
                event_id=row["event_id"],
                target_url=row["target_url"],
                attempt=row["attempt"],
                delivered_at=row["delivered_at"],
                http_status=row["http_status"],
                outcome=row["outcome"],
                ordering_index=row["ordering_index"],
                payload_json=from_json(row["payload_json"]),
                correlation_id=row["correlation_id"],
            )
            for row in rows
        ]

    def list_states(self, run_id: str) -> list[ObjectStateRecord]:
        with self.storage.tx() as conn:
            rows = conn.execute(
                "SELECT * FROM object_states WHERE run_id = ? ORDER BY recorded_at", (run_id,)
            ).fetchall()
        return [
            ObjectStateRecord(
                id=row["id"],
                run_id=row["run_id"],
                object_type=row["object_type"],
                object_id=row["object_id"],
                state_json=from_json(row["state_json"]),
                recorded_at=row["recorded_at"],
            )
            for row in rows
        ]

    def save_diff_report(self, report: DiffReportRecord) -> None:
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT INTO diff_reports(
                    id,run_id_a,run_id_b,status,diff_json,diagnosis_json,created_at
                )
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    report.id,
                    report.run_id_a,
                    report.run_id_b,
                    report.status,
                    to_json(report.diff_json),
                    to_json(report.diagnosis_json),
                    report.created_at,
                ),
            )

    def list_diff_reports(self) -> list[DiffReportRecord]:
        with self.storage.tx() as conn:
            rows = conn.execute("SELECT * FROM diff_reports ORDER BY created_at DESC").fetchall()
        return [
            DiffReportRecord(
                id=row["id"],
                run_id_a=row["run_id_a"],
                run_id_b=row["run_id_b"],
                status=row["status"],
                diff_json=from_json(row["diff_json"]),
                diagnosis_json=from_json(row["diagnosis_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def idempotency_lookup(
        self, method: str, path: str, idempotency_key: str, request_payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        cache_key = f"{method}:{path}:{idempotency_key}"
        request_hash = hashlib.sha256(to_json(request_payload).encode()).hexdigest()
        with self.storage.tx() as conn:
            row = conn.execute(
                "SELECT request_hash,response_json FROM idempotency_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None or row["request_hash"] != request_hash:
            return None
        return from_json(row["response_json"])

    def idempotency_store(
        self,
        method: str,
        path: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> None:
        cache_key = f"{method}:{path}:{idempotency_key}"
        request_hash = hashlib.sha256(to_json(request_payload).encode()).hexdigest()
        with self.storage.tx() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency_cache(
                    cache_key,method,path,request_hash,response_json,created_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (cache_key, method, path, request_hash, to_json(response_payload), utc_now()),
            )

    def as_dict(self, record: Any) -> dict[str, Any]:
        return asdict(record)
