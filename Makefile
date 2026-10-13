DATABASE_URL ?= postgresql://d1:d1@127.0.0.1:5432/d1
export DATABASE_URL

VENV := .venv/bin

.PHONY: setup lint test db-up db-reset generate safety-scan eval-download eval-store ingest-replay demo e2e openapi

API_PATH := services/api:contracts/src:services/scoring:services/safety:services/ingest/src:services/llm

setup:
	python3 -m venv .venv
	$(VENV)/pip install -U pip
	$(VENV)/pip install -e contracts -e services/api -e services/scoring -e services/safety pytest ruff 'datamodel-code-generator>=0.26'
	npm install --prefix contracts/ts
	npm install --prefix apps/web
	$(MAKE) generate

generate:
	$(VENV)/datamodel-codegen \
		--input contracts/pipeline.schema.json \
		--input-file-type jsonschema \
		--output contracts/src/d1_contracts/generated.py \
		--output-model-type pydantic_v2.BaseModel \
		--target-python-version 3.12 \
		--use-schema-description \
		--enum-field-as-literal all
	sed -i '/^#   timestamp:/d' contracts/src/d1_contracts/generated.py
	$(VENV)/ruff format contracts/src/d1_contracts/generated.py
	$(VENV)/ruff check --fix contracts/src/d1_contracts/generated.py
	npm --prefix contracts/ts exec -- json2ts \
		--input $(CURDIR)/contracts/pipeline.schema.json \
		--output $(CURDIR)/contracts/ts/src/generated.ts \
		--unreachableDefinitions \
		--additionalProperties false
	PYTHONPATH="$(API_PATH)" $(VENV)/python -m app.export_openapi

db-up:
	@if command -v docker >/dev/null 2>&1; then \
		docker compose up -d --wait; \
	else \
		pg_isready -q || sudo pg_ctlcluster 16 main start; \
		sudo -u postgres psql -v ON_ERROR_STOP=1 -f db/local_role.sql; \
	fi

db-reset: db-up
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f db/reset.sql
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f db/001_roles.sql
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f db/002_gate.sql

lint:
	$(VENV)/ruff check contracts services tests eval
	$(VENV)/ruff format --check contracts services tests eval
	npm --prefix contracts/ts run lint
	npm --prefix apps/web run lint

test: db-reset
	npm --prefix contracts/ts run build
	$(VENV)/pytest

safety-scan:
	PYTHONPATH=services/safety $(VENV)/python -m d1_safety

EVAL_PATH := PYTHONPATH="eval:contracts/src:services/scoring:services/ingest/src"

eval-download:
	mkdir -p data/eval
	$(EVAL_PATH) $(VENV)/python -m d1_eval download --dest data/eval

eval-store: eval-download
	$(EVAL_PATH) $(VENV)/python -m d1_eval store --data data/eval --out eval/RESULTS.md

# --- services/ingest ----------------------------------------------------------
# Reference loaders and the on-device monthly change list. Archives are local
# files. Nothing in this target sends a variant anywhere.
#   make ingest-replay INGEST_ARCHIVES="a.txt.gz b.txt.gz"
INGEST_OUT ?= services/ingest/change-list-size.tsv

ingest-replay:
	PYTHONPATH="services/ingest/src:contracts/src" $(VENV)/python -m d1_ingest.replay \
		--out "$(INGEST_OUT)" $(INGEST_ARCHIVES)

openapi:
	PYTHONPATH="$(API_PATH)" $(VENV)/python -m app.export_openapi

demo: db-reset
	PYTHONPATH="$(API_PATH)" $(VENV)/python scripts/demo.py

e2e: db-reset
	cd apps/web && npx playwright test
