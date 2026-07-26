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


def create_session_factory(url: str) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_database_engine(url),
        autoflush=False,
        expire_on_commit=False,
    )


# Below is for the command line tools and for Alembic, which legitimately have nothing but
# the environment to go on. The web application never uses these: it is handed its settings
# when it is built and keeps its own session factory, so that answering a request never
# depends on what happens to be in the environment at the time.
@lru_cache
def get_engine() -> Engine:
    return create_database_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
