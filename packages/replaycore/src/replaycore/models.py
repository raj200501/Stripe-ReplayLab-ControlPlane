from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass(slots=True)
class Scenario:
    id: str
    name: str
    description: str
    seed: int
    target_url: str
    chaos_profile: dict[str, Any]
    expected_invariants: dict[str, Any]
    created_at: str = field(default_factory=now_iso)


@dataclass(slots=True)
class Run:
    id: str
    scenario_id: str
    status: str
    started_at: str
    finished_at: str | None
    seed: int
    config_snapshot: dict[str, Any]


@dataclass(slots=True)
class Delivery:
    id: str
    run_id: str
    event_type: str
    payload_json: dict[str, Any]
    headers_json: dict[str, str]
    attempt_no: int
    scheduled_at: str
    sent_at: str | None
    result_status: int | None
    latency_ms: int | None


@dataclass(slots=True)
class Finding:
    id: str
    run_id: str
    severity: str
    category: str
    summary: str
    details_json: dict[str, Any]
    suggested_fix: str
    evidence_links: list[str]


@dataclass(slots=True)
class Artifact:
    id: str
    run_id: str
    kind: str
    content_json: dict[str, Any]
