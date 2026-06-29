import json
from pathlib import Path

import pytest

from src.connectors.eia import EiaApiError, EiaClient, EiaConfigError


FIXTURE = Path(__file__).parent / "fixtures" / "eia_crude_inventories.json"


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


def test_eia_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    with pytest.raises(EiaConfigError):
        EiaClient()


def test_eia_client_requests_series_with_api_key():
    session = FakeSession(FakeResponse(json.loads(FIXTURE.read_text())))
    client = EiaClient(api_key="eia-key", session=session)

    response = client.series_data("PET.WCRSTUS1.W")

    assert response.payload["response"]["total"] == 2
    assert session.calls[0]["url"] == "https://api.eia.gov/v2/seriesid/PET.WCRSTUS1.W"
    assert session.calls[0]["params"]["api_key"] == "eia-key"


def test_eia_client_raises_on_http_error():
    session = FakeSession(FakeResponse({}, status_code=403))
    client = EiaClient(api_key="eia-key", session=session)

    with pytest.raises(EiaApiError):
        client.series_data("PET.WCRSTUS1.W")
