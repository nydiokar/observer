import os
from dataclasses import dataclass
from typing import Any

import requests


class BlsApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class BlsResponse:
    source_name: str
    dataset_name: str
    request_url: str
    request_params: dict[str, Any]
    payload: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]


class BlsClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.bls.gov/publicAPI/v2",
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("BLS_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def series_data(
        self,
        series_codes: list[str] | str,
        *,
        start_year: int | str,
        end_year: int | str,
    ) -> BlsResponse:
        if isinstance(series_codes, str):
            series_codes = [series_codes]
        if not series_codes:
            msg = "At least one BLS series code is required"
            raise ValueError(msg)

        payload: dict[str, Any] = {
            "seriesid": series_codes,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if self.api_key:
            payload["registrationkey"] = self.api_key

        request_url = f"{self.base_url}/timeseries/data/"
        response = self.session.post(request_url, json=payload, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            msg = f"BLS series request failed for {', '.join(series_codes)}: HTTP {response.status_code}"
            raise BlsApiError(msg)

        response_payload = response.json()
        if response_payload.get("status") != "REQUEST_SUCCEEDED":
            messages = "; ".join(response_payload.get("message", []))
            msg = f"BLS series request failed for {', '.join(series_codes)}: {messages or response_payload.get('status')}"
            raise BlsApiError(msg)

        return BlsResponse(
            source_name="BLS",
            dataset_name="timeseries_data",
            request_url=request_url,
            request_params=payload,
            payload=response_payload,
        )
