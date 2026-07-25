from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

from fleetkeeper.config import get_settings
from fleetkeeper.database import create_database_engine
from fleetkeeper.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure_and_run(connection: Connection | None = None, url: str | None = None) -> None:
    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        # Without these two, a widened column or a changed default is silently ignored by
        # autogenerate and the models quietly drift away from the real schema.
        compare_type=True,
        compare_server_default=True,
        literal_binds=url is not None,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    _configure_and_run(url=get_settings().database_url)
else:
    engine = create_database_engine(get_settings().database_url)
    try:
        with engine.connect() as connection:
            _configure_and_run(connection=connection)
    finally:
        engine.dispose()
