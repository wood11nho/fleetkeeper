from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from fleetkeeper.config import Settings
from fleetkeeper.models.user import User
from fleetkeeper.security import sessions


class NotSignedInError(Exception):
    """Raised by a page that needs a signed-in user, turned into a redirect by a handler.

    A dependency cannot return a response, and raising an HTTP error would show the visitor
    a status code instead of the sign-in form.
    """

    def __init__(self, requested_path: str) -> None:
        self.requested_path = requested_path


def get_session(request: Request) -> Iterator[Session]:
    """A database session from the factory this application was built with.

    Same reasoning as the settings below: an application that resolves its own database
    connection per request behaves differently depending on the environment it happens to be
    answering in.
    """
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session


def get_configuration(request: Request) -> Settings:
    """The settings this application was built with.

    Deliberately not a fresh read of the environment. Doing that during a request means the
    application behaves differently depending on whether a .env file happens to sit in the
    working directory, which is a difference between a developer's machine and a server.
    """
    settings: Settings = request.app.state.settings
    return settings


DatabaseSession = Annotated[Session, Depends(get_session)]
Configuration = Annotated[Settings, Depends(get_configuration)]


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
