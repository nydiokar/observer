from datetime import datetime, timezone
from pathlib import Path

from src.db.raw_archive import archive_payload, sanitize_request_metadata


def test_sanitize_request_metadata_redacts_secret_like_keys():
    metadata = {
        "series_id": "DFF",
        "api_key": "secret",
        "nested": {"Authorization": "Bearer token", "other": "visible"},
    }

    assert sanitize_request_metadata(metadata) == {
        "series_id": "DFF",
        "api_key": "<redacted>",
        "nested": {"Authorization": "<redacted>", "other": "visible"},
    }


def test_archive_payload_writes_partitioned_file_with_checksum(tmp_path):
    retrieved_at = datetime(2026, 6, 29, 12, 30, tzinfo=timezone.utc)

    archived = archive_payload(
        source_name="FRED",
        dataset_name="observations",
        payload={"value": 1.25, "date": "2026-06-29"},
        response_format="json",
        request_url="https://api.example.test?api_key=secret",
        request_params={"series_id": "DFF", "api_key": "secret"},
        retrieved_at=retrieved_at,
        base_dir=tmp_path,
    )

    assert archived.storage_path.endswith(".json")
    assert "/fred/observations/2026/06/29/" in archived.storage_path
    assert archived.request_url_hash is not None
    assert archived.request_params_json == {"series_id": "DFF", "api_key": "<redacted>"}
    assert len(archived.checksum) == 64
    assert b"2026-06-29" in Path(archived.storage_path).read_bytes()
