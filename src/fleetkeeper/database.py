from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from fleetkeeper.config import get_settings


def create_database_engine(url: str) -> Engine:
    return create_engine(
        url,
        # Neon suspends the compute after a few minutes of inactivity, which leaves
        # dead connections in the pool. Checking one out is cheap; discovering it is
        # broken halfway through a request is not.
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
    )


@lru_cache
def get_engine() -> Engine:
    return create_database_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session
