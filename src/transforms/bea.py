from datetime import date, datetime, timezone
from typing import Any

from src.db.models import SeriesEntry


def parse_bea_series_code(source_series_code: str | None) -> tuple[str, str, str]:
    if not source_series_code:
        msg = "BEA source_series_code is required"
        raise ValueError(msg)
    parts = source_series_code.split(":")
    if len(parts) != 3:
        msg = "BEA source_series_code must use DATASET:TABLE:LINE format"
        raise ValueError(msg)
    return parts[0], parts[1], parts[2]


def parse_bea_month(value: str | None) -> date | None:
    if not value or "M" not in value:
        return None
    year, month = value.split("M", 1)
    return date(int(year), int(month), 1)


def parse_bea_value(value: str | int | float | None) -> float | None:
    if value in {None, "", "(NA)", "---"}:
        return None
    return float(str(value).replace(",", ""))


def normalize_bea_nipa_table(
    *,
    series: SeriesEntry,
    payload: dict[str, Any],
    retrieved_at: datetime | None = None,
    raw_payload_id: str | None = None,
) -> list[dict[str, Any]]:
    dataset, table_name, line_number = parse_bea_series_code(series.source_series_code)
    if dataset != "NIPA":
        msg = f"Unsupported BEA dataset for NIPA transform: {dataset}"
        raise ValueError(msg)

    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for item in payload.get("BEAAPI", {}).get("Results", {}).get("Data", []):
        if item.get("TableName") != table_name or str(item.get("LineNumber")) != line_number:
            continue
        observation_date = parse_bea_month(item.get("TimePeriod"))
        value = parse_bea_value(item.get("DataValue"))
        if observation_date is None or value is None:
            continue
        rows.append(
            {
                "series_id": series.series_id,
                "observation_date": observation_date,
                "value": value,
                "unit": series.unit,
                "source_name": "BEA",
                "source_series_code": series.source_series_code,
                "retrieved_at": retrieved_at,
                "retrieved_on": retrieved_at.date(),
                "quality_flag": "ok",
                "raw_payload_id": raw_payload_id,
            }
        )
    return rows
