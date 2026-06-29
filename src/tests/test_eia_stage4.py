import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.db.models import SeriesEntry
from src.ingest.eia import stage4_eia_series
from src.transforms.eia import normalize_eia_series_data, parse_eia_date, parse_eia_value


FIXTURE = Path(__file__).parent / "fixtures" / "eia_crude_inventories.json"


def _series() -> SeriesEntry:
    return SeriesEntry(
        series_id="CRUDE_INVENTORIES",
        display_name="Weekly Crude Oil Inventories",
        engine="commodities",
        data_class="official_actual",
        source_name="EIA",
        source_series_code="PET.WCRSTUS1.W",
        frequency="weekly",
        unit="thousand_barrels",
        access_type="free_official",
        license_class="public",
        priority="useful",
        refresh_policy="weekly",
    )


def test_parse_eia_date_and_value():
    assert parse_eia_date("2026-06-19") == date(2026, 6, 19)
    assert parse_eia_value(743325) == 743325.0
    assert parse_eia_value("") is None


def test_normalize_eia_series_data():
    retrieved_at = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)
    rows = normalize_eia_series_data(
        series=_series(),
        payload=json.loads(FIXTURE.read_text()),
        retrieved_at=retrieved_at,
        raw_payload_id="raw-1",
    )

    assert len(rows) == 2
    assert rows[0]["series_id"] == "CRUDE_INVENTORIES"
    assert rows[0]["observation_date"] == date(2026, 6, 19)
    assert rows[0]["value"] == 743325.0
    assert rows[0]["unit"] == "thousand_barrels"
    assert rows[0]["source_name"] == "EIA"


def test_stage4_eia_series_includes_crude_inventories():
    series_ids = {series.series_id for series in stage4_eia_series()}

    assert "CRUDE_INVENTORIES" in series_ids
