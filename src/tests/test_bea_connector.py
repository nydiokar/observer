import json
from pathlib import Path

import pytest

from src.connectors.bea import BeaApiError, BeaClient, BeaConfigError


FIXTURE = Path(__file__).parent / "fixtures" / "bea_nipa_t20804.json"


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


def test_bea_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("BEA_API_KEY", raising=False)

    with pytest.raises(BeaConfigError):
        BeaClient()


def test_bea_client_requests_nipa_table_with_user_id():
    session = FakeSession(FakeResponse(json.loads(FIXTURE.read_text())))
    client = BeaClient(api_key="bea-key", session=session)

    response = client.nipa_table(table_name="T20804", frequency="M", years=[2025, 2026])

    assert response.payload["BEAAPI"]["Results"]["Data"][0]["TableName"] == "T20804"
    assert session.calls[0]["url"] == "https://apps.bea.gov/api/data"
    assert session.calls[0]["params"]["UserID"] == "bea-key"
    assert session.calls[0]["params"]["TableName"] == "T20804"
    assert session.calls[0]["params"]["Frequency"] == "M"
    assert session.calls[0]["params"]["Year"] == "2025,2026"


def test_bea_client_raises_on_api_error_payload():
    payload = {"BEAAPI": {"Results": {"Error": {"APIErrorDescription": "bad key"}}}}
    session = FakeSession(FakeResponse(payload))
    client = BeaClient(api_key="bea-key", session=session)

    with pytest.raises(BeaApiError):
        client.nipa_table(table_name="T20804", frequency="M", years=[2026])
