.PHONY: install test backfill refresh dashboard clean lint

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

lint:
	ruff check src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
