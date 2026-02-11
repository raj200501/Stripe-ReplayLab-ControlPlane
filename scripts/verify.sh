#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=apps/api:packages/replaycore/src:packages/webhooksim/src \
python -m pytest apps/api/tests/test_services.py apps/api/tests/unit
python -m ruff check apps/api/app apps/api/tests/test_services.py apps/api/tests/unit packages/replaycore/src

cd apps/dashboard
npm ci
npm run lint
npm run typecheck
npm run test:coverage
npm run build
