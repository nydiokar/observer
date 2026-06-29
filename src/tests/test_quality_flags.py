from datetime import date

from src.db.models import Frequency
from src.transforms.quality_flags import latest_observation_quality_flag


def test_latest_observation_quality_flag_marks_missing():
    assert latest_observation_quality_flag(
        observation_date=None,
        as_of_date=date(2026, 6, 29),
        frequency=Frequency.daily,
    ) == "missing"


def test_latest_observation_quality_flag_marks_stale_daily_series():
    assert latest_observation_quality_flag(
        observation_date=date(2026, 6, 1),
        as_of_date=date(2026, 6, 29),
        frequency=Frequency.daily,
    ) == "stale"


def test_latest_observation_quality_flag_marks_current_monthly_series():
    assert latest_observation_quality_flag(
        observation_date=date(2026, 6, 1),
        as_of_date=date(2026, 6, 29),
        frequency=Frequency.monthly,
    ) == "ok"
