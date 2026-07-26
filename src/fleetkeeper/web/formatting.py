def thousands(value: int | None) -> str:
    """Group digits the Romanian way, with a dot: 187400 becomes 187.400.

    Six digit odometer readings are hard to read as a run of digits, and misreading one is how
    a wrong figure gets typed in.
    """
    if value is None:
        return "—"
    return f"{value:,}".replace(",", ".")
