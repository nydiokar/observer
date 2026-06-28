# Macro-Financial Market Intelligence Platform — v2 Specification

**Status:** implementation specification  
**Date:** 2026-06-28  
**Primary system name:** Macro-Financial Market Intelligence Platform  
**Internal short name:** Market Intelligence Engine  
**Previous working name:** Market Observability Engine  
**Primary purpose:** build a source-backed monitoring system for macro, liquidity, valuation, earnings, AI/semi, and balance-sheet conditions affecting U.S. equities.

---

## 1. Product definition

The platform is a structured market intelligence system.

It ingests official and vendor-backed datasets, normalizes them into a consistent time-series and fundamentals model, computes derived indicators, tracks data quality and freshness, and exposes dashboards that show current conditions, historical context, deltas, and source provenance.

The system should answer:

1. What changed in the macro environment?
2. What changed in liquidity, credit, leverage, rates, and market stress?
3. What changed in broad equity valuation and drawdown context?
4. What changed in AI/semi cycle strength?
5. What changed in Big Tech capex, cash generation, and balance-sheet pressure?
6. Which indicators are stale, missing, revised, delayed, or vendor-dependent?
7. Which observations are official actuals versus vendor estimates or derived metrics?

The v2 specification replaces commentary language with implementation boundaries, data contracts, ingestion stages, and acceptance criteria.

---

## 2. Professional terminology

Use the following terms in code, documentation, dashboard labels, and agent handoffs.

| Term | Use |
|---|---|
| **Macro-Financial Market Intelligence Platform** | External/project-level name. |
| **Market Intelligence Engine** | Internal short name. |
| **Macro-financial monitoring** | Description of the macro/liquidity function. |
| **Investment research monitoring system** | Broader workflow description. |
| **Economic and market data platform** | Data-layer description. |
| **Source-backed indicator registry** | Registry concept for all metrics. |

Avoid using **observability** as the primary product term. It is acceptable only as an internal analogy for telemetry, source freshness, pipeline health, and data quality.

---

## 3. Scope

### 3.1 Core scope

Build a compact intelligence platform covering:

1. Macro and Federal Reserve conditions.
2. Inflation and labor-market conditions.
3. Liquidity, leverage, volatility, rates, dollar, commodity, and credit stress.
4. Equity index, ETF, sector, and fixed-basket valuation context.
5. Earnings calendar, EPS/revenue surprise, and post-earnings reaction for a fixed universe.
6. AI/semi cycle indicators.
7. Big Tech capex, cash-flow, debt, and balance-sheet pressure.
8. Data freshness, data provenance, revision handling, and quality flags.

### 3.2 Fixed v1/v2 universe

#### Index / ETF proxies

| Area | Primary instruments | Purpose |
|---|---|---|
| Broad U.S. market | SPY, optional S&P 500 index | Broad market level, return, drawdown. |
| Growth / Nasdaq | QQQ, optional Nasdaq 100 / Nasdaq Composite | Growth/tech sensitivity. |
| Semiconductors | SMH or SOXX | Semiconductor basket proxy. |
| Technology | XLK | Broad tech proxy. |
| Defensives | XLV, XLP, XLU | Rotation comparison. |
| Financials | XLF | Financial-sector proxy. |

#### Company universe

**Big Tech / Magnificent 7**

- AAPL
- MSFT
- GOOGL
- AMZN
- META
- NVDA
- TSLA

**Semiconductor / AI infrastructure basket**

- NVDA
- AMD
- AVGO
- MU
- ASML
- TSM
- LRCX
- AMAT
- INTC
- TXN

Optional later additions:

- QCOM
- ARM
- ORCL
- SMCI

Additions require an explicit registry change, source coverage check, and dashboard impact review.

---

## 4. Explicit exclusions

Do not implement these in the initial build:

1. Automated buy/sell decisions.
2. Broad all-stock screening.
3. Stock-type taxonomy or classification rules.
4. News classification.
5. Geopolitical event parser.
6. Tariff parser.
7. Transcript/guidance NLP.
8. Broad sector valuation atlas.
9. Full institutional estimates database.
10. Portfolio execution logic.
11. Backtesting or signal optimization.

Allowed later only after the data platform is stable:

1. Manual notes layer.
2. Watchlist-specific annotations.
3. Estimate-revision tracking.
4. Transcript/guidance integration from a licensed provider.
5. Alerting on data-quality issues and threshold crossings.

---

## 5. Architecture

### 5.1 Recommended stack

| Layer | Recommended tool | Reason |
|---|---|---|
| Language | Python | Best ecosystem for economic data, APIs, ETL, pandas, DuckDB, validation. |
| Canonical DB | PostgreSQL | Durable relational store, good dashboard compatibility. |
| Raw archive | Parquet files partitioned by source/dataset/date | Cheap replay, auditability, backfills, raw preservation. |
| Analytical replay | DuckDB | Fast local queries over Parquet without heavy infrastructure. |
| Orchestration | Dagster or a simple scheduled job runner first | Asset scheduling, cadence-aware ingestion, retry logic. |
| Data contracts | Great Expectations, dbt tests, or custom pytest contracts | Non-null, uniqueness, freshness, bounds, relationship checks. |
| Dashboard | Grafana first; Metabase optional | Grafana fits time series and Postgres; Metabase fits exploratory BI. |
| API | FastAPI optional | Only needed if dashboard/frontend requires custom endpoints. |
| Config | YAML registry files | Human-readable source map, metric definitions, enable/disable flags. |

### 5.2 Minimum viable architecture

For the fastest credible build:

```text
/config
  sources.yaml
  series_registry.yaml
  instruments.yaml
  baskets.yaml

/src
  connectors/
    fred.py
    alfred.py
    bls.py
    bea.py
    eia.py
    finra.py
    sec_edgar.py
    fmp.py
    alpha_vantage.py
    prices.py
  ingest/
    run_backfill.py
    run_refresh.py
    scheduler.py
  transforms/
    macro_transforms.py
    price_transforms.py
    fundamentals_transforms.py
    valuation_transforms.py
    quality_flags.py
  db/
    migrations/
    models.py
    upsert.py
  tests/
    test_contracts.py
    test_registry.py
    test_connectors.py

/data
  raw/
  normalized/
  derived/

/dashboards
  grafana/
  sql/

/docs
  source_coverage.md
  operations.md
  metric_dictionary.md
```

Use this structure unless the existing repository already has a stronger convention.

---

## 6. Data model

### 6.1 Core principles

1. Store raw responses before normalization.
2. Store normalized observations separately from derived metrics.
3. Preserve source, retrieval time, release time, and vintage where available.
4. Never overwrite history without preserving revision context.
5. Treat estimates, official actuals, vendor metrics, and derived metrics as different data classes.
6. Use visible quality flags instead of silent imputation.
7. Every metric must be registered before ingestion.

### 6.2 Tables

#### `series_registry`

Defines all non-instrument time series and derived macro/liquidity indicators.

Required fields:

| Column | Meaning |
|---|---|
| `series_id` | Stable internal ID. |
| `display_name` | Human-readable label. |
| `engine` | Macro, liquidity, credit, valuation, AI/semi, balance sheet, earnings. |
| `data_class` | official_actual, vendor_actual, vendor_estimate, derived, manual. |
| `source_name` | FRED, ALFRED, BLS, BEA, EIA, FINRA, SEC, FMP, Alpha Vantage, etc. |
| `source_series_code` | Native source code where available. |
| `frequency` | daily, weekly, monthly, quarterly, annual, irregular. |
| `unit` | percent, index, USD, ratio, count, bps, etc. |
| `access_type` | free_official, free_vendor, freemium, paid, manual. |
| `license_class` | public, internal_only, display_restricted, unknown. |
| `priority` | core, useful, optional, defer. |
| `is_direct` | true if directly retrieved. |
| `calculation_notes` | Required for derived metrics. |
| `fallback_source` | Fallback path. |
| `refresh_policy` | daily, weekly, monthly, quarterly, release_calendar, manual. |
| `enabled` | boolean. |

#### `series_observations`

Stores normalized observations.

Required fields:

| Column | Meaning |
|---|---|
| `series_id` | FK to registry. |
| `observation_date` | Economic/market date represented by the value. |
| `value` | Numeric value. |
| `unit` | Unit at observation time. |
| `source_name` | Source used. |
| `source_series_code` | Native source code. |
| `release_date` | Official release date if available. |
| `available_at` | Timestamp when value became knowable, if available. |
| `vintage_date` | Vintage date for revisable macro series. |
| `retrieved_at` | Timestamp of retrieval. |
| `revision_no` | Optional integer revision counter. |
| `quality_flag` | ok, stale, missing, partial, revised, estimated, vendor_limited, manual, failed. |
| `raw_payload_id` | Pointer to archived raw response. |

Uniqueness:

```text
(series_id, observation_date, vintage_date, source_name)
```

If vintage is unavailable:

```text
(series_id, observation_date, source_name, retrieved_at::date)
```

#### `raw_payloads`

Stores source responses and files.

Required fields:

| Column | Meaning |
|---|---|
| `raw_payload_id` | Stable ID. |
| `source_name` | Source. |
| `dataset_name` | Dataset or endpoint. |
| `retrieved_at` | Retrieval timestamp. |
| `request_url_hash` | Hash, not necessarily full URL if API key present. |
| `request_params_json` | Sanitized params. |
| `response_format` | json, csv, xls, html, pdf, parquet. |
| `storage_path` | Path in raw archive. |
| `checksum` | Payload checksum. |
| `status` | success, partial, failed. |

#### `instruments`

Required fields:

| Column | Meaning |
|---|---|
| `instrument_id` | Stable internal ID. |
| `ticker` | Symbol. |
| `name` | Full name. |
| `instrument_type` | equity, ETF, index, basket. |
| `primary_exchange` | Exchange if relevant. |
| `currency` | USD etc. |
| `engine` | valuation, AI/semi, balance sheet, earnings. |
| `basket_name` | If member of a fixed basket. |
| `enabled` | boolean. |

#### `market_prices`

Required fields:

| Column | Meaning |
|---|---|
| `instrument_id` | FK. |
| `date` | Market date. |
| `open` | OHLC. |
| `high` | OHLC. |
| `low` | OHLC. |
| `close` | OHLC. |
| `adjusted_close` | Adjusted close if available. |
| `volume` | Volume if available. |
| `source_name` | Source. |
| `retrieved_at` | Retrieval timestamp. |
| `quality_flag` | ok, stale, missing, split_adjustment_unknown, vendor_limited. |

Uniqueness:

```text
(instrument_id, date, source_name)
```

#### `financial_facts`

Company reported fundamentals.

Required fields:

| Column | Meaning |
|---|---|
| `ticker` | Company ticker. |
| `cik` | SEC CIK where applicable. |
| `period_end` | Fiscal period end. |
| `fiscal_year` | Fiscal year. |
| `fiscal_period` | Q1, Q2, Q3, Q4, FY. |
| `fact_name` | Normalized fact. |
| `value` | Numeric value. |
| `unit` | USD, shares, etc. |
| `source_name` | SEC, FMP, Alpha Vantage, etc. |
| `filing_accession` | SEC accession if SEC-backed. |
| `form_type` | 10-Q, 10-K, 8-K, etc. |
| `filed_at` | Filing date/time if available. |
| `accepted_at` | SEC acceptance timestamp if available. |
| `retrieved_at` | Retrieval timestamp. |
| `quality_flag` | ok, missing, restated, vendor_limited, concept_mapped, manual_review. |

#### `derived_metrics`

Required fields:

| Column | Meaning |
|---|---|
| `metric_id` | Stable derived metric ID. |
| `instrument_id` | Optional instrument FK. |
| `series_id` | Optional series FK. |
| `basket_id` | Optional basket FK. |
| `date` | Metric date. |
| `value` | Numeric value. |
| `calculation_version` | Version string. |
| `input_refs_json` | Inputs used. |
| `quality_flag` | ok, partial, missing_inputs, stale_inputs, estimated_inputs. |

#### `earnings_events`

Required fields:

| Column | Meaning |
|---|---|
| `ticker` | Ticker. |
| `fiscal_period` | Quarter/year. |
| `earnings_date` | Event date. |
| `reported_eps` | Actual EPS. |
| `estimated_eps` | Consensus EPS estimate if available. |
| `eps_surprise` | Actual minus estimate. |
| `eps_surprise_pct` | Surprise percent. |
| `reported_revenue` | Actual revenue. |
| `estimated_revenue` | Consensus revenue estimate if available. |
| `revenue_surprise` | Actual minus estimate. |
| `revenue_surprise_pct` | Surprise percent. |
| `source_name` | Vendor/source. |
| `retrieved_at` | Retrieval timestamp. |
| `quality_flag` | ok, estimate_missing, revenue_missing, vendor_limited. |

---

## 7. Source strategy

### 7.1 Source hierarchy

#### Tier 1 — official/free/defensible

Use first when coverage is sufficient.

| Source | Use | Access |
|---|---|---|
| FRED | Macro, rates, spreads, VIX, Fed balance sheet, broad public time series | Free API/CSV |
| ALFRED | Vintage macro data and point-in-time macro history | Free API/CSV |
| BLS | CPI, PPI, labor data, CPI components | Free API |
| BEA | PCE, Core PCE, NIPA data | Free API key |
| EIA | Crude oil, inventories, energy data | Free API |
| SEC EDGAR | Filings, submissions, company facts, XBRL | Free JSON APIs; compliant User-Agent required |
| FINRA | Margin debt statistics | Free XLS/web publication |
| Federal Reserve | FOMC target range, SEP/dot plot, balance sheet fallback | Free web/PDF/XLS |
| Treasury | Treasury yields fallback | Free |
| ISM | Manufacturing/services PMI | Public reports/calendar; ingestion may require manual/semi-automated parser |

#### Tier 2 — practical vendor layer

Use only where official/free data are insufficient.

| Source | Best use | Notes |
|---|---|---|
| FMP | Prices, fundamentals, key metrics, earnings calendar, estimates | Best low-cost default for v1 vendor layer. |
| Alpha Vantage | Backup prices, earnings, company data, economic indicators | Free tier is too constrained for backbone use. |
| Finnhub | Alternative vendor for estimates, calendar, company metrics | Compare only if FMP coverage is poor. |
| Polygon / Massive | Cleaner market data and aggregates | Better if price-data quality matters more than low cost. |

#### Tier 3 — later/research layer

Use only after core platform stability.

| Source | Use |
|---|---|
| Quartr | Transcripts, IR documents, company event material. |
| Visible Alpha / S&P / FactSet / LSEG / Bloomberg | Institutional consensus, forward estimates, deep research workflows. |
| Macrobond | Full macro platform replacement or benchmark. |

### 7.2 Source decisions by metric class

| Metric class | Primary path | Fallback | Implementation decision |
|---|---|---|---|
| Macro rates/inflation/labor | FRED + ALFRED | BLS/BEA direct APIs | Start with FRED; add ALFRED metadata/vintages for core series. |
| CPI components | BLS | FRED where equivalent exists | Use BLS mappings for components that matter. |
| PCE/Core PCE | BEA or FRED | BEA direct | FRED acceptable; BEA direct preferred if transformations require exact NIPA mapping. |
| Energy/oil inventories | EIA | FRED for spot prices | EIA for inventories; FRED acceptable for WTI price. |
| Margin debt | FINRA XLS/web | Manual ingest if parser breaks | Treat as monthly report source, not API. |
| PMI | ISM report | Manual controlled input | Build manual/semi-automated ingestion; do not overbuild scraper early. |
| Prices | FMP or Polygon | Alpha Vantage | FMP default for cost/scope; Polygon if price fidelity becomes priority. |
| Actual fundamentals | SEC + FMP normalization | FMP only for speed | Use FMP for fast scaffold; validate core facts against SEC for key tickers. |
| Forward P/E / estimates | FMP | Alpha Vantage/Finnhub | Vendor-dependent; flag as estimate/vendor data. |
| Earnings surprise | FMP or Alpha Vantage | Manual source check | Vendor data acceptable for v1, with quality flags. |
| Guidance | None in v1 | Estimate revisions + post-earnings reaction | Do not parse guidance text in initial build. |
| Transcripts/IR docs | Deferred | Quartr later | Do not scrape IR pages in initial build. |

---

## 8. Indicator registry

### 8.1 Engines

Use these engine names:

1. `macro_fed`
2. `inflation`
3. `labor`
4. `activity`
5. `liquidity_fear`
6. `credit_rates`
7. `commodities`
8. `valuation`
9. `earnings`
10. `ai_semiconductor`
11. `balance_sheet`
12. `data_quality`

### 8.2 Core indicators

#### Macro / Fed

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| Effective federal funds rate | FRED `DFF` or `FEDFUNDS` | Core | Direct. |
| Fed target upper/lower | FRED `DFEDTARU`, `DFEDTARL` | Useful | Direct. |
| Fed projected target median | FRED `FEDTARMD` if available | Useful | Fallback to SEP manually. |
| Fed balance sheet | FRED `WALCL` | Core | Weekly. |
| QT pace | Derived from `WALCL` | Core | Weekly/monthly deltas. |

#### Inflation

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| CPI YoY/MoM | FRED/BLS | Core | Include vintage/release metadata where possible. |
| Core CPI YoY/MoM | FRED/BLS | Core | Same. |
| Core PCE YoY/MoM | FRED/BEA | Core | Same. |
| PPI Final Demand MoM | FRED/BLS | Core | Same. |
| Shelter CPI | BLS/FRED mapping | Core | Component mapping must be tested. |
| Services less energy services CPI | BLS | Useful | Component mapping. |
| Transportation services CPI | BLS | Optional | Component mapping. |
| Medical care services CPI | BLS | Optional | Component mapping. |
| Inflation expectations | FRED `MICH` | Useful | Lag/availability flag. |

#### Labor / activity

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| Unemployment rate | FRED/BLS | Core | Monthly. |
| Initial jobless claims | FRED/DOL | Core | Weekly. |
| Nonfarm payrolls | FRED/BLS | Core | Monthly. |
| Retail sales | FRED/Census | Useful | Monthly. |
| Existing home sales | FRED/NAR source | Useful | Check licensing/display constraints. |
| Home price index | FRED Case-Shiller | Useful | Monthly. |
| ISM Manufacturing PMI | ISM/manual | Core | Report-source ingestion. |
| ISM Services PMI | ISM/manual | Core | Report-source ingestion. |
| Consumer sentiment | FRED `UMCSENT` | Useful | Monthly. |

#### Liquidity / fear / credit / commodities

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| VIX | FRED `VIXCLS` | Core | Daily. |
| FINRA margin debt | FINRA | Core | Monthly XLS/web. |
| Margin debt MoM change | Derived | Core | Absolute and percent. |
| High-yield spread | FRED `BAMLH0A0HYM2` | Core | Daily. |
| 10Y Treasury yield | FRED `DGS10` | Core | Daily. |
| Broad dollar index | FRED `DTWEXBGS` | Core | DXY proxy. |
| WTI crude price | FRED/EIA | Core | Daily. |
| Crude inventories | EIA | Useful | Weekly. |

#### Valuation / prices

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| SPY price | FMP/Polygon/Alpha Vantage | Core | Daily OHLCV. |
| QQQ price | FMP/Polygon/Alpha Vantage | Core | Daily OHLCV. |
| SMH/SOXX price | FMP/Polygon/Alpha Vantage | Core | Daily OHLCV. |
| XLK/XLV/XLP/XLU/XLF prices | FMP/Polygon/Alpha Vantage | Useful | Optional proxy set. |
| Drawdown from trailing high | Derived | Core | Use adjusted close. |
| Company market cap | FMP + price/shares fallback | Core | Vendor direct or derived. |
| Forward P/E | FMP/Finnhub/Alpha Vantage | Core if vendor available | Vendor-dependent flag. |
| Trailing P/E | FMP/SEC-derived | Useful | Fallback when forward missing. |
| EV/EBITDA | FMP or derived from SEC + market data | Core | Direct first; validate. |
| Basket median forward P/E | Derived | Core if inputs available | Do not fabricate missing inputs. |

#### Earnings

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| Earnings calendar | FMP/Finnhub/Alpha Vantage | Core | Fixed universe only. |
| EPS actual vs estimate | FMP/Alpha Vantage/Finnhub | Core | Vendor estimate. |
| Revenue actual vs estimate | FMP/Finnhub | Core if available | Missing is acceptable. |
| Post-earnings 1d/3d/5d return | Derived from prices | Useful | Requires event date. |
| Estimate revision | FMP/Finnhub snapshot history | Useful | Only possible after own snapshots begin. |
| Guidance vs consensus | Deferred | Defer | Use proxy only. |

#### AI / semiconductor / capex

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| Semi ETF price | FMP/Polygon | Core | SMH/SOXX. |
| Semi basket median forward P/E | Vendor + derived | Core if inputs available | Fixed semi universe. |
| Semi earnings surprise | FMP/Alpha Vantage/Finnhub | Core | EPS first. |
| MU earnings | FMP/Alpha Vantage/Finnhub | Core | Memory proxy. |
| Big Tech capex | SEC/FMP | Core | Quarterly/TTM. |
| Operating cash flow | SEC/FMP | Core | Quarterly/TTM. |
| Free cash flow | Derived | Core | OCF - capex. |
| Capex / OCF | Derived | Core | Quarterly/TTM. |
| Capex / FCF | Derived | Useful | Handle negative FCF carefully. |
| Cash and equivalents | SEC/FMP | Core | Quarterly. |
| Total debt | SEC/FMP | Core | Quarterly. |
| Net debt | Derived | Core | Debt - cash. |
| Interest expense | SEC/FMP | Useful | Mapping can vary. |

#### Balance sheet / capital structure

| Indicator | Source | Priority | Notes |
|---|---|---|---|
| Short-term debt | SEC/FMP | Core | Quarterly. |
| Long-term debt | SEC/FMP | Core | Quarterly. |
| Total debt | Derived/vendor | Core | Include leases if mapped. |
| Cash/equivalents | SEC/FMP | Core | Quarterly. |
| Enterprise value | FMP or derived | Core | Market cap + debt + preferred + minority - cash. |
| Operating income | SEC/FMP | Core | Quarterly/TTM. |
| D&A | SEC/FMP | Core | Cash-flow mapping. |
| EBITDA | FMP or derived | Core | Operating income + D&A. |
| Debt / EBITDA | Derived | Core | TTM. |
| EBITDA / interest expense | Derived | Core | Guard divide-by-zero. |
| Capex / revenue | Derived | Useful | TTM. |

---

## 9. Data quality flags

Use a strict quality-flag vocabulary.

| Flag | Meaning |
|---|---|
| `ok` | Valid value retrieved and transformed. |
| `missing` | Expected value absent from source. |
| `stale` | Latest value older than expected cadence. |
| `partial` | Some but not all components available. |
| `revised` | Value changed versus previous vintage/retrieval. |
| `estimated` | Consensus/vendor estimate, not official actual. |
| `vendor_limited` | Missing because plan/API tier does not include field. |
| `manual` | Manually entered or manually confirmed. |
| `source_failed` | Retrieval failed. |
| `parse_failed` | Payload retrieved but parser failed. |
| `mapping_uncertain` | SEC/XBRL/component mapping requires review. |
| `license_restricted` | Display or redistribution may be restricted. |
| `missing_inputs` | Derived metric cannot be computed because input is absent. |
| `stale_inputs` | Derived metric computed from stale input. |

---

## 10. Update cadence

| Data class | Cadence |
|---|---|
| Market prices | Daily after market close. |
| VIX, yields, spreads, dollar, oil | Daily. |
| Initial claims | Weekly after release. |
| Fed balance sheet | Weekly after release. |
| EIA crude inventories | Weekly after release. |
| FINRA margin debt | Monthly, after FINRA publication. |
| CPI/PPI/labor/payrolls/retail sales | Monthly, release-calendar aware. |
| PCE/Core PCE | Monthly, release-calendar aware. |
| ISM PMI | Monthly, release-calendar/manual aware. |
| Company fundamentals | Quarterly, after filing and vendor update. |
| Earnings calendar | Daily during earnings season, weekly otherwise. |
| Forward estimates | Daily if vendor allows; otherwise weekly snapshot. |
| Derived metrics | After upstream refresh. |
| Dashboard health checks | Daily. |

---

## 11. Dashboard specification

### 11.1 Required dashboards

#### Dashboard 1 — Macro/Fed

Panels:

1. Effective fed funds rate.
2. Fed target range.
3. Fed balance sheet level and 4-week / 13-week change.
4. CPI YoY/MoM.
5. Core CPI YoY/MoM.
6. Core PCE YoY/MoM.
7. PPI Final Demand MoM.
8. Unemployment rate.
9. Initial claims.
10. Nonfarm payrolls.
11. ISM manufacturing/services.
12. Consumer sentiment.

Required table:

- Latest value
- Previous value
- 1m/3m/6m delta where applicable
- Observation date
- Release date
- Retrieved at
- Quality flag
- Source

#### Dashboard 2 — Liquidity/Fear/Credit

Panels:

1. VIX.
2. High-yield spread.
3. 10Y Treasury yield.
4. Broad dollar index.
5. FINRA margin debt.
6. Margin debt MoM change.
7. WTI crude.
8. Crude inventories.
9. Fed balance sheet delta.

Required table:

- Current stress indicators
- Latest values
- Deltas
- Quality flags

#### Dashboard 3 — Valuation

Panels:

1. SPY/QQQ/SMH/XLK price trend.
2. Drawdown from 52-week high and all-time high.
3. Company forward P/E for fixed universe if available.
4. Company trailing P/E fallback.
5. EV/EBITDA.
6. Basket medians.
7. Vendor coverage/missingness.

#### Dashboard 4 — Earnings

Panels:

1. Upcoming earnings calendar.
2. Recent earnings surprises.
3. EPS actual vs estimate.
4. Revenue actual vs estimate.
5. Post-earnings 1d/3d/5d return.
6. Estimate revision snapshot status if implemented.

#### Dashboard 5 — AI/Semi/Capex

Panels:

1. SMH/SOXX trend.
2. Semi basket returns.
3. Semi valuation medians.
4. Semi earnings surprises.
5. Big Tech capex.
6. Capex / OCF.
7. Capex / FCF.
8. Cash, total debt, net debt.
9. Debt-funded capex proxy components.

#### Dashboard 6 — Data Quality

Panels:

1. Source freshness by source.
2. Failed ingestion jobs.
3. Missing core indicators.
4. Vendor-limited fields.
5. Stale values.
6. Revised values.
7. Manual data requiring review.
8. License-restricted datasets.

---

## 12. Reading guides

Reading guides are dashboard annotations only. They are not decision rules.

Each guide must include:

1. Metric.
2. Threshold or range.
3. Interpretation label.
4. Source of threshold: transcript_derived, conventional, user_defined, vendor_defined, or manual.
5. Confidence level: low, medium, high.
6. Last reviewed date.

Initial guide registry:

| Metric | Range / condition | Label |
|---|---|---|
| VIX | 15–20 | calm |
| VIX | below 10 | complacent |
| VIX | above 30 | high fear |
| VIX | above 50 | crisis-like stress |
| CPI YoY | near 2% | Fed target area |
| CPI YoY | 2.5–3.5% sticky | difficult Fed backdrop |
| CPI YoY | above 4% | restrictive inflation backdrop |
| PPI MoM | 0–0.2% | normal producer inflation zone |
| PPI MoM | above 0.2% | producer-cost pressure |
| Unemployment | below 4% | strong labor market |
| Unemployment | 4–5.5% | normal range |
| Unemployment | above 5.5% | weak labor market |
| Initial claims | below 250k | strong labor market |
| Initial claims | 250k–350k | normal range |
| Initial claims | above 350k | weak labor market |
| Payrolls | above 250k | strong labor market |
| Payrolls | 50k–250k | normal range |
| Payrolls | below 50k | weak labor market |
| PMI | above 55 | strong expansion |
| PMI | around 50 | neutral |
| PMI | below 50 | contraction |
| Index drawdown | above 20% | major valuation reset |
| Big Tech forward P/E | 20–25x | lower valuation zone |
| Big Tech forward P/E | 30–35x | stretched zone |
| Semi forward P/E | 50–60x | elevated valuation zone |
| Capex / OCF | rising materially | increasing capex burden |
| Capex + debt + falling cash | simultaneous deterioration | debt-funded capex pressure |

---

## 13. Acceptance criteria

### 13.1 Registry

Accepted when:

1. All core indicators exist in `series_registry`.
2. Every indicator has source, frequency, unit, priority, access type, license class, fallback, and refresh policy.
3. No ingestion runs for unregistered metrics.
4. Disabled/deferred metrics are visible but not executed.

### 13.2 Ingestion

Accepted when:

1. Raw payloads are archived.
2. Normalized rows are written idempotently.
3. Retries and failures are logged.
4. Quality flags are set.
5. Backfill can be rerun without duplicating observations.
6. API keys are never committed.
7. SEC requests use a compliant User-Agent.

### 13.3 Derived metrics

Accepted when:

1. Every derived metric records input references.
2. Missing inputs produce `missing_inputs`, not zero.
3. Divide-by-zero cases are guarded.
4. Calculation version is stored.
5. Derived values can be regenerated.

### 13.4 Dashboards

Accepted when:

1. Each dashboard has a latest-value table.
2. Each metric displays source, observation date, retrieved time, and quality flag.
3. Stale/missing/vendor-limited data is visible.
4. No dashboard silently suppresses core missing data.
5. Dashboard SQL is stored in version control.

### 13.5 Documentation

Accepted when:

1. Metric dictionary exists.
2. Source coverage matrix exists.
3. Operations runbook exists.
4. Known limitations are listed.
5. Vendor-dependent metrics are labeled.

---

## 14. Implementation constraints

1. Build official/free ingestion before vendor-dependent modules.
2. Keep the fixed universe small.
3. Do not add broad screening.
4. Do not add NLP/news parsing.
5. Do not expand the dashboard set before core ingestion is stable.
6. Keep manual/semi-manual handling for ISM and other report-only sources if automation would be brittle.
7. Use vendor estimates only with explicit flags.
8. Prefer boring, inspectable code over abstractions.
9. Treat source freshness as a product feature.
10. Treat missing data as information.
