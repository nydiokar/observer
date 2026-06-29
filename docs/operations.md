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
| `make verify-stage3` | Verify Stage 3 FRED series have latest rows and report freshness |
| `make bls-backfill` | Backfill enabled Stage 4 BLS CPI component series |
| `pytest` | Run all tests |
| `python -m src.db.migrations.run` | Apply migrations |

## Stage 3 FRED verification

On 2026-06-29, `make backfill` completed against PostgreSQL with `FRED_API_KEY` set. It loaded 18 Stage 3 FRED backbone series, 66,184 `series_observations` rows, and 36 `raw_payloads` metadata rows.

Use `python -m src.ingest.verify_stage3 --strict-freshness` after backfill or refresh to fail on missing or stale latest observations.

## Stage 4 BLS verification

On 2026-06-29, `make bls-backfill` completed against PostgreSQL with `BLS_API_KEY` set. It loaded Shelter CPI and Services Less Energy Services CPI component rows through 2026-05-01.

## Not implemented yet

Dashboards are not implemented yet. ALFRED vintage backfill requires `FRED_API_KEY`; BEA and EIA direct ingestion are not implemented yet.

## Recovery

If a job fails, check the ingestion run log, fix the source issue, and re-run.
