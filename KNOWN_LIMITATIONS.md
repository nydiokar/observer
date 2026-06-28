# Known Limitations

## Source limitations

| Limitation | Details |
|---|---|
| ISM PMI | No clean universal free API. Requires manual/semi-automated ingestion. |
| FINRA margin debt | No clean API feed. Parsed from public XLS/web publication. |
| SEC XBRL facts | Concepts vary by filer and period. Mapping confidence flags used. |
| Forward P/E | Requires vendor estimates. Free official sources provide no consensus. |
| Revenue estimates | Often vendor-tier dependent. Missingness is visible. |
| Guidance parsing | Deferred. Not implemented in v1. |

## Data quality

- Vintage/revision metadata is only available where the source provides it (ALFRED for some FRED series).
- ETF/index valuation may differ between vendor sources and company-basket medians.
- License/display rights may restrict redistribution of certain vendor datasets.
- No automated alerting or threshold-crossing notifications in v1.
