# Operations Runbook

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Fill in API keys in .env
createdb marketintel
make db-setup
```

## Common commands

| Command | Description |
|---|---|
| `make stage2-check` | Validate registry and run tests for the Stage 0-2 foundation |
| `make db` | Apply PostgreSQL migrations |
| `make sync-registry` | Upsert YAML registry, instruments, and baskets into PostgreSQL |
| `make backfill` | Backfill enabled Stage 3 FRED macro backbone series |
| `make refresh` | Refresh enabled Stage 3 FRED macro backbone series |
| `pytest` | Run all tests |
| `python -m src.db.migrations.run` | Apply migrations |

## Not implemented yet

ALFRED vintage ingestion and dashboards are not implemented yet.

## Recovery

If a job fails, check the ingestion run log, fix the source issue, and re-run.
