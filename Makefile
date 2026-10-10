DATABASE_URL ?= postgresql://d1:d1@127.0.0.1:5432/d1
export DATABASE_URL

VENV := .venv/bin

.PHONY: setup lint test db-up db-reset generate

setup:
	python3 -m venv .venv
	$(VENV)/pip install -U pip
	$(VENV)/pip install -e contracts -e services/api pytest ruff 'datamodel-code-generator>=0.26'
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
	$(VENV)/ruff check contracts services tests
	$(VENV)/ruff format --check contracts services tests
	npm --prefix contracts/ts run lint
	npm --prefix apps/web run lint

test: db-reset
	npm --prefix contracts/ts run build
	$(VENV)/pytest

# --- services/ingest ----------------------------------------------------------
# Reference loaders and the on-device monthly change list. Archives are local
# files. Nothing in this target sends a variant anywhere.
#   make ingest-replay INGEST_ARCHIVES="a.txt.gz b.txt.gz"
INGEST_OUT ?= services/ingest/change-list-size.tsv

.PHONY: ingest-replay

ingest-replay:
	PYTHONPATH="services/ingest/src:contracts/src" $(VENV)/python -m d1_ingest.replay \
		--out "$(INGEST_OUT)" $(INGEST_ARCHIVES)
