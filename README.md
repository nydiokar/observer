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
make db-setup
```

### Stage 0-2 verification

```bash
# Validate registry and run the Stage 0-2 test suite
make stage2-check

# Apply schema only
make db

# Sync YAML registry, instruments, and baskets into PostgreSQL
make sync-registry

# Backfill Stage 3 FRED macro backbone series once FRED_API_KEY is configured
make backfill
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

- [Specification](docs/spec/macro_financial_market_intelligence_spec_v2.md)
- [Autonomous Build Roadmap](docs/spec/autonomous_build_roadmap_and_agent_handoff.md)
- [Source Coverage](docs/source_coverage.md)
- [Known Limitations](docs/known_limitations.md)
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
