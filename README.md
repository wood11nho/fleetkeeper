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

Create the schema and install the service catalogue:

```bash
alembic upgrade head
fleetkeeper sync-catalog
```

Run the development server:

```bash
uvicorn --factory fleetkeeper.main:create_app --reload
```

The app is then available at http://127.0.0.1:8000.

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
    web/              routes, templates, static assets
migrations/           Alembic revisions
tests/                test suite
```

## Roadmap

- [x] Project skeleton, tooling, continuous integration
- [x] Data model, migrations and service catalogue
- [ ] Authentication and mobile-first layout
- [ ] Vehicles and odometer tracking
- [ ] Service history with attachments
- [ ] Due-date engine
- [ ] Insurance and inspection documents
- [ ] Fuel log and consumption
- [ ] Cost reports
- [ ] Email reminders
- [ ] Deployment to Azure

## License

MIT
