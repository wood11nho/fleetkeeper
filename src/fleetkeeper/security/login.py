from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleetkeeper.models.user import User
from fleetkeeper.security.passwords import verify_password

ALLOWED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=15)


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User | None = None
    locked_until: datetime | None = None

    @property
    def succeeded(self) -> bool:
        return self.user is not None


def attempt(session: Session, email: str, password: str) -> LoginResult:
    """Check a set of credentials, counting failures against the account.

    The caller is told only whether it worked, never whether the address exists: "there is
    no such account" is a useful sentence for whoever is guessing.
    """
    user = session.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if user is None:
        # Still spend the time a real check would take, so a missing account cannot be
        # distinguished from a wrong password by how quickly the answer comes back.
        verify_password(password, _DUMMY_HASH)
        return LoginResult()

    now = datetime.now(UTC)
    if user.locked_until is not None and user.locked_until > now:
        return LoginResult(locked_until=user.locked_until)

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= ALLOWED_ATTEMPTS:
            user.locked_until = now + LOCKOUT
            user.failed_login_count = 0
            return LoginResult(locked_until=user.locked_until)
        return LoginResult()

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    return LoginResult(user=user)


# A real bcrypt hash of a value nobody knows, used only to keep the timing of a failed
# lookup similar to that of a wrong password.
_DUMMY_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEe.rXQBjWiTVDdVLbLM7iP3v7BQaWTNP0O"
