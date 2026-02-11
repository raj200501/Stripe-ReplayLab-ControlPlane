from __future__ import annotations

from .repository import ReplayRepository


def ensure_seed_scenarios(repo: ReplayRepository) -> int:
    existing = repo.list_scenarios()
    if existing:
        return 0

    presets = [
        (
            "Baseline Happy Path",
            "No chaos; deterministic baseline for diffs.",
            {
                "steps": ["create_customer", "create_payment_intent", "confirm_payment_intent"],
                "webhook_out_of_order_probability": 0.0,
                "webhook_duplicate_probability": 0.0,
                "api_500_probability": 0.0,
            },
        ),
        (
            "Out-of-Order Delivery",
            "Forces webhook sequence inversions.",
            {
                "steps": ["create_customer", "create_payment_intent", "confirm_payment_intent"],
                "webhook_out_of_order_probability": 1.0,
                "webhook_duplicate_probability": 0.0,
                "api_500_probability": 0.0,
            },
        ),
        (
            "Duplicate Storm",
            "Inject duplicate payment_intent.succeeded deliveries.",
            {
                "steps": ["create_customer", "create_payment_intent", "confirm_payment_intent"],
                "webhook_out_of_order_probability": 0.0,
                "webhook_duplicate_probability": 1.0,
                "api_500_probability": 0.0,
            },
        ),
        (
            "Flaky API",
            "Inject intermittent 500s from gateway.",
            {
                "steps": ["create_customer", "create_payment_intent", "confirm_payment_intent"],
                "webhook_out_of_order_probability": 0.3,
                "webhook_duplicate_probability": 0.2,
                "api_500_probability": 0.4,
            },
        ),
    ]

    for name, description, config in presets:
        repo.create_scenario(name=name, description=description, version=1, config_json=config)
    return len(presets)
