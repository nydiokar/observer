# Metric Dictionary

*To be populated as metrics are registered and ingested.*

## Structure

Each metric entry includes:
- `series_id` — stable internal ID
- `display_name` — human-readable label
- `engine` — macro_fed, inflation, labor, activity, liquidity_fear, credit_rates, commodities, valuation, earnings, ai_semiconductor, balance_sheet, data_quality
- `source_name` — FRED, BLS, BEA, EIA, FINRA, SEC, FMP, etc.
- `frequency` — daily, weekly, monthly, quarterly, annual, irregular
- `unit` — percent, index, USD, ratio, count, bps
- `quality_flag` — ok, stale, missing, vendor_limited, etc.
