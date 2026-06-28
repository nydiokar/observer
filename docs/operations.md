# Operations Runbook

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Fill in API keys in .env
createdb marketintel
python -m src.db.migrations.run
```

## Common commands

| Command | Description |
|---|---|
| `pytest` | Run all tests |
| `python -m src.ingest.run_backfill` | Full backfill |
| `python -m src.ingest.run_refresh` | Refresh latest data |
| `python -m src.ingest.scheduler` | Start scheduler |
| `python -m src.db.migrations.run` | Apply migrations |

## Recovery

If a job fails, check the ingestion run log, fix the source issue, and re-run.
