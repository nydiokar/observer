from datetime import date, datetime, timezone
from typing import Any

from src.db.models import SeriesEntry


def parse_eia_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_eia_value(value: str | int | float | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def normalize_eia_series_data(
    *,
    series: SeriesEntry,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
    raw_payload_id: str | None = None,
) -> list[dict[str, Any]]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for item in payload.get("response", {}).get("data", []):
        observation_date = parse_eia_date(item.get("period"))
        value = parse_eia_value(item.get("value"))
        if observation_date is None or value is None:
            continue
        rows.append(
            {
                "series_id": series.series_id,
                "observation_date": observation_date,
                "value": value,
                "unit": series.unit,
                "source_name": "EIA",
                "source_series_code": series.source_series_code,
                "retrieved_at": retrieved_at,
                "retrieved_on": retrieved_at.date(),
                "quality_flag": "ok",
                "raw_payload_id": raw_payload_id,
            }
        )
    return rows
