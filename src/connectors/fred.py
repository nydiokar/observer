import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import requests

from src.db.models import SeriesEntry


class FredConfigError(RuntimeError):
    pass


class FredApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class FredObservation:
    realtime_start: date | None
    realtime_end: date | None
    observation_date: date
    value: float | None
    raw_value: str


@dataclass(frozen=True)
class FredResponse:
    source_name: str
    dataset_name: str
    request_url: str
    request_params: dict[str, Any]
    payload: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]


def get_fred_api_key(api_key: str | None = None) -> str:
    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        msg = "FRED_API_KEY is required for FRED/ALFRED ingestion"
        raise FredConfigError(msg)
    return key


def parse_fred_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_fred_value(value: str) -> float | None:
    if value in {"", "."}:
        return None
    return float(value)


def normalize_fred_observations(payload: dict[str, Any]) -> list[FredObservation]:
    observations = []
    for item in payload.get("observations", []):
        raw_value = str(item.get("value", ""))
        observations.append(
            FredObservation(
                realtime_start=parse_fred_date(item.get("realtime_start")),
                realtime_end=parse_fred_date(item.get("realtime_end")),
                observation_date=parse_fred_date(item["date"]),
                value=parse_fred_value(raw_value),
                raw_value=raw_value,
            )
        )
    return observations


def observations_to_db_rows(
    *,
    series: SeriesEntry,
    payload: dict[str, Any],
    source_name: str,
    retrieved_at: datetime | None = None,
    raw_payload_id: str | None = None,
    include_vintage: bool = False,
) -> list[dict[str, Any]]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    rows = []
    for observation in normalize_fred_observations(payload):
        if observation.value is None:
            continue
        row = {
            "series_id": series.series_id,
            "observation_date": observation.observation_date,
            "value": observation.value,
            "unit": series.unit,
            "source_name": source_name,
            "source_series_code": series.source_series_code,
            "retrieved_at": retrieved_at,
            "retrieved_on": retrieved_at.date(),
            "quality_flag": "ok",
            "raw_payload_id": raw_payload_id,
        }
        if include_vintage:
            row["vintage_date"] = observation.realtime_start
        rows.append(row)
    return rows


class FredClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.stlouisfed.org/fred",
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = get_fred_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def series_observations(
        self,
        series_code: str | None = None,
        *,
        series_id: str | None = None,
        observation_start: date | str | None = None,
        observation_end: date | str | None = None,
        realtime_start: date | str | None = None,
        realtime_end: date | str | None = None,
        source_name: str = "FRED",
    ) -> FredResponse:
        series_code = series_code or series_id
        if not series_code:
            msg = "series_code or series_id is required"
            raise ValueError(msg)
        params: dict[str, Any] = {
            "series_id": series_code,
            "api_key": self.api_key,
            "file_type": "json",
        }
        optional = {
            "observation_start": observation_start,
            "observation_end": observation_end,
            "realtime_start": realtime_start,
            "realtime_end": realtime_end,
        }
        for key, value in optional.items():
            if value is not None:
                params[key] = value.isoformat() if hasattr(value, "isoformat") else value

        request_url = f"{self.base_url}/series/observations"
        response = self.session.get(request_url, params=params, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            msg = f"{source_name} observations request failed for {series_code}: HTTP {response.status_code}"
            raise FredApiError(msg)
        payload = response.json()
        if "error_code" in payload:
            msg = f"{source_name} observations request failed for {series_code}: {payload.get('error_message')}"
            raise FredApiError(msg)
        return FredResponse(
            source_name=source_name,
            dataset_name="series_observations",
            request_url=request_url,
            request_params=params,
            payload=payload,
        )


class AlfredClient(FredClient):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("base_url", "https://api.stlouisfed.org/alfred")
        super().__init__(**kwargs)

    def series_observations(self, *args, **kwargs) -> FredResponse:
        kwargs.setdefault("source_name", "ALFRED")
        return super().series_observations(*args, **kwargs)
