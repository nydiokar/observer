import argparse
from dataclasses import dataclass
from datetime import date

import dotenv
from sqlalchemy.orm import Session

from src.db.models import SeriesEntry
from src.db.queries import get_latest_series_observation
from src.db.session import make_sessionmaker
from src.ingest.fred import stage3_fred_series
from src.transforms.quality_flags import latest_observation_quality_flag


@dataclass(frozen=True)
class Stage3SeriesStatus:
    series_id: str
    latest_date: date | None
    quality_flag: str


def latest_status_for_series(
    *,
    series: SeriesEntry,
    latest_observation_date: date | None,
    as_of_date: date,
) -> Stage3SeriesStatus:
    return Stage3SeriesStatus(
        series_id=series.series_id,
        latest_date=latest_observation_date,
        quality_flag=latest_observation_quality_flag(
            observation_date=latest_observation_date,
            as_of_date=as_of_date,
            frequency=series.frequency,
        ),
    )


def verify_stage3_fred(session: Session, *, as_of_date: date) -> list[Stage3SeriesStatus]:
    statuses: list[Stage3SeriesStatus] = []
    for series in stage3_fred_series():
        latest = get_latest_series_observation(session, series.series_id)
        statuses.append(
            latest_status_for_series(
                series=series,
                latest_observation_date=latest.observation_date if latest else None,
                as_of_date=as_of_date,
            )
        )
    return statuses


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Verify Stage 3 FRED backbone data coverage")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument(
        "--strict-freshness",
        action="store_true",
        help="Exit nonzero when latest observations are stale for their configured frequency",
    )
    args = parser.parse_args()

    session_factory = make_sessionmaker(args.dsn)
    with session_factory() as session:
        statuses = verify_stage3_fred(session, as_of_date=args.as_of)

    for status in statuses:
        latest_date = status.latest_date.isoformat() if status.latest_date else "missing"
        print(f"{status.series_id}: latest={latest_date} quality={status.quality_flag}")

    missing = [status.series_id for status in statuses if status.quality_flag == "missing"]
    stale = [status.series_id for status in statuses if status.quality_flag == "stale"]
    if missing:
        parser.exit(2, f"Missing Stage 3 observations: {', '.join(missing)}\n")
    if args.strict_freshness and stale:
        parser.exit(3, f"Stale Stage 3 observations: {', '.join(stale)}\n")


if __name__ == "__main__":
    main()
