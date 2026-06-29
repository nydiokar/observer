import hashlib
from datetime import date, datetime, timezone

from sqlalchemy.dialects import postgresql

from src.db.raw_archive import archive_raw_payload, sanitize_request_params
from src.db.session import normalize_database_url
from src.db.upsert import upsert_series_observations


class RecordingSession:
    def __init__(self):
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)


def compile_postgres(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


def test_normalize_database_url_uses_psycopg_driver():
    assert normalize_database_url("postgresql://user@localhost/db") == (
        "postgresql+psycopg://user@localhost/db"
    )
    assert normalize_database_url("postgresql+psycopg://user@localhost/db") == (
        "postgresql+psycopg://user@localhost/db"
    )


def test_raw_archive_writes_payload_and_sanitizes_request_metadata(tmp_path):
    payload = {"observations": [{"date": "2026-01-01", "value": 1.25}]}
    metadata = archive_raw_payload(
        source_name="FRED",
        dataset_name="series/observations",
        payload=payload,
        response_format="json",
        request_url="https://api.example.test/series?api_key=secret",
        request_params={"series_id": "DFF", "api_key": "secret"},
        retrieved_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        raw_data_dir=tmp_path,
    )

    archived_path = tmp_path / "fred" / "series_observations" / "2026" / "01" / "02"
    assert metadata.storage_path.startswith(str(archived_path))
    body = open(metadata.storage_path, "rb").read()
    assert metadata.checksum == hashlib.sha256(body).hexdigest()
    assert metadata.request_params_json == {
        "series_id": "DFF",
        "api_key": "<redacted>",
    }
    assert metadata.request_url_hash is not None


def test_sanitize_request_params_redacts_common_secret_names():
    assert sanitize_request_params(
        {
            "token": "x",
            "Authorization": "Bearer y",
            "plain": "ok",
        }
    ) == {
        "token": "<redacted>",
        "Authorization": "<redacted>",
        "plain": "ok",
    }


def test_series_observation_upsert_uses_vintage_and_nonvintage_conflicts():
    session = RecordingSession()
    retrieved_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    count = upsert_series_observations(
        session,
        [
            {
                "series_id": "FED_FUNDS_EFFECTIVE",
                "observation_date": date(2026, 1, 1),
                "value": 4.25,
                "unit": "percent",
                "source_name": "FRED",
                "retrieved_at": retrieved_at,
            },
            {
                "series_id": "CPI_YOY",
                "observation_date": date(2026, 1, 1),
                "value": 2.9,
                "unit": "percent",
                "source_name": "ALFRED",
                "retrieved_at": retrieved_at,
                "vintage_date": date(2026, 1, 15),
            },
        ],
    )

    assert count == 2
    assert len(session.statements) == 2
    sql = "\n".join(compile_postgres(statement) for statement in session.statements)
    assert "ON CONFLICT" in sql
    assert "vintage_date IS NOT NULL" in sql
    assert "vintage_date IS NULL" in sql
    assert "retrieved_on" in sql


def test_initial_migration_contains_stage2_constraints():
    sql = open("src/db/migrations/001_initial_schema.sql").read()
    assert "raw_payload_id    TEXT PRIMARY KEY" in sql
    assert "retrieved_on      DATE NOT NULL" in sql
    assert "source_name, retrieved_on" in sql
    assert "uq_derived_metric_scope" in sql
    assert "COALESCE(instrument_id, -1)" in sql
