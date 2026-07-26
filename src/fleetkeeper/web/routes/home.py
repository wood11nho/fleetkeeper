from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from fleetkeeper.models.garage import Garage, GarageMember
from fleetkeeper.web.dependencies import CurrentUser, DatabaseSession
from fleetkeeper.web.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: DatabaseSession, user: CurrentUser) -> Response:
    garages = list(
        db.scalars(
            select(Garage)
            .join(GarageMember, GarageMember.garage_id == Garage.id)
            .where(GarageMember.user_id == user.id)
            .order_by(Garage.name)
        )
    )
    return templates.TemplateResponse(
        request,
        "home.html",
        {"user": user, "garages": garages},
    )
