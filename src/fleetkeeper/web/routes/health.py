from fastapi import APIRouter
from pydantic import BaseModel

from fleetkeeper import __version__

router = APIRouter(tags=["monitoring"])


class HealthStatus(BaseModel):
    status: str
    version: str


@router.get("/health")
def health() -> HealthStatus:
    return HealthStatus(status="ok", version=__version__)
