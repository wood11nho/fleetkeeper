from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy.orm import Session

from fleetkeeper.models.user import User
from fleetkeeper.security import login
from fleetkeeper.security.passwords import hash_password

PASSWORD = "parola-mea-secreta"


class SingleUserLookup:
    """Stands in for a database session that holds at most one account.

    login.attempt only ever runs one query, so a stub is honest here and keeps the lockout
    rules testable without a database.
    """

    def __init__(self, user: User | None) -> None:
        self._user = user

    def scalar(self, statement: object) -> User | None:
        return self._user


def make_user(**overrides: object) -> User:
    defaults: dict[str, object] = {
        "email": "eu@example.com",
        "full_name": "Utilizator Test",
        "password_hash": hash_password(PASSWORD),
        "failed_login_count": 0,
        "locked_until": None,
        "last_login_at": None,
    }
    return User(**(defaults | overrides))


def attempt(user: User | None, password: str) -> login.LoginResult:
    return login.attempt(cast(Session, SingleUserLookup(user)), "eu@example.com", password)


def test_the_right_password_signs_you_in() -> None:
    user = make_user()

    result = attempt(user, PASSWORD)

    assert result.succeeded
    assert result.user is user
    assert user.last_login_at is not None


def test_an_unknown_address_reports_the_same_failure_as_a_wrong_password() -> None:
    assert not attempt(None, PASSWORD).succeeded
    assert not attempt(make_user(), "greșit").succeeded


def test_failures_accumulate() -> None:
    user = make_user()

    attempt(user, "greșit")
    attempt(user, "greșit")

    assert user.failed_login_count == 2
    assert user.locked_until is None


def test_the_account_locks_after_the_allowed_number_of_attempts() -> None:
    user = make_user()

    for _ in range(login.ALLOWED_ATTEMPTS - 1):
        assert attempt(user, "greșit").locked_until is None

    result = attempt(user, "greșit")

    assert result.locked_until is not None
    assert not result.succeeded


def test_a_locked_account_is_refused_even_with_the_right_password() -> None:
    locked_until = datetime.now(UTC) + timedelta(minutes=5)
    user = make_user(locked_until=locked_until)

    result = attempt(user, PASSWORD)

    assert not result.succeeded
    assert result.locked_until == locked_until


def test_a_lock_that_has_expired_no_longer_blocks() -> None:
    user = make_user(locked_until=datetime.now(UTC) - timedelta(minutes=1))

    assert attempt(user, PASSWORD).succeeded


def test_signing_in_clears_earlier_failures() -> None:
    user = make_user(failed_login_count=3)

    attempt(user, PASSWORD)

    assert user.failed_login_count == 0
    assert user.locked_until is None
