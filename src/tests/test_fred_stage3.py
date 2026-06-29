import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy.dialects import postgresql

from src.connectors.fred import AlfredClient, FredClient
from src.db.models import SeriesEntry
from src.db.queries import latest_series_observation_query
from src.ingest.fred import stage3_fred_series
from src.transforms.fred import normalize_fred_observations, parse_fred_value
from src.transforms.quality_flags import staleness_flag

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class FakeResponse:
    status_code = 200
    text = "ok"

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeRequestsSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_fred_client_builds_series_observation_request():
    payload = load_fixture("fred_observations.json")
    fake_session = FakeRequestsSession(payload)
    client = FredClient(api_key="test-key", session=fake_session)

    response = client.series_observations(
        series_code="DFF",
        observation_start="2026-06-01",
        observation_end="2026-06-29",
    )

    call = fake_session.calls[0]
    assert call["url"] == "https://api.stlouisfed.org/fred/series/observations"
    assert call["params"]["series_id"] == "DFF"
    assert call["params"]["api_key"] == "test-key"
    assert call["params"]["file_type"] == "json"
    assert response.payload == payload


def test_alfred_client_uses_alfred_base_url_and_source_name():
    payload = load_fixture("fred_observations.json")
    fake_session = FakeRequestsSession(payload)
    client = AlfredClient(api_key="test-key", session=fake_session)

    response = client.series_observations(series_code="DFF")

    assert fake_session.calls[0]["url"] == "https://api.stlouisfed.org/alfred/series/observations"
    assert response.source_name == "ALFRED"


def test_normalize_fred_observations_skips_missing_and_sets_vintage():
    payload = load_fixture("fred_observations.json")
    series = SeriesEntry(
        series_id="FED_FUNDS_EFFECTIVE",
        display_name="Effective Federal Funds Rate",
        engine="macro_fed",
        data_class="official_actual",
        source_name="FRED",
        source_series_code="DFF",
        frequency="daily",
        unit="percent",
        access_type="free_official",
        license_class="public",
        priority="core",
        refresh_policy="daily",
    )
    retrieved_at = datetime(2026, 6, 29, 10, tzinfo=timezone.utc)

    rows = normalize_fred_observations(
        series=series,
        payload=payload,
        source_name="ALFRED",
        retrieved_at=retrieved_at,
        raw_payload_id="raw-1",
        include_vintage=True,
        as_of=date(2026, 6, 29),
    )

    assert len(rows) == 2
    assert rows[0]["series_id"] == "FED_FUNDS_EFFECTIVE"
    assert rows[0]["observation_date"] == date(2026, 6, 25)
    assert rows[0]["value"] == 4.33
    assert rows[0]["vintage_date"] == date(2026, 6, 29)
    assert rows[0]["retrieved_on"] == date(2026, 6, 29)
    assert rows[0]["raw_payload_id"] == "raw-1"


def test_parse_fred_value_handles_missing_dot():
    assert parse_fred_value(".") is None
    assert parse_fred_value("1.25") == 1.25


def test_staleness_flag_respects_frequency_threshold():
    assert staleness_flag(observation_date=date(2026, 6, 25), frequency="daily", as_of=date(2026, 6, 29)) == "ok"
    assert staleness_flag(observation_date=date(2026, 1, 1), frequency="daily", as_of=date(2026, 6, 29)) == "stale"


def test_stage3_fred_series_matches_backbone_subset():
    series_ids = {series.series_id for series in stage3_fred_series()}

    assert "FED_FUNDS_EFFECTIVE" in series_ids
    assert "VIX" in series_ids
    assert "WTI_CRUDE" in series_ids
    assert "CPI_MOM" not in series_ids
    assert "SHELTER_CPI" not in series_ids


def test_latest_series_observation_query_compiles():
    sql = str(latest_series_observation_query("FED_FUNDS_EFFECTIVE").compile(dialect=postgresql.dialect()))

    assert "series_observations" in sql
    assert "max" in sql.lower()
