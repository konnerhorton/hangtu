"""The judgments file (docs/work/m13a-judgments.md, Spec Decisions 1 and 3)."""

import hashlib
import textwrap

import pytest

import hangtu as ht
from hangtu._judgments import as_judgments

SAMPLE = """\
unit_weight:
  by: geology_unit
  units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
  project: {bulk_unit_weight: 19.0, reason: "median LDEN of all units, n=41"}
  values:
    Fill:     {bulk_unit_weight: 18.5, reason: "median LDEN, n=12"}
    Alluvium: {bulk_unit_weight: 19.0, saturated_unit_weight: 20.0}
water_level:
  units: {depth: m}
  project: {depth: 3.0, reason: "highest standpipe reading, 2026-09"}
  by_hole:
    BH01: {depth: 2.5, reason: standpipe reading 2026-09-14}
"""


def write(tmp_path, text, name="judgments.yaml"):
    path = tmp_path / name
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def test_the_spec_sample_reads(tmp_path):
    path = write(tmp_path, SAMPLE)
    read = ht.judgments(path).read()
    assert read.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    unit_weight = read.judgments["unit_weight"]
    assert unit_weight.by == "geology_unit"
    assert unit_weight.values["Alluvium"].values == {
        "bulk_unit_weight": 19.0,
        "saturated_unit_weight": 20.0,
    }
    assert unit_weight.values["Fill"].reason == "median LDEN, n=12"
    assert unit_weight.project.values == {"bulk_unit_weight": 19.0}
    water_level = read.judgments["water_level"]
    assert water_level.by == "loca_id"
    assert water_level.units == {"depth": "m"}
    assert water_level.values["BH01"].values == {"depth": 2.5}


def test_an_empty_file_holds_no_judgments(tmp_path):
    assert ht.judgments(write(tmp_path, "")).read().judgments == {}


def test_a_water_level_above_ground_reads(tmp_path):
    path = write(
        tmp_path,
        """\
        water_level:
          units: {depth: m}
          by_hole:
            BH01: {depth: -1.2}
        """,
    )
    entry = ht.judgments(path).read().judgments["water_level"].values["BH01"]
    assert entry.values == {"depth": -1.2}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            "unitweight: {}",
            r"judgments.yaml: 'unitweight' isn't a judgment.*unit_weight, water_level",
        ),
        ("- 1", r"judgments.yaml: the file must map judgment names"),
        (
            "unit_weight: {units: {bulk_unit_weight: kN/m3}, value: {}}",
            r"judgments.yaml, unit_weight: 'value' isn't a section.*values",
        ),
        (
            "unit_weight: {by: geology_unit, values: {Fill: {bulk_unit_weight: 18}}}",
            r"judgments.yaml, unit_weight: 'units' is missing",
        ),
        (
            "unit_weight: {units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 18}}}",
            r"judgments.yaml, unit_weight: 'by' is missing",
        ),
        (
            "unit_weight: {units: {bulk_unit_weight: kN/m3},"
            " project: {bulk_unit_weight: 18}}",
            r"judgments.yaml, unit_weight, project: 'reason' is missing",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kPa},"
            " values: {Fill: {bulk_unit_weight: 18}}}",
            r"judgments.yaml, unit_weight, units.bulk_unit_weight: .*unit weight",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kNpm3},"
            " values: {Fill: {bulk_unit_weight: 18}}}",
            r"judgments.yaml, unit_weight, units.bulk_unit_weight: .*isn't recognized",
        ),
        (
            "unit_weight: {by: geology_unit, units: {density: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 18}}}",
            r"unit_weight, units: 'density' isn't a field.*bulk_unit_weight",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 18, saturated_unit_weight: 20}}}",
            r"unit_weight, values.Fill, saturated_unit_weight: has no unit",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {saturated_unit_weight: 20}}}",
            r"unit_weight, values.Fill: 'bulk_unit_weight' is missing",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 0}}}",
            r"unit_weight, values.Fill, bulk_unit_weight: must be a positive number",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: heavy}}}",
            r"values.Fill, bulk_unit_weight: must be a positive number, not 'heavy'",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 18, colour: red}}}",
            r"unit_weight, values.Fill: 'colour' isn't a field",
        ),
        (
            "unit_weight: {by: geology_unit, units: {bulk_unit_weight: kN/m3},"
            " values: {Fill: {bulk_unit_weight: 18, reason: median, n=12}}}",
            r"values.Fill: 'n=12' isn't a field.*put the reason in quotes",
        ),
        (
            "water_level: {units: {depth: m}, by_hole: {BH01: {}}}",
            r"water_level, by_hole.BH01: give exactly one of depth or elevation",
        ),
        (
            "water_level: {units: {depth: m, elevation: m},"
            " by_hole: {BH01: {depth: 1, elevation: 9}}}",
            r"water_level, by_hole.BH01: give exactly one of depth or elevation",
        ),
        (
            "water_level: {units: {depth: kN/m3}, by_hole: {BH01: {depth: 1}}}",
            r"water_level, units.depth: .*length",
        ),
        (
            "water_level: {by: loca_id, units: {depth: m}}",
            r"water_level: 'by' isn't a section.*units, project, by_hole",
        ),
        (
            "water_level: {units: {depth: m}, by_hole: {yes: {depth: 1}}}",
            r"water_level, by_hole: the key True isn't text.*quotes",
        ),
        (
            "water_level: {units: {depth: m}, by_hole: {1: {depth: 1}}}",
            r"water_level, by_hole: the key 1 isn't text",
        ),
        (
            "water_level:\n  units: {depth: m\n",
            r"The judgments file '.*judgments.yaml' isn't valid YAML at line 3",
        ),
    ],
)
def test_file_errors_name_the_file_judgment_and_entry(tmp_path, text, message):
    # Criterion 5.
    path = write(tmp_path, text)
    with pytest.raises(ht.HangtuError, match=message):
        ht.judgments(path)


def test_a_missing_file_says_so(tmp_path):
    with pytest.raises(FileNotFoundError, match="No judgments file at"):
        ht.judgments(tmp_path / "nowhere.yaml")


def test_repr_lists_values_units_and_reasons(tmp_path):
    text = repr(ht.judgments(write(tmp_path, SAMPLE)))
    assert text.startswith("Judgments('")
    assert "  unit_weight, by geology_unit:" in text
    assert "    Fill: bulk_unit_weight 18.5 kN/m3 (median LDEN, n=12)" in text
    assert (
        "    Alluvium: bulk_unit_weight 19 kN/m3, saturated_unit_weight 20 kN/m3"
        in text
    )
    assert "  water_level, by hole:" in text
    assert "    BH01: depth 2.5 m (standpipe reading 2026-09-14)" in text
    assert "    project: depth 3 m (highest standpipe reading, 2026-09)" in text


def test_repr_of_a_file_broken_since_opening_says_so(tmp_path):
    path = write(tmp_path, SAMPLE)
    j = ht.judgments(path)
    path.write_text("unitweight: {}", encoding="utf-8")
    assert "can't be read: judgments.yaml: 'unitweight'" in repr(j)


def test_read_after_an_edit_returns_the_new_values_and_hash(tmp_path):
    # Half of criterion 6; the other half is in tests/analysis.
    path = write(tmp_path, SAMPLE)
    j = ht.judgments(path)
    before = j.read()
    path.write_text(SAMPLE.replace("BH01: {depth: 2.5", "BH01: {depth: 4.0"))
    after = j.read()
    assert after.sha256 != before.sha256
    assert after.judgments["water_level"].values["BH01"].values == {"depth": 4.0}


def test_judgments_argument_takes_an_object_a_path_or_none(tmp_path):
    path = write(tmp_path, SAMPLE)
    j = ht.judgments(path)
    assert as_judgments(j) is j
    assert as_judgments(str(path)).path == path
    assert as_judgments(None) is None
    with pytest.raises(ht.HangtuError, match=r"judgments= takes ht.judgments"):
        as_judgments({"unit_weight": 19})


# Gs (docs/work/m14b-phase-relations.md, Decision 4; AC 8).
SPECIFIC_GRAVITY = """\
specific_gravity:
  by: geology_unit
  project: {specific_gravity: 2.70, reason: "quartz sands"}
  values:
    Alluvium: {specific_gravity: 2.68, reason: "median of 6 LPDN, measured"}
"""


def test_specific_gravity_reads_without_units(tmp_path):
    judgment = (
        ht.judgments(write(tmp_path, SPECIFIC_GRAVITY))
        .read()
        .judgments["specific_gravity"]
    )
    assert judgment.by == "geology_unit"
    assert judgment.values["Alluvium"].values == {"specific_gravity": 2.68}
    assert judgment.project.values == {"specific_gravity": 2.70}


def test_repr_shows_specific_gravity_without_a_unit(tmp_path):
    text = repr(ht.judgments(write(tmp_path, SPECIFIC_GRAVITY)))
    assert "specific_gravity, by geology_unit:" in text
    assert "Alluvium: specific_gravity 2.68 (median of 6 LPDN, measured)" in text


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("units: {specific_gravity: '%'}\n  ", "takes no units"),
        ("", "Alluvium, specific_gravity: must be a positive number, not 0"),
    ],
)
def test_specific_gravity_errors(tmp_path, entry, message):
    value = "0" if not entry else "2.68"
    text = (
        "specific_gravity:\n  by: geology_unit\n  "
        + entry
        + "values:\n    Alluvium: {specific_gravity: "
        + value
        + "}\n"
    )
    with pytest.raises(ht.HangtuError, match=message):
        ht.judgments(write(tmp_path, text))


def test_specific_gravity_outside_the_plausible_range_warns(tmp_path):
    text = (
        "specific_gravity:\n  by: geology_unit\n"
        "  values:\n    Peat: {specific_gravity: 1.5}\n"
    )
    with pytest.warns(
        UserWarning, match=r"Peat, specific_gravity: 1.5 is outside 2-3.2"
    ):
        ht.judgments(write(tmp_path, text))


# --- significance_level (docs/work/m15d-compare.md, Decision 8) ----------------------

ALPHA = (
    "significance_level:\n"
    '  project: {significance_level: 0.05, reason: "the usual convention"}\n'
)


def test_significance_level_reads_as_one_project_value(tmp_path):
    judgment = (
        ht.judgments(write(tmp_path, ALPHA)).read().judgments["significance_level"]
    )
    assert judgment.by is None
    assert judgment.values == {}
    assert judgment.project.values == {"significance_level": 0.05}
    assert judgment.project.reason == "the usual convention"


def test_repr_shows_significance_level(tmp_path):
    text = repr(ht.judgments(write(tmp_path, ALPHA)))
    assert "significance_level:" in text
    assert "project: significance_level 0.05 (the usual convention)" in text


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            "significance_level:\n  by: geology_unit\n",
            r"significance_level takes only project:.*not by:",
        ),
        (
            "significance_level:\n  values:\n    Fill: {significance_level: 0.05}\n",
            r"significance_level takes only project:.*not values:",
        ),
        (
            "significance_level:\n  units: {significance_level: '%'}\n",
            "takes no units",
        ),
        ("significance_level: {}\n", r"significance_level: 'project' is missing"),
        (
            "significance_level:\n  project: {significance_level: 0.05}\n",
            r"significance_level, project: 'reason' is missing.*every call",
        ),
        (
            "significance_level:\n  project: {significance_level: 0, reason: x}\n",
            r"significance_level: must be a number between 0 and 1, e.g. 0.05, not 0",
        ),
        (
            "significance_level:\n  project: {significance_level: 1, reason: x}\n",
            r"between 0 and 1.*not 1",
        ),
    ],
)
def test_significance_level_errors(tmp_path, text, message):
    # Criterion 9: a values: entry is an error; 0 and 1 are errors.
    with pytest.raises(ht.HangtuError, match=message):
        ht.judgments(write(tmp_path, text))


def test_significance_level_outside_the_plausible_range_warns(tmp_path):
    text = "significance_level:\n  project: {significance_level: 0.3, reason: x}\n"
    with pytest.warns(UserWarning, match=r"significance_level: 0.3 is outside"):
        ht.judgments(write(tmp_path, text))
