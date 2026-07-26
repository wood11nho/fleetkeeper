from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from fleetkeeper.services import garages
from fleetkeeper.web.dependencies import CurrentUser, DatabaseSession
from fleetkeeper.web.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: DatabaseSession, user: CurrentUser) -> Response:
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "user": user,
            "garages": garages.garages_for(db, user),
            "vehicles": garages.vehicles_for(db, user),
        },
    )
