from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from src.connectors.bea import BeaClient
from src.db.config import load_series_registry
from src.db.models import DataClass, SeriesEntry
from src.db.raw_archive import archive_payload
from src.db.upsert import upsert_raw_payload_metadata, upsert_series_observations
from src.transforms.bea import normalize_bea_nipa_table, parse_bea_series_code


def stage4_bea_series() -> list[SeriesEntry]:
    return [
        series
        for series in load_series_registry()
        if series.enabled
        and series.source_name == "BEA"
        and series.is_direct
        and series.data_class == DataClass.official_actual
        and series.source_series_code
    ]


def ingest_bea_series(
    *,
    session: Session,
    series: SeriesEntry,
    client: BeaClient,
    start_year: int,
    end_year: int,
    retrieved_at: datetime | None = None,
) -> int:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    dataset_name, table_name, _line_number = parse_bea_series_code(series.source_series_code)
    if dataset_name != "NIPA":
        msg = f"Unsupported BEA dataset for ingestion: {dataset_name}"
        raise ValueError(msg)
    response = client.nipa_table(
        table_name=table_name,
        frequency="M",
        years=list(range(start_year, end_year + 1)),
    )
    archived = archive_payload(
        source_name=response.source_name,
        dataset_name=f"nipa_{series.source_series_code}",
        payload=response.payload,
        response_format="json",
        request_url=response.request_url,
        request_params=response.request_params,
        retrieved_at=retrieved_at,
    )
    upsert_raw_payload_metadata(session, archived.db_row())
    rows = normalize_bea_nipa_table(
        series=series,
        payload=response.payload,
        retrieved_at=retrieved_at,
        raw_payload_id=archived.raw_payload_id,
    )
    return upsert_series_observations(session, rows)


def ingest_stage4_bea_pce(
    *,
    session: Session,
    observation_start: date | str | None = None,
    observation_end: date | str | None = None,
) -> dict[str, int]:
    start = date.fromisoformat(str(observation_start)) if observation_start else date(1990, 1, 1)
    end = date.fromisoformat(str(observation_end)) if observation_end else date.today()
    client = BeaClient()
    counts: dict[str, int] = {}
    for series in stage4_bea_series():
        counts[series.series_id] = ingest_bea_series(
            session=session,
            series=series,
            client=client,
            start_year=start.year,
            end_year=end.year,
        )
    return counts


def ingest_stage4_bea(**kwargs) -> dict[str, int]:
    return ingest_stage4_bea_pce(**kwargs)
