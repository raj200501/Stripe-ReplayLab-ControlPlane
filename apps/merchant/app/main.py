from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request

DB_PATH = Path(".replaylab/merchant.sqlite3")
SIGNING_SECRET = "whsec_demo_secret"
BUG_FLAGS = {
    "ignore_idempotency": False,
    "order_bug": False,
    "signature_off": False,
}

app = FastAPI(title="Merchant Sandbox")


def conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_schema() -> None:
    with conn() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed (idempotency_key TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, status TEXT NOT NULL, version INTEGER NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS charges (id TEXT PRIMARY KEY, amount INTEGER NOT NULL, status TEXT NOT NULL, source_event_id TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, email TEXT NOT NULL, version INTEGER NOT NULL);
            """
        )


@app.on_event("startup")
def startup() -> None:
    init_schema()


def verify_signature(raw: bytes, signature: str | None) -> None:
    if BUG_FLAGS["signature_off"]:
        return
    if not signature:
        raise HTTPException(status_code=400, detail="missing_signature")
    digest = hmac.new(SIGNING_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    expected = f"v1={digest}"
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="invalid_signature")


@app.post("/webhook")
async def webhook(request: Request, x_replaylab_signature: str | None = Header(default=None), x_idempotency_key: str | None = Header(default=None)) -> dict[str, str]:
    raw = await request.body()
    verify_signature(raw, x_replaylab_signature)
    event = json.loads(raw.decode() or "{}")
    event_type = event.get("type", "unknown")
    event_id = event.get("id", "evt_unknown")
    sequence = int(event.get("data", {}).get("object", {}).get("sequence", 0))

    with conn() as db:
        if not BUG_FLAGS["ignore_idempotency"] and x_idempotency_key:
            existing = db.execute("SELECT 1 FROM processed WHERE idempotency_key=?", (x_idempotency_key,)).fetchone()
            if existing:
                return {"status": "duplicate_ignored", "event_id": event_id}
            db.execute("INSERT INTO processed(idempotency_key) VALUES (?)", (x_idempotency_key,))

        if event_type == "payment_intent.succeeded":
            charge_id = f"ch_{event_id}"
            db.execute(
                "INSERT OR REPLACE INTO charges(id, amount, status, source_event_id) VALUES (?, ?, ?, ?)",
                (charge_id, 1000, "succeeded", event_id),
            )
            order = db.execute("SELECT id, version FROM orders WHERE id='order_1'").fetchone()
            if order:
                version = order["version"] + 1
                db.execute("UPDATE orders SET status=?, version=?, updated_at=CURRENT_TIMESTAMP WHERE id='order_1'", ("paid", version))
            else:
                db.execute("INSERT INTO orders(id, status, version) VALUES ('order_1', 'paid', 1)")

        if event_type == "customer.subscription.updated":
            current = db.execute("SELECT version FROM customers WHERE id='cus_demo'").fetchone()
            current_version = current["version"] if current else 0
            if BUG_FLAGS["order_bug"]:
                new_version = sequence - 1
            else:
                new_version = max(sequence, current_version)
            db.execute(
                "INSERT OR REPLACE INTO customers(id, email, version) VALUES ('cus_demo', 'customer@example.com', ?)",
                (new_version,),
            )

    return {"status": "accepted", "event_id": event_id}


@app.get("/state/orders")
def state_orders() -> list[dict[str, str | int]]:
    with conn() as db:
        rows = db.execute("SELECT * FROM orders ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]


@app.get("/state/charges")
def state_charges() -> list[dict[str, str | int]]:
    with conn() as db:
        rows = db.execute("SELECT * FROM charges ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.post("/admin/reset")
def admin_reset() -> dict[str, bool]:
    with conn() as db:
        db.execute("DELETE FROM processed")
        db.execute("DELETE FROM orders")
        db.execute("DELETE FROM charges")
        db.execute("DELETE FROM customers")
    return {"reset": True}


@app.post("/admin/toggle-bug")
def toggle_bug(name: str) -> dict[str, bool]:
    if name not in BUG_FLAGS:
        raise HTTPException(404, "bug_not_found")
    BUG_FLAGS[name] = not BUG_FLAGS[name]
    return {"enabled": BUG_FLAGS[name]}
