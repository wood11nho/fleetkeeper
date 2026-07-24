from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from fleetkeeper import __version__
from fleetkeeper.config import Settings, get_settings
from fleetkeeper.web.routes import health, home
from fleetkeeper.web.templating import STATIC_DIR


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(health.router)
    app.include_router(home.router)

    return app


app = create_app()
