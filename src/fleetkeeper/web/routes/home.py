from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fleetkeeper import __version__
from fleetkeeper.web.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html", {"version": __version__})
