"""Findings raised while reading an AGS file (docs/data/ingest.md §9)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """One finding, as stored in the ``finding`` table.

    ``severity`` is ``"error"``, ``"warning"`` or ``"info"``. ``group``,
    ``heading`` and ``line`` are None when the finding isn't tied to one.
    """

    rule: str
    severity: str
    message: str
    group: str | None = None
    heading: str | None = None
    line: int | None = None
