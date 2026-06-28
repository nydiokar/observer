.PHONY: install test lint db clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

backfill:
	python -m src.ingest.run_backfill

refresh:
	python -m src.ingest.run_refresh

dashboard:
	@echo "Run: grafana-server or open dashboards/sql/"

db:
	python -m src.db.migrations.run --migration 001_initial_schema.sql

lint:
	ruff check src/

db:
	python -m src.db.migrations.run

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
