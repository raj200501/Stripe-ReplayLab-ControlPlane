# Architecture

## Data model
- `Scenario`: deterministic config and target
- `Run`: execution lifecycle and seed snapshot
- `Delivery`: all webhook attempts with timing and status
- `Finding`: diagnosis records by category
- `Artifact`: timeline and diff-friendly summaries

## Event flow
1. Scenario is created via API.
2. Run executes with deterministic seed.
3. Replay engine generates events + chaos profile.
4. Deliveries are sent to merchant sandbox and recorded.
5. Analyzer emits findings + artifact timeline.
6. Dashboard consumes APIs and SSE stream.

## Determinism strategy
- PRNG is always seeded per scenario or explicit run seed.
- Chaos transforms (duplicates/reorder/retries) are deterministic functions of seed.
- Payload IDs and idempotency keys derive from run ID and sequence index.

## Extending event types
- Add template event in `webhooksim/templates.py`.
- Update analyzer invariants in `replaycore/engine.py`.
- Add UI table columns in `apps/dashboard/src/pages.tsx`.
