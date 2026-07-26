from typing import Annotated

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from fleetkeeper.security import csrf, login, sessions
from fleetkeeper.web.dependencies import Configuration, DatabaseSession, MaybeUser
from fleetkeeper.web.templating import templates

router = APIRouter()

SIGN_IN_PATH = "/autentificare"
HOME_PATH = "/"

WRONG_CREDENTIALS = "Adresa de email sau parola nu sunt corecte."
EXPIRED_FORM = "Formularul a expirat. Încearcă din nou."


@router.get(SIGN_IN_PATH, response_class=HTMLResponse)
def sign_in_form(request: Request, user: MaybeUser, next: str = HOME_PATH) -> Response:
    if user is not None:
        return RedirectResponse(HOME_PATH, status_code=status.HTTP_303_SEE_OTHER)

    return _sign_in_page(request, _safe_destination(next))


@router.post(SIGN_IN_PATH, response_class=HTMLResponse)
def sign_in(
    request: Request,
    db: DatabaseSession,
    settings: Configuration,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    csrf_token: Annotated[str, Form()] = "",
    remember: Annotated[bool, Form()] = False,
    next: Annotated[str, Form()] = HOME_PATH,
) -> Response:
    destination = _safe_destination(next)

    if not csrf.is_valid(request, csrf_token):
        return _sign_in_page(request, destination, error=EXPIRED_FORM, email=email)

    result = login.attempt(db, email, password)
    db.commit()

    if result.locked_until is not None:
        return _sign_in_page(request, destination, error=_lockout_message(), email=email)

    if result.user is None:
        return _sign_in_page(request, destination, error=WRONG_CREDENTIALS, email=email)

    token = sessions.start(
        db,
        result.user,
        remember=remember,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    response = RedirectResponse(destination, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        sessions.COOKIE_NAME,
        token,
        # Without max_age the cookie dies with the browser session, which is exactly what
        # someone who did not tick "remember me" asked for.
        max_age=int(sessions.REMEMBERED_LIFETIME.total_seconds()) if remember else None,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
        path="/",
    )
    return response


@router.post("/iesire")
def sign_out(
    request: Request, db: DatabaseSession, csrf_token: Annotated[str, Form()] = ""
) -> Response:
    if csrf.is_valid(request, csrf_token):
        token = request.cookies.get(sessions.COOKIE_NAME)
        if token:
            sessions.end(db, token)
            db.commit()

    response = RedirectResponse(SIGN_IN_PATH, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(sessions.COOKIE_NAME, path="/")
    return response


def _sign_in_page(
    request: Request,
    destination: str,
    *,
    error: str | None = None,
    email: str = "",
) -> Response:
    return templates.TemplateResponse(
        request,
        "auth/sign_in.html",
        {"next": destination, "error": error, "email": email},
        status_code=status.HTTP_400_BAD_REQUEST if error else status.HTTP_200_OK,
    )


def _lockout_message() -> str:
    minutes = int(login.LOCKOUT.total_seconds() // 60)
    return (
        f"Prea multe încercări greșite. Contul este blocat pentru {minutes} de minute, "
        "apoi poți încerca din nou."
    )


def _safe_destination(candidate: str) -> str:
    """Only allow redirects back into this site.

    Without this, a link carrying ?next=https://example.com would land someone on a copy of
    the sign-in page right after a genuine sign-in.
    """
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return HOME_PATH
