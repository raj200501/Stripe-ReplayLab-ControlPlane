from __future__ import annotations

import asyncio
import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Any, Callable, Iterator

from .models import Artifact, Delivery, Finding, Run, Scenario, new_id, now_iso
from .storage import ReplayStorage


class ReplayEngine:
    def __init__(self, storage: ReplayStorage, emit: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.storage = storage
        self.emit = emit or (lambda _: None)

    async def execute_run(self, scenario: Scenario, seed: int | None = None) -> Run:
        real_seed = seed if seed is not None else scenario.seed
        rng = random.Random(real_seed)
        run = Run(
            id=new_id("run"),
            scenario_id=scenario.id,
            status="running",
            started_at=now_iso(),
            finished_at=None,
            seed=real_seed,
            config_snapshot={"scenario": asdict(scenario)},
        )
        self.storage.create_run(run)
        self.emit({"type": "run.started", "run": asdict(run)})

        for delivery in self._generate_deliveries(run.id, scenario, rng):
            started = time.perf_counter()
            self.emit({"type": "delivery.scheduled", "delivery": asdict(delivery)})
            try:
                req = urllib.request.Request(
                    scenario.target_url,
                    data=json.dumps(delivery.payload_json).encode(),
                    headers={**delivery.headers_json, "Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3) as response:
                    delivery.result_status = response.status
            except urllib.error.HTTPError as exc:
                delivery.result_status = exc.code
            except Exception:
                delivery.result_status = 599
            delivery.sent_at = now_iso()
            delivery.latency_ms = int((time.perf_counter() - started) * 1000)
            self.storage.create_delivery(delivery)
            self.emit({"type": "delivery.sent", "delivery": asdict(delivery)})
            await asyncio.sleep(0)

        findings = self._analyze(run.id)
        for finding in findings:
            self.storage.create_finding(finding)
            self.emit({"type": "finding.created", "finding": asdict(finding)})
        artifact = self._build_artifact(run.id)
        self.storage.create_artifact(artifact)
        self.storage.update_run(run.id, status="completed", finished_at=now_iso())
        final_run = self.storage.get_run(run.id)
        assert final_run is not None
        self.emit({"type": "run.completed", "run": asdict(final_run)})
        return final_run

    def _generate_deliveries(self, run_id: str, scenario: Scenario, rng: random.Random) -> Iterator[Delivery]:
        base_events = [
            "payment_intent.succeeded",
            "charge.refunded",
            "invoice.paid",
            "customer.subscription.updated",
        ]
        chaos = scenario.chaos_profile
        duplicate_rate = float(chaos.get("duplicates", 0.0))
        reorder_window = int(chaos.get("out_of_order_window", 0))
        retry_storm = int(chaos.get("retry_storm", 0))

        events: list[str] = []
        for event in base_events:
            events.append(event)
            if rng.random() < duplicate_rate:
                events.append(event)
        if reorder_window > 0:
            for idx in range(0, len(events), max(1, reorder_window)):
                chunk = events[idx : idx + reorder_window]
                chunk.reverse()
                events[idx : idx + reorder_window] = chunk

        for idx, event in enumerate(events):
            payload = {
                "id": f"evt_{run_id}_{idx}",
                "type": event,
                "data": {"object": {"sequence": idx, "event_type": event}},
            }
            headers = {
                "X-ReplayLab-Run": run_id,
                "X-Idempotency-Key": f"idem-{run_id}-{idx if retry_storm == 0 else idx // (retry_storm + 1)}",
                "X-ReplayLab-Signature": f"sig_{run_id}_{idx}",
            }
            attempts = 1 + retry_storm if idx % 2 == 0 else 1
            for attempt in range(attempts):
                yield Delivery(
                    id=new_id("dlv"),
                    run_id=run_id,
                    event_type=event,
                    payload_json=payload,
                    headers_json=headers,
                    attempt_no=attempt + 1,
                    scheduled_at=now_iso(),
                    sent_at=None,
                    result_status=None,
                    latency_ms=None,
                )

    def _analyze(self, run_id: str) -> list[Finding]:
        deliveries = self.storage.list_deliveries(run_id)
        findings: list[Finding] = []
        by_event: dict[str, int] = {}
        non_2xx = 0
        for item in deliveries:
            by_event[item.event_type] = by_event.get(item.event_type, 0) + 1
            if (item.result_status or 0) >= 400:
                non_2xx += 1

        duplicate_types = [event for event, count in by_event.items() if count > 1]
        if duplicate_types:
            findings.append(
                Finding(
                    id=new_id("finding"),
                    run_id=run_id,
                    severity="high",
                    category="idempotency",
                    summary="Duplicate events observed; verify dedupe table behavior",
                    details_json={"duplicate_types": duplicate_types},
                    suggested_fix="Store processed event ids and short-circuit duplicates before business logic.",
                    evidence_links=[f"delivery-type:{name}" for name in duplicate_types],
                )
            )

        event_order = [delivery.event_type for delivery in deliveries]
        if event_order != sorted(event_order):
            findings.append(
                Finding(
                    id=new_id("finding"),
                    run_id=run_id,
                    severity="medium",
                    category="order",
                    summary="Out-of-order delivery pattern produced",
                    details_json={"first_events": event_order[:8]},
                    suggested_fix="Use monotonic version checks and recompute projection from canonical source.",
                    evidence_links=["artifact:timeline"],
                )
            )

        if non_2xx > 0:
            findings.append(
                Finding(
                    id=new_id("finding"),
                    run_id=run_id,
                    severity="high",
                    category="timeout",
                    summary="Merchant endpoint returned failures/timeouts",
                    details_json={"non_2xx": non_2xx},
                    suggested_fix="Implement retries with bounded backoff and dead-letter processing.",
                    evidence_links=["artifact:trace"],
                )
            )
        return findings

    def _build_artifact(self, run_id: str) -> Artifact:
        deliveries = self.storage.list_deliveries(run_id)
        findings = self.storage.list_findings(run_id)
        timeline = [
            {
                "delivery_id": item.id,
                "event_type": item.event_type,
                "status": item.result_status,
                "latency_ms": item.latency_ms,
            }
            for item in deliveries
        ]
        return Artifact(
            id=new_id("artifact"),
            run_id=run_id,
            kind="timeline",
            content_json={
                "timeline": timeline,
                "diagnosis": [f.summary for f in findings],
                "repro": f"make replay RUN_ID={run_id}",
            },
        )
