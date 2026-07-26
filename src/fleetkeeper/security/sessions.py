import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fleetkeeper.models.session import UserSession
from fleetkeeper.models.user import User

COOKIE_NAME = "fleetkeeper_session"

REMEMBERED_LIFETIME = timedelta(days=30)
BROWSER_LIFETIME = timedelta(hours=12)


def start(session: Session, user: User, *, remember: bool, user_agent: str | None) -> str:
    """Open a session and return the token to hand to the browser.

    The token is returned rather than stored anywhere retrievable: from this point on only
    its digest exists on the server.
    """
    token = secrets.token_urlsafe(32)
    lifetime = REMEMBERED_LIFETIME if remember else BROWSER_LIFETIME

    session.add(
        UserSession(
            user_id=user.id,
            token_digest=_digest(token),
            expires_at=datetime.now(UTC) + lifetime,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    return token


def authenticate(session: Session, token: str) -> User | None:
    record = session.scalar(
        select(UserSession).where(
            UserSession.token_digest == _digest(token),
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    if record is None:
        return None

    record.last_seen_at = datetime.now(UTC)
    return record.user


def end(session: Session, token: str) -> None:
    session.execute(delete(UserSession).where(UserSession.token_digest == _digest(token)))


def _digest(token: str) -> str:
    # A session token is 256 bits of randomness, so a plain digest is the right tool here.
    # bcrypt exists to make weak, guessable secrets expensive to attack; using it on every
    # request to protect a value nobody can guess would only add latency.
    return hashlib.sha256(token.encode()).hexdigest()
