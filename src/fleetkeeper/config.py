from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FLEETKEEPER_",
        extra="ignore",
    )

    app_name: str = "FleetKeeper"
    debug: bool = False

    # All dates shown to the user and all reminder schedules are anchored to
    # Romanian local time, regardless of where the container happens to run.
    timezone: str = "Europe/Bucharest"


@lru_cache
def get_settings() -> Settings:
    return Settings()
