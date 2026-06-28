# Macro-Financial Market Intelligence Platform

A source-backed monitoring system for macro, liquidity, valuation, earnings, AI/semi, and balance-sheet conditions affecting U.S. equities.

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- (Optional) Grafana for dashboards

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd observer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment file and fill in API keys
cp .env.example .env

# Set up database
createdb marketintel
python -m src.db.migrations.run
```

### Quick start

```bash
# Backfill all enabled sources
make backfill

# Refresh latest data
make refresh

# Run tests
make test

# Launch dashboards
make dashboard
```

### Project structure

```
config/              # Source/registry/instrument YAML configs
src/
  connectors/        # Source-specific data connectors
  ingest/            # Ingestion orchestration (backfill, refresh, scheduler)
  transforms/        # Normalization and derived metric computation
  db/                # Database models, migrations, upsert helpers
  tests/             # Data contracts and connector tests
data/
  raw/               # Archived raw payloads (Parquet/JSON/CSV)
  normalized/        # Normalized observation snapshots
  derived/           # Derived metric outputs
dashboards/
  grafana/           # Grafana provisioning JSON
  sql/               # Dashboard SQL queries
docs/                # Source coverage, operations runbook, metric dictionary
```

## Documentation

- [Source Coverage](SOURCE_COVERAGE.md)
- [Known Limitations](KNOWN_LIMITATIONS.md)
- [docs/operations.md](docs/operations.md)
- [docs/metric_dictionary.md](docs/metric_dictionary.md)

## API Keys Required

| Key | Required | Purpose |
|---|---|---|
| `FRED_API_KEY` | Yes | Macro backbone |
| `SEC_USER_AGENT` | Yes | SEC compliance |
| `FMP_API_KEY` | Recommended | Prices, estimates, earnings |
| See `.env.example` for full list |

## License

Proprietary. See license file.
