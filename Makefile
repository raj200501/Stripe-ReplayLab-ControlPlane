.PHONY: bootstrap verify coverage loc demo seed replay reset

bootstrap:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install -e ./packages/replaycore -e ./packages/webhooksim -e ./apps/api[dev]
	cd apps/dashboard && npm ci

verify:
	bash scripts/verify.sh

coverage: verify

seed:
	PYTHONPATH=apps/api:packages/replaycore/src:packages/webhooksim/src python -m apps.runner seed

demo:
	PYTHONPATH=apps/api:packages/replaycore/src:packages/webhooksim/src python -m apps.runner demo

replay:
	PYTHONPATH=apps/api:packages/replaycore/src:packages/webhooksim/src python -m apps.runner replay $(RUN_ID)

reset:
	rm -rf .replaylab/

loc:
	python3 scripts/loc.py
