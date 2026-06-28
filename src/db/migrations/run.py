import argparse
import os
from pathlib import Path

import dotenv

MIGRATIONS_DIR = Path(__file__).resolve().parent


def run_migration(sql_file: str, dsn: str | None = None) -> None:
    if dsn is None:
        dsn = os.environ.get("DATABASE_URL")
    if dsn is None:
        msg = "DATABASE_URL not set; provide --dsn or set the environment variable"
        raise RuntimeError(msg)

    import psycopg2

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    path = MIGRATIONS_DIR / sql_file
    sql = path.read_text()

    cur.execute(sql)
    cur.close()
    conn.close()
    print(f"Migration {sql_file} applied successfully.")


def main() -> None:
    dotenv.load_dotenv()
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--dsn", help="PostgreSQL DSN (default: $DATABASE_URL)")
    parser.add_argument(
        "--migration",
        default="001_initial_schema.sql",
        help="Migration file name (default: 001_initial_schema.sql)",
    )
    args = parser.parse_args()
    run_migration(args.migration, args.dsn)


if __name__ == "__main__":
    main()
