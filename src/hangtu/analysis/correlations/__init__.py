"""Published correlations, one function per source (SPEC §4).

Each function reads the one input column its correlation was derived with,
returns a copy of ``df`` with the estimate in the target property's column,
``correlation_name`` and ``correlation_note``, and gives NaN, never an
extrapolated value, where the correlation doesn't apply. Several estimates
compare with ``pd.concat`` and ``ht.plot.profile(..., color_by="correlation_name")``.
"""

from typing import Any

from hangtu.analysis.correlations._framework import entry
from hangtu.analysis.correlations._friction_angle import hatanaka_uchida_1996

__all__ = ["describe", "hatanaka_uchida_1996"]


def describe(name: str) -> dict[str, Any]:
    """Return a correlation's entry: its equation, inputs, range and sources.

    The same entry ``df.attrs["correlations"][name]`` holds on a result, for
    when the attrs are lost (after a merge, or a file round trip).

    Parameters
    ----------
    name : str
        The correlation's function name, as in ``correlation_name``.

    Returns
    -------
    dict
        A copy of its entry in ``config/correlations.yaml``: ``target``,
        ``equation``, ``inputs`` (column, variant and unit), ``range``,
        ``applies_to``, ``not_for``, ``scatter``, ``notes`` and ``sources``
        (each with its locator).

    Examples
    --------
    >>> ht.analysis.correlations.describe("hatanaka_uchida_1996")["range"]
    {'spt_n1_60': {'at_least': 4.55, 'at_most': 39.0}}
    """
    return entry(name)
