from datetime import date
from decimal import Decimal

NOTHING = "—"


def thousands(value: int | None) -> str:
    """Group digits the Romanian way, with a dot: 187400 becomes 187.400.

    Six digit odometer readings are hard to read as a run of digits, and misreading one is how a
    wrong figure gets typed in.
    """
    if value is None:
        return NOTHING
    return f"{value:,}".replace(",", ".")


def money(value: Decimal | None) -> str:
    """Romanian convention: a dot groups thousands, a comma separates the bani. 1.234,56 lei."""
    if value is None:
        return NOTHING
    whole, _, bani = f"{value:,.2f}".partition(".")
    return f"{whole.replace(',', '.')},{bani} lei"


def day(value: date | None) -> str:
    if value is None:
        return NOTHING
    return value.strftime("%d.%m.%Y")
