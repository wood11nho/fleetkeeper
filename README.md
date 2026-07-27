# FleetKeeper

Maintenance tracker for a small family fleet: what was done to each car, what falls due next,
and an email before a deadline is missed.

Three cars, two owners, and a paper trail spread across glovebox folders, invoices and memory.
Oil changes, timing belts, insurance and roadworthiness inspections all come due on different
schedules, and the cost of forgetting ranges from a fine to a destroyed engine. This is the one
place that history lives, and it does the arithmetic so nobody has to remember whether the
gearbox oil was done at 180,000 km or 190,000.

The interface and the reminders are in Romanian, because that is the language of the people who
use it. Code, docs and commit history are in English.

## What it does

- Keeps the service history of every car: what, when, at what mileage, at what cost
- Gives each car its own maintenance schedule, derived from its engine, gearbox, drivetrain and
  equipment — a manual gearbox is never offered a dual-clutch fluid change
- Tracks insurance, roadworthiness and road tax, which expire on a date rather than a mileage
- Records fuel stops and works out real consumption
- Emails a reminder before anything falls due

## How it decides what is due

Maintenance items have an interval in kilometres, in months, or both. For each car the app takes
the last time an item was done and works out the mileage and the date at which it comes round
again — then turns the mileage into a date using the average distance covered per day, so a
warning can arrive *before* the threshold rather than after it. Whichever comes first wins,
which is how service schedules are actually written: *every 15,000 km or 12 months, whichever
comes sooner*.

Every interval says where it came from: a published service schedule, a workshop convention, or
an admitted estimate. Items with no defensible figure carry no interval at all and explain what
to look for instead. Brake pads are measured, not calendared.

## Built with

Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy · Alembic · Jinja2 · hand-written CSS, no
JavaScript build step · pytest, ruff, mypy in strict mode · GitHub Actions

## Running it locally

Needs [conda](https://docs.conda.io/) and git. Nothing else is installed on the machine — the
database lives in the cloud and container images are built in CI.

```bash
conda env create -f environment.yml
conda activate fleetkeeper
pip install -e ".[dev]"
pre-commit install
```

Point it at a PostgreSQL database:

```bash
cp .env.example .env    # then fill in FLEETKEEPER_DATABASE_URL
```

Set up the schema, the service catalogue and an account:

```bash
alembic upgrade head
fleetkeeper sync-catalog
fleetkeeper create-user
```

Run it:

```bash
uvicorn --factory fleetkeeper.main:create_app --reload
```

Then open http://127.0.0.1:8000.

## Development

```bash
ruff check .    # lint
ruff format .   # format
mypy            # types
pytest          # tests
```

The same four run in CI on every push.

## Roadmap

- [x] Data model, migrations, service catalogue
- [x] Authentication and mobile-first interface
- [x] Vehicles, odometer readings, per-car schedules
- [ ] Service history with receipts and photographs
- [ ] Due-date engine and the dashboard
- [ ] Insurance and inspection documents
- [ ] Fuel log and consumption
- [ ] Cost reports
- [ ] Email reminders
- [ ] Deployment to Azure

## License

MIT
