from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


@dataclass(slots=True)
class ScenarioRecord:
    id: str
    name: str
    description: str
    version: int
    config_json: dict[str, Any]
    created_at: str
    updated_at: str
    deleted: int = 0


@dataclass(slots=True)
class RunRecord:
    id: str
    scenario_id: str
    status: str
    seed: int
    started_at: str
    finished_at: str | None
    baseline_run_id: str | None
    summary_json: dict[str, Any]


@dataclass(slots=True)
class ApiCallRecord:
    id: str
    run_id: str
    service: str
    method: str
    path: str
    request_json: dict[str, Any]
    response_json: dict[str, Any]
    status_code: int
    idempotency_key: str | None
    correlation_id: str
    started_at: str
    ended_at: str
    latency_ms: int
    cache_hit: int = 0


@dataclass(slots=True)
class WebhookDeliveryRecord:
    id: str
    run_id: str
    event_type: str
    event_id: str
    target_url: str
    attempt: int
    delivered_at: str
    http_status: int
    outcome: str
    ordering_index: int
    payload_json: dict[str, Any]
    correlation_id: str


@dataclass(slots=True)
class ObjectStateRecord:
    id: str
    run_id: str
    object_type: str
    object_id: str
    state_json: dict[str, Any]
    recorded_at: str


@dataclass(slots=True)
class DiffReportRecord:
    id: str
    run_id_a: str
    run_id_b: str
    status: str
    diff_json: dict[str, Any]
    diagnosis_json: dict[str, Any]
    created_at: str
