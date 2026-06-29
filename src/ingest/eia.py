from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.connectors.eia import EiaClient
from src.db.config import load_series_registry
from src.db.models import DataClass, SeriesEntry
from src.db.raw_archive import archive_payload
from src.db.upsert import upsert_raw_payload_metadata, upsert_series_observations
from src.transforms.eia import normalize_eia_series_data


def stage4_eia_series() -> list[SeriesEntry]:
    return [
        series
        for series in load_series_registry()
        if series.enabled
        and series.source_name == "EIA"
        and series.is_direct
        and series.data_class == DataClass.official_actual
        and series.source_series_code
    ]


def ingest_eia_series(
    *,
    session: Session,
    series: SeriesEntry,
    client: EiaClient,
    retrieved_at: datetime | None = None,
) -> int:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    response = client.series_data(series.source_series_code or series.series_id)
    archived = archive_payload(
        source_name=response.source_name,
        dataset_name=f"seriesid_{series.source_series_code}",
        payload=response.payload,
        response_format="json",
        request_url=response.request_url,
        request_params=response.request_params,
        retrieved_at=retrieved_at,
    )
    upsert_raw_payload_metadata(session, archived.db_row())
    rows = normalize_eia_series_data(
        series=series,
        payload=response.payload,
        retrieved_at=retrieved_at,
        raw_payload_id=archived.raw_payload_id,
    )
    return upsert_series_observations(session, rows)


def ingest_stage4_eia_energy(*, session: Session) -> dict[str, int]:
    client = EiaClient()
    counts: dict[str, int] = {}
    for series in stage4_eia_series():
        counts[series.series_id] = ingest_eia_series(
            session=session,
            series=series,
            client=client,
        )
    return counts


def ingest_stage4_eia(**kwargs) -> dict[str, int]:
    return ingest_stage4_eia_energy(**kwargs)
