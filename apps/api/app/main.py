from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from replaycore.models import Scenario, new_id

from .state import AppState


class ScenarioCreate(BaseModel):
    name: str
    description: str = ""
    seed: int = 1
    target_url: str
    chaos_profile: dict[str, Any] = Field(default_factory=dict)
    expected_invariants: dict[str, Any] = Field(default_factory=dict)


class ScenarioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    seed: int | None = None
    target_url: str | None = None
    chaos_profile: dict[str, Any] | None = None
    expected_invariants: dict[str, Any] | None = None


class RunRequest(BaseModel):
    seed: int | None = None


app = FastAPI(title="Webhook Reliability & Idempotency Lab")
state = AppState(Path(".replaylab/replaylab.sqlite3"))


@app.on_event("startup")
def startup() -> None:
    state.ensure_seed_data()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "replaylab-api"}


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    return [asdict(item) for item in state.storage.list_scenarios()]


@app.post("/api/scenarios")
def create_scenario(payload: ScenarioCreate) -> dict[str, Any]:
    scenario = Scenario(id=new_id("scn"), **payload.model_dump())
    state.storage.create_scenario(scenario)
    return asdict(scenario)


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = state.storage.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario_not_found")
    return asdict(scenario)


@app.put("/api/scenarios/{scenario_id}")
def update_scenario(scenario_id: str, payload: ScenarioUpdate) -> dict[str, Any]:
    scenario = state.storage.update_scenario(
        scenario_id,
        {key: value for key, value in payload.model_dump().items() if value is not None},
    )
    if not scenario:
        raise HTTPException(404, "scenario_not_found")
    return asdict(scenario)


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str) -> dict[str, bool]:
    deleted = state.storage.delete_scenario(scenario_id)
    if not deleted:
        raise HTTPException(404, "scenario_not_found")
    return {"deleted": True}


@app.post("/api/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, payload: RunRequest | None = None) -> dict[str, Any]:
    scenario = state.storage.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario_not_found")
    run = await state.engine.execute_run(scenario, seed=payload.seed if payload else None)
    return asdict(run)


@app.get("/api/runs")
def list_runs(scenario_id: str | None = None) -> list[dict[str, Any]]:
    return [asdict(item) for item in state.storage.list_runs(scenario_id)]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    run = state.storage.get_run(run_id)
    if not run:
        raise HTTPException(404, "run_not_found")
    return asdict(run)


@app.get("/api/runs/{run_id}/deliveries")
def list_deliveries(run_id: str) -> list[dict[str, Any]]:
    return [asdict(item) for item in state.storage.list_deliveries(run_id)]


@app.get("/api/runs/{run_id}/findings")
def list_findings(run_id: str) -> list[dict[str, Any]]:
    return [asdict(item) for item in state.storage.list_findings(run_id)]


@app.get("/api/runs/{run_id}/artifacts")
def list_artifacts(run_id: str) -> list[dict[str, Any]]:
    return [asdict(item) for item in state.storage.list_artifacts(run_id)]


@app.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: str) -> dict[str, bool]:
    run = state.storage.get_run(run_id)
    if not run:
        raise HTTPException(404, "run_not_found")
    state.storage.update_run(run_id, status="cancelled")
    return {"cancelled": True}


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    async def event_stream() -> Any:
        async for event in state.bus.stream():
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
