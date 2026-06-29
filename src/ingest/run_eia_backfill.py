import argparse

import dotenv

from src.db.session import make_sessionmaker
from src.ingest.eia import ingest_stage4_eia


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Backfill Stage 4 EIA energy series")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    args = parser.parse_args()

    session_factory = make_sessionmaker(args.dsn)
    with session_factory() as session:
        counts = ingest_stage4_eia(session=session)
        session.commit()

    for series_id, count in counts.items():
        print(f"{series_id}: {count} observations")


if __name__ == "__main__":
    main()
