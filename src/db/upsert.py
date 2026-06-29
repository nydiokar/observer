from collections.abc import Iterable
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.db.config import load_baskets, load_instruments, load_series_registry
from src.db.models import BasketEntry, InstrumentEntry, SeriesEntry
from src.db.orm import (
    Basket,
    BasketMember,
    Instrument,
    RawPayload,
    SeriesObservation,
    SeriesRegistry,
)

MAX_OBSERVATION_UPSERT_ROWS = 1_000


def _model_dump_json(entry: Any) -> dict[str, Any]:
    if isinstance(entry, BaseModel):
        return entry.model_dump(mode="json")
    return dict(entry)


def _coerce_rows(entries: Any) -> list[dict[str, Any]]:
    if isinstance(entries, BaseModel) or isinstance(entries, dict):
        return [_model_dump_json(entries)]
    return [_model_dump_json(entry) for entry in entries]


def _upsert_by_pk(session: Session, table, rows: list[dict[str, Any]], key_columns: list[str]) -> int:
    if not rows:
        return 0
    statement = insert(table).values(rows)
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in key_columns and column.name != "created_at"
    }
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[getattr(table.c, key) for key in key_columns],
            set_=update_columns,
        )
    )
    return len(rows)


def upsert_series_registry(session: Session, entries: Iterable[SeriesEntry] | SeriesEntry | dict[str, Any]) -> int:
    rows = _coerce_rows(entries)
    return _upsert_by_pk(session, SeriesRegistry.__table__, rows, ["series_id"])


def upsert_instruments(
    session: Session,
    entries: Iterable[InstrumentEntry] | InstrumentEntry | dict[str, Any],
) -> int:
    rows = _coerce_rows(entries)
    return _upsert_by_pk(session, Instrument.__table__, rows, ["ticker"])


def upsert_baskets(session: Session, entries: Iterable[BasketEntry]) -> int:
    entries = list(entries)
    rows = [
        entry.model_dump(mode="json", exclude={"members"})
        for entry in entries
    ]
    count = _upsert_by_pk(session, Basket.__table__, rows, ["name"])
    for entry in entries:
        session.execute(delete(BasketMember).where(BasketMember.basket_name == entry.name))
        member_rows = [
            {"basket_name": entry.name, "ticker": member}
            for member in entry.members
        ]
        if member_rows:
            session.execute(
                insert(BasketMember.__table__)
                .values(member_rows)
                .on_conflict_do_nothing()
            )
    return count


def sync_registry_config(session: Session) -> dict[str, int]:
    instruments = upsert_instruments(session, load_instruments())
    baskets = upsert_baskets(session, load_baskets())
    series = upsert_series_registry(session, load_series_registry())
    return {
        "series_registry": series,
        "instruments": instruments,
        "baskets": baskets,
    }


def upsert_raw_payload_metadata(session: Session, metadata: dict[str, Any]) -> int:
    return _upsert_by_pk(session, RawPayload.__table__, [metadata], ["raw_payload_id"])


def insert_raw_payload(session: Session, metadata: dict[str, Any]) -> int:
    return upsert_raw_payload_metadata(session, metadata)


def _normalize_observation(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    retrieved_at = row["retrieved_at"]
    if isinstance(retrieved_at, str):
        retrieved_at = datetime.fromisoformat(retrieved_at)
        row["retrieved_at"] = retrieved_at
    row.setdefault("retrieved_on", retrieved_at.date())
    row.setdefault("quality_flag", "ok")
    return row


def _upsert_observation_batch(
    session: Session,
    rows: list[dict[str, Any]],
    index_elements: list[str],
    index_where,
) -> int:
    if not rows:
        return 0
    table = SeriesObservation.__table__
    count = 0
    for offset in range(0, len(rows), MAX_OBSERVATION_UPSERT_ROWS):
        batch = rows[offset:offset + MAX_OBSERVATION_UPSERT_ROWS]
        statement = insert(table).values(batch)
        update_columns = {
            column.name: getattr(statement.excluded, column.name)
            for column in table.columns
            if column.name not in {"id", *index_elements}
        }
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[getattr(table.c, key) for key in index_elements],
                index_where=index_where,
                set_=update_columns,
            )
        )
        count += len(batch)
    return count


def upsert_series_observations(
    session: Session,
    rows: Iterable[dict[str, Any]] | dict[str, Any],
    *,
    require_registered: bool = True,
) -> int:
    del require_registered  # Real database sessions enforce this through the FK.
    if isinstance(rows, dict):
        rows = [rows]
    normalized = [_normalize_observation(row) for row in rows]
    vintage_rows = [row for row in normalized if row.get("vintage_date") is not None]
    current_rows = [row for row in normalized if row.get("vintage_date") is None]
    table = SeriesObservation.__table__
    return _upsert_observation_batch(
        session,
        vintage_rows,
        ["series_id", "observation_date", "vintage_date", "source_name"],
        table.c.vintage_date.is_not(None),
    ) + _upsert_observation_batch(
        session,
        current_rows,
        ["series_id", "observation_date", "source_name", "retrieved_on"],
        table.c.vintage_date.is_(None),
    )
