import os
from dataclasses import dataclass
from typing import Any

import requests


class EiaConfigError(RuntimeError):
    pass


class EiaApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class EiaResponse:
    source_name: str
    dataset_name: str
    request_url: str
    request_params: dict[str, Any]
    payload: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]


def get_eia_api_key(api_key: str | None = None) -> str:
    key = api_key or os.environ.get("EIA_API_KEY")
    if not key:
        msg = "EIA_API_KEY is required for EIA ingestion"
        raise EiaConfigError(msg)
    return key


class EiaClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.eia.gov/v2",
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = get_eia_api_key(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def series_data(self, series_id: str) -> EiaResponse:
        request_url = f"{self.base_url}/seriesid/{series_id}"
        params = {"api_key": self.api_key}
        response = self.session.get(request_url, params=params, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            msg = f"EIA series request failed for {series_id}: HTTP {response.status_code}"
            raise EiaApiError(msg)
        payload = response.json()
        if "error" in payload:
            msg = f"EIA series request failed for {series_id}: {payload['error']}"
            raise EiaApiError(msg)
        return EiaResponse(
            source_name="EIA",
            dataset_name="seriesid",
            request_url=request_url,
            request_params=params,
            payload=payload,
        )
