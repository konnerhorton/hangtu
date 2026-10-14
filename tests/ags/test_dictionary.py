"""Heading types, units, keys and parents from the dictionaries (ingest.md §6)."""

from pathlib import Path

import pytest

from hangtu.ags import _dictionary, _read

DATA = Path(__file__).parents[1] / "data" / "ags"


def _for(name, tmp_path=None, replace=None):
    path = DATA / name
    if replace:
        text = path.read_bytes().decode("utf-8")
        path = tmp_path / name
        path.write_bytes(text.replace(*replace, 1).encode("utf-8"))
    ags = _read.read(path)
    return ags, *_dictionary.for_file(ags)


def test_standard_headings_come_from_4_2():
    _, dictionary, findings = _for("site_si.ags")
    nval = dictionary.heading("ISPT", "ISPT_NVAL")
    assert (nval.type, nval.unit, nval.status, nval.source) == (
        "0DP",
        "",
        "OTHER",
        "4.2",
    )
    assert dictionary.heading("PTST", "PTST_BDEN").unit == "Mg/m3"
    assert dictionary.heading("LNMC", "LNMC_MC").type == "X"
    assert findings == []


def test_keys_and_parents():
    _, dictionary, _ = _for("site_si.ags")
    assert dictionary.keys("SAMP") == [
        "LOCA_ID",
        "SAMP_TOP",
        "SAMP_REF",
        "SAMP_TYPE",
        "SAMP_ID",
    ]
    assert dictionary.group("GRAT").parent == "GRAG"
    assert dictionary.ancestors("GRAT") == ["GRAG", "SAMP", "LOCA", "PROJ"]
    assert dictionary.ancestors("PROJ") == []


def test_user_defined_group_comes_from_the_file_dict():
    _, dictionary, findings = _for("site_si.ags")
    group = dictionary.group("XPPT")
    assert (group.parent, group.source) == ("LOCA", "DICT")
    assert dictionary.keys("XPPT") == ["LOCA_ID", "XPPT_DPTH"]
    res = dictionary.heading("XPPT", "XPPT_RES")
    assert (res.type, res.unit, res.source) == ("0DP", "kPa", "DICT")
    assert not any(f.group == "XPPT" for f in findings)  # decision 8


def test_user_defined_group_with_no_dict_entry():
    _, dictionary, _ = _for("defects.ags")
    assert dictionary.group("XUND") is None
    assert dictionary.heading("XUND", "XUND_VAL") is None
    assert dictionary.keys("XUND") == []
    assert dictionary.ancestors("XUND") == []


def test_groups_4_2_removed_come_from_the_file_version():
    ags, dictionary, findings = _for("site_v404.ags")
    iprg = dictionary.group("IPRG")
    assert (iprg.parent, iprg.source) == ("LOCA", "4.0.4")
    assert dictionary.heading("IPRG", "IPRG_IPRM").unit == "m/s"
    assert dictionary.heading("IPRT", "IPRT_TIME").type == "T"
    assert dictionary.keys("IPRT") == [
        "LOCA_ID",
        "IPRG_TOP",
        "IPRG_TESN",
        "IPRG_BASE",
        "IPRG_STG",
        "IPRT_TIME",
    ]
    # Groups still in 4.2 are read with 4.2, even in a 4.0.4 file.
    assert dictionary.heading("ISPT", "ISPT_NVAL").source == "4.2"
    m001 = {(f.group, f.heading): f for f in findings}
    assert set(m001) == {("IPRG", None), ("IPRT", None), ("RUCS", "RUCS_E")}
    assert m001["IPRG", None].line == ags.group_lines["IPRG"]
    assert m001["RUCS", "RUCS_E"].line == ags.heading_lines["RUCS"]
    assert all(f.rule == "M001" and f.severity == "info" for f in findings)
    assert "AGS 4.2 removed it" in m001["RUCS", "RUCS_E"].message


def test_heading_4_2_removed_comes_from_the_file_version():
    _, dictionary, _ = _for("site_v404.ags")
    rucs_e = dictionary.heading("RUCS", "RUCS_E")
    assert (rucs_e.unit, rucs_e.source) == ("GPa", "4.0.4")


def test_deprecated_4_1_groups_are_read_with_4_1(tmp_path):
    _, dictionary, findings = _for("site_v404.ags", tmp_path, ('"4.0.4"', '"4.1"'))
    assert dictionary.group("IPRG").source == "4.1"
    assert {f.group for f in findings if f.heading is None} == {"IPRG", "IPRT"}


@pytest.mark.parametrize("version", _read.VERSIONS)
def test_every_standard_dictionary_loads(version):
    dictionary = _dictionary.standard(version)
    assert "LOCA" in dictionary.groups
    assert ("LOCA", "LOCA_ID") in dictionary.headings
