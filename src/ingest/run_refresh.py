import argparse

import dotenv

from src.connectors.fred import FredConfigError
from src.db.session import make_sessionmaker
from src.db.upsert import sync_registry_config
from src.ingest.fred import ingest_stage3_fred_backbone


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Refresh latest Stage 3 FRED macro backbone")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    parser.add_argument("--lookback-start", default="2020-01-01")
    args = parser.parse_args()

    session_factory = make_sessionmaker(args.dsn)
    with session_factory.begin() as session:
        sync_registry_config(session)
        try:
            counts = ingest_stage3_fred_backbone(
                session=session,
                observation_start=args.lookback_start,
            )
        except FredConfigError as exc:
            parser.error(str(exc))

    for series_id, count in counts.items():
        print(f"{series_id}: {count} observations")


if __name__ == "__main__":
    main()
