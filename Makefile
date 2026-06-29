PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: install test lint validate-registry db sync-registry db-setup stage2-check backfill refresh verify-stage3 dashboard clean

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -v

db:
	$(PYTHON) -m src.db.migrations.run

sync-registry:
	$(PYTHON) -m src.db.sync_registry

db-setup: db sync-registry

validate-registry:
	$(PYTHON) -m src.db.validate_registry

stage2-check: validate-registry test

backfill:
	$(PYTHON) -m src.ingest.run_backfill

refresh:
	$(PYTHON) -m src.ingest.run_refresh

verify-stage3:
	$(PYTHON) -m src.ingest.verify_stage3

dashboard:
	@echo "Dashboards are not implemented yet. Build after normalized observations exist."
	@exit 2

lint:
	$(PYTHON) -m ruff check src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
