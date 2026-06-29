import argparse

import dotenv

from src.ingest.bls import ingest_stage4_bls_components
from src.db.session import make_sessionmaker


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Backfill Stage 4 BLS CPI component series")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    parser.add_argument("--observation-start", default="1990-01-01")
    parser.add_argument("--observation-end")
    args = parser.parse_args()

    session_factory = make_sessionmaker(args.dsn)
    with session_factory() as session:
        counts = ingest_stage4_bls_components(
            session=session,
            observation_start=args.observation_start,
            observation_end=args.observation_end,
        )
        session.commit()

    for series_id, count in counts.items():
        print(f"{series_id}: {count} observations")


if __name__ == "__main__":
    main()
