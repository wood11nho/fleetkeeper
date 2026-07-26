"""Route level checks for the paths that must hold even before a database exists.

Every request below stops short of a query, which is what makes them runnable anywhere: a
missing cookie is answered from the cookie alone, and a bad token is rejected before any
account is looked up.
"""

from fastapi.testclient import TestClient

from fleetkeeper.security import csrf
from fleetkeeper.web.routes.auth import HOME_PATH, SIGN_IN_PATH, _safe_destination


def test_the_sign_in_page_offers_a_form_and_a_token(client: TestClient) -> None:
    response = client.get(SIGN_IN_PATH)

    assert response.status_code == 200
    assert 'name="password"' in response.text
    assert csrf.COOKIE_NAME in response.cookies


def test_the_token_in_the_form_matches_the_one_in_the_cookie(client: TestClient) -> None:
    """The two halves of the double submit have to agree on the very first attempt."""
    response = client.get(SIGN_IN_PATH)

    assert f'value="{response.cookies[csrf.COOKIE_NAME]}"' in response.text


def test_a_signed_out_visitor_is_sent_to_the_form(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == f"{SIGN_IN_PATH}?next=/"


def test_signing_in_without_a_token_is_refused(client: TestClient) -> None:
    response = client.post(
        SIGN_IN_PATH,
        data={"email": "eu@example.com", "password": "parola-mea-secreta"},
    )

    assert response.status_code == 400


def test_a_token_from_somewhere_else_is_refused(client: TestClient) -> None:
    client.get(SIGN_IN_PATH)

    response = client.post(
        SIGN_IN_PATH,
        data={
            "email": "eu@example.com",
            "password": "parola-mea-secreta",
            csrf.FIELD_NAME: "un-token-inventat",
        },
    )

    assert response.status_code == 400


def test_the_health_endpoint_stays_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_only_local_destinations_survive() -> None:
    assert _safe_destination("/masini/3") == "/masini/3"
    assert _safe_destination("https://example.com") == HOME_PATH
    assert _safe_destination("//example.com") == HOME_PATH
    assert _safe_destination("") == HOME_PATH
