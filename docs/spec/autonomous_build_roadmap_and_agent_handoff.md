# Autonomous Build Roadmap and Agent Handoff — Macro-Financial Market Intelligence Platform

**Date:** 2026-06-28  
**Use with:** `macro_financial_market_intelligence_spec_v2.md`  
**Mission:** scaffold and implement the Macro-Financial Market Intelligence Platform in controlled stages until a working source-backed dashboard exists.

---

## 1. Build objective

Build a reliable market intelligence platform that ingests official and vendor-backed data, stores raw and normalized observations, computes derived indicators, tracks source freshness and data quality, and exposes dashboards for macro, liquidity, valuation, earnings, AI/semi, and balance-sheet monitoring.

The implementation must prioritize:

1. Correct registry and source map.
2. Reliable ingestion.
3. Point-in-time metadata where available.
4. Raw payload preservation.
5. Quality flags.
6. Small fixed universe.
7. Simple dashboards.
8. Minimal scope expansion.

---

## 2. Operating rules for the implementation agent

1. Start from the specification file.
2. Do not expand product scope.
3. Build in stages.
4. Commit after each working stage.
5. Include tests for every connector and transform.
6. Add sample `.env.example`; never commit secrets.
7. Archive raw payloads for every source.
8. Use idempotent upserts.
9. Preserve source metadata.
10. Show missing/stale/vendor-limited data explicitly.
11. Prefer manual controlled ingestion over brittle scraping when a source has no clean API.
12. Stop and document if a required source is unavailable under current access.
13. Do not fabricate estimates, forward metrics, or unavailable values.
14. Maintain a `KNOWN_LIMITATIONS.md` file from the first stage.
15. Maintain a `SOURCE_COVERAGE.md` file from the first stage.

---

## 3. Stage plan

## Stage 0 — Repository audit and project scaffold

### Goal

Detect the current repo structure and create only the missing pieces needed for the platform.

### Tasks

1. Inspect repository.
2. Identify language/runtime conventions.
3. Create or align folders:
   - `config/`
   - `src/connectors/`
   - `src/ingest/`
   - `src/transforms/`
   - `src/db/`
   - `src/tests/`
   - `data/raw/`
   - `data/normalized/`
   - `dashboards/`
   - `docs/`
4. Add `.env.example`.
5. Add `README.md` section for local setup.
6. Add `KNOWN_LIMITATIONS.md`.
7. Add `SOURCE_COVERAGE.md`.

### Acceptance criteria

- Project boots locally.
- No secrets are committed.
- Repo structure is documented.
- First commit contains only scaffold/config/docs.

---

## Stage 1 — Registry and configuration

### Goal

Create a source-backed registry before ingestion code.

### Tasks

1. Create `config/sources.yaml`.
2. Create `config/series_registry.yaml`.
3. Create `config/instruments.yaml`.
4. Create `config/baskets.yaml`.
5. Include all core indicators from the v2 specification.
6. Mark each metric:
   - `engine`
   - `data_class`
   - `source_name`
   - `source_series_code`
   - `frequency`
   - `unit`
   - `access_type`
   - `license_class`
   - `priority`
   - `refresh_policy`
   - `enabled`
7. Add registry validation script.
8. Add tests for:
   - no duplicate `series_id`
   - required fields present
   - enabled metrics have source and refresh policy
   - derived metrics have calculation notes
   - vendor metrics have license class

### Acceptance criteria

- Registry validation passes.
- Every core metric is registered.
- Disabled/deferred metrics are visible but not scheduled.
- No ingestion can run against an unknown metric.

---

## Stage 2 — Database and raw archive

### Goal

Create durable storage before external ingestion.

### Tasks

1. Add PostgreSQL schema/migrations for:
   - `series_registry`
   - `series_observations`
   - `raw_payloads`
   - `instruments`
   - `market_prices`
   - `financial_facts`
   - `derived_metrics`
   - `earnings_events`
   - `ingestion_runs`
2. Add local dev database setup.
3. Add idempotent upsert helpers.
4. Add raw payload archive helper:
   - stores JSON/CSV/XLS responses under `data/raw/{source}/{dataset}/{yyyy}/{mm}/{dd}/`
   - records checksum
   - records sanitized request metadata
5. Add migration test.
6. Add upsert test.

### Acceptance criteria

- Database schema applies cleanly.
- Raw archive writes and records payload metadata.
- Upserts are idempotent.
- Duplicate rows are prevented by constraints.

---

## Stage 3 — Official macro ingestion: FRED and ALFRED

### Goal

Ingest the official macro backbone.

### Tasks

1. Implement FRED connector.
2. Implement ALFRED/vintage support for selected core series where available.
3. Backfill:
   - effective fed funds
   - Fed target range
   - Fed balance sheet
   - CPI
   - Core CPI
   - Core PCE
   - PPI Final Demand
   - unemployment
   - initial claims
   - nonfarm payrolls
   - VIX
   - high-yield spread
   - 10Y yield
   - broad dollar index
   - WTI
   - consumer sentiment
4. Normalize observations.
5. Add quality flags for stale/missing values.
6. Add latest-value query.
7. Add tests using saved fixture payloads.

### Acceptance criteria

- Historical backfill completes.
- Latest rows exist for all enabled FRED core series.
- Raw payloads are archived.
- Observation rows include source, retrieved_at, observation_date, and vintage_date if available.
- Staleness detection works.

---

## Stage 4 — BLS, BEA, EIA direct connectors

### Goal

Add direct official-source connectors where FRED is insufficient or where component mapping matters.

### Tasks

1. Implement BLS connector.
2. Add CPI component mappings:
   - shelter CPI
   - services less energy services CPI
   - transportation services CPI if enabled
   - medical care services CPI if enabled
3. Implement BEA connector for PCE/Core PCE fallback or direct source.
4. Implement EIA connector:
   - crude inventories
   - optional WTI fallback
5. Add raw fixture tests.
6. Compare overlapping FRED/BLS/BEA series for sanity.

### Acceptance criteria

- Component CPI ingestion works.
- EIA crude inventories are stored.
- Overlapping official values are reconciled or documented.
- Source coverage file updated.

---

## Stage 5 — FINRA and ISM report-source ingestion

### Goal

Handle sources that are public but not clean API feeds.

### Tasks

1. Implement FINRA margin debt ingestion from XLS/web publication.
2. Store:
   - debit balances in customers' securities margin accounts
   - MoM absolute change
   - MoM percent change
3. Implement ISM ingestion as controlled manual/semi-automated source:
   - manufacturing PMI
   - services PMI
4. Create `manual_inputs/ism_pmi.csv` if automated parsing is brittle.
5. Add validation around date, value bounds, and duplicate periods.
6. Mark manual/semi-manual values with proper quality flags.

### Acceptance criteria

- FINRA monthly series is available.
- FINRA parser failure does not break the whole refresh.
- ISM values can be loaded reliably.
- Manual values are clearly flagged.
- Source coverage file states the ingestion method.

---

## Stage 6 — Market prices for fixed universe

### Goal

Ingest daily OHLCV for ETFs and fixed tickers.

### Tasks

1. Choose first vendor path:
   - default: FMP
   - fallback: Alpha Vantage
   - alternative: Polygon/Massive
2. Implement price connector behind a vendor interface.
3. Ingest:
   - SPY
   - QQQ
   - SMH or SOXX
   - XLK
   - XLV
   - XLP
   - XLU
   - XLF
   - AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
   - AMD, AVGO, MU, ASML, TSM, LRCX, AMAT, INTC, TXN
4. Use adjusted close for drawdown/return metrics.
5. Compute:
   - daily return
   - 5d/1m/3m/6m/1y return
   - drawdown from 52-week high
   - drawdown from all-time high where history exists
6. Add vendor-limit flags.

### Acceptance criteria

- All enabled instruments have price history.
- Missing symbols are visible in quality dashboard.
- Drawdowns compute correctly.
- Price ingestion is idempotent.
- Vendor errors are isolated by symbol.

---

## Stage 7 — SEC and fundamentals layer

### Goal

Ingest actual company fundamentals for the fixed universe.

### Tasks

1. Build CIK mapping for all fixed companies.
2. Implement SEC submissions connector.
3. Implement SEC company facts connector.
4. Map core facts:
   - revenue
   - operating income
   - depreciation and amortization
   - capex
   - operating cash flow
   - cash and equivalents
   - short-term debt
   - long-term debt
   - total debt where directly available
   - interest expense where available
5. Add FMP fundamentals as a fast normalization source if API key exists.
6. Store both SEC-backed and vendor-backed facts where available.
7. Add mapping confidence:
   - `ok`
   - `concept_mapped`
   - `mapping_uncertain`
8. Compute TTM values.

### Acceptance criteria

- Every fixed company has at least basic SEC filing metadata.
- Core Big Tech facts are available or explicitly flagged.
- SEC raw payloads are archived.
- Fact mappings are documented.
- Vendor facts do not silently overwrite SEC facts.

---

## Stage 8 — Derived valuation and balance-sheet metrics

### Goal

Compute the core ratios.

### Tasks

1. Compute:
   - free cash flow = operating cash flow - capex
   - total debt = short-term debt + long-term debt where needed
   - net debt = total debt - cash
   - EBITDA = operating income + D&A
   - debt / EBITDA
   - EBITDA / interest expense
   - capex / revenue
   - capex / OCF
   - capex / FCF
2. Implement EV and market cap:
   - vendor direct first
   - fallback to price × shares where reliable
3. Compute:
   - EV/EBITDA
   - trailing P/E where possible
4. Compute basket medians for:
   - Big Tech
   - semi basket
5. Guard:
   - negative denominators
   - zero denominators
   - missing inputs
   - stale inputs

### Acceptance criteria

- Derived metrics store input refs.
- Missing inputs generate quality flags.
- Ratio math is tested.
- Basket medians exclude missing values but report coverage count.
- Derived metric versioning exists.

---

## Stage 9 — Earnings and estimates layer

### Goal

Add earnings calendar and surprise metrics for the fixed universe.

### Tasks

1. Implement vendor endpoint for earnings calendar.
2. Implement EPS actual vs estimate.
3. Implement revenue actual vs estimate if available.
4. Store earnings events.
5. Compute:
   - EPS surprise
   - EPS surprise percent
   - revenue surprise
   - revenue surprise percent
   - post-earnings 1d/3d/5d price reaction
6. Add estimate-revision snapshot table only if vendor access allows.
7. Mark all consensus data as `vendor_estimate`.

### Acceptance criteria

- Earnings calendar works for fixed universe.
- Recent and upcoming earnings are visible.
- EPS surprise is available where vendor provides it.
- Revenue surprise missingness is visible.
- Post-earnings returns compute from stored prices.

---

## Stage 10 — Dashboard layer

### Goal

Create usable dashboards from the canonical database.

### Tasks

1. Add Grafana provisioning or SQL dashboard files.
2. Create dashboards:
   - Macro/Fed
   - Liquidity/Fear/Credit
   - Valuation
   - Earnings
   - AI/Semi/Capex
   - Data Quality
3. Each dashboard must include:
   - latest-value table
   - chart panels
   - source field
   - observation date
   - retrieved_at
   - quality flag
4. Add dashboard screenshots or exported JSON if Grafana is used.
5. Store dashboard SQL in version control.

### Acceptance criteria

- Dashboards load locally.
- Every core metric appears somewhere.
- Data-quality dashboard exposes stale/missing/vendor-limited fields.
- No chart hides missing data silently.

---

## Stage 11 — Scheduling and operations

### Goal

Automate refreshes safely.

### Tasks

1. Add scheduled jobs by cadence:
   - daily prices/market data
   - daily macro market series
   - weekly claims/Fed balance sheet/EIA
   - monthly CPI/PPI/labor/PCE/FINRA/ISM
   - quarterly fundamentals
   - earnings calendar refresh
2. Add ingestion run log.
3. Add retry policy.
4. Add source-level timeout policy.
5. Add `make backfill`, `make refresh`, `make test`, `make dashboard` or equivalent scripts.
6. Add operations runbook.

### Acceptance criteria

- Scheduled refresh can run without manual ordering.
- Failed source does not corrupt existing data.
- Ingestion run history is visible.
- Operator can backfill one source or all sources.
- Runbook explains recovery from failed jobs.

---

## Stage 12 — Final hardening

### Goal

Make the platform safe to hand off.

### Tasks

1. Run full backfill.
2. Run all tests.
3. Run refresh twice to verify idempotency.
4. Check latest values.
5. Check stale flags.
6. Check dashboard load.
7. Update:
   - `README.md`
   - `SOURCE_COVERAGE.md`
   - `KNOWN_LIMITATIONS.md`
   - `docs/metric_dictionary.md`
   - `docs/operations.md`
8. Produce final implementation report.

### Acceptance criteria

- Fresh clone setup works.
- All tests pass.
- Full refresh completes.
- Dashboards load.
- Missing data is documented.
- Vendor-dependent metrics are labeled.
- Final report lists completed stages, skipped items, and next recommended work.

---

## 4. Build order summary

Strict order:

1. Scaffold.
2. Registry.
3. Database/raw archive.
4. FRED/ALFRED.
5. BLS/BEA/EIA.
6. FINRA/ISM.
7. Prices.
8. SEC/fundamentals.
9. Derived ratios.
10. Earnings.
11. Dashboards.
12. Scheduling/hardening.

Do not build dashboards before the registry and database are stable.

Do not build earnings/forward metrics before price ingestion and fixed universe are stable.

Do not build transcript/guidance parsing.

---

## 5. Source access checklist

Create `.env.example`:

```bash
FRED_API_KEY=
BEA_API_KEY=
BLS_API_KEY=
EIA_API_KEY=
FMP_API_KEY=
ALPHA_VANTAGE_API_KEY=
POLYGON_API_KEY=
SEC_USER_AGENT="Your Name your.email@example.com"
DATABASE_URL=postgresql://marketintel:marketintel@localhost:5432/marketintel
RAW_DATA_DIR=./data/raw
```

Required for first useful build:

| Key | Required? | Notes |
|---|---:|---|
| `FRED_API_KEY` | Yes | Macro backbone. |
| `SEC_USER_AGENT` | Yes | SEC compliance. |
| `DATABASE_URL` | Yes | Storage. |
| `FMP_API_KEY` | Recommended | Prices, estimates, earnings, key metrics. |
| `BEA_API_KEY` | Useful | PCE/direct BEA. |
| `BLS_API_KEY` | Useful | Higher limits/newer API features. |
| `EIA_API_KEY` | Useful | Energy inventories. |
| `ALPHA_VANTAGE_API_KEY` | Optional | Backup. |
| `POLYGON_API_KEY` | Optional | Alternative price vendor. |

---

## 6. Data contracts

Implement these tests.

### Registry tests

1. `series_id` unique.
2. Required fields present.
3. Enabled metrics have source and refresh policy.
4. Derived metrics have calculation notes.
5. Vendor metrics have license class.
6. No unknown engine names.
7. No unknown priority values.
8. No unknown quality flag values.

### Observation tests

1. No duplicate unique keys.
2. Core series latest value is not stale beyond expected cadence.
3. Numeric values parse.
4. Percent/rate values are within sanity bounds.
5. Observation dates are not in the future except explicitly allowed.
6. Retrieved_at is present.
7. Source name is present.
8. Vintage date is present where available for ALFRED-backed series.

### Price tests

1. OHLC fields are non-negative.
2. High >= low.
3. Adjusted close exists or is flagged.
4. Volume is non-negative or null with flag.
5. Enabled instruments have latest price.

### Fundamentals tests

1. Fiscal periods are valid.
2. SEC-backed facts include CIK/accession where available.
3. Currency units are normalized.
4. TTM calculations have enough periods or are flagged.
5. Derived ratios do not divide by zero silently.

### Dashboard tests

1. Every dashboard query runs.
2. Every core metric appears in at least one dashboard.
3. Data-quality dashboard includes missing/stale/vendor-limited rows.
4. No panel uses hardcoded demo values.

---

## 7. Known hard areas and required handling

| Area | Problem | Required handling |
|---|---|---|
| Forward P/E | Requires estimates. Free official sources do not provide consensus. | Use vendor data; mark `vendor_estimate`; fallback to trailing metrics. |
| Revenue estimates | Often vendor-tier dependent. | Allow missing; show coverage. |
| Guidance | No clean free universal source. | Defer. Use estimate revisions and post-earnings reaction only if available. |
| ISM PMI | Public reports, not clean universal free API. | Manual/semi-automated ingestion acceptable. |
| FINRA margin debt | No clean feed. | Parse public XLS/web; fail gracefully. |
| SEC XBRL facts | Concepts vary by filer and period. | Use mapping confidence and manual review flags. |
| ETF/index valuation | ETF fund pages and vendors may differ. | Prefer company-basket medians for fixed universe; flag source. |
| Licensed vendor data | Display rights can differ from API access. | Track license class per metric/source. |

---

## 8. Autonomous agent prompt

Use this prompt with the two files:

- `macro_financial_market_intelligence_spec_v2.md`
- `autonomous_build_roadmap_and_agent_handoff.md`

```text
You are implementing the Macro-Financial Market Intelligence Platform.

Read `macro_financial_market_intelligence_spec_v2.md` and `autonomous_build_roadmap_and_agent_handoff.md` before making changes.

Your mission is to scaffold and build the platform in staged milestones. Follow the roadmap order exactly unless the existing repository structure requires a small adaptation. Do not expand the product scope.

Build rules:
1. Implement registry/config before ingestion.
2. Implement database/raw archive before external connectors.
3. Preserve raw payloads for every source.
4. Store source metadata, retrieved_at, observation_date, release_date/available_at/vintage_date where available.
5. Use quality flags for missing/stale/vendor-limited/manual/failed data.
6. Use idempotent upserts.
7. Add tests for connectors, transforms, registry validation, and derived metrics.
8. Keep the fixed universe only.
9. Use official/free sources first.
10. Use vendor APIs only where official/free sources cannot provide the required data.
11. Do not implement broad screening, stock picking, trading logic, news classification, geopolitical parsing, transcript parsing, or guidance NLP.
12. Do not fabricate missing values.
13. Commit after each working stage with a concise message.
14. Maintain `SOURCE_COVERAGE.md`, `KNOWN_LIMITATIONS.md`, and `docs/operations.md`.

Start with Stage 0:
- inspect the repo,
- identify current conventions,
- create missing folders,
- create `.env.example`,
- add source coverage and limitations docs,
- then proceed to Stage 1 registry/config.

At the end of every stage, report:
- files changed,
- tests added,
- commands run,
- what passed,
- what failed,
- what is blocked,
- next stage.

The first major milestone is a reliable macro/liquidity dashboard backed by FRED/ALFRED/BLS/BEA/EIA/FINRA/ISM where feasible. The second major milestone is fixed-universe prices, fundamentals, earnings, and derived valuation/capex/balance-sheet ratios.
```

---

## 9. First implementation milestone

The first useful milestone is not the full system. It is:

1. Registry complete.
2. Database initialized.
3. Raw archive working.
4. FRED/ALFRED ingestion working.
5. FINRA and ISM handled.
6. Macro/Fed and Liquidity/Fear dashboards working.
7. Data-quality dashboard working.

Stop there before adding vendor prices and fundamentals.

---

## 10. Final implementation report template

The agent should finish with:

```markdown
# Implementation Report

## Completed stages

## Files changed

## Commands run

## Tests

## Data sources implemented

## Data sources not implemented

## Metrics available

## Metrics missing or vendor-limited

## Dashboard status

## Known limitations

## Required secrets/API keys

## Next recommended stage
```
