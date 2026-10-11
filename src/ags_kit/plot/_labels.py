"""Axis labels (docs/plots/P00-framework.md §7)."""


def axis_label(
    text: str,
    unit: str | None = None,
    datum: str | None = None,
    unknown: bool = False,
) -> str:
    """Build an axis label: ``"Elevation (ft, NAVD88)"``, ``"SPT N60"``.

    Parameters
    ----------
    text
        The quantity, from the registry ``label``, a preset or ``label=``.
    unit
        The display unit text from ``to_display``; None for no unit.
    datum
        The vertical datum. Callers pass it for elevation labels only.
    unknown
        True when the column's units are unknown; replaces the unit.
    """
    parts = ["units unknown" if unknown else unit, datum]
    inside = ", ".join(part for part in parts if part)
    return f"{text} ({inside})" if inside else text
