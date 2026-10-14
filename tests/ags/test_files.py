"""The synthetic AGS4 test files (docs/data/ingest.md §11)."""

import importlib.util
from pathlib import Path

import pytest
from python_ags4 import AGS4

DATA = Path(__file__).parents[1] / "data" / "ags"
GOOD = ["site_si.ags", "site_us.ags", "site_v404.ags"]
NOT_FINDINGS = {"Metadata", "Summary of data"}


def _check(name, capsys, dictionary=None):
    errors = AGS4.check_file(DATA / name, standard_AGS4_dictionary=dictionary)
    capsys.readouterr()  # python-ags4 prints progress notes
    return {rule: rows for rule, rows in errors.items() if rule not in NOT_FINDINGS}


@pytest.mark.parametrize("name", GOOD)
def test_good_files_pass_python_ags4(name, capsys):
    assert _check(name, capsys) == {}


def test_defects_file_breaks_the_rules_it_was_built_for(capsys):
    # Ingest validates an unrecognized version against 4.2 (ingest.md §6).
    errors = _check("defects.ags", capsys, dictionary="4.2")
    orphans = [row["desc"] for row in errors["AGS Format Rule 10c"]]
    assert any("BH2|7.00|9|D|BH2-D9" in desc for desc in orphans)
    undefined = [row["desc"] for row in errors["AGS Format Rule 9"]]
    assert any(desc.startswith("XUND_VAL") for desc in undefined)
    assert "AGS Format Rule 18" in errors
    assert any("4.9" in row["desc"] for row in errors["FYI"])


def test_files_match_the_script_that_writes_them(tmp_path):
    script = DATA / "_make_files.py"
    spec = importlib.util.spec_from_file_location("_make_files", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(tmp_path)
    for name in [*GOOD, "defects.ags"]:
        assert (tmp_path / name).read_bytes() == (DATA / name).read_bytes(), name
