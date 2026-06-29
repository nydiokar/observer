import json
from pathlib import Path

import pytest

from src.connectors.bls import BlsApiError, BlsClient


FIXTURE = Path(__file__).parent / "fixtures" / "bls_series_data.json"


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

    def post(self, url, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return self.response


def test_bls_client_posts_series_request_with_registration_key():
    payload = json.loads(FIXTURE.read_text())
    session = FakeSession(FakeResponse(payload))
    client = BlsClient(api_key="key-1", session=session)

    result = client.series_data("CUSR0000SAH1", start_year=2025, end_year=2026)

    assert result["status"] == "REQUEST_SUCCEEDED"
    assert session.calls[0]["url"] == "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    assert session.calls[0]["json"]["seriesid"] == ["CUSR0000SAH1"]
    assert session.calls[0]["json"]["startyear"] == "2025"
    assert session.calls[0]["json"]["endyear"] == "2026"
    assert session.calls[0]["json"]["registrationkey"] == "key-1"


def test_bls_client_raises_on_api_error_payload():
    session = FakeSession(FakeResponse({"status": "REQUEST_FAILED", "message": ["bad series"]}))
    client = BlsClient(api_key="key-1", session=session)

    with pytest.raises(BlsApiError):
        client.series_data("bad", start_year=2026, end_year=2026)
