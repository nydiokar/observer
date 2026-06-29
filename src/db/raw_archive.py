import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.db.upsert import insert_raw_payload

SECRET_KEY_RE = re.compile(
    "(api[_-]?key|token|secret|password|authorization|auth|user[_-]?id|userid)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ArchivedPayload:
    raw_payload_id: str
    source_name: str
    dataset_name: str
    retrieved_at: datetime
    request_url_hash: str | None
    request_params_json: dict[str, Any] | None
    response_format: str
    storage_path: str
    checksum: str
    status: str = "success"

    def db_row(self) -> dict[str, Any]:
        return {
            "raw_payload_id": self.raw_payload_id,
            "source_name": self.source_name,
            "dataset_name": self.dataset_name,
            "retrieved_at": self.retrieved_at,
            "request_url_hash": self.request_url_hash,
            "request_params_json": self.request_params_json,
            "response_format": self.response_format,
            "storage_path": self.storage_path,
            "checksum": self.checksum,
            "status": self.status,
        }


def raw_data_dir(path: str | Path | None = None) -> Path:
    return Path(path or os.environ.get("RAW_DATA_DIR", "./data/raw"))


def sanitize_request_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, nested in value.items():
            if SECRET_KEY_RE.search(str(key)):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = sanitize_request_metadata(nested)
        return sanitized
    if isinstance(value, list):
        return [sanitize_request_metadata(item) for item in value]
    return value


def sanitize_request_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    return sanitize_request_metadata(params) if params is not None else None


def safe_path_component(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "_", value)
    return value.strip("._") or "unknown"


def request_url_hash(url: str | None) -> str | None:
    if not url:
        return None
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def payload_bytes(payload: bytes | str | dict[str, Any] | list[Any]) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_raw_payload_id(
    *,
    source_name: str,
    dataset_name: str,
    retrieved_at: datetime,
    checksum: str,
) -> str:
    seed = f"{source_name}:{dataset_name}:{retrieved_at.isoformat()}:{checksum}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def archive_payload(
    *,
    source_name: str,
    dataset_name: str,
    payload: bytes | str | dict[str, Any] | list[Any],
    response_format: str,
    request_url: str | None = None,
    request_params: dict[str, Any] | None = None,
    retrieved_at: datetime | None = None,
    status: str = "success",
    base_dir: str | Path | None = None,
) -> ArchivedPayload:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)
    content = payload_bytes(payload)
    checksum = hashlib.sha256(content).hexdigest()
    payload_id = build_raw_payload_id(
        source_name=source_name,
        dataset_name=dataset_name,
        retrieved_at=retrieved_at,
        checksum=checksum,
    )
    extension = safe_path_component(response_format).lstrip(".")
    partition = (
        Path(safe_path_component(source_name))
        / safe_path_component(dataset_name)
        / f"{retrieved_at:%Y}"
        / f"{retrieved_at:%m}"
        / f"{retrieved_at:%d}"
    )
    directory = raw_data_dir(base_dir) / partition
    directory.mkdir(parents=True, exist_ok=True)

    filename = f"{retrieved_at:%Y%m%dT%H%M%SZ}_{checksum[:16]}.{extension}"
    path = directory / filename
    path.write_bytes(content)

    return ArchivedPayload(
        raw_payload_id=payload_id,
        source_name=source_name,
        dataset_name=dataset_name,
        retrieved_at=retrieved_at,
        request_url_hash=request_url_hash(request_url),
        request_params_json=sanitize_request_params(request_params),
        response_format=response_format,
        storage_path=str(path),
        checksum=checksum,
        status=status,
    )


def archive_and_record_payload(session: Session, **kwargs) -> int:
    archived = archive_payload(**kwargs)
    return insert_raw_payload(session, archived.db_row())


def archive_raw_payload(*, session: Session | None = None, raw_data_dir: str | Path | None = None, **kwargs):
    archived = archive_payload(base_dir=raw_data_dir, **kwargs)
    if session is not None:
        insert_raw_payload(session, archived.db_row())
    return archived
