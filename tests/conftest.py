import pytest
from fastapi.testclient import TestClient

from fleetkeeper.config import Settings
from fleetkeeper.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(debug=True)))
