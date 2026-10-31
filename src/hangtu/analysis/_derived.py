"""The results of fits to test results (docs/work/m11b-envelope-fit.md, Decision 12).

A fit of test results gives a *derived* value of a parameter (Eurocode 7's
measured → derived → representative → design), not a statistic of a property,
so its results are a family of their own beside the statistics results (SPEC §5).
"""

import html
from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from hangtu.stats._result import _plain


@dataclass(frozen=True, repr=False)
class _DerivedResult:
    """What every derived result records: what was fitted, and from what.

    A subclass is a ``@dataclass(frozen=True, repr=False)`` with ``__str__``
    and ``to_frame()``; ``repr()`` and the notebook view show ``str()``.
    """

    #: The function that made the result, e.g. ``"mohr_coulomb_fit"``.
    function: str
    #: The unit of the results that have one, or None.
    unit: str | None
    #: The lines of the summary under the table.
    notes: tuple[str, ...]
    #: ``attrs["judgments"]`` of the input, when it carries them.
    judgments: dict[str, Any]
    hangtu_version: str
    #: Always ``"derived"``: a value derived from test results (SPEC §5).
    kind: str = field(default="derived", init=False)

    def to_dict(self) -> dict[str, Any]:
        """Return every field, JSON-serializable (NaN as None)."""
        return _plain(asdict(self))

    def to_frame(self) -> pd.DataFrame:
        raise NotImplementedError

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return f"<pre>{html.escape(str(self))}</pre>"
