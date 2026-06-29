from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from src.db import orm


def latest_series_observation_query(series_id: str) -> Select:
    latest_date = (
        select(func.max(orm.SeriesObservation.observation_date))
        .where(orm.SeriesObservation.series_id == series_id)
        .scalar_subquery()
    )
    return (
        select(orm.SeriesObservation)
        .where(orm.SeriesObservation.series_id == series_id)
        .where(orm.SeriesObservation.observation_date == latest_date)
        .order_by(orm.SeriesObservation.retrieved_at.desc())
        .limit(1)
    )


def get_latest_series_observation(session: Session, series_id: str):
    return session.execute(latest_series_observation_query(series_id)).scalar_one_or_none()


def missing_latest_rows_for_series(session: Session, series_ids: list[str]) -> list[str]:
    if not series_ids:
        return []
    existing = set(
        session.execute(
            select(orm.SeriesObservation.series_id)
            .where(orm.SeriesObservation.series_id.in_(series_ids))
            .group_by(orm.SeriesObservation.series_id)
        ).scalars()
    )
    return [series_id for series_id in series_ids if series_id not in existing]
