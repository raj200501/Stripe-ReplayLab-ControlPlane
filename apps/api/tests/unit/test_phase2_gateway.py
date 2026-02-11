from __future__ import annotations

from pathlib import Path

from app.core.gateway import GatewaySimulator
from app.core.repository import ReplayRepository
from app.core.storage import Storage


def build_gateway(tmp_path: Path, seed: int = 77) -> tuple[GatewaySimulator, ReplayRepository]:
    storage = Storage(tmp_path / "phase2.sqlite3")
    storage.init_schema()
    repo = ReplayRepository(storage)
    gateway = GatewaySimulator(repo=repo, seed=seed)
    return gateway, repo


def test_payment_intent_state_machine(tmp_path: Path) -> None:
    gateway, _repo = build_gateway(tmp_path)
    run_id = "run_state"
    corr = "corr_state"

    create = gateway.create_payment_intent(run_id, 1500, "usd", corr, idempotency_key=None)
    intent_id = create.body["id"]
    assert create.body["status"] == "requires_payment_method"

    confirm_1 = gateway.confirm_payment_intent(run_id, intent_id, corr, idempotency_key=None)
    confirm_2 = gateway.confirm_payment_intent(run_id, intent_id, corr, idempotency_key=None)
    confirm_3 = gateway.confirm_payment_intent(run_id, intent_id, corr, idempotency_key=None)

    assert confirm_1.body["status"] == "requires_confirmation"
    assert confirm_2.body["status"] == "processing"
    assert confirm_3.body["status"] == "succeeded"


def test_idempotency_key_caching(tmp_path: Path) -> None:
    gateway, repo = build_gateway(tmp_path)
    run_id = "run_idem"
    corr = "corr_idem"

    first = gateway.create_payment_intent(run_id, 2000, "usd", corr, idempotency_key="idem-abc")
    second = gateway.create_payment_intent(run_id, 2000, "usd", corr, idempotency_key="idem-abc")

    assert first.body["id"] == second.body["id"]
    calls = repo.list_api_calls(run_id)
    assert len(calls) == 2
    assert calls[-1].cache_hit == 1


def test_server_timing_and_correlation_headers(tmp_path: Path) -> None:
    gateway, _repo = build_gateway(tmp_path)
    response = gateway.create_customer("run_headers", "test@example.com", "corr_headers")

    assert "Server-Timing" in response.headers
    assert response.headers["X-Correlation-Id"] == "corr_headers"


def test_deterministic_behavior_under_seed(tmp_path: Path) -> None:
    gateway_a, _repo_a = build_gateway(tmp_path, seed=7)
    gateway_b, _repo_b = build_gateway(tmp_path, seed=7)

    values_a = [gateway_a.deterministic_failure(0.4) for _ in range(5)]
    values_b = [gateway_b.deterministic_failure(0.4) for _ in range(5)]

    assert values_a == values_b
