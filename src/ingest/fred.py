from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from src.connectors.fred import AlfredClient, FredClient
from src.db.config import load_series_registry
from src.db.models import DataClass, SeriesEntry
from src.db.raw_archive import archive_payload
from src.db.upsert import upsert_raw_payload_metadata, upsert_series_observations
from src.transforms.fred import normalize_fred_observations

STAGE3_FRED_SERIES_IDS = {
    "FED_FUNDS_EFFECTIVE",
    "FED_TARGET_UPPER",
    "FED_TARGET_LOWER",
    "FED_BALANCE_SHEET",
    "CPI_YOY",
    "CORE_CPI_YOY",
    "CORE_PCE_YOY",
    "PPI_FINAL_DEMAND_MOM",
    "INFLATION_EXPECTATIONS",
    "UNEMPLOYMENT_RATE",
    "INITIAL_CLAIMS",
    "NONFARM_PAYROLLS",
    "CONSUMER_SENTIMENT",
    "VIX",
    "HY_SPREAD",
    "TEN_YEAR_YIELD",
    "BROAD_DOLLAR_INDEX",
    "WTI_CRUDE",
}


def stage3_fred_series() -> list[SeriesEntry]:
    return [
        series
        for series in load_series_registry()
        if series.enabled
        and series.series_id in STAGE3_FRED_SERIES_IDS
        and series.source_name == "FRED"
        and series.is_direct
        and series.data_class == DataClass.official_actual
        and series.source_series_code
    ]


def ingest_fred_series(
    *,
    session: Session,
    series: SeriesEntry,
    client: FredClient,
    observation_start: date | str | None = None,
    observation_end: date | str | None = None,
    retrieved_at: datetime | None = None,
    include_vintage: bool = False,
) -> int:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    response = client.series_observations(
        series_code=series.source_series_code or series.series_id,
        observation_start=observation_start,
        observation_end=observation_end,
    )
    archived = archive_payload(
        source_name=response.source_name,
        dataset_name=f"series_observations_{series.source_series_code}",
        payload=response.payload,
        response_format="json",
        request_url=response.request_url,
        request_params=response.request_params,
        retrieved_at=retrieved_at,
    )
    upsert_raw_payload_metadata(session, archived.db_row())
    rows = normalize_fred_observations(
        series=series,
        payload=response.payload,
        source_name=response.source_name,
        retrieved_at=retrieved_at,
        raw_payload_id=archived.raw_payload_id,
        include_vintage=include_vintage,
    )
    return upsert_series_observations(session, rows)


def ingest_stage3_fred_backbone(
    *,
    session: Session,
    observation_start: date | str | None = None,
    observation_end: date | str | None = None,
    include_alfred_vintages: bool = False,
) -> dict[str, int]:
    fred_client = FredClient()
    alfred_client = AlfredClient() if include_alfred_vintages else None
    counts: dict[str, int] = {}
    for series in stage3_fred_series():
        counts[series.series_id] = ingest_fred_series(
            session=session,
            series=series,
            client=fred_client,
            observation_start=observation_start,
            observation_end=observation_end,
        )
        if alfred_client is not None:
            counts[f"ALFRED:{series.series_id}"] = ingest_fred_series(
                session=session,
                series=series,
                client=alfred_client,
                observation_start=observation_start,
                observation_end=observation_end,
                include_vintage=True,
            )
    return counts
