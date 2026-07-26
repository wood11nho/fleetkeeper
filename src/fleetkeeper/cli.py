"""Administrative commands, kept out of the web application.

Reference data is deliberately loaded from here rather than from a migration: a migration
that imports application code breaks the moment that code moves on, while this command can
be re-run against any environment at any version.
"""

import argparse
import sys
from collections.abc import Callable
from getpass import getpass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleetkeeper.catalog import sync_builtin_categories
from fleetkeeper.database import get_session_factory
from fleetkeeper.models.garage import Garage, GarageMember
from fleetkeeper.models.user import User
from fleetkeeper.security.passwords import (
    PasswordRejectedError,
    describe_requirements,
    hash_password,
)


def sync_catalog() -> int:
    with get_session_factory()() as session:
        result = sync_builtin_categories(session)
        session.commit()

    print(f"catalogue synchronised: {result.created} created, {result.updated} updated")
    if result.retired:
        print(f"no longer defined in code, left in place: {', '.join(result.retired)}")
    return 0


def create_user() -> int:
    """Create an account and put it in a garage.

    Interactive on purpose: a password passed as a command line argument ends up in the shell
    history and in the process list.
    """
    print("Cont nou în FleetKeeper.")
    print(describe_requirements())
    print()

    full_name = _ask("Nume complet")
    email = _ask("Adresă de email").lower()

    password = getpass("Parolă: ")
    if password != getpass("Confirmă parola: "):
        print("Parolele nu coincid.", file=sys.stderr)
        return 1

    try:
        password_hash = hash_password(password)
    except PasswordRejectedError as rejection:
        print(rejection, file=sys.stderr)
        return 1

    with get_session_factory()() as session:
        if _email_taken(session, email):
            print(f"Există deja un cont cu adresa {email}.", file=sys.stderr)
            return 1

        garage = _choose_garage(session)
        if garage is None:
            return 1

        user = User(full_name=full_name, email=email, password_hash=password_hash)
        session.add(user)
        session.flush()
        session.add(GarageMember(garage_id=garage.id, user_id=user.id))
        session.commit()

        print()
        print(f"Contul {user.email} a fost creat și adăugat în garajul „{garage.name}”.")

    return 0


def _choose_garage(session: Session) -> Garage | None:
    existing = list(session.scalars(select(Garage).order_by(Garage.name)))

    if existing:
        print()
        print("Garaje existente:")
        for garage in existing:
            print(f"  {garage.id}. {garage.name}")
        answer = input("Numărul garajului, sau Enter pentru a crea unul nou: ").strip()
        if answer:
            chosen = next((garage for garage in existing if str(garage.id) == answer), None)
            if chosen is None:
                print(f"Nu există un garaj cu numărul {answer}.", file=sys.stderr)
            return chosen

    name = _ask("Nume pentru garajul nou")
    garage = Garage(name=name)
    session.add(garage)
    session.flush()
    return garage


def _email_taken(session: Session, email: str) -> bool:
    return session.scalar(select(User.id).where(func.lower(User.email) == email)) is not None


def _ask(question: str) -> str:
    while True:
        answer = input(f"{question}: ").strip()
        if answer:
            return answer
        print("Câmpul nu poate rămâne gol.")


COMMANDS: dict[str, Callable[[], int]] = {
    "create-user": create_user,
    "sync-catalog": sync_catalog,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fleetkeeper")
    parser.add_argument("command", choices=sorted(COMMANDS))
    arguments = parser.parse_args(argv)
    return COMMANDS[arguments.command]()


if __name__ == "__main__":
    sys.exit(main())
