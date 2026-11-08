import ast
import re
from pathlib import Path

import pytest

import hangtu as ht
from hangtu.errors import warn


@pytest.mark.parametrize("error", [ht.UnitsError, ht.ColumnError])
def test_data_errors_are_hangtu_and_value_errors(error):
    assert issubclass(error, ht.HangtuError)
    assert issubclass(error, ValueError)


def test_hint_is_a_user_warning():
    assert issubclass(ht.HangtuHint, UserWarning)


def test_warn_points_at_the_callers_line():
    with pytest.warns(ht.HangtuHint, match="a hint") as record:
        warn("a hint", ht.HangtuHint)
    assert record[0].filename == __file__


# What a user can't follow: an internal spec, a TODO item, a milestone or a wave.
INTERNAL_REFERENCE = re.compile(r"SPEC §|docs/|TODO #|\bM\d{1,2}\b|\bwave \d\b")
SOURCE = Path(ht.__file__).parent


def _docstrings(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
            ):
                found.add(id(body[0].value))
    return found


def test_messages_cite_no_internal_files():
    # Error, warning and note text reaches users; SPEC, docs/ and TODO don't.
    hits = []
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = _docstrings(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and INTERNAL_REFERENCE.search(node.value)
            ):
                hits.append(f"{path.relative_to(SOURCE)}:{node.lineno}")
    assert hits == [], "\n".join(hits)


def test_source_cites_no_work_file():
    # A decision's spec is a living doc (docs/analysis/, docs/data/, a plot
    # spec); docs/work/ files are history, so code points at the living doc.
    hits = []
    for pattern in ("*.py", "*.yaml"):
        for path in sorted(SOURCE.rglob(pattern)):
            for number, line in enumerate(path.read_text("utf-8").splitlines(), 1):
                if "docs/work/" in line:
                    hits.append(f"{path.relative_to(SOURCE)}:{number}")
    assert hits == [], "\n".join(hits)
