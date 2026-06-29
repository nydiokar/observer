from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from src.connectors.bls import BlsClient
from src.db.config import load_series_registry
from src.db.models import DataClass, SeriesEntry
from src.db.raw_archive import archive_payload
from src.db.upsert import upsert_raw_payload_metadata, upsert_series_observations
from src.transforms.bls import normalize_bls_series_data

BLS_MAX_YEAR_WINDOW = 20


def stage4_bls_series() -> list[SeriesEntry]:
    return [
        series
        for series in load_series_registry()
        if series.enabled
        and series.source_name == "BLS"
        and series.is_direct
        and series.data_class == DataClass.official_actual
        and series.source_series_code
    ]


def _year_windows(start_year: int, end_year: int) -> list[tuple[int, int]]:
    windows = []
    current = start_year
    while current <= end_year:
        window_end = min(end_year, current + BLS_MAX_YEAR_WINDOW - 1)
        windows.append((current, window_end))
        current = window_end + 1
    return windows


def ingest_bls_series(
    *,
    session: Session,
    series: SeriesEntry,
    client: BlsClient,
    start_year: int,
    end_year: int,
    retrieved_at: datetime | None = None,
) -> int:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    total = 0
    for window_start, window_end in _year_windows(start_year, end_year):
        response = client.series_data(
            series.source_series_code or series.series_id,
            start_year=window_start,
            end_year=window_end,
        )
        archived = archive_payload(
            source_name=response.source_name,
            dataset_name=f"timeseries_data_{series.source_series_code}",
            payload=response.payload,
            response_format="json",
            request_url=response.request_url,
            request_params=response.request_params,
            retrieved_at=retrieved_at,
        )
        upsert_raw_payload_metadata(session, archived.db_row())
        rows = normalize_bls_series_data(
            series=series,
            payload=response.payload,
            retrieved_at=retrieved_at,
            raw_payload_id=archived.raw_payload_id,
        )
        total += upsert_series_observations(session, rows)
    return total


def ingest_stage4_bls_components(
    *,
    session: Session,
    observation_start: date | str | None = None,
    observation_end: date | str | None = None,
) -> dict[str, int]:
    start = date.fromisoformat(str(observation_start)) if observation_start else date(1990, 1, 1)
    end = date.fromisoformat(str(observation_end)) if observation_end else date.today()
    client = BlsClient()
    counts: dict[str, int] = {}
    for series in stage4_bls_series():
        counts[series.series_id] = ingest_bls_series(
            session=session,
            series=series,
            client=client,
            start_year=start.year,
            end_year=end.year,
        )
    return counts
