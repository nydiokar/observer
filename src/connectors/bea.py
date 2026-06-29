import os
from dataclasses import dataclass
from typing import Any

import requests


class BeaConfigError(RuntimeError):
    pass


class BeaApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class BeaResponse:
    source_name: str
    dataset_name: str
    request_url: str
    request_params: dict[str, Any]
    payload: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.payload[key]


def get_bea_api_key(api_key: str | None = None) -> str:
    key = api_key or os.environ.get("BEA_API_KEY")
    if not key:
        msg = "BEA_API_KEY is required for BEA ingestion"
        raise BeaConfigError(msg)
    return key


class BeaClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://apps.bea.gov/api/data",
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = get_bea_api_key(api_key)
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def nipa_table(
        self,
        *,
        table_name: str,
        frequency: str,
        years: list[int] | str,
    ) -> BeaResponse:
        year_value = ",".join(str(year) for year in years) if isinstance(years, list) else years
        params: dict[str, Any] = {
            "UserID": self.api_key,
            "method": "GETDATA",
            "DatasetName": "NIPA",
            "TableName": table_name,
            "Frequency": frequency,
            "Year": year_value,
            "ResultFormat": "JSON",
        }
        response = self.session.get(self.base_url, params=params, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            msg = f"BEA NIPA request failed for {table_name}: HTTP {response.status_code}"
            raise BeaApiError(msg)

        payload = response.json()
        results = payload.get("BEAAPI", {}).get("Results", {})
        if "Error" in results:
            error = results["Error"]
            msg = f"BEA NIPA request failed for {table_name}: {error.get('APIErrorDescription', error)}"
            raise BeaApiError(msg)

        return BeaResponse(
            source_name="BEA",
            dataset_name="nipa_table",
            request_url=self.base_url,
            request_params=params,
            payload=payload,
        )
