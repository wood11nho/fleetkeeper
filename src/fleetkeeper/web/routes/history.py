from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleetkeeper import odometer
from fleetkeeper.inputs import ServiceEventInput
from fleetkeeper.models.maintenance import ServiceEvent
from fleetkeeper.models.user import User
from fleetkeeper.models.vehicle import Vehicle
from fleetkeeper.schedule import Reading
from fleetkeeper.security import csrf
from fleetkeeper.services import garages, history, vehicles
from fleetkeeper.web import labels
from fleetkeeper.web.dependencies import CurrentUser, DatabaseSession
from fleetkeeper.web.formatting import day, thousands
from fleetkeeper.web.forms import PART_ROWS, parse, parse_parts, previous_values
from fleetkeeper.web.templating import templates

router = APIRouter(prefix="/masini/{vehicle_id}/istoric")

EXPIRED_FORM = "Formularul a expirat. Încearcă din nou."


@router.get("", response_class=HTMLResponse)
def index(
    request: Request,
    db: DatabaseSession,
    user: CurrentUser,
    vehicle_id: int,
    categorie: int | None = None,
    an: int | None = None,
) -> Response:
    vehicle = _owned_vehicle(db, user, vehicle_id)
    counted, spent = history.total_spent(db, vehicle)

    return templates.TemplateResponse(
        request,
        "history/index.html",
        {
            "user": user,
            "vehicle": vehicle,
            "events": history.for_vehicle(db, vehicle, category_id=categorie, year=an),
            "categories": history.loggable_categories(db, vehicle),
            "years": history.recorded_years(db, vehicle),
            "chosen_category": categorie,
            "chosen_year": an,
            "counted": counted,
            "spent": spent,
            "section_labels": labels.SECTION_LABELS,
        },
    )


@router.get("/adauga", response_class=HTMLResponse)
def new(
    request: Request,
    db: DatabaseSession,
    user: CurrentUser,
    vehicle_id: int,
    categorie: int | None = None,
) -> Response:
    vehicle = _owned_vehicle(db, user, vehicle_id)
    prefilled: dict[str, Any] = {"performed_on": date.today().isoformat()}
    if categorie is not None:
        prefilled["category_id"] = str(categorie)

    return _form_page(request, db, user, vehicle, prefilled, {})


@router.post("/adauga", response_class=HTMLResponse)
async def create(
    request: Request, db: DatabaseSession, user: CurrentUser, vehicle_id: int
) -> Response:
    vehicle = _owned_vehicle(db, user, vehicle_id)
    form = await request.form()
    typed = previous_values(form)

    if not csrf.is_valid(request, str(form.get(csrf.FIELD_NAME, ""))):
        return _form_page(request, db, user, vehicle, typed, {}, notice=EXPIRED_FORM)

    submitted, errors = parse(ServiceEventInput, form)
    parts, part_problems = parse_parts(form)
    errors |= part_problems

    if submitted is None or errors:
        return _form_page(request, db, user, vehicle, typed, errors)

    if not _category_is_available(db, vehicle, submitted.category_id):
        errors["category_id"] = "Alege o operațiune din listă."
        return _form_page(request, db, user, vehicle, typed, errors)

    if submitted.mileage_km is not None:
        ruled_out = vehicles.impossible_mileage(
            db, vehicle, submitted.mileage_km, on=submitted.performed_on
        )
        if ruled_out is not None:
            errors["mileage_km"] = _impossible_mileage(ruled_out)
            return _form_page(request, db, user, vehicle, typed, errors)

    history.record(db, vehicle, submitted, parts, author=user.id)
    db.commit()

    return RedirectResponse(f"/masini/{vehicle.id}/istoric", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{event_id}/sterge")
async def remove(
    request: Request, db: DatabaseSession, user: CurrentUser, vehicle_id: int, event_id: int
) -> Response:
    vehicle = _owned_vehicle(db, user, vehicle_id)
    form = await request.form()

    if csrf.is_valid(request, str(form.get(csrf.FIELD_NAME, ""))):
        event = db.scalar(
            select(ServiceEvent).where(
                ServiceEvent.id == event_id,
                ServiceEvent.vehicle_id == vehicle.id,
            )
        )
        if event is not None:
            history.remove(db, event)
            db.commit()

    return RedirectResponse(f"/masini/{vehicle.id}/istoric", status_code=status.HTTP_303_SEE_OTHER)


def _owned_vehicle(db: Session, user: User, vehicle_id: int) -> Vehicle:
    vehicle = garages.vehicle_for(db, user, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return vehicle


def _last_reading(db: Session, vehicle: Vehicle) -> Reading | None:
    """The most recent odometer figure, shown as a hint under the mileage field.

    The field itself is left empty rather than filled in with it. A form that arrives carrying
    today's odometer looks right for something that happened today and quietly wrong for a visit
    from February, since the date can be changed and the number cannot follow it without
    JavaScript. Worse, a figure that was estimated then becomes a figure somebody typed, which is
    how an estimate loses the label that made it honest.
    """
    readings = vehicles.readings_for(db, vehicle)
    return readings[-1] if readings else None


def _impossible_mileage(ruled_out: odometer.Bracket) -> str:
    """Name the readings that rule the figure out, and the day each was taken.

    Refusing without saying why would look like fussiness. Naming the two readings turns it into
    something checkable: the owner can see which one is wrong, and correct that one instead.
    """
    bounds = [
        f"pe {day(reading.on)} erau {thousands(reading.kilometres)} km"
        for reading in (ruled_out.at_least, ruled_out.at_most)
        if reading is not None
    ]
    return (
        "Kilometrajul scris nu se potrivește cu ce știm: "
        + ", iar ".join(bounds)
        + ". Verifică cifra, sau lasă câmpul gol și o estimăm noi."
    )


def _category_is_available(db: Session, vehicle: Vehicle, category_id: int) -> bool:
    """A category has to be one this garage may use.

    Otherwise a hand-made request could attach an intervention to another garage's own category,
    which would then show up in their history.
    """
    return any(category.id == category_id for category in history.loggable_categories(db, vehicle))


def _form_page(
    request: Request,
    db: Session,
    user: User,
    vehicle: Vehicle,
    values: dict[str, Any],
    errors: dict[str, str],
    notice: str | None = None,
) -> Response:
    return templates.TemplateResponse(
        request,
        "history/new.html",
        {
            "user": user,
            "vehicle": vehicle,
            "categories": history.loggable_categories(db, vehicle),
            "suggestions": history.suggestions(db, vehicle.garage_id),
            "part_rows": range(PART_ROWS),
            "last_reading": _last_reading(db, vehicle),
            "values": values,
            "errors": errors,
            "notice": notice,
            "today": date.today().isoformat(),
            "section_labels": labels.SECTION_LABELS,
        },
        status_code=status.HTTP_400_BAD_REQUEST if (errors or notice) else status.HTTP_200_OK,
    )
