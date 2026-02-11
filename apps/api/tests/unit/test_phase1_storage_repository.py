from __future__ import annotations

from pathlib import Path

from app.core.repository import ReplayRepository
from app.core.schema import ApiCallRecord, ObjectStateRecord, WebhookDeliveryRecord, new_id, utc_now
from app.core.seeds import ensure_seed_scenarios
from app.core.storage import Storage


def build_repo(tmp_path: Path) -> ReplayRepository:
    storage = Storage(tmp_path / "phase1.sqlite3")
    storage.init_schema()
    return ReplayRepository(storage)


def test_seed_loader_inserts_default_scenarios(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    count = ensure_seed_scenarios(repo)
    assert count == 4
    scenarios = repo.list_scenarios()
    assert len(scenarios) == 4


def test_scenario_crud_and_soft_delete_pattern(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    created = repo.create_scenario(
        name="Checkout Flow",
        description="Simple PI flow",
        version=3,
        config_json={"webhook_duplicate_probability": 0.0},
    )
    fetched = repo.get_scenario(created.id)
    assert fetched is not None
    assert fetched.name == "Checkout Flow"
    assert fetched.version == 3


def test_run_creation_and_summary_update(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    scenario = repo.create_scenario("Run scenario", "desc", 1, {"api_500_probability": 0.0})
    run = repo.create_run(scenario.id, seed=11)
    assert run.status == "running"
    repo.finish_run(
        run.id, status="succeeded", summary_json={"api_calls": 2, "webhooks": 2, "states": 1}
    )

    finished = repo.get_run(run.id)
    assert finished is not None
    assert finished.status == "succeeded"
    assert finished.summary_json["api_calls"] == 2
    assert finished.finished_at is not None


def test_persistence_roundtrip_for_calls_webhooks_and_states(tmp_path: Path) -> None:
    repo = build_repo(tmp_path)
    scenario = repo.create_scenario("Persist", "desc", 1, {})
    run = repo.create_run(scenario.id, seed=22)

    api_call = ApiCallRecord(
        id=new_id("api"),
        run_id=run.id,
        service="gateway",
        method="POST",
        path="/v1/payment_intents",
        request_json={"amount": 1000, "currency": "usd"},
        response_json={"id": "pi_123", "status": "requires_confirmation"},
        status_code=200,
        idempotency_key="idem_1",
        correlation_id="corr_1",
        started_at=utc_now(),
        ended_at=utc_now(),
        latency_ms=5,
    )
    hook = WebhookDeliveryRecord(
        id=new_id("wh"),
        run_id=run.id,
        event_type="payment_intent.succeeded",
        event_id="evt_1",
        target_url="http://localhost:9000/webhooks",
        attempt=1,
        delivered_at=utc_now(),
        http_status=200,
        outcome="delivered",
        ordering_index=0,
        payload_json={"id": "evt_1"},
        correlation_id="corr_1",
    )
    state = ObjectStateRecord(
        id=new_id("state"),
        run_id=run.id,
        object_type="payment_intent",
        object_id="pi_123",
        state_json={"status": "succeeded"},
        recorded_at=utc_now(),
    )

    repo.save_api_call(api_call)
    repo.save_webhook_delivery(hook)
    repo.save_object_state(state)

    calls = repo.list_api_calls(run.id)
    hooks = repo.list_webhooks(run.id)
    states = repo.list_states(run.id)

    assert len(calls) == 1 and calls[0].path == "/v1/payment_intents"
    assert len(hooks) == 1 and hooks[0].event_type == "payment_intent.succeeded"
    assert len(states) == 1 and states[0].state_json["status"] == "succeeded"
