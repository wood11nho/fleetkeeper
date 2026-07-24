from fastapi.testclient import TestClient

from fleetkeeper import __version__


def test_health_reports_running_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_home_page_renders(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'lang="ro"' in response.text
