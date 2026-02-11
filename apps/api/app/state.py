from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

from replaycore import ReplayEngine, ReplayStorage
from replaycore.models import Scenario, new_id


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []

    def emit(self, event: dict[str, Any]) -> None:
        for queue in self._subscribers:
            queue.put_nowait(event)

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)


class AppState:
    def __init__(self, db_path: Path | None = None) -> None:
        self.bus = EventBus()
        self.storage = ReplayStorage(db_path)
        self.engine = ReplayEngine(self.storage, emit=self.bus.emit)

    def ensure_seed_data(self) -> None:
        if self.storage.list_scenarios():
            return
        scenarios = [
            Scenario(
                id=new_id("scn"),
                name="Baseline happy path",
                description="No chaos, validates deterministic baseline behavior",
                seed=7,
                target_url="http://127.0.0.1:9000/webhook",
                chaos_profile={"duplicates": 0.0, "out_of_order_window": 0, "retry_storm": 0},
                expected_invariants={"charges_exactly_once": True},
            ),
            Scenario(
                id=new_id("scn"),
                name="Duplicate pressure",
                description="Inject duplicates and retry storms",
                seed=11,
                target_url="http://127.0.0.1:9000/webhook",
                chaos_profile={"duplicates": 0.6, "out_of_order_window": 0, "retry_storm": 2},
                expected_invariants={"charges_exactly_once": True},
            ),
            Scenario(
                id=new_id("scn"),
                name="Out of order invoices",
                description="Out-of-order windows to surface non-commutative updates",
                seed=14,
                target_url="http://127.0.0.1:9000/webhook",
                chaos_profile={"duplicates": 0.1, "out_of_order_window": 3, "retry_storm": 1},
                expected_invariants={"subscription_latest_version": True},
            ),
        ]
        for scenario in scenarios:
            self.storage.create_scenario(scenario)


def model_to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
