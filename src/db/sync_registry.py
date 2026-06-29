import argparse

import dotenv

from src.db.session import make_sessionmaker
from src.db.upsert import sync_registry_config


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Sync YAML registry config into PostgreSQL")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    args = parser.parse_args()

    session_factory = make_sessionmaker(args.dsn)
    with session_factory.begin() as session:
        counts = sync_registry_config(session)

    print(
        "Registry sync complete: "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
    )


if __name__ == "__main__":
    main()
