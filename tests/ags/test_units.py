"""Heading units on ingest (docs/data/ingest.md §7)."""

from pathlib import Path

import pytest

from hangtu.ags import _dictionary, _read
from hangtu.ags import _units as u
from hangtu.ags._dictionary import Heading

DATA = Path(__file__).parents[1] / "data" / "ags"


def standard(unit, ags_type="2DP", source="4.2"):
    return Heading("GRP", "GRP_X", "OTHER", ags_type, unit, source)


def resolve(file_unit, entry, file_type="2DP", system="SI", defined=None):
    return u.resolve_heading(
        "GRP", "GRP_X", file_unit, file_type, entry, system, 7, defined
    )


def converted(file_unit, entry, value, **kwargs):
    result, finding = resolve(file_unit, entry, **kwargs)
    assert result.status == u.CONVERTED, finding
    return result.convert([value])[0], result, finding


@pytest.mark.parametrize(
    ("file_unit", "dictionary_unit", "value", "expected"),
    [
        ("ft", "m", 10.0, 3.048),
        ("psf", "kPa", 2000.0, 95.76052),
        ("tsf", "kPa", 1.5, 143.64078),
        ("t/m2", "kPa", 2.0, 19.6133),
        ("cm/s", "m/s", 1.0e-3, 1.0e-5),
        ("in", "mm", 6.0, 152.4),
        ("m", "m", 2.5, 2.5),
        ("degC", "DegC", 105.0, 105.0),  # AGS 4.0.x spelling
        ("Bar", "bar", 1.0, 1.0),
    ],
)
def test_converts_to_the_dictionary_unit(file_unit, dictionary_unit, value, expected):
    result, heading, finding = converted(file_unit, standard(dictionary_unit), value)
    assert result == pytest.approx(expected, rel=1e-6)
    assert heading.unit == dictionary_unit
    assert finding is None


def test_quantity_kind_of_the_canonical_unit():
    assert resolve("ft", standard("m"))[0].quantity == "length"
    assert resolve("psf", standard("kPa"))[0].quantity == "stress"
    assert resolve("%", standard("%"))[0].quantity == "percent"


@pytest.mark.parametrize(
    ("group", "heading"),
    [("GRAT", "GRAT_SIZE"), ("LLPL", "LLPL_SIZE"), ("PTST", "PTST_SZUN")],
)
def test_particle_sizes_are_the_particle_size_kind(group, heading):
    # datasets.md §10: mm in US output too, not inches (TODO #17).
    entry = Heading(group, heading, "OTHER", "3SF", "mm", "4.2")
    result, finding = u.resolve_heading(group, heading, "in", "3SF", entry, "US", 7)
    assert (result.quantity, result.unit, finding) == ("particle_size", "mm", None)
    assert result.convert([1.0])[0] == pytest.approx(25.4)


def test_other_mm_headings_stay_small_lengths():
    entry = Heading("ISPT", "ISPT_NPEN", "OTHER", "0DP", "mm", "4.2")
    result, _ = u.resolve_heading("ISPT", "ISPT_NPEN", "mm", "0DP", entry, "SI", 7)
    assert result.quantity == "small_length"


def test_pcf_in_a_density_heading_is_pounds_per_cubic_foot():
    # P00 §4.3 #1: 125 lb/ft³ = 2.0023 Mg/m³.
    value, heading, finding = converted("pcf", standard("Mg/m3"), 125.0)
    assert value == pytest.approx(2.002308, rel=1e-6)
    assert (heading.unit, heading.quantity) == ("Mg/m3", "density")
    assert finding.rule == "U002" and "density" in finding.message


def test_pcf_in_a_unit_weight_heading_is_pounds_force_per_cubic_foot():
    # P00 §4.3 #1: 125 lbf/ft³ = 19.636 kN/m³.
    value, heading, finding = converted("pcf", standard("kN/m3"), 125.0)
    assert value == pytest.approx(19.63593, rel=1e-6)
    assert (heading.unit, heading.quantity) == ("kN/m3", "unit_weight")
    assert finding.rule == "U002" and "unit weight" in finding.message


def test_pcf_in_a_user_defined_heading_is_not_converted():
    # Even when the UNIT group defines pcf: that doesn't say which pcf it is.
    defined = {"pcf": "pounds per cubic foot"}
    for entry in (None, Heading("GRP", "GRP_X", "OTHER", "2DP", "pcf", "DICT")):
        result, finding = resolve("pcf", entry, defined=defined)
        assert result.status == u.RAW_ONLY
        assert (finding.rule, finding.severity) == ("U001", "error")
        assert "density" in finding.message and "unit weight" in finding.message


@pytest.mark.parametrize(
    ("text", "system", "dictionary_unit", "expected"),
    [
        ("t", "US", "kN", 8.896443),  # short ton-force
        ("t", "SI", "kN", 9.80665),  # metric tonne-force
        ("ton", "US", "kg", 907.18474),
        ("ton", "SI", "kg", 1000.0),
    ],
)
def test_a_bare_ton_follows_the_file_unit_system(
    text, system, dictionary_unit, expected
):
    value, _, finding = converted(text, standard(dictionary_unit), 1.0, system=system)
    assert value == pytest.approx(expected, rel=1e-6)
    assert finding.rule == "U002"


def test_a_bare_ton_with_no_unit_system_is_unknown():
    result, finding = resolve("t", standard("kN"), system=None)
    assert result.status == u.RAW_ONLY and finding.rule == "U001"


def test_unknown_unit_is_u001():
    result, finding = resolve("Ft", standard("m"))
    assert (result.status, result.unit) == (u.RAW_ONLY, None)
    assert (finding.rule, finding.severity, finding.line) == ("U001", "error", 7)
    assert 'Did you mean "ft"?' in finding.message
    assert "raw_GRP only" in finding.message


SWELL = {"%/log cycle": "percent strain per log cycle of stress"}
USER_DEFINED = Heading("GRP", "GRP_X", "OTHER", "2DP", "%/log cycle", "DICT")


@pytest.mark.parametrize("entry", [None, USER_DEFINED])
def test_a_unit_the_file_defines_is_kept_as_written_with_u005(entry):
    result, finding = resolve("%/log cycle", entry, defined=SWELL)
    assert (result.status, result.unit, result.quantity) == (
        u.FILE_UNIT,
        "%/log cycle",
        None,
    )
    assert list(result.convert([1.5])) == [1.5]
    assert (finding.rule, finding.severity, finding.line) == ("U005", "info", 7)
    assert finding.message == (
        'GRP_X (GRP): the unit "%/log cycle" isn\'t one hangtu knows, but the '
        "file's UNIT group defines it (\"percent strain per log cycle of "
        'stress"). The values are kept as written, not converted.'
    )


def test_a_unit_the_file_defines_with_no_description():
    _, finding = resolve("%/log cycle", None, defined={"%/log cycle": ""})
    assert finding.rule == "U005" and "defines it. The values" in finding.message


def test_a_unit_the_file_doesnt_define_is_u001():
    result, finding = resolve("%/log cycle", None, defined={"%": "percent"})
    assert result.status == u.RAW_ONLY and finding.rule == "U001"
    assert "UNIT group" not in finding.message


@pytest.mark.parametrize("listed", ["%/Log cycle", "%/log  cycle"])
def test_the_unit_group_is_matched_exactly(listed):
    result, finding = resolve("%/log cycle", None, defined={listed: "swell"})
    assert result.status == u.RAW_ONLY and finding.rule == "U001"


def test_a_standard_heading_in_a_unit_the_file_defines_is_still_u001():
    result, finding = resolve("Ft", standard("m"), defined={"Ft": "foot"})
    assert result.status == u.RAW_ONLY
    assert (finding.rule, finding.severity) == ("U001", "error")
    assert (
        'The file\'s UNIT group defines it as "foot", but GRP_X is a standard '
        'heading in "m".'
    ) in finding.message


def test_file_units_reads_the_unit_group():
    ags = _read.read(DATA / "site_si.ags")
    defined = u.file_units(ags)
    assert defined["kPa"] == "kilopascal"
    assert defined["yyyy-mm-dd"] == "year month day"


def test_a_unit_only_pint_knows_is_u002():
    value, _, finding = converted("feet", standard("m"), 10.0)
    assert value == pytest.approx(3.048)
    assert (finding.rule, finding.severity) == ("U002", "info")
    assert 'ht.add_unit_alias("feet"' in finding.message


def test_blank_unit_where_the_dictionary_has_one_is_u003():
    result, finding = resolve("", standard("m"))
    assert result.status == u.RAW_ONLY
    assert (finding.rule, finding.severity) == ("U003", "warning")
    assert '"m"' in finding.message


def test_blank_unit_where_the_dictionary_has_none_is_stored_as_is():
    result, finding = resolve("", standard("", "0DP"), file_type="0DP")
    assert (result.status, result.unit, finding) == (u.AS_IS, None, None)
    assert result.convert([12.0])[0] == 12.0


def test_wrong_dimension_is_u004():
    result, finding = resolve("kPa", standard("m"))
    assert result.status == u.RAW_ONLY
    assert (finding.rule, finding.severity) == ("U004", "error")
    assert "a length" in finding.message and "a stress" in finding.message


def test_a_unit_where_the_dictionary_has_none_is_u004():
    assert resolve("%", standard("", "0DP"))[1].rule == "U004"


def test_user_defined_headings_convert_to_the_p00_canonical_unit():
    value, heading, finding = converted("psf", None, 2000.0)
    assert value == pytest.approx(95.76052, rel=1e-6)
    assert (heading.unit, heading.quantity) == ("kPa", "stress")
    assert finding is None
    assert converted("ft", None, 10.0)[1].unit == "m"
    assert converted("%", None, 12.0)[0] == 12.0  # percent stays percent


@pytest.mark.parametrize("text", ["kN/mm", "kg/m", "l/s"])
def test_a_unit_no_quantity_kind_covers_keeps_the_files_string(text):
    value, heading, finding = converted(text, None, 2.0)
    assert value == 2.0
    assert (heading.unit, heading.quantity, finding) == (text, None, None)


def test_micrometers_convert_to_meters():
    value, heading, finding = converted("um", None, 75.0)
    assert value == pytest.approx(75.0e-6)
    assert (heading.unit, heading.quantity, finding) == ("m", "length", None)


@pytest.mark.parametrize(
    ("ags_type", "has_unit", "kind"),
    [
        ("2DP", False, u.NUMBER),
        ("3SF", True, u.NUMBER),
        ("1SCI", True, u.NUMBER),
        ("10SF", True, u.NUMBER),
        ("XN", False, u.NUMBER),
        ("U", False, u.NUMBER),
        ("MC", False, u.NUMBER),
        ("X", True, u.NUMBER),  # LNMC_MC: X with %
        ("X", False, u.TEXT),
        ("ID", False, u.TEXT),
        ("PA", False, u.TEXT),
        ("DT", True, u.DATE),
        ("T", True, u.TIME),
        ("YN", False, u.YES_NO),
        ("DMS", False, u.DMS),
    ],
)
def test_value_kind(ags_type, has_unit, kind):
    assert u.value_kind(ags_type, has_unit) == kind


def test_date_and_time_formats_never_reach_the_unit_parser():
    result, finding = resolve("hh:mm", standard("hh:mm", "T"), file_type="T")
    assert (result.kind, result.unit, finding) == (u.TIME, "s", None)
    result, finding = resolve(
        "yyyy-mm-dd", standard("yyyy-mm-dd", "DT"), file_type="DT"
    )
    assert (result.kind, result.unit, finding) == (u.DATE, None, None)


def _resolve_file(name):
    ags = _read.read(DATA / name)
    dictionary, _ = _dictionary.for_file(ags)
    return ags, *u.resolve(ags, dictionary)


@pytest.mark.parametrize("name", ["site_si.ags", "site_v404.ags"])
def test_good_si_files_need_no_unit_findings(name):
    _, _, findings = _resolve_file(name)
    assert findings == []


def test_us_file_resolves_pcf_by_heading():
    _, headings, findings = _resolve_file("site_us.ags")
    assert {(f.rule, f.heading) for f in findings} == {
        ("U002", "PTST_BDEN"),
        ("U002", "GRAG_PDEN"),
        ("U002", "CPTP_SUW1"),
    }
    assert headings["PTST", "PTST_BDEN"].unit == "Mg/m3"
    assert headings["CPTP", "CPTP_SUW1"].unit == "kN/m3"
    assert headings["XPPT", "XPPT_RES"].unit == "kPa"  # user-defined, tsf


def test_defects_file_unit_findings():
    ags, headings, findings = _resolve_file("defects.ags")
    by_heading = {f.heading: f for f in findings}
    assert {h: f.rule for h, f in by_heading.items()} == {
        "LOCA_FDEP": "U001",
        "SAMP_BASE": "U002",
        "ISPT_CAS": "U003",
        "LOCA_NATE": "U004",
        "XUND_SWEL": "U005",
        "XUND_BLOW": "U001",
    }
    assert by_heading["LOCA_FDEP"].line == ags.unit_lines["LOCA"]
    assert headings["LOCA", "LOCA_FDEP"].status == u.RAW_ONLY
    assert headings["SAMP", "SAMP_BASE"].status == u.CONVERTED
    assert headings["XUND", "XUND_SWEL"].status == u.FILE_UNIT
    assert headings["XUND", "XUND_BLOW"].status == u.RAW_ONLY
    assert headings["XUND", "XUND_STIF"].unit == "kN/mm"
    assert headings["XUND", "XUND_SIZE"].unit == "m"


def test_file_unit_system():
    assert u.file_system(_read.read(DATA / "site_si.ags")) == "SI"
    assert u.file_system(_read.read(DATA / "site_us.ags")) == "US"


def test_meta_heading_standard_flag():
    _, headings, _ = _resolve_file("site_v404.ags")
    assert headings["ISPT", "ISPT_NVAL"].standard
    assert not headings["RUCS", "RUCS_E"].standard  # removed in 4.2
    assert not headings["XPPT", "XPPT_RES"].standard  # user-defined
