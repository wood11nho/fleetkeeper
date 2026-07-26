from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from fleetkeeper.security import csrf

WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def _shared_context(request: Request) -> dict[str, Any]:
    # Every page carries a sign-out button, which is a form, which needs a token. Providing
    # it here means no route has to remember to pass it through.
    return {"csrf_token": csrf.token_for(request), "csrf_field": csrf.FIELD_NAME}


templates = Jinja2Templates(directory=TEMPLATES_DIR, context_processors=[_shared_context])
