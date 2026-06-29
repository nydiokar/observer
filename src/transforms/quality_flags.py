from datetime import date, timedelta

from src.db.models import Frequency


MAX_AGE_BY_FREQUENCY = {
    Frequency.daily: timedelta(days=5),
    Frequency.weekly: timedelta(days=14),
    Frequency.monthly: timedelta(days=45),
    Frequency.quarterly: timedelta(days=110),
    Frequency.annual: timedelta(days=400),
    Frequency.irregular: timedelta(days=45),
}


def is_stale_latest_observation(
    *,
    observation_date: date,
    as_of_date: date,
    frequency: Frequency,
) -> bool:
    max_age = MAX_AGE_BY_FREQUENCY[frequency]
    return as_of_date - observation_date > max_age


def latest_observation_quality_flag(
    *,
    observation_date: date | None,
    as_of_date: date,
    frequency: Frequency,
) -> str:
    if observation_date is None:
        return "missing"
    if is_stale_latest_observation(
        observation_date=observation_date,
        as_of_date=as_of_date,
        frequency=frequency,
    ):
        return "stale"
    return "ok"


def staleness_flag(
    *,
    observation_date: date | None,
    frequency: Frequency | str,
    as_of: date | None = None,
) -> str:
    as_of = as_of or date.today()
    if isinstance(frequency, str):
        frequency = Frequency(frequency)
    return latest_observation_quality_flag(
        observation_date=observation_date,
        as_of_date=as_of,
        frequency=frequency,
    )
