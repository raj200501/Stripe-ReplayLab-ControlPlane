# Stripe-ReplayLab-Integration-Chaos-ControlPlane

ReplayLab is a local-first integration reliability lab for Stripe-like flows. It records API calls and webhooks, replays deterministic seeded runs, and generates diff + diagnosis reports.

## Quickstart (verified)
1. `make bootstrap`
2. `make verify`
3. `make demo`
4. Open `http://localhost:5173`

## Architecture
- `apps/api`: FastAPI control plane + gateway simulation endpoints
- `apps/runner`: deterministic demo run generator
- `apps/dashboard`: React control-plane dashboard with 12 pages

## Deterministic replay
Each run uses a seed. Chaos behavior (ordering, duplicates, failures) comes from seeded PRNG for reproducibility.

## Interview talking points
- Deterministic reliability harness
- Webhook ordering + duplicate diagnosis
- Idempotency semantics
- State-machine testing
- CI coverage gates and verified quickstarts
