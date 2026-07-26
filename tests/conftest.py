import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fleetkeeper.config import Settings, get_settings
from fleetkeeper.main import create_app

# Creating an engine does not open a connection, so the tests that only exercise routing
# and rendering need a syntactically valid URL and nothing more.
UNUSED_DATABASE_URL = "postgresql://fleetkeeper:fleetkeeper@localhost:5432/fleetkeeper"


@pytest.fixture(autouse=True)
def without_ambient_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run every test the way the build server does: with nothing to fall back on.

    A .env file sitting in the working directory twice hid code that read its configuration
    from the environment at request time. Both times the suite passed here and failed on the
    server, which is the worst way to find out. Taking the fallback away means the two
    environments cannot drift apart again.
    """
    for name in [name for name in os.environ if name.startswith("FLEETKEEPER_")]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(debug=True, database_url=UNUSED_DATABASE_URL)))
