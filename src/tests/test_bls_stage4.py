import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.db.models import SeriesEntry
from src.ingest.bls import _year_windows, stage4_bls_series
from src.transforms.bls import normalize_bls_series_data, parse_bls_period, parse_bls_value


FIXTURE = Path(__file__).parent / "fixtures" / "bls_series_data.json"


def _series() -> SeriesEntry:
    return SeriesEntry(
        series_id="SHELTER_CPI",
        display_name="Shelter CPI",
        engine="inflation",
        data_class="official_actual",
        source_name="BLS",
        source_series_code="CUSR0000SAH1",
        frequency="monthly",
        unit="index",
        access_type="free_official",
        license_class="public",
        priority="core",
        refresh_policy="monthly",
    )


def test_parse_bls_period_handles_months_and_skips_annual_average():
    assert parse_bls_period("2026", "M05") == date(2026, 5, 1)
    assert parse_bls_period("2026", "M13") is None
    assert parse_bls_period("2026", "Q01") is None


def test_parse_bls_value_handles_missing_dash():
    assert parse_bls_value("-") is None
    assert parse_bls_value("423.499") == 423.499


def test_normalize_bls_series_data_skips_annual_average():
    payload = json.loads(FIXTURE.read_text())
    retrieved_at = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

    rows = normalize_bls_series_data(
        series=_series(),
        payload=payload,
        retrieved_at=retrieved_at,
        raw_payload_id="raw-1",
    )

    assert len(rows) == 1
    assert rows[0]["series_id"] == "SHELTER_CPI"
    assert rows[0]["observation_date"] == date(2026, 5, 1)
    assert rows[0]["value"] == 423.499
    assert rows[0]["unit"] == "index"
    assert rows[0]["source_name"] == "BLS"
    assert rows[0]["retrieved_on"] == date(2026, 6, 29)
    assert rows[0]["raw_payload_id"] == "raw-1"


def test_bls_backfill_splits_into_twenty_year_windows():
    assert _year_windows(1990, 2026) == [(1990, 2009), (2010, 2026)]


def test_stage4_bls_series_includes_enabled_component_mappings():
    series_ids = {series.series_id for series in stage4_bls_series()}

    assert "SHELTER_CPI" in series_ids
    assert "SERVICES_LESS_ENERGY_CPI" in series_ids
    assert "CPI_YOY_VALUE" not in series_ids
