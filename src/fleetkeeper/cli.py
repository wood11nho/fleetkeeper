"""Administrative commands, kept out of the web application.

Reference data is deliberately loaded from here rather than from a migration: a migration
that imports application code breaks the moment that code moves on, while this command can
be re-run against any environment at any version.
"""

import argparse
import sys
from collections.abc import Callable

from fleetkeeper.catalog import sync_builtin_categories
from fleetkeeper.database import get_session_factory


def sync_catalog() -> int:
    with get_session_factory()() as session:
        result = sync_builtin_categories(session)
        session.commit()

    print(f"catalogue synchronised: {result.created} created, {result.updated} updated")
    if result.retired:
        print(f"no longer defined in code, left in place: {', '.join(result.retired)}")
    return 0


COMMANDS: dict[str, Callable[[], int]] = {
    "sync-catalog": sync_catalog,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fleetkeeper")
    parser.add_argument("command", choices=sorted(COMMANDS))
    arguments = parser.parse_args(argv)
    return COMMANDS[arguments.command]()


if __name__ == "__main__":
    sys.exit(main())
