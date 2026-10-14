import importlib.util
from pathlib import Path

import pandas as pd
import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
FILES = ("site_si", "site_us", "site_v404", "defects", "qc_defects")


def _load_make_files():
    spec = importlib.util.spec_from_file_location(
        "_make_files", DATA / "_make_files.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_files = _load_make_files()
group = make_files.group


@pytest.fixture(scope="session")
def projects(tmp_path_factory):
    """Each test file in a project database, display units US. Don't modify them."""
    folder = tmp_path_factory.mktemp("qc")
    return {
        name: ht.Project.from_ags(
            DATA / f"{name}.ags", db=folder / f"{name}.sqlite", display_units="US"
        )
        for name in FILES
    }


@pytest.fixture
def build(tmp_path):
    """Build a project from groups written with ``group()``, as a 4.2 file."""
    count = 0

    def build(*groups, **settings):
        nonlocal count
        count += 1
        path = tmp_path / f"case{count}.ags"
        make_files.write_file(path, "4.2", list(groups))
        settings.setdefault("display_units", "SI")
        return ht.Project.from_ags(
            path, db=tmp_path / f"case{count}.sqlite", **settings
        )

    return build


def loca(*rows):
    """LOCA rows as (LOCA_ID, LOCA_NATE, LOCA_NATN, LOCA_GL, LOCA_FDEP)."""
    return group(
        "LOCA",
        [
            ("LOCA_ID", "ID", ""),
            ("LOCA_NATE", "2DP", "m"),
            ("LOCA_NATN", "2DP", "m"),
            ("LOCA_GL", "2DP", "m"),
            ("LOCA_FDEP", "2DP", "m"),
        ],
        [list(row) for row in rows],
    )


def geol(*rows, unit="m"):
    """GEOL rows as (LOCA_ID, GEOL_TOP, GEOL_BASE)."""
    return group(
        "GEOL",
        [
            ("LOCA_ID", "ID", ""),
            ("GEOL_TOP", "2DP", unit),
            ("GEOL_BASE", "2DP", unit),
            ("GEOL_DESC", "X", ""),
        ],
        [[*row, "CLAY"] for row in rows],
    )


def found(report, rule_id):
    """The findings of one rule, as (loca_id, heading, source_line) tuples."""
    rows = report.findings.query("rule_id == @rule_id")
    return [
        tuple(None if pd.isna(value) else value for value in row)
        for row in zip(
            rows["loca_id"], rows["heading"], rows["source_line"], strict=True
        )
    ]
