#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=apps/api python3 -m pytest apps/api/tests
ruff check apps/api/app/services.py apps/api/tests/test_services.py
cd apps/dashboard
npm run lint
npm run typecheck
npm run test:coverage
npm run build
