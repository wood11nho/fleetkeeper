import pytest
from fastapi.testclient import TestClient

from fleetkeeper.config import Settings
from fleetkeeper.main import create_app

# Creating an engine does not open a connection, so the tests that only exercise routing
# and rendering need a syntactically valid URL and nothing more.
UNUSED_DATABASE_URL = "postgresql://fleetkeeper:fleetkeeper@localhost:5432/fleetkeeper"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(debug=True, database_url=UNUSED_DATABASE_URL)))
