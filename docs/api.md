# API

- `GET /healthz`
- `GET/POST /api/scenarios`
- `GET/PUT/DELETE /api/scenarios/{id}`
- `POST /api/scenarios/{id}/run`
- `GET /api/runs?scenario_id=...`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/deliveries`
- `GET /api/runs/{run_id}/findings`
- `GET /api/runs/{run_id}/artifacts`
- `POST /api/runs/{run_id}/cancel`
- `GET /api/stream` (SSE)

Merchant sandbox:
- `POST /webhook`
- `GET /state/orders`
- `GET /state/charges`
- `POST /admin/reset`
- `POST /admin/toggle-bug?name=...`
