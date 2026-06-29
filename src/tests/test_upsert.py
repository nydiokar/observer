from datetime import date, datetime, timezone

from sqlalchemy.dialects import postgresql

from src.db.upsert import upsert_series_observations, upsert_series_registry


class FakeSession:
    def __init__(self):
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)
        return None


def _compile(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


def test_series_registry_upsert_uses_series_id_conflict_target():
    session = FakeSession()

    upsert_series_registry(
        session,
        {
            "series_id": "FED_FUNDS_EFFECTIVE",
            "display_name": "Effective Federal Funds Rate",
            "engine": "macro_fed",
            "data_class": "official_actual",
            "source_name": "FRED",
            "source_series_code": "DFF",
            "frequency": "daily",
            "unit": "percent",
            "access_type": "free_official",
            "license_class": "public",
            "priority": "core",
            "is_direct": True,
            "refresh_policy": "daily",
            "enabled": True,
        },
    )

    sql = _compile(session.statements[0])
    assert "ON CONFLICT (series_id) DO UPDATE" in sql


def test_series_observation_upsert_preserves_non_vintage_retrieval_day():
    session = FakeSession()

    upsert_series_observations(
        session,
        {
            "series_id": "FED_FUNDS_EFFECTIVE",
            "observation_date": date(2026, 6, 29),
            "value": 4.25,
            "unit": "percent",
            "source_name": "FRED",
            "source_series_code": "DFF",
            "retrieved_at": datetime(2026, 6, 29, 13, 0, tzinfo=timezone.utc),
            "quality_flag": "ok",
        },
        require_registered=False,
    )

    sql = _compile(session.statements[0])
    assert "ON CONFLICT (series_id, observation_date, source_name, retrieved_on)" in sql
    assert "WHERE vintage_date IS NULL" in sql


def test_series_observation_upsert_uses_vintage_conflict_target():
    session = FakeSession()

    upsert_series_observations(
        session,
        {
            "series_id": "CPI_YOY",
            "observation_date": date(2026, 5, 1),
            "value": 3.1,
            "unit": "percent",
            "source_name": "ALFRED",
            "source_series_code": "CPIAUCSL",
            "vintage_date": date(2026, 6, 15),
            "retrieved_at": datetime(2026, 6, 29, 13, 0, tzinfo=timezone.utc),
            "quality_flag": "ok",
        },
        require_registered=False,
    )

    sql = _compile(session.statements[0])
    assert "ON CONFLICT (series_id, observation_date, vintage_date, source_name)" in sql
    assert "WHERE vintage_date IS NOT NULL" in sql
