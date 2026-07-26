from collections.abc import Awaitable, Callable
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from fleetkeeper import __version__
from fleetkeeper.config import Settings, get_settings
from fleetkeeper.database import create_session_factory
from fleetkeeper.security import csrf
from fleetkeeper.web.dependencies import NotSignedInError
from fleetkeeper.web.routes import auth, health, home
from fleetkeeper.web.templating import STATIC_DIR


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application.

    Deliberately a function rather than a module-level instance: importing this module must
    not require a configured environment, or the test suite and every tool that merely
    inspects the code would need a database URL to be present. Uvicorn is pointed at this
    factory with --factory.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )

    # Routes read their configuration and their database from here rather than resolving
    # either one per request, so an application answers exactly as it was built, wherever it
    # happens to be running. Building an engine opens no connection.
    app.state.settings = settings
    app.state.session_factory = create_session_factory(settings.database_url)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(home.router)

    @app.middleware("http")
    async def ensure_csrf_cookie(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if csrf.COOKIE_NAME not in request.cookies:
            csrf.attach(response, csrf.token_for(request), secure=settings.secure_cookies)
        return response

    @app.exception_handler(NotSignedInError)
    def show_sign_in_form(request: Request, exception: Exception) -> Response:
        requested = (
            exception.requested_path if isinstance(exception, NotSignedInError) else auth.HOME_PATH
        )
        return RedirectResponse(
            f"{auth.SIGN_IN_PATH}?next={quote(requested)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return app
