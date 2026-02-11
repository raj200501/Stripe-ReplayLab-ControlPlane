from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Scenario(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    description: str = ""
    version: int = 1
    config_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    deleted: bool = False
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    scenario_id: str
    status: str = "queued"
    seed: int
    started_at: datetime = Field(default_factory=now_utc)
    finished_at: Optional[datetime] = None
    baseline_run_id: Optional[str] = None
    summary_json: dict = Field(default_factory=dict, sa_column=Column(JSON))


class ApiCall(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    run_id: str
    service: str
    method: str
    path: str
    request_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    response_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status_code: int
    idempotency_key: Optional[str] = None
    correlation_id: str
    started_at: datetime = Field(default_factory=now_utc)
    ended_at: datetime = Field(default_factory=now_utc)
    latency_ms: int = 0


class WebhookDelivery(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    run_id: str
    event_type: str
    event_id: str
    target_url: str
    attempt: int = 1
    delivered_at: datetime = Field(default_factory=now_utc)
    http_status: int = 200
    outcome: str = "delivered"
    ordering_index: int = 0
    payload_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    correlation_id: str


class ObjectState(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    run_id: str
    object_type: str
    object_id: str
    state_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    recorded_at: datetime = Field(default_factory=now_utc)


class DiffReport(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    run_id_a: str
    run_id_b: str
    status: str = "generated"
    diff_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    diagnosis_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)


class PaymentIntent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: f"pi_{uuid4().hex[:14]}", primary_key=True)
    amount: int
    currency: str
    status: str = "requires_payment_method"
    customer_id: Optional[str] = None
