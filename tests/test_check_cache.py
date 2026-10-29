"""The run-wide cache of AGS4.check_file in conftest.py (docs/work/test-speed.md)."""

import io
import logging
from pathlib import Path

import pytest
from python_ags4 import AGS4

from hangtu.ags import _read

DATA = Path(__file__).parent / "data" / "ags"


def _duplicate_heading(tmp_path):
    """site_si with a duplicate heading, which only python-ags4's log reports."""
    text = (DATA / "site_si.ags").read_bytes().decode("utf-8")  # keeps CRLF
    text = text.replace(
        '"HEADING","LOCA_ID","LOCA_TYPE"', '"HEADING","LOCA_ID","LOCA_ID"', 1
    )
    path = tmp_path / "duplicate.ags"
    path.write_bytes(text.encode("utf-8"))
    return path


@pytest.mark.parametrize("name", ["site_si", "defects", "qc_defects", "duplicate"])
def test_findings_are_the_same_with_and_without_the_cache(check_cache, tmp_path, name):
    path = _duplicate_heading(tmp_path) if name == "duplicate" else DATA / f"{name}.ags"
    with check_cache.disabled():
        uncached = _read.read(path)
    _read.read(path)  # fills the cache if no earlier test has
    hits = check_cache.hits
    cached = _read.read(path)
    assert check_cache.hits == hits + 1
    assert cached.findings == uncached.findings
    if name == "duplicate":
        assert any(f.rule == "VLOG" for f in cached.findings)


def test_a_hit_logs_what_the_check_logged(check_cache, caplog, tmp_path):
    # Today every message only check_file logs is quiet or also logged by the
    # parser, so the findings above can't show the records are logged again.
    text = _duplicate_heading(tmp_path).read_bytes().decode("utf-8") + "\r\n"

    def logged():
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="python_ags4"):
            AGS4.check_file(io.StringIO(text, newline=""))
        return [(r.name, r.levelno, r.getMessage()) for r in caplog.records]

    with check_cache.disabled():
        expected = logged()
    hits = check_cache.hits
    assert logged() == expected  # a miss
    assert logged() == expected and check_cache.hits == hits + 1
    assert any("duplicate" in message for *_, message in expected)


def test_a_changed_text_is_checked_again(check_cache, tmp_path):
    path = _duplicate_heading(tmp_path)
    _read.read(path)
    hits = check_cache.hits
    path.write_bytes(path.read_bytes() + b"\r\n")
    _read.read(path)
    assert check_cache.hits == hits


def test_a_changed_result_doesnt_reach_the_next_hit(check_cache):
    text = (DATA / "defects.ags").read_bytes().decode("utf-8")
    first = AGS4.check_file(io.StringIO(text, newline=""))
    first.clear()
    again = AGS4.check_file(io.StringIO(text, newline=""))
    assert again and again == AGS4.check_file(io.StringIO(text, newline=""))


def test_a_path_goes_to_the_real_check(check_cache):
    hits = check_cache.hits
    AGS4.check_file(DATA / "site_si.ags")
    AGS4.check_file(DATA / "site_si.ags")
    assert check_cache.hits == hits
