from datetime import date

from src.db.models import SeriesEntry
from src.ingest.verify_stage3 import latest_status_for_series


def _series(frequency: str = "daily") -> SeriesEntry:
    return SeriesEntry(
        series_id="FED_FUNDS_EFFECTIVE",
        display_name="Effective Federal Funds Rate",
        engine="macro_fed",
        data_class="official_actual",
        source_name="FRED",
        source_series_code="DFF",
        frequency=frequency,
        unit="percent",
        access_type="free_official",
        license_class="public",
        priority="core",
        refresh_policy="daily",
    )


def test_latest_status_for_series_marks_missing():
    status = latest_status_for_series(
        series=_series(),
        latest_observation_date=None,
        as_of_date=date(2026, 6, 29),
    )

    assert status.series_id == "FED_FUNDS_EFFECTIVE"
    assert status.latest_date is None
    assert status.quality_flag == "missing"


def test_latest_status_for_series_marks_stale_daily_row():
    status = latest_status_for_series(
        series=_series(),
        latest_observation_date=date(2026, 6, 20),
        as_of_date=date(2026, 6, 29),
    )

    assert status.quality_flag == "stale"


def test_latest_status_for_series_marks_current_daily_row():
    status = latest_status_for_series(
        series=_series(),
        latest_observation_date=date(2026, 6, 26),
        as_of_date=date(2026, 6, 29),
    )

    assert status.quality_flag == "ok"
