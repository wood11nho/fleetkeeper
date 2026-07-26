from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from fleetkeeper.models.garage import Garage
from fleetkeeper.models.user import User
from fleetkeeper.models.vehicle import Vehicle
from fleetkeeper.security import csrf
from fleetkeeper.services import garages, vehicles
from fleetkeeper.web import labels
from fleetkeeper.web.dependencies import CurrentUser, DatabaseSession
from fleetkeeper.web.formatting import thousands
from fleetkeeper.web.forms import MileageForm, VehicleForm, parse, previous_values
from fleetkeeper.web.templating import templates

router = APIRouter(prefix="/masini")

EXPIRED_FORM = "Formularul a expirat. Încearcă din nou."
NO_GARAGE = "Alege garajul în care intră mașina."


@router.get("", response_class=HTMLResponse)
def index(request: Request, db: DatabaseSession, user: CurrentUser) -> Response:
    return templates.TemplateResponse(
        request,
        "vehicles/index.html",
        {
            "user": user,
            "vehicles": garages.vehicles_for(db, user),
            "fuel_labels": labels.FUEL_LABELS,
        },
    )


@router.get("/adauga", response_class=HTMLResponse)
def new(request: Request, db: DatabaseSession, user: CurrentUser) -> Response:
    return _form_page(request, db, user, values={}, errors={})


@router.post("/adauga", response_class=HTMLResponse)
async def create(request: Request, db: DatabaseSession, user: CurrentUser) -> Response:
    form = await request.form()

    if not csrf.is_valid(request, str(form.get(csrf.FIELD_NAME, ""))):
        return _form_page(
            request,
            db,
            user,
            previous_values(form, repeated=("equipment",)),
            {},
            notice=EXPIRED_FORM,
        )

    submitted, errors = parse(VehicleForm, form, repeated=("equipment",))
    garage = _chosen_garage(db, user, submitted)
    if garage is None and submitted is not None:
        errors["garage_id"] = NO_GARAGE

    if submitted is None or garage is None:
        return _form_page(request, db, user, previous_values(form, repeated=("equipment",)), errors)

    vehicle = vehicles.create(db, garage, submitted, author=user.id)
    db.commit()

    return RedirectResponse(f"/masini/{vehicle.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{vehicle_id}", response_class=HTMLResponse)
def detail(request: Request, db: DatabaseSession, user: CurrentUser, vehicle_id: int) -> Response:
    return _detail_page(request, db, user, _owned_vehicle(db, user, vehicle_id))


@router.post("/{vehicle_id}/kilometraj", response_class=HTMLResponse)
async def record_odometer(
    request: Request, db: DatabaseSession, user: CurrentUser, vehicle_id: int
) -> Response:
    vehicle = _owned_vehicle(db, user, vehicle_id)
    form = await request.form()

    if not csrf.is_valid(request, str(form.get(csrf.FIELD_NAME, ""))):
        return _detail_page(request, db, user, vehicle, notice=EXPIRED_FORM)

    submitted, errors = parse(MileageForm, form)
    if submitted is None:
        return _detail_page(request, db, user, vehicle, notice=errors.get("mileage_km"))

    try:
        vehicles.record_odometer(
            db,
            vehicle,
            submitted.mileage_km,
            on=submitted.recorded_on or date.today(),
            author=user.id,
        )
    except vehicles.OdometerWentBackwardsError as refused:
        return _detail_page(
            request,
            db,
            user,
            vehicle,
            notice=(
                "Kilometrajul nu poate scădea. Ultima valoare înregistrată este "
                f"{thousands(refused.previous_reading)} km. Dacă s-a schimbat ceasul de bord, "
                "corectează întâi datele mașinii."
            ),
        )

    db.commit()
    return RedirectResponse(f"/masini/{vehicle.id}", status_code=status.HTTP_303_SEE_OTHER)


def _owned_vehicle(db: Session, user: User, vehicle_id: int) -> Vehicle:
    vehicle = garages.vehicle_for(db, user, vehicle_id)
    if vehicle is None:
        # Not a refusal: a stranger has no business learning that this vehicle exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return vehicle


def _chosen_garage(db: Session, user: User, submitted: VehicleForm | None) -> Garage | None:
    if submitted is not None and submitted.garage_id is not None:
        return garages.garage_for(db, user, submitted.garage_id)

    owned = garages.garages_for(db, user)
    return owned[0] if len(owned) == 1 else None


def _form_page(
    request: Request,
    db: Session,
    user: User,
    values: dict[str, Any],
    errors: dict[str, str],
    notice: str | None = None,
) -> Response:
    return templates.TemplateResponse(
        request,
        "vehicles/new.html",
        {
            "user": user,
            "garages": garages.garages_for(db, user),
            "values": values,
            "errors": errors,
            "notice": notice,
            "fuel_types": labels.FUEL_TYPES,
            "gearbox_types": labels.GEARBOX_TYPES,
            "drivetrains": labels.DRIVETRAINS,
            "equipment": labels.EQUIPMENT,
        },
        status_code=status.HTTP_400_BAD_REQUEST if (errors or notice) else status.HTTP_200_OK,
    )


def _detail_page(
    request: Request,
    db: Session,
    user: User,
    vehicle: Vehicle,
    notice: str | None = None,
) -> Response:
    return templates.TemplateResponse(
        request,
        "vehicles/detail.html",
        {
            "user": user,
            "vehicle": vehicle,
            "sections": vehicles.rules_by_section(db, vehicle),
            "today": date.today().isoformat(),
            "notice": notice,
            "fuel_labels": labels.FUEL_LABELS,
            "gearbox_labels": labels.GEARBOX_LABELS,
            "drivetrain_labels": labels.DRIVETRAIN_LABELS,
            "equipment_labels": labels.EQUIPMENT_LABELS,
            "section_labels": labels.SECTION_LABELS,
            "source_labels": labels.INTERVAL_SOURCE_LABELS,
        },
        status_code=status.HTTP_400_BAD_REQUEST if notice else status.HTTP_200_OK,
    )
