from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from .db import get_session, init_db
from .models import ApiCall, DiffReport, ObjectState, PaymentIntent, Run, Scenario, WebhookDelivery
from .services import create_run, generate_diff, upsert_intent, validate_scenario_config

app = FastAPI(title="ReplayLab Control Plane")
subscribers: list[asyncio.Queue] = []


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "replaylab-api"}


@app.get("/api/scenarios")
def list_scenarios(session: Session = Depends(get_session)) -> list[Scenario]:
    return session.exec(select(Scenario).where(Scenario.deleted == False)).all()


@app.post("/api/scenarios")
def create_scenario(payload: dict, session: Session = Depends(get_session)) -> Scenario:
    errors = validate_scenario_config(payload.get("config_json", {}))
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    scenario = Scenario(**payload)
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str, session: Session = Depends(get_session)) -> Scenario:
    scenario = session.get(Scenario, scenario_id)
    if not scenario or scenario.deleted:
        raise HTTPException(404, detail={"error": "scenario_not_found"})
    return scenario


@app.put("/api/scenarios/{scenario_id}")
def update_scenario(scenario_id: str, payload: dict, session: Session = Depends(get_session)) -> Scenario:
    scenario = get_scenario(scenario_id, session)
    for k, v in payload.items():
        setattr(scenario, k, v)
    scenario.updated_at = datetime.utcnow()
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str, session: Session = Depends(get_session)) -> dict:
    scenario = get_scenario(scenario_id, session)
    scenario.deleted = True
    session.add(scenario)
    session.commit()
    return {"deleted": True}


@app.post("/api/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, payload: dict | None = None, session: Session = Depends(get_session)) -> Run:
    scenario = get_scenario(scenario_id, session)
    run = create_run(session, scenario, seed=(payload or {}).get("seed"))
    event = {"type": "run.completed", "run_id": run.id, "status": run.status}
    for q in subscribers:
        await q.put(event)
    return run


@app.get("/api/runs")
def list_runs(session: Session = Depends(get_session)) -> list[Run]:
    return session.exec(select(Run)).all()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)) -> Run:
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(404, detail={"error": "run_not_found"})
    return run


@app.get("/api/runs/{run_id}/events")
def run_events(run_id: str, limit: int = 100, session: Session = Depends(get_session)) -> list[dict]:
    hooks = session.exec(select(WebhookDelivery).where(WebhookDelivery.run_id == run_id)).all()[:limit]
    return [{"kind": "webhook", "event_type": h.event_type, "correlation_id": h.correlation_id} for h in hooks]


@app.get("/api/runs/{run_id}/api-calls")
def api_calls(run_id: str, session: Session = Depends(get_session)) -> list[ApiCall]:
    return session.exec(select(ApiCall).where(ApiCall.run_id == run_id)).all()


@app.get("/api/runs/{run_id}/webhooks")
def webhooks(run_id: str, session: Session = Depends(get_session)) -> list[WebhookDelivery]:
    return session.exec(select(WebhookDelivery).where(WebhookDelivery.run_id == run_id)).all()


@app.get("/api/runs/{run_id}/states")
def states(run_id: str, session: Session = Depends(get_session)) -> list[ObjectState]:
    return session.exec(select(ObjectState).where(ObjectState.run_id == run_id)).all()


@app.post("/api/diffs")
def create_diff(payload: dict, session: Session = Depends(get_session)) -> DiffReport:
    return generate_diff(session, payload["run_id_a"], payload["run_id_b"])


@app.get("/api/diffs/{diff_id}")
def get_diff(diff_id: str, session: Session = Depends(get_session)) -> DiffReport:
    diff = session.get(DiffReport, diff_id)
    if not diff:
        raise HTTPException(404, detail={"error": "diff_not_found"})
    return diff


@app.get("/api/metrics/overview")
def metrics(session: Session = Depends(get_session)) -> dict:
    runs = session.exec(select(Run)).all()
    failed = len([r for r in runs if r.status == "failed"])
    return {"runs": len(runs), "failures": failed, "p95_api_latency": 40, "webhook_retries": 0}


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    await ws.accept()
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.append(queue)
    try:
        while True:
            event = await queue.get()
            await ws.send_json(event)
    finally:
        subscribers.remove(queue)


@app.get("/sse/live")
async def sse_live() -> StreamingResponse:
    async def event_stream():
        q: asyncio.Queue = asyncio.Queue()
        subscribers.append(q)
        try:
            while True:
                item = await q.get()
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            subscribers.remove(q)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/v1/payment_intents")
def create_payment_intent(
    payload: dict,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_session),
) -> dict:
    intent = upsert_intent(session, idempotency_key, payload["amount"], payload.get("currency", "usd"))
    session.add(
        ApiCall(
            run_id="gateway",
            service="gateway",
            method="POST",
            path="/v1/payment_intents",
            request_json=payload,
            response_json={"id": intent.id, "status": intent.status},
            status_code=200,
            idempotency_key=idempotency_key,
            correlation_id=f"corr_{intent.id}",
        )
    )
    session.commit()
    return {"id": intent.id, "status": intent.status}


@app.post("/v1/payment_intents/{intent_id}/confirm")
def confirm_intent(intent_id: str, session: Session = Depends(get_session)) -> dict:
    intent = session.get(PaymentIntent, intent_id)
    if not intent:
        raise HTTPException(404, detail={"error": "intent_not_found"})
    intent.status = "processing" if intent.status == "requires_confirmation" else "succeeded"
    session.add(intent)
    session.commit()
    return {"id": intent.id, "status": intent.status}


@app.post("/v1/customers")
def customers() -> dict:
    return {"id": "cus_demo"}


@app.post("/v1/refunds")
def refunds() -> dict:
    return {"id": "re_demo", "status": "succeeded"}


@app.post("/v1/events")
def events() -> dict:
    return {"ok": True}


@app.get("/internal/state")
def internal_state(debug: bool = True) -> dict:
    if not debug:
        raise HTTPException(403, detail={"error": "disabled"})
    return {"state": "available"}
