"""Errors and warnings raised by hangtu (docs/plots/P00-framework.md §12)."""

import os
import warnings

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep


class AgsKitError(Exception):
    """Base class for every error hangtu raises on purpose."""


class UnitsError(AgsKitError, ValueError):
    """A unit string is unknown, missing, or has the wrong dimension."""


class ColumnError(AgsKitError, ValueError):
    """A column or template is missing or unknown."""


class AgsKitHint(UserWarning):
    """A suggestion about optional data that would improve a plot.

    Turn hints off with ``ak.settings.hints = False``.
    """


def warn(message: str, category: type[Warning] = UserWarning) -> None:
    """Issue a warning that points at the user's line, not at hangtu's code."""
    warnings.warn(message, category, skip_file_prefixes=(_PACKAGE_DIR,))
