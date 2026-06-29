# Source Coverage

| Source | Status | Coverage | Access Type | Notes |
|---|---|---|---|---|
| FRED | Backfilling | Macro, rates, spreads, VIX, Fed balance sheet | Free API key | Connector, raw archive, normalization, and DB upsert path are tested. Live backfill verified on 2026-06-29 with 18 backbone series and 66,184 observations in PostgreSQL. |
| ALFRED | Implemented | Vintage/revision data for select FRED series | Free API key | Connector supports vintage rows via `--include-alfred-vintages`. Live use requires `FRED_API_KEY`. |
| BLS | Not started | CPI, PPI, labor, CPI components | Free API | |
| BEA | Not started | PCE, Core PCE, NIPA | Free API key | |
| EIA | Not started | Crude inventories, energy | Free API | |
| SEC EDGAR | Not started | Filings, company facts, XBRL | Free API | Requires compliant User-Agent |
| FINRA | Not started | Margin debt | Free XLS/web | Manual/semi-automated parsing |
| ISM | Not started | Manufacturing/services PMI | Public report | Manual/semi-automated ingestion |
| FMP | Not started | Prices, fundamentals, earnings, estimates | Vendor API | Default vendor layer |
| Alpha Vantage | Not started | Backup prices, earnings | Vendor API | Fallback only |
| Polygon | Not started | Alternative market data | Vendor API | Optional upgrade path |

## Legend

- **Not started** — connector not yet implemented
- **Implemented** — connector exists and tested
- **Backfilling** — connector exists, historical data loading in progress
- **Live** — connector running on schedule
- **Degraded** — connector has known issues
- **Deferred** — intentionally postponed
