from datetime import date, datetime, timezone
from typing import Any

from src.db.models import SeriesEntry


def parse_bls_period(year: str, period: str) -> date | None:
    if not period.startswith("M") or period == "M13":
        return None
    month = int(period[1:])
    if month < 1 or month > 12:
        return None
    return date(int(year), month, 1)


def parse_bls_value(value: str | int | float | None) -> float | None:
    if value in {None, "", "-"}:
        return None
    return float(value)


def normalize_bls_series_data(
    *,
    series: SeriesEntry,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
    raw_payload_id: str | None = None,
) -> list[dict[str, Any]]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for result_series in payload.get("Results", {}).get("series", []):
        if result_series.get("seriesID") != series.source_series_code:
            continue
        for item in result_series.get("data", []):
            observation_date = parse_bls_period(str(item.get("year", "")), str(item.get("period", "")))
            value = parse_bls_value(item.get("value"))
            if observation_date is None or value is None:
                continue
            rows.append(
                {
                    "series_id": series.series_id,
                    "observation_date": observation_date,
                    "value": value,
                    "unit": series.unit,
                    "source_name": "BLS",
                    "source_series_code": series.source_series_code,
                    "retrieved_at": retrieved_at,
                    "retrieved_on": retrieved_at.date(),
                    "quality_flag": "ok",
                    "raw_payload_id": raw_payload_id,
                }
            )
    return rows
