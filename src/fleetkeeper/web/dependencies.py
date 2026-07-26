from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from fleetkeeper.config import Settings, get_settings
from fleetkeeper.database import get_session
from fleetkeeper.models.user import User
from fleetkeeper.security import sessions


class NotSignedInError(Exception):
    """Raised by a page that needs a signed-in user, turned into a redirect by a handler.

    A dependency cannot return a response, and raising an HTTP error would show the visitor
    a status code instead of the sign-in form.
    """

    def __init__(self, requested_path: str) -> None:
        self.requested_path = requested_path


DatabaseSession = Annotated[Session, Depends(get_session)]
Configuration = Annotated[Settings, Depends(get_settings)]


def signed_in_user(request: Request, db: DatabaseSession) -> User | None:
    token = request.cookies.get(sessions.COOKIE_NAME)
    if not token:
        return None
    return sessions.authenticate(db, token)


def require_user(request: Request, user: Annotated[User | None, Depends(signed_in_user)]) -> User:
    if user is None:
        raise NotSignedInError(request.url.path)
    return user


CurrentUser = Annotated[User, Depends(require_user)]
MaybeUser = Annotated[User | None, Depends(signed_in_user)]
