"""Typing values and flagging recognized text (docs/data/ingest.md §7, §8)."""

from pathlib import Path

import pytest

from hangtu.ags import _dictionary, _read, _values
from hangtu.ags import _units as u
from hangtu.ags._dictionary import Heading

DATA = Path(__file__).parents[1] / "data" / "ags"


def heading(group, name, ags_type, unit="", file_unit=None):
    entry = Heading(group, name, "OTHER", ags_type, unit, "4.2")
    file_unit = unit if file_unit is None else file_unit
    result, _ = u.resolve_heading(group, name, file_unit, ags_type, entry, "SI")
    return result


def typed(column, *cells):
    return _values.type_column(column, list(cells), list(range(10, 10 + len(cells))))


PL = heading("LLPL", "LLPL_PL", "XN", "%")


def test_numbers_and_blanks():
    values, flags, findings = typed(
        heading("LOCA", "LOCA_GL", "2DP", "m"), "12.40", "", " 3 "
    )
    assert values == [12.40, None, 3.0]
    assert flags == findings == []


@pytest.mark.parametrize(
    ("text", "value", "flag", "bound"),
    [
        ("NP", None, "NP", None),
        (" NP ", None, "NP", None),  # trimmed
        ("Dry", None, "DRY", None),
        ("<0.1", 0.1, "LT", 0.1),
        (">50", 50.0, "GT", 50.0),
        ("#2.65", 2.65, "ASSUMED", None),
    ],
)
def test_recognized_text(text, value, flag, bound):
    values, flags, findings = typed(PL, text)
    assert values == [value]
    assert flags == [_values.ValueFlag(1, "LLPL_PL", flag, bound, text.strip())]
    assert findings == []


@pytest.mark.parametrize("text", ["np", "abc", "dry", "< x", "inf"])
def test_unrecognized_text_is_other_with_t001(text):
    values, flags, findings = typed(PL, "20", text)
    assert values == [20.0, None]
    assert flags == [_values.ValueFlag(2, "LLPL_PL", "OTHER", None, text)]
    [t001] = findings
    assert (t001.rule, t001.severity, t001.group, t001.heading, t001.line) == (
        "T001",
        "info",
        "LLPL",
        "LLPL_PL",
        11,
    )
    assert f'"{text}"' in t001.message and "flag OTHER" in t001.message


def test_bounds_are_converted_with_the_value():
    wat = heading("ISPT", "ISPT_WAT", "XN", "m", file_unit="ft")
    values, flags, _ = typed(wat, "<10", "Dry")
    assert values[0] == pytest.approx(3.048)
    assert flags[0].bound == pytest.approx(3.048)
    assert flags[1].flag == "DRY" and values[1] is None


def test_x_with_a_unit_is_numeric_and_x_without_is_text():
    mc = heading("LNMC", "LNMC_MC", "X", "%")
    assert typed(mc, "32", "NP")[0] == [32.0, None]
    remark = heading("LOCA", "LOCA_REM", "X")
    assert typed(remark, "NP", "", "Some text")[0] == ["NP", None, "Some text"]
    assert typed(remark, "NP")[1] == []


def test_refusal_in_the_n_value_keeps_the_blows():
    nval = heading("ISPT", "ISPT_NVAL", "0DP")
    values, flags, findings = typed(nval, "50/75", "12")
    assert values == [50.0, 12.0]
    assert flags == [_values.ValueFlag(1, "ISPT_NVAL", "REFUSAL", None, "50/75")]
    assert findings == []


def test_refusal_in_the_report_flags_the_n_value():
    rows = [{"ISPT_REP": "N=12"}, {"ISPT_REP": "25/75 50/75"}, {"ISPT_REP": ""}]
    flags = _values.refusal_flags("ISPT", ["ISPT_NVAL", "ISPT_REP"], rows)
    assert flags == [_values.ValueFlag(2, "ISPT_NVAL", "REFUSAL", None, "25/75 50/75")]
    assert _values.refusal_flags("GEOL", ["ISPT_REP"], rows) == []


@pytest.mark.parametrize(
    ("ags_format", "text", "expected"),
    [
        ("yyyy-mm-dd", "2026-10-14", "2026-10-14"),
        ("yyyy-mm-ddThh:mm", "2026-10-14T09:30", "2026-10-14T09:30:00"),
        ("yyyy-mm-ddThh:mm:ss", "2026-09-03T10:15:00", "2026-09-03T10:15:00"),
        (
            "yyyy-mm-ddThh:mm:ss.sss",
            "2026-09-03T10:15:00.250",
            "2026-09-03T10:15:00.250000",
        ),
        ("dd/mm/yyyy", "14/10/2026", "2026-10-14"),
        ("hh:mm", "09:30", "09:30:00"),
    ],
)
def test_dates_become_iso_8601(ags_format, text, expected):
    assert typed(heading("SAMP", "SAMP_DTIM", "DT", ags_format), text)[0] == [expected]


def test_a_date_not_in_its_format_is_other():
    values, flags, findings = typed(
        heading("LOCA", "LOCA_STAR", "DT", "yyyy-mm-dd"), "14/10/2026"
    )
    assert values == [None] and flags[0].flag == "OTHER" and findings[0].rule == "T001"


@pytest.mark.parametrize(
    ("ags_format", "text", "seconds"),
    [
        ("hh:mm:ss", "01:20:00", 4800.0),
        ("mm:ss", "05:30", 330.0),
        ("hh:mm:ss", "26:00:00", 93600.0),
    ],
)
def test_times_become_seconds(ags_format, text, seconds):
    assert typed(heading("SAMP", "SAMP_DURN", "T", ags_format), text)[0] == [seconds]


def test_a_time_not_in_its_format_is_other():
    assert (
        typed(heading("SAMP", "SAMP_DURN", "T", "hh:mm:ss"), "05:30")[1][0].flag
        == "OTHER"
    )


def test_yes_no():
    values, flags, _ = typed(heading("GRAG", "GRAG_SUFF", "YN"), "Y", "N", "Yes")
    assert values == [1, 0, None] and flags[0].flag == "OTHER"


@pytest.mark.parametrize(
    ("text", "degrees"),
    [
        ("37:47:36.100", 37 + 47 / 60 + 36.1 / 3600),
        ("52:30:15.0N", 52.504166667),
        ("122:25:10W", -(122 + 25 / 60 + 10 / 3600)),
        ("-33:52:00", -(33 + 52 / 60)),
    ],
)
def test_dms_becomes_decimal_degrees(text, degrees):
    assert typed(heading("LOCA", "LOCA_LAT", "DMS"), text)[0][0] == pytest.approx(
        degrees
    )


def test_raw_only_columns_are_blank_with_no_flags():
    column = heading("LOCA", "LOCA_FDEP", "2DP", "m", file_unit="Ft")
    assert column.status == u.RAW_ONLY
    assert typed(column, "10.00", "NP") == ([None, None], [], [])


def test_site_file_flags():
    ags = _read.read(DATA / "site_si.ags")
    dictionary, _ = _dictionary.for_file(ags)
    headings, _ = u.resolve(ags, dictionary)
    found = {}
    for group, table in ags.tables.items():
        for name in ags.headings[group]:
            _, flags, findings = _values.type_column(
                headings[group, name], list(table[name]), list(table["_line"])
            )
            assert findings == [], (group, name)
            found.update({(group, f.heading, f.row): f.flag for f in flags})
        rows = table.to_dict("records")
        found.update(
            {
                (group, f.heading, f.row): f.flag
                for f in _values.refusal_flags(group, ags.headings[group], rows)
            }
        )
    assert found == {
        ("ISPT", "ISPT_NVAL", 2): "REFUSAL",
        ("ISPT", "ISPT_WAT", 5): "DRY",
        ("LLPL", "LLPL_PL", 2): "NP",
        ("LLPL", "LLPL_PL", 4): "NP",
        ("GRAG", "GRAG_PDEN", 1): "ASSUMED",
        ("FGHG", "FGHG_ILUG", 1): "LT",
        ("FGHS", "FGHS_ILUG", 1): "LT",
        ("FGHS", "FGHS_ILUG", 2): "GT",
    }
