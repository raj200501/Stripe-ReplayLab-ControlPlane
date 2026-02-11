# Stripe ReplayLab Control Plane

Webhook Reliability & Idempotency Lab for Stripe-style integrations.

## Why this exists
Teams shipping webhook integrations struggle to prove idempotency under duplicates, retries, and out-of-order delivery. ReplayLab provides deterministic scenario generation, replay execution, and diagnostics with actionable fix patterns.

## Architecture

```
Dashboard (React/Vite) ---> FastAPI Control Plane ---> replaycore engine ---> Merchant Sandbox
       ^                           |                    |                      |
       |                           v                    v                      v
       +------- SSE live stream ---+             SQLite runs/findings      SQLite state
```

## Quickstart

```bash
make bootstrap
make verify
make demo
```

## Notable capabilities
- Deterministic seeds produce reproducible runs.
- Real merchant simulator with bug toggles for idempotency/order/signature failure modes.
- Diagnostics with findings + suggested fixes + replay command.
- 10+ dashboard pages with routing, filtering, validation, and live command palette.

See `docs/architecture.md`, `docs/api.md`, `docs/demo.md`.
