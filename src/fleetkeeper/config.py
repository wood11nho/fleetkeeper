from functools import lru_cache
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DRIVER_SCHEME = "postgresql+psycopg"
_PLAIN_SCHEMES = frozenset({"postgres", "postgresql"})


def _with_psycopg_driver(value: str) -> str:
    scheme, separator, rest = value.partition("://")
    if not separator:
        raise ValueError("expected a URL of the form postgresql://user:password@host/database")
    # Hosting providers hand out plain postgresql:// URLs, which SQLAlchemy resolves to
    # psycopg2. Rewriting the scheme here means whoever edits .env can paste the string
    # verbatim instead of remembering to append the driver.
    if scheme in _PLAIN_SCHEMES:
        return f"{_DRIVER_SCHEME}://{rest}"
    return value


DatabaseUrl = Annotated[str, BeforeValidator(_with_psycopg_driver)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FLEETKEEPER_",
        extra="ignore",
    )

    app_name: str = "FleetKeeper"
    debug: bool = False

    database_url: DatabaseUrl

    # All dates shown to the user and all reminder schedules are anchored to
    # Romanian local time, regardless of where the container happens to run.
    timezone: str = "Europe/Bucharest"


@lru_cache
def get_settings() -> Settings:
    # mypy sees database_url as a missing argument; pydantic-settings fills it from the
    # environment, which the type checker cannot know about.
    return Settings()  # type: ignore[call-arg]
