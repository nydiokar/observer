from datetime import date, datetime, timezone
from typing import Any

from src.db.models import SeriesEntry
def parse_fred_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_fred_value(value: str | int | float | None) -> float | None:
    if value in (None, ""):
        return None
    if value == ".":
        return None
    return float(value)


def normalize_fred_observations(
    *,
    series: SeriesEntry,
    payload: dict[str, Any],
    source_name: str,
    retrieved_at: datetime | None = None,
    raw_payload_id: str | None = None,
    include_vintage: bool = False,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    del as_of  # Staleness is evaluated for latest-observation checks, not every historical row.
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []

    for observation in payload.get("observations", []):
        observation_date = parse_fred_date(observation.get("date"))
        value = parse_fred_value(observation.get("value"))
        if observation_date is None or value is None:
            continue
        vintage_date = parse_fred_date(observation.get("realtime_start")) if include_vintage else None

        rows.append(
            {
                "series_id": series.series_id,
                "observation_date": observation_date,
                "value": value,
                "unit": series.unit,
                "source_name": source_name,
                "source_series_code": series.source_series_code,
                "vintage_date": vintage_date,
                "retrieved_at": retrieved_at,
                "retrieved_on": retrieved_at.date(),
                "quality_flag": "ok",
                "raw_payload_id": raw_payload_id,
            }
        )
    return rows
