"""Who is allowed to see what.

Every query that reaches a garage's data goes through `garage_ids`. Written once and reused,
it cannot be forgotten in one place out of twenty, which is how one family ends up looking at
another family's cars.
"""

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from fleetkeeper.models.garage import Garage, GarageMember
from fleetkeeper.models.user import User
from fleetkeeper.models.vehicle import Vehicle


def garage_ids(user: User) -> Select[tuple[int]]:
    return select(GarageMember.garage_id).where(GarageMember.user_id == user.id)


def garages_for(session: Session, user: User) -> list[Garage]:
    return list(
        session.scalars(select(Garage).where(Garage.id.in_(garage_ids(user))).order_by(Garage.name))
    )


def garage_for(session: Session, user: User, garage_id: int) -> Garage | None:
    return session.scalar(
        select(Garage).where(Garage.id == garage_id, Garage.id.in_(garage_ids(user)))
    )


def vehicles_for(session: Session, user: User) -> list[Vehicle]:
    return list(
        session.scalars(
            select(Vehicle)
            .where(Vehicle.garage_id.in_(garage_ids(user)), Vehicle.is_active)
            .order_by(Vehicle.name)
        )
    )


def vehicle_for(session: Session, user: User, vehicle_id: int) -> Vehicle | None:
    """A vehicle the user may see, or nothing.

    Nothing rather than a refusal on purpose: telling a stranger that a vehicle exists but is
    not theirs is more than they need to know.
    """
    return session.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.garage_id.in_(garage_ids(user)),
        )
    )
