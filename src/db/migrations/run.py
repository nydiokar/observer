import argparse
from pathlib import Path

import dotenv

from src.db.session import make_engine

MIGRATIONS_DIR = Path(__file__).resolve().parent


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    dollar_quote = False
    i = 0
    while i < len(sql):
        char = sql[i]
        next_two = sql[i : i + 2]

        if not in_single_quote and next_two == "$$":
            dollar_quote = not dollar_quote
            current.append(next_two)
            i += 2
            continue

        if not dollar_quote and char == "'":
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue

        if char == ";" and not in_single_quote and not dollar_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(char)
        i += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements


def run_migration(sql_file: str, dsn: str | None = None) -> None:
    path = MIGRATIONS_DIR / sql_file
    sql = path.read_text()
    engine = make_engine(dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        for statement in split_sql_statements(sql):
            connection.exec_driver_sql(statement)
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
