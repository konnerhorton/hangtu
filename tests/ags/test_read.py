"""Reading an AGS file into text tables and findings (docs/data/ingest.md §3, §10)."""

import logging
from pathlib import Path

import pytest

from hangtu.ags import _read
from hangtu.errors import AgsFileError

DATA = Path(__file__).parents[1] / "data" / "ags"
SITE = DATA / "site_si.ags"


def _line_of(path, prefix):
    lines = path.read_text(encoding="utf-8").splitlines()
    return next(i for i, line in enumerate(lines, start=1) if line.startswith(prefix))


def _write(tmp_path, text, name="test.ags"):
    path = tmp_path / name
    path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    return path


def _site_text():
    return SITE.read_bytes().decode("utf-8")  # keeps the CRLF line ends


def test_reads_data_rows_as_text_with_their_lines():
    ags = _read.read(SITE)
    loca = ags.tables["LOCA"]
    assert list(loca["LOCA_ID"]) == ["BH1", "BH2", "BH3"]
    assert loca.loc[0, "LOCA_FDEP"] == "10.00"
    assert loca.loc[2, "LOCA_LAT"] == ""
    assert loca.loc[0, "_line"] == _line_of(SITE, '"DATA","BH1","CP"')
    assert ags.group_lines["LOCA"] == _line_of(SITE, '"GROUP","LOCA"')


def test_keeps_headings_units_and_types_by_group():
    ags = _read.read(SITE)
    assert ags.headings["ISPT"][:3] == ["LOCA_ID", "ISPT_TOP", "ISPT_NPEN"]
    assert ags.units["ISPT"]["ISPT_NPEN"] == "mm"
    assert ags.types["ISPT"]["ISPT_WAT"] == "XN"
    assert list(ags.tables)[:3] == ["PROJ", "TRAN", "UNIT"]  # file order


def test_records_hash_size_and_version():
    ags = _read.read(SITE)
    data = SITE.read_bytes()
    assert ags.size == len(data)
    assert len(ags.sha256) == 64
    assert (ags.version, ags.version_source) == ("4.2", "TRAN_AGS")
    assert _read.read(DATA / "site_v404.ags").version == "4.0.4"


@pytest.mark.parametrize("name", ["site_si.ags", "site_us.ags", "site_v404.ags"])
def test_good_files_have_no_findings(name):
    # In particular no Rule 2a: the file's CRLF line ends reach python-ags4 intact.
    assert _read.read(DATA / name).findings == []


def test_a_bom_is_accepted(tmp_path):
    path = _write(tmp_path, b"\xef\xbb\xbf" + SITE.read_bytes())
    with_bom, without = _read.read(path), _read.read(SITE)
    assert with_bom.findings == []
    assert with_bom.tables["LOCA"].equals(without.tables["LOCA"])


@pytest.mark.parametrize(
    ("tran_ags", "said"),
    [('"4.9"', 'TRAN_AGS is "4.9"'), ('""', "TRAN_AGS is missing")],
)
def test_an_unknown_version_is_read_as_4_2_with_v000(tmp_path, tran_ags, said):
    path = _write(tmp_path, _site_text().replace('"4.2"', tran_ags, 1))
    ags = _read.read(path)
    assert (ags.version, ags.version_source) == ("4.2", "assumed")
    [v000] = [f for f in ags.findings if f.rule == "V000"]
    assert said in v000.message and "read as AGS 4.2" in v000.message
    assert (v000.severity, v000.group, v000.heading) == ("warning", "TRAN", "TRAN_AGS")
    assert v000.line == _line_of(path, '"DATA","1"')
    # python-ags4's own note names the 4.1.1 dictionary, which ingest doesn't use.
    assert not any("not a recognized AGS4 version" in f.message for f in ags.findings)


def test_validation_results_become_v_findings():
    findings = _read.read(DATA / "defects.ags").findings
    orphan = next(f for f in findings if f.rule == "V10c" and f.line is not None)
    assert orphan.severity == "error"
    assert orphan.group == "LLPL"
    assert orphan.line == _line_of(DATA / "defects.ags", '"DATA","BH2","7.00"')
    assert {f.rule for f in findings} == {"V000", "V7", "V9", "V10c", "V18"}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("AGS Format Rule 10b", ("V10b", "error")),
        ("AGS Format Rule 8", ("V8", "error")),
        ("FYI (Related to Rule 16)", ("V16", "info")),
        ("FYI", ("VFYI", "info")),
        ("Warning (Related to Rule 3)", ("V3", "warning")),
        ("Warning", ("VWARNING", "warning")),
        ("General", ("VGENERAL", "warning")),
        ("Validator Process Error", ("VPROCESS", "error")),
    ],
)
def test_python_ags4_result_names_map_to_rules(name, expected):
    assert _read._rule_of(name) == expected


def test_prints_and_logs_nothing(capsys, caplog):
    logger = logging.getLogger("python_ags4")
    handlers = list(logger.handlers)
    with caplog.at_level(logging.DEBUG):
        _read.read(DATA / "defects.ags")
    assert capsys.readouterr() == ("", "")
    assert caplog.records == []
    assert logger.handlers == handlers and logger.propagate


def test_a_logged_problem_becomes_a_finding(tmp_path):
    text = _site_text().replace(
        '"HEADING","LOCA_ID","LOCA_TYPE"', '"HEADING","LOCA_ID","LOCA_ID"', 1
    )
    ags = _read.read(_write(tmp_path, text))
    assert "LOCA_ID_1" in ags.headings["LOCA"]  # python-ags4 renames the duplicate
    # check_file doesn't report the duplicate; only python-ags4's log does.
    [logged] = [f for f in ags.findings if f.rule == "VLOG"]
    assert logged.severity == "warning"
    assert "LOCA" in logged.message and "duplicate" in logged.message


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="No AGS file at"):
        _read.read(tmp_path / "nope.ags")


@pytest.mark.parametrize("text", ["", "hello world\r\nfoo,bar\r\n"])
def test_not_an_ags4_file(tmp_path, text):
    with pytest.raises(
        AgsFileError, match=r'isn\'t an AGS4 file: it has no GROUP line.*"GROUP","PROJ"'
    ):
        _read.read(_write(tmp_path, text))


def test_ags3_file(tmp_path):
    text = '"**PROJ"\r\n"*PROJ_ID","*PROJ_NAME"\r\n"1","x"\r\n'
    with pytest.raises(AgsFileError, match=r"looks like an AGS3 file.*AGS4 only"):
        _read.read(_write(tmp_path, text))


def test_parse_failure_names_the_line(tmp_path):
    path = _write(
        tmp_path, _site_text().replace('"DATA","BH1","CP"', '"DATA","BH1"', 1)
    )
    line = _line_of(path, '"DATA","BH1"')
    with pytest.raises(
        AgsFileError, match=f"Line {line} does not have the same number"
    ):
        _read.read(path)


def test_not_utf8_names_the_line(tmp_path):
    data = SITE.read_bytes().replace(b"hangtu synthetic site", b"site \xb0 north", 1)
    path = _write(tmp_path, data)
    line = _line_of(SITE, '"DATA","HT-SYN-1"')
    with pytest.raises(
        AgsFileError, match=f"isn't UTF-8 text: line {line} .*Save the file as UTF-8"
    ):
        _read.read(path)
