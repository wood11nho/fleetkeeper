# FleetKeeper

Maintenance tracker for a small family fleet. It records what was done to each car, works out
when the next service is due from mileage and elapsed time, and sends an email reminder before
a deadline is missed.

The user interface and all notifications are in Romanian, because that is the language of the
people who use it. Code, documentation and commit history are in English.

## Why it exists

Three cars, two owners, and a paper trail spread across glovebox folders, invoices and memory.
Oil changes, timing belts, insurance and roadworthiness inspections all come due on different
schedules, and the cost of forgetting ranges from a fine to a destroyed engine. FleetKeeper is
the single place where that history lives, and it does the arithmetic so nobody has to remember
whether the gearbox oil was done at 180,000 or 190,000 km.

## How due dates are worked out

Every maintenance item has an interval in kilometres, an interval in months, or both. For each
car the app finds the last time an item was done, then computes:

- the mileage at which it falls due
- the date at which it falls due
- an estimated date for the mileage threshold, using the average daily distance derived from
  recorded odometer readings

The effective deadline is whichever comes first, which is how manufacturer schedules are
actually written: *every 15,000 km or 12 months, whichever comes sooner*. Documents such as
insurance and roadworthiness certificates are simpler — they expire on a fixed date.

## Stack

- Python 3.12, FastAPI
- PostgreSQL with SQLAlchemy and Alembic migrations
- Server-rendered Jinja2 templates with HTMX, hand-written CSS, no JavaScript build step
- Email reminders sent by a scheduled job, separate from the web application
- Docker image built in CI, deployed to Azure Container Apps

## Getting started

Requires [conda](https://docs.conda.io/) and git. Nothing else is installed on the host: the
database runs in the cloud and container images are built by CI.

```bash
conda env create -f environment.yml
conda activate fleetkeeper
pip install -e ".[dev]"
pre-commit install
```

Copy the example configuration and point it at a PostgreSQL database:

```bash
cp .env.example .env
```

Create the schema, install the service catalogue and make yourself an account:

```bash
alembic upgrade head
fleetkeeper sync-catalog
fleetkeeper create-user
```

`create-user` prompts for a name, an address, a password and a garage. It is interactive
because a password given as a command line argument survives in the shell history and is
visible in the process list while it runs.

Run the development server:

```bash
uvicorn --factory fleetkeeper.main:create_app --reload
```

The app is then available at http://127.0.0.1:8000.

To try it on a phone, uvicorn has to listen on every interface rather than only on the
loopback address, and the phone has to be told the machine's address on the network — 127.0.0.1
means "this device", so a phone asking for it looks at itself:

```bash
uvicorn --factory fleetkeeper.main:create_app --host 0.0.0.0 --port 8000
```

Anyone on the same network can then reach it, which is worth remembering before doing this
somewhere other than home.

## Data model

Vehicles, service history, documents and fuel logs all belong to a *garage*, and a user
sees a garage's data by being a member of it. Every member has the same rights, which
keeps the number of concepts down for the least technical person in the household.

Tenant isolation is enforced by the database rather than by remembering to add a filter.
Child tables carry `garage_id` alongside `vehicle_id` and reference the pair through a
composite foreign key, so a row whose garage disagrees with its vehicle's garage cannot be
written at all.

The service catalogue is reference data defined in `catalog/builtin.py` and installed by
`fleetkeeper sync-catalog`. Each entry declares which fuel types, gearboxes, drivetrains
and equipment it needs, so a manual gearbox is never offered a dual-clutch fluid change and
a timing chain never asks for a belt. Adding an item is a row in that list rather than a
change to any logic, and a garage can add categories of its own.

## Where the intervals come from

A figure the manufacturer publishes and a figure a workshop finds reasonable are different
claims, and presenting them identically invites the owner to trust the weaker one. Every
interval therefore records its provenance, shown beside it in the interface:

- **manufacturer** — from a published service schedule
- **practice** — a widely used workshop convention, often where the manufacturer says
  "lifetime"
- **estimate** — a rough default with no authority behind it

Items with no defensible figure carry no interval at all. Their explanation says what to
look for instead, because a symptom is honest and an invented deadline is not.

Wear parts are a separate kind: brake pads, dampers and tyres have no replacement schedule,
so their interval is a cadence for *inspection* and replacement is recorded whenever
measurement says it is due. A pad that lasts one summer of mountain driving and four years
of commuting cannot be put in a calendar.

A check constraint refuses to store an interval without a source, which makes the rule
impossible to forget rather than merely documented. None of these defaults is authoritative
for a specific engine code, and all of them are editable per vehicle.

Romanian legal obligations are the exception. Inspection intervals, road tax validity
periods, insurance terms, the winter tyre rule and the lifetime of an LPG tank are public
and checkable, so those explanations state them precisely and the sources are listed at the
top of `catalog/builtin.py`.

When an owner corrects an interval for their own car, `maintenance_rules.source_note`
records where the better figure came from — a page in the service book, a mechanic's
advice. Provenance applies to the owner's numbers as much as to the defaults, and a figure
changed two years ago is otherwise impossible to account for.

## When a car's description changes

Editing the fuel, gearbox, drivetrain or equipment re-derives which catalogue items apply.
Newly applicable ones are added; ones that no longer apply are switched off rather than
deleted, so an interval the owner corrected and the note saying where it came from survive a
change of mind. Nothing is switched back on automatically: a rule turned off deliberately must
stay off, and the database does not record which of the two reasons applied.

An odometer correction is not a new reading. Correcting downwards discards the readings above
the new figure, because those are the mistaken ones and leaving them behind would keep
distorting the average distance per day — the number that decides whether a warning arrives
before a deadline or after it. A reading that is merely lower than the last one is refused
outright; corrections belong on the edit page, where the consequence is stated.

## Interface decisions

A field offers a list only where the application has to reason about the answer: fuel, gearbox,
drivetrain and equipment, which together decide what appears in a car's schedule. Make, model,
part numbers, oil brands and workshops are typed freely, because no list anyone could maintain
would stay complete, and an incomplete list blocks the person trying to record something real.

Those four lists are radio groups rather than dropdowns. Every option and its explanation stays
on screen, with nothing to open, scroll and mis-tap — and the explanations matter, because
whether a car has a timing belt or a timing chain decides whether it ever gets a distribution
reminder, and most owners do not know which they have.

Errors come back as a sentence beside the field that caused them, with everything else still
filled in. Optional fields are labelled as optional rather than required ones being starred,
which reads as permission to skip rather than as a demand.

## Configuration

An application is handed its settings when it is built and keeps its own session factory.
Nothing in the request path reads the environment or resolves a database connection of its
own, because an application that does behaves differently depending on whether a `.env` file
happens to sit in the working directory — which is precisely the difference between a
developer's machine and a server. The command line tools and Alembic do read the
environment, since it is all they have.

The test suite runs with the environment stripped and the working directory moved, so that
difference cannot reappear unnoticed.

## Signing in

Passwords are hashed with bcrypt. Anything longer than bcrypt's 72 byte limit is refused
rather than accepted and silently truncated, because a truncated passphrase protects only
its beginning while looking like it protects all of it.

Sessions are rows in the database, not signed cookies, so they can be ended from the server:
a phone left in a taxi is a realistic problem and a cookie valid for thirty days cannot be
taken back. Only the digest of each session token is stored, so a leaked backup yields
nothing that can be used to sign in. A plain digest is correct here — bcrypt exists to make
guessable secrets expensive to attack, and a 256 bit random token is not guessable.

Repeated failures lock an account for fifteen minutes. Two accounts reachable from the open
internet would otherwise be limited only by network speed. A sign-in attempt against an
unknown address still spends the time a real check would take, so the response cannot be used
to find out which addresses have accounts.

Forms are protected against cross-site request forgery by the double submit cookie method,
which needs no server state — useful for the sign-in form, where there is no session to keep
a token in yet. A context processor supplies the token to every template so no route has to
remember it.

## Development

```bash
ruff check .          # lint
ruff format .         # format
mypy                  # type check
pytest                # tests
```

The same four commands run in CI on every push and pull request.

## Layout

```
src/fleetkeeper/
    config.py         application settings, read from environment
    database.py       engine and session factory
    main.py           application factory
    cli.py            administrative commands
    models/           SQLAlchemy models, one module per area
    catalog/          the built-in service catalogue and its installer
    security/         passwords, sessions, sign-in throttling, CSRF
    services/         who may see what, and what happens when a car is added
    web/              routes, forms, labels, templates, static assets
migrations/           Alembic revisions
tests/                test suite
```

## Roadmap

- [x] Project skeleton, tooling, continuous integration
- [x] Data model, migrations and service catalogue
- [x] Authentication and mobile-first layout
- [x] Vehicles, odometer tracking, schedules generated per car
- [x] Editing a vehicle and adjusting its intervals
- [ ] Service history with attachments
- [ ] Due-date engine
- [ ] Insurance and inspection documents
- [ ] Fuel log and consumption
- [ ] Cost reports
- [ ] Email reminders
- [ ] Deployment to Azure

## License

MIT
