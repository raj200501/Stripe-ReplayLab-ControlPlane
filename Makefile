.PHONY: bootstrap verify coverage loc demo

bootstrap:
	python3 -m venv .venv
	cd apps/dashboard && npm ci

verify:
	bash scripts/verify.sh

coverage: verify

demo:
	@echo "Deterministic demo run"
	PYTHONPATH=apps/api python3 -c "from app.services import Scenario, simulate_run; s=Scenario(id='demo', name='demo', config_json={'webhook_duplicate_probability':1.0}); print(simulate_run(s,42))"

loc:
	python3 scripts/loc.py
