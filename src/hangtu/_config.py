"""Read the data files that ship inside the package."""

from functools import cache
from importlib.resources import files
from os import PathLike
from pathlib import Path
from typing import Any

import yaml

from hangtu.errors import HangtuError


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


def read_file(path: str | PathLike[str], what: str) -> bytes:
    """Return the bytes of a user's file; ``what`` names it in errors."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"No {what} file at {str(path)!r}. Check the path; it is "
            f"relative to {str(Path.cwd())!r} unless it starts from a drive or /."
        )
    return path.read_bytes()


def parse_yaml(data: bytes, path: str | PathLike[str], what: str, guide: str) -> Any:
    """Parse a user's YAML file; a syntax error names its line and ``guide``."""
    try:
        return yaml.safe_load(data.decode("utf-8"))
    except yaml.YAMLError as error:
        where = getattr(error, "problem_mark", None)
        line = f" at line {where.line + 1}" if where else ""
        raise HangtuError(
            f"The {what} file {str(path)!r} isn't valid YAML{line}. "
            f"Check its indentation and colons against {guide}."
        ) from None


def read_yaml(path: str | PathLike[str], what: str, guide: str) -> Any:
    """Read a user's YAML file (QC rules, accepted findings, judgments)."""
    return parse_yaml(read_file(path, what), path, what, guide)
