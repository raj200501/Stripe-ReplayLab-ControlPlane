from __future__ import annotations

import random
from typing import Any


def build_template_events(seed: int, template: str = "default") -> list[dict[str, Any]]:
    rng = random.Random(seed)
    base = [
        "payment_intent.succeeded",
        "charge.refunded",
        "invoice.paid",
        "customer.subscription.updated",
    ]
    if template == "payments_only":
        base = ["payment_intent.succeeded", "charge.refunded"]
    events: list[dict[str, Any]] = []
    for idx, event in enumerate(base):
        events.append(
            {
                "id": f"evt_{seed}_{idx}",
                "type": event,
                "created": 1700000000 + idx,
                "data": {
                    "object": {
                        "id": f"obj_{idx}",
                        "amount": rng.randint(100, 9999),
                        "currency": "usd",
                        "sequence": idx,
                    }
                },
            }
        )
    return events
