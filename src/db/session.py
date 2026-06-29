import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def get_database_url(database_url: str | None = None) -> str:
    if database_url:
        return normalize_database_url(database_url)
    env_url = os.environ.get("DATABASE_URL")
    if not env_url:
        msg = "DATABASE_URL not set; provide a database URL or set the environment variable"
        raise RuntimeError(msg)
    return normalize_database_url(env_url)


def make_engine(database_url: str | None = None, **kwargs) -> Engine:
    return create_engine(get_database_url(database_url), future=True, **kwargs)


def make_sessionmaker(database_url: str | None = None, **kwargs) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url, **kwargs), expire_on_commit=False)


@contextmanager
def session_scope(database_url: str | None = None) -> Generator[Session, None, None]:
    session_factory = make_sessionmaker(database_url)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
