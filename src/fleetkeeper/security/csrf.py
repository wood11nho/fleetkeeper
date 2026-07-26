"""Cross-site request forgery protection, by the double submit cookie method.

A random value is placed both in a cookie and in a hidden form field, and a request is only
accepted when the two match. Another site can make your browser send a request carrying your
cookies, but it cannot read them, so it cannot put the matching value in the form.

This holds no server state, which matters for the sign-in form: there is no session to keep
a token in yet.
"""

import secrets

from fastapi import Request, Response

COOKIE_NAME = "fleetkeeper_csrf"
FIELD_NAME = "csrf_token"

# Long enough that it outlives a remembered sign-in, so the sign-out button on a browser
# reopened three weeks later still works.
LIFETIME_SECONDS = 60 * 60 * 24 * 60


def token_for(request: Request) -> str:
    """The token for this request, reusing the visitor's cookie when there is one.

    A freshly minted token is remembered on the request so that the template and the cookie
    end up with the same value; minting twice would guarantee a mismatch on the first ever
    form submission.
    """
    from_cookie = request.cookies.get(COOKIE_NAME)
    if from_cookie:
        return from_cookie

    minted: str | None = getattr(request.state, "csrf_token", None)
    if minted is None:
        minted = secrets.token_urlsafe(32)
        request.state.csrf_token = minted
    return minted


def attach(response: Response, token: str, *, secure: bool) -> None:
    # The template writes the token into the form, so nothing on the page needs to read the
    # cookie and it may as well be closed to scripts.
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=LIFETIME_SECONDS,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def is_valid(request: Request, submitted: str | None) -> bool:
    expected = request.cookies.get(COOKIE_NAME)
    if not expected or not submitted:
        return False
    return secrets.compare_digest(expected, submitted)
