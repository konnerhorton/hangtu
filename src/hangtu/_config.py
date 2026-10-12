"""Read the data files that ship inside the package."""

from functools import cache
from importlib.resources import files
from typing import Any

import yaml


@cache
def load(path: str) -> Any:
    """Return the parsed YAML file at ``path``, relative to the package.

    The result is cached and shared, so callers must not modify it.
    """
    text = files("hangtu").joinpath(path).read_text(encoding="utf-8")
    return yaml.safe_load(text)


def quantity_kinds() -> dict[str, dict[str, Any]]:
    """Return the quantity-kind table from ``config/defaults.yaml``."""
    return load("config/defaults.yaml")["quantity_kinds"]
