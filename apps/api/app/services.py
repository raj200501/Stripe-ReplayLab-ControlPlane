from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    id: str
    name: str
    config_json: dict[str, Any]


@dataclass
class Run:
    id: str
    scenario_id: str
    seed: int
    webhooks: list[dict[str, Any]] = field(default_factory=list)
    api_calls: list[dict[str, Any]] = field(default_factory=list)


def validate_scenario_config(config: dict[str, float]) -> list[str]:
    errors = []
    for key, value in config.items():
        if key.endswith("_probability") and not 0 <= value <= 1:
            errors.append(f"{key} must be between 0 and 1")
    return errors


def simulate_run(scenario: Scenario, seed: int) -> Run:
    prng = random.Random(seed)
    run = Run(id=f"run_{seed}", scenario_id=scenario.id, seed=seed)
    order = ["payment_intent.processing", "payment_intent.succeeded"]
    if prng.random() < scenario.config_json.get("webhook_out_of_order_probability", 0):
        order.reverse()
    for idx, event_type in enumerate(order):
        run.webhooks.append({"event_type": event_type, "ordering_index": idx})
    if prng.random() < scenario.config_json.get("webhook_duplicate_probability", 0):
        run.webhooks.append(
            {"event_type": "payment_intent.succeeded", "ordering_index": 2, "duplicate": True}
        )
    missing = scenario.config_json.get("force_missing_idempotency", False)
    run.api_calls.append(
        {"path": "/v1/payment_intents/confirm", "idempotency_key": None if missing else "idem"}
    )
    return run


def generate_diff(baseline: Run, candidate: Run) -> dict[str, Any]:
    hints: list[str] = []
    if len(candidate.webhooks) > len(baseline.webhooks):
        hints.append("Your handler is not idempotent: duplicate webhooks observed.")
    if [w["event_type"] for w in baseline.webhooks] != [
        w["event_type"] for w in candidate.webhooks[: len(baseline.webhooks)]
    ]:
        hints.append("You rely on webhook order; make handler ordering-independent.")
    if any(call.get("idempotency_key") is None for call in candidate.api_calls):
        hints.append("Retry without idempotency key detected on confirm call.")
    return {
        "diff_json": {"baseline": baseline.id, "candidate": candidate.id},
        "diagnosis_json": {"hints": hints},
    }
