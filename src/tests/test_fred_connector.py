import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from src.connectors.fred import (
    FredApiError,
    FredClient,
    FredConfigError,
    normalize_fred_observations,
    observations_to_db_rows,
)
from src.db.models import SeriesEntry


FIXTURE = Path(__file__).parent / "fixtures" / "fred_observations_dff.json"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response


def test_fred_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(FredConfigError):
        FredClient()


def test_fred_client_requests_observations_with_required_params():
    payload = json.loads(FIXTURE.read_text())
    session = FakeSession(FakeResponse(payload))
    client = FredClient(api_key="x" * 32, session=session)

    result = client.series_observations("DFF", observation_start="2026-06-25")

    assert result["count"] == 3
    assert session.calls[0]["url"] == "https://api.stlouisfed.org/fred/series/observations"
    assert session.calls[0]["params"]["series_id"] == "DFF"
    assert session.calls[0]["params"]["file_type"] == "json"
    assert session.calls[0]["params"]["observation_start"] == "2026-06-25"


def test_fred_client_raises_on_api_error_payload():
    session = FakeSession(FakeResponse({"error_code": 400, "error_message": "Bad request"}))
    client = FredClient(api_key="x" * 32, session=session)

    with pytest.raises(FredApiError):
        client.series_observations("DFF")


def test_normalize_fred_observations_preserves_missing_values():
    payload = json.loads(FIXTURE.read_text())

    observations = normalize_fred_observations(payload)

    assert len(observations) == 3
    assert observations[0].observation_date == date(2026, 6, 25)
    assert observations[0].value == 4.33
    assert observations[1].value is None


def test_observations_to_db_rows_skips_missing_values_and_adds_vintage():
    payload = json.loads(FIXTURE.read_text())
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
    retrieved_at = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

    rows = observations_to_db_rows(
        series=series,
        payload=payload,
        source_name="ALFRED",
        retrieved_at=retrieved_at,
        raw_payload_id="payload-1",
        include_vintage=True,
    )

    assert len(rows) == 2
    assert rows[0]["series_id"] == "FED_FUNDS_EFFECTIVE"
    assert rows[0]["source_name"] == "ALFRED"
    assert rows[0]["vintage_date"] == date(2026, 6, 29)
    assert rows[0]["retrieved_on"] == date(2026, 6, 29)
    assert rows[0]["raw_payload_id"] == "payload-1"
