"""Reported gradings: ``GRAG`` fractions with no ``GRAT`` curve (datasets.md §6.13).

The lab's percentages are read as size ranges of the fraction system the
project says the lab used (the ``grag_fraction_system`` setting), and a
requested fraction is filled only where those ranges make it up exactly.
Nothing is interpolated or converted.
"""

from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from hangtu.analysis._fractions import builtin_systems, content_column
from hangtu.datasets._frame import Build

#: The GRAG percentage headings, finest first.
HEADINGS = (
    "GRAG_CLAY",
    "GRAG_SILT",
    "GRAG_FINE",
    "GRAG_SAND",
    "GRAG_GRAV",
    "GRAG_VCRE",
)

#: How far gravel, sand and fines may add up from 100 for a blank GRAG_VCRE to
#: count as 0: QC P003's default tolerance, fixed because a dataset doesn't take
#: QC overrides (§6.13).
TOLERANCE = 2.0


class Reported(NamedTuple):
    """A requested system's fractions from reported gradings."""

    #: The ``<fraction>_content`` columns, indexed like the rows given.
    contents: pd.DataFrame
    #: Fractions blank on some row because the stated system has no boundary at
    #: one of their sizes, in the requested system's order.
    other_boundaries: list[str]
    #: Rows with at least one of those fractions blank.
    blank_rows: int


def reported_specimens(build: Build) -> pd.DataFrame:
    """Return the reported gradings: ``GRAG`` rows whose specimen has no ``GRAT``.

    A specimen counts as having a curve when it has any ``GRAT`` row in the
    file, before §7 leaves incomplete records out, so a curve whose points are
    incomplete never turns into a reported grading. The frame holds the
    specimen columns, ``uniformity_coefficient`` and
    ``curvature_coefficient`` (``GRAG_UC``, ``GRAG_CC``), each percentage
    heading as a number, and ``_sample_id``.
    """
    from hangtu.datasets._lab import specimens  # _lab imports this module

    if not build.has("GRAG"):
        return pd.DataFrame()
    rows = reported_rows(build)
    frame = specimens(build, "GRAG", rows)
    add_values(build, frame, rows)
    frame["_sample_id"] = rows["sample_id"]
    return frame


def reported_rows(build: Build) -> pd.DataFrame:
    """Return the ``GRAG`` rows whose specimen has no ``GRAT`` row in the file."""
    rows = build.rows("GRAG")
    if build.has("GRAT"):
        curves = build.data.table("GRAT")["specimen_id"].dropna()
        rows = rows[~rows["specimen_id"].isin(curves)]
    return rows


def add_values(build: Build, frame: pd.DataFrame, rows: pd.DataFrame) -> None:
    """Add Cu, Cc and the percentage headings of ``rows`` to ``frame``."""
    frame["uniformity_coefficient"] = build.numbers(rows, "GRAG_UC")
    frame["curvature_coefficient"] = build.numbers(rows, "GRAG_CC")
    for heading in HEADINGS:
        frame[heading] = build.numbers(rows, heading)


def heading_ranges(stated: str) -> dict[str, tuple[float, float]]:
    """Return each heading's size range (mm) in a built-in system (§6.13 table).

    The open upper size is ``inf``.
    """
    system = builtin_systems()[stated]
    by_name = {fraction["name"]: fraction for fraction in system["fractions"]}
    ranges = {}
    for heading, names in system["grag"].items():
        upper = by_name[names[-1]]["upper"]
        ranges[heading] = (
            float(by_name[names[0]]["lower"]),
            np.inf if upper is None else float(upper),
        )
    return ranges


def _headings(frame: pd.DataFrame, stated: str) -> dict[str, pd.Series]:
    """Return the stated system's heading values, with the blank-heading rules.

    A blank ``GRAG_FINE`` is ``GRAG_SILT`` + ``GRAG_CLAY`` where both are given
    (as QC P003 reads it). A blank ``GRAG_VCRE`` is 0 where gravel, sand and
    fines are given and add up to 100 within ``TOLERANCE``.
    """
    values = {
        heading: frame[heading].astype(float)
        if heading in frame
        else pd.Series(np.nan, index=frame.index)
        for heading in HEADINGS
    }
    values["GRAG_FINE"] = values["GRAG_FINE"].fillna(
        values["GRAG_SILT"] + values["GRAG_CLAY"]
    )
    rest = values["GRAG_GRAV"] + values["GRAG_SAND"] + values["GRAG_FINE"]
    complete = (rest - 100).abs() <= TOLERANCE
    values["GRAG_VCRE"] = values["GRAG_VCRE"].mask(
        values["GRAG_VCRE"].isna() & complete, 0.0
    )
    ranges = heading_ranges(stated)
    return {heading: values[heading] for heading in ranges}


def _chains(
    ranges: dict[str, tuple[float, float]], lower: float, upper: float
) -> list[list[str]]:
    """Every run of adjacent headings spanning exactly ``lower`` to ``upper``.

    The fewest headings first, so ``GRAG_FINE`` comes before ``GRAG_CLAY`` +
    ``GRAG_SILT``.
    """
    found: list[list[str]] = []

    def extend(chain: list[str], at: float) -> None:
        if at == upper:
            found.append(chain)
            return
        for heading, (start, end) in ranges.items():
            if start == at and end <= upper and heading not in chain:
                extend([*chain, heading], end)

    extend([], lower)
    return sorted(found, key=len)


def reported_fractions(
    frame: pd.DataFrame, requested: list[dict[str, Any]], stated: str | None
) -> Reported:
    """Return the requested fractions of reported gradings (§6.13, rules 1 to 3).

    ``frame`` holds the ``GRAG`` percentage headings, as
    ``reported_specimens()`` gives them; ``requested`` is the fractions of the
    system a dataset asks for; ``stated`` is the project's
    ``grag_fraction_system``. A requested fraction is the sum of the headings
    whose ranges make it up exactly (blank if one is blank), else 0 where it
    lies inside one heading's range and that heading is 0, else blank. With no
    stated system every fraction is blank.
    """
    columns = [content_column(fraction["name"]) for fraction in requested]
    contents = pd.DataFrame(np.nan, index=frame.index, columns=columns, dtype=float)
    if stated is None or frame.empty:
        return Reported(contents, [], 0)
    ranges = heading_ranges(stated)
    values = _headings(frame, stated)
    boundaries = {np.inf} | {
        float(fraction["lower"]) for fraction in builtin_systems()[stated]["fractions"]
    }
    other: list[str] = []
    for fraction, column in zip(requested, columns, strict=True):
        lower = float(fraction["lower"])
        upper = np.inf if fraction["upper"] is None else float(fraction["upper"])
        result = pd.Series(np.nan, index=frame.index, dtype=float)
        for chain in _chains(ranges, lower, upper):
            total = sum((values[heading] for heading in chain), start=0.0)
            result = result.fillna(total)
        for heading, (start, end) in ranges.items():
            if start <= lower and upper <= end:
                result = result.mask(result.isna() & (values[heading] == 0), 0.0)
        contents[column] = result
        if result.isna().any() and not {lower, upper} <= boundaries:
            other.append(fraction["name"])
    blank = contents[[content_column(name) for name in other]].isna().any(axis=1)
    return Reported(contents, other, int(blank.sum()))


# --- Warnings (§6.13), shared by grain_size_summary() and index_properties() ---


def _gradings(count: int) -> str:
    return f"{count} grading is" if count == 1 else f"{count} gradings are"


def no_system_message(count: int) -> str:
    """Return the warning for reported gradings when no system is set."""
    them = "its fractions are" if count == 1 else "their fractions are"
    return (
        f"{_gradings(count)} reported only as fractions (GRAG), and {them} blank "
        "because the project's GRAG fraction system isn't set. AGS 4 defines "
        "these headings with ISO 14688 boundaries (2 mm, 0.063 mm), but many "
        "labs report ASTM D2487 fractions (4.75 mm, 0.075 mm) in them. Set the "
        "system the lab used, for example "
        'p.settings.grag_fraction_system = "astm_uscs".'
    )


def other_boundaries_message(
    count: int, stated: str, requested: str, names: list[str]
) -> str:
    """Return the warning for requested fractions the stated system can't give."""
    return (
        f"{_gradings(count)} reported as {stated} fractions (GRAG), so the "
        f"{requested} fractions with other boundaries are blank: "
        f"{', '.join(names)}."
    )


def uscs_blank_message(count: int, stated: str, names: list[str]) -> str:
    """Return the warning for samples whose reported USCS fractions are blank."""
    samples = (
        "1 sample's grading is" if count == 1 else f"{count} samples' gradings are"
    )
    return (
        f"{samples} reported as {stated} fractions (GRAG), so their USCS "
        f"fractions with other boundaries ({', '.join(names)}) and symbols are "
        "blank."
    )
