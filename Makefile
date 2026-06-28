.PHONY: install test lint db clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

db:
	python -m src.db.migrations.run

lint:
	ruff check src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
