import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.db.models import SeriesEntry
from src.ingest.bea import stage4_bea_series
from src.transforms.bea import normalize_bea_nipa_table, parse_bea_month, parse_bea_series_code, parse_bea_value


FIXTURE = Path(__file__).parent / "fixtures" / "bea_nipa_t20804.json"


def _series() -> SeriesEntry:
    return SeriesEntry(
        series_id="CORE_PCE_PRICE_INDEX_BEA",
        display_name="Core PCE Price Index (BEA)",
        engine="inflation",
        data_class="official_actual",
        source_name="BEA",
        source_series_code="NIPA:T20804:25",
        frequency="monthly",
        unit="index",
        access_type="free_official",
        license_class="public",
        priority="useful",
        refresh_policy="monthly",
    )


def test_parse_bea_series_code_requires_dataset_table_and_line():
    assert parse_bea_series_code("NIPA:T20804:25") == ("NIPA", "T20804", "25")


def test_parse_bea_month_and_value():
    assert parse_bea_month("2026M05") == date(2026, 5, 1)
    assert parse_bea_month("2026Q01") is None
    assert parse_bea_value("1,234.5") == 1234.5
    assert parse_bea_value("(NA)") is None


def test_normalize_bea_nipa_table_filters_exact_line():
    retrieved_at = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)
    rows = normalize_bea_nipa_table(
        series=_series(),
        payload=json.loads(FIXTURE.read_text()),
        retrieved_at=retrieved_at,
        raw_payload_id="raw-1",
    )

    assert len(rows) == 1
    assert rows[0]["series_id"] == "CORE_PCE_PRICE_INDEX_BEA"
    assert rows[0]["observation_date"] == date(2026, 5, 1)
    assert rows[0]["value"] == 128.173
    assert rows[0]["unit"] == "index"
    assert rows[0]["source_name"] == "BEA"
    assert rows[0]["raw_payload_id"] == "raw-1"


def test_stage4_bea_series_includes_verified_pce_index_rows():
    series_ids = {series.series_id for series in stage4_bea_series()}

    assert "PCE_PRICE_INDEX_BEA" in series_ids
    assert "CORE_PCE_PRICE_INDEX_BEA" in series_ids
