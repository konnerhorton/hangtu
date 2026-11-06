"""friction_angle_from_shear_box(): docs/work/m18d-sources-compared.md, AC 1-4.

G1 is the spec's, hand-calculated from Kulhawy & Mayne (1990) Eq. 4-10 and
Tables 4-2 and 4-5 with Python's math, not from the implementation. The frames
are built so the free line's angle is exactly φ′ds: τ = 5 + σn tan φ′ds.
"""

import hashlib
import json
import math
import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

REL = 1e-6
NAME = "critical_state_friction_angle"
BELOW = r"φ′ds < tan⁻¹\(sin φ′cv\) in Terrace \(free\)"
#: G1: (φ′ds, φ′cv) -> (φ′psc, φ′tc cohesionless, φ′tc NC cohesive, below).
G1 = [
    ((30, 32), (34.2470, 30.5777, 31.1336, False)),
    ((28, 30), (31.5485, 28.1683, 28.6804, False)),
    ((25, 33), (29.0744, 25.9593, 26.4313, True)),
]
FILE = """\
critical_state_friction_angle:
  by: geology_unit
  units: {critical_state_friction_angle: deg}
  values:
    Terrace: {critical_state_friction_angle: 32, reason: "ring shear, BH02 4.0 m"}
    Alluvium: {critical_state_friction_angle: 30, reason: "literature, silty sand"}
"""


def _frame(angles, normal=(50.0, 100.0, 200.0), intercept=5.0, **columns):
    """Stages τ = c + σn tan φ′ds per unit, ``angles`` as {geology_unit: φ′ds}."""
    rows = []
    for unit, angle in angles.items():
        for sigma in normal:
            rows.append(
                {
                    "geology_unit": unit,
                    "applied_normal_stress": sigma,
                    "peak_shear_stress": intercept
                    + sigma * math.tan(math.radians(angle)),
                    "residual_shear_stress": sigma * math.tan(math.radians(20)),
                }
            )
    df = pd.DataFrame(rows)
    for name, values in columns.items():
        df[name] = values
    df.attrs["units"] = {
        "applied_normal_stress": "kPa",
        "peak_shear_stress": "kPa",
        "residual_shear_stress": "kPa",
    }
    return df


def _fit(angles, **kwargs):
    df = _frame(angles, **{k: v for k, v in kwargs.items() if k != "cohesion"})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.shear_box_fit(
            df, group_by="geology_unit", cohesion=kwargs.get("cohesion")
        )


def _convert(fit, **kwargs):
    """Convert, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.analysis.friction_angle_from_shear_box(fit, **kwargs)


def _line(result, kind="free", group=0):
    return next(
        line for line in result.groups[group]["lines"] if line["line_kind"] == kind
    )


def _file(tmp_path, text=FILE):
    path = tmp_path / "judgments.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- AC 1, 4: G1, both soils, below critical state -----------------------------------


@pytest.mark.parametrize(("given", "expected"), G1)
def test_g1_both_soils(given, expected):
    friction, critical = given
    plane_strain, cohesionless, cohesive, below = expected
    fit = _fit({"Terrace": friction})
    results = {}
    for soil in ("cohesionless", "normally_consolidated_cohesive"):
        call = ht.analysis.friction_angle_from_shear_box
        kwargs = {"soil": soil, NAME: critical}
        if below:
            with pytest.warns(UserWarning, match=BELOW) as caught:
                results[soil] = call(fit, **kwargs)
            assert len(caught) == 1
        else:
            results[soil] = _convert(fit, **kwargs)
    for soil, tc in (
        ("cohesionless", cohesionless),
        ("normally_consolidated_cohesive", cohesive),
    ):
        line = _line(results[soil])
        assert line["peak_friction_angle"] == pytest.approx(friction, rel=REL)
        assert line["plane_strain_friction_angle"] == pytest.approx(
            plane_strain, abs=1e-4
        )
        assert line["effective_friction_angle"] == pytest.approx(tc, abs=1e-4)
        assert line["below_critical_state"] is below
        assert line["no_conversion_reason"] is None
        # K&M p. 4-12: φ′psc some 2 to 7 degrees above φ′ds.
        assert 2 < line["plane_strain_friction_angle"] - friction < 7


def test_g1_below_critical_state_is_flagged_and_noted():
    fit = _fit({"Terrace": 25})
    with pytest.warns(UserWarning, match=BELOW):
        result = ht.analysis.friction_angle_from_shear_box(
            fit, soil="cohesionless", critical_state_friction_angle=33
        )
    assert math.degrees(math.atan(math.sin(math.radians(33)))) == pytest.approx(
        28.5744, abs=1e-4
    )
    frame = result.to_frame()
    assert frame.loc[frame["line_kind"] == "free", "below_critical_state"].item()
    assert any("Below critical state" in note for note in result.notes)


def test_soil_mapping_by_geology_unit():
    fit = _fit({"Alluvium": 28, "Terrace": 30})
    result = _convert(
        fit,
        soil={"Terrace": "cohesionless", "Alluvium": "normally_consolidated_cohesive"},
        critical_state_friction_angle={"Terrace": 32, "Alluvium": 30},
    )
    frame = result.to_frame().set_index(["geology_unit", "line_kind"])
    assert frame.loc[("Terrace", "free"), "effective_friction_angle"] == pytest.approx(
        30.5777, abs=1e-4
    )
    assert frame.loc[("Alluvium", "free"), "effective_friction_angle"] == (
        pytest.approx(28.6804, abs=1e-4)
    )
    assert frame.loc[("Alluvium", "free"), "conversion_soil"] == (
        "normally_consolidated_cohesive"
    )
    assert result.soil == {
        "Terrace": "cohesionless",
        "Alluvium": "normally_consolidated_cohesive",
    }


def test_both_line_kinds_converted_main_line_first():
    fit = _fit({"Terrace": 30}, cohesion=0)
    result = _convert(fit, soil="cohesionless", critical_state_friction_angle=32)
    kinds = [line["line_kind"] for line in result.groups[0]["lines"]]
    assert kinds == ["through_origin", "free"]
    origin = _line(result, "through_origin")
    fitted = fit.groups[0]["strengths"]["peak"]["lines"][0]["friction_angle"]
    assert origin["peak_friction_angle"] == fitted
    expected = math.degrees(
        math.atan(math.tan(math.radians(fitted)) / math.cos(math.radians(32)))
    )
    assert origin["plane_strain_friction_angle"] == pytest.approx(expected, rel=REL)
    assert origin["effective_friction_angle"] == pytest.approx(expected / 1.12, rel=REL)


def test_residual_and_cohesion_kept_with_notes():
    fit = _fit({"Terrace": 30})
    result = _convert(fit, soil="cohesionless", critical_state_friction_angle=32)
    line = _line(result)
    assert line["peak_cohesion"] == pytest.approx(5.0, rel=REL)
    assert line["residual_friction_angle"] == pytest.approx(20.0, rel=REL)
    notes = " ".join(result.notes)
    assert "independent of test type (Kulhawy & Mayne 1990, p. 4-10)" in notes
    assert "peak_cohesion is kept as fitted" in notes
    assert "effective and the test as drained (ASTM D3080)" in notes
    assert "Speculative" not in notes
    cohesive = _convert(
        fit, soil="normally_consolidated_cohesive", critical_state_friction_angle=32
    )
    assert "effective and the test as drained" in " ".join(cohesive.notes)
    assert '"Speculative, based on results from sand"' in " ".join(cohesive.notes)


def test_to_frame_columns_units_views_and_points():
    df = _frame({"Terrace": 30}, depth=[4.0, 6.5, 9.0])
    df.attrs["units"]["depth"] = "m"
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    result = _convert(fit, soil="cohesionless", critical_state_friction_angle=32)
    frame = result.to_frame()
    assert list(frame.columns) == [
        "geology_unit",
        "line_kind",
        "peak_friction_angle",
        "critical_state_friction_angle",
        "conversion_soil",
        "plane_strain_friction_angle",
        "effective_friction_angle",
        "conversion_name",
        "below_critical_state",
        "count",
        "lowest_normal_stress",
        "highest_normal_stress",
        "no_conversion_reason",
    ]
    assert set(frame["conversion_name"]) == {
        "friction_angle_from_shear_box_kulhawy_mayne_1990"
    }
    assert frame.attrs["units"]["effective_friction_angle"] == "deg"
    assert frame.attrs["units"]["lowest_normal_stress"] == "kPa"
    assert list(frame["count"]) == [3, 3]
    assert [p["depth"] for p in result.groups[0]["points"]] == [4.0, 6.5, 9.0]
    assert result.depth_units == {"depth": "m"}
    record = json.loads(json.dumps(result.to_dict()))
    assert record["kind"] == "derived"
    assert record["function"] == "friction_angle_from_shear_box"
    text = str(result)
    assert "Terrace: cohesionless, φ′psc = 1.12 φ′tc (Table 4-2, p. 4-14)" in text
    assert "free: φ′ds 30.0° → φ′psc 34.2° → φ′tc 30.6°, 3 points" in text
    assert repr(result) == text


def test_names_are_registered():
    registered = set(ht.columns()["name"])
    for name in (
        "critical_state_friction_angle",
        "plane_strain_friction_angle",
        "effective_friction_angle",
        "peak_friction_angle",
        "conversion_name",
        "conversion_soil",
    ):
        assert name in registered


# --- AC 4: lines with no value -------------------------------------------------------


def test_a_line_with_no_fit_keeps_its_reason():
    df = _frame({"Terrace": 30}, normal=(100.0,))
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    free = fit.groups[0]["strengths"]["peak"]["lines"][0]
    assert free["no_fit_reason"]
    result = _convert(fit, soil="cohesionless", critical_state_friction_angle=32)
    line = _line(result)
    assert line["no_conversion_reason"] == free["no_fit_reason"]
    assert math.isnan(line["effective_friction_angle"])
    assert line["below_critical_state"] is None
    assert _line(result, "through_origin")["no_conversion_reason"] is None


def test_a_zero_angle_gets_no_value_and_needs_no_judgment():
    df = _frame({"Terrace": 0}, intercept=0.0)
    df["peak_shear_stress"] = 0.0
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    result = _convert(fit, soil="cohesionless")
    for kind in ("free", "through_origin"):
        line = _line(result, kind)
        assert line["no_conversion_reason"] == (
            "φ′ds is 0°: Eq. 4-10 converts a friction angle above 0°"
        )
    assert NAME not in result.judgments


# --- AC 2: soil= ---------------------------------------------------------------------


def test_soil_missing_names_both():
    with pytest.raises(HangtuError, match=r"needs soil=: \"cohesionless\".*Table 4-2"):
        ht.analysis.friction_angle_from_shear_box(
            _fit({"Terrace": 30}), critical_state_friction_angle=32
        )


@pytest.mark.parametrize("soil", ["overconsolidated", "rock", "sand", 1.12])
def test_soil_outside_the_tables(soil):
    with pytest.raises(
        HangtuError,
        match=r"must be \"cohesionless\".*\"normally_consolidated_cohesive\".*"
        r"overconsolidated cohesive soils, rock and rock joints aren't covered.*"
        r"peak_friction_angle unconverted",
    ):
        ht.analysis.friction_angle_from_shear_box(
            _fit({"Terrace": 30}), soil=soil, critical_state_friction_angle=32
        )


def test_soil_mapping_missing_a_unit_names_it():
    fit = _fit({"Alluvium": 28, "Terrace": 30})
    with pytest.raises(
        HangtuError, match=r"no soil type for the geology_unit 'Alluvium'"
    ):
        ht.analysis.friction_angle_from_shear_box(
            fit,
            soil={"Terrace": "cohesionless"},
            critical_state_friction_angle={"Terrace": 32, "Alluvium": 30},
        )


def test_a_mapping_needs_the_fit_grouped_by_geology_unit():
    df = _frame({"Terrace": 30})
    fit = ht.analysis.shear_box_fit(df)
    with pytest.raises(
        HangtuError, match=r"soil= is keyed by geology_unit.*group_by='geology_unit'"
    ):
        ht.analysis.friction_angle_from_shear_box(
            fit, soil={"Terrace": "cohesionless"}, critical_state_friction_angle=32
        )
    result = _convert(fit, soil="cohesionless", critical_state_friction_angle=32)
    assert _line(result)["effective_friction_angle"] == pytest.approx(30.5777, abs=1e-4)


def test_not_a_shear_box_fit():
    with pytest.raises(HangtuError, match=r"takes the ShearBoxFit.*not DataFrame"):
        ht.analysis.friction_angle_from_shear_box(
            _frame({"Terrace": 30}), soil="cohesionless"
        )


# --- AC 3: φ′cv ---------------------------------------------------------------------


def test_cv_from_the_argument_is_recorded():
    result = _convert(
        _fit({"Terrace": 30}), soil="cohesionless", critical_state_friction_angle=32
    )
    assert result.groups[0]["critical_state_friction_angle"] == 32
    assert result.groups[0]["critical_state_friction_angle_source"] == "argument"
    assert result.judgments[NAME] == {
        "source": "argument",
        "by": None,
        "values": {"all": "32 deg"},
    }
    mapped = _convert(
        _fit({"Terrace": 30}),
        soil="cohesionless",
        critical_state_friction_angle={"Terrace": 32},
    )
    assert mapped.judgments[NAME]["by"] == "geology_unit"
    assert mapped.judgments[NAME]["values"] == {"Terrace": "32 deg"}


def test_cv_from_judgments_argument(tmp_path):
    path = _file(tmp_path)
    fit = _fit({"Alluvium": 28, "Terrace": 30})
    result = _convert(
        fit,
        soil={"Terrace": "cohesionless", "Alluvium": "cohesionless"},
        judgments=path,
    )
    frame = result.to_frame().set_index(["geology_unit", "line_kind"])
    assert frame.loc[("Terrace", "free"), "critical_state_friction_angle"] == 32
    assert frame.loc[("Alluvium", "free"), "effective_friction_angle"] == (
        pytest.approx(28.1683, abs=1e-4)
    )
    record = result.judgments[NAME]
    assert record["source"] == str(path)
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["by"] == "geology_unit"
    assert record["values"]["Terrace"] == {
        NAME: "32 deg",
        "reason": "ring shear, BH02 4.0 m",
    }
    terrace = next(g for g in result.groups if g["key"]["geology_unit"] == "Terrace")
    assert terrace["critical_state_friction_angle_source"] == "judgments.yaml"
    assert terrace["critical_state_friction_angle_reason"] == "ring shear, BH02 4.0 m"
    assert "φ′cv = 32.0° (judgments.yaml: ring shear, BH02 4.0 m)" in str(result)


def test_cv_from_the_projects_file_through_the_fit(tmp_path):
    path = _file(tmp_path)
    df = _frame({"Terrace": 30})
    df.attrs["judgments_file"] = str(path)
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    assert fit.judgments_file == str(path)
    result = _convert(fit, soil="cohesionless")
    assert _line(result)["effective_friction_angle"] == pytest.approx(30.5777, abs=1e-4)
    assert result.judgments[NAME]["source"] == str(path)
    assert result.judgments_file == str(path)


def test_cv_argument_replaces_the_file_with_a_warning(tmp_path):
    df = _frame({"Terrace": 30})
    df.attrs["judgments_file"] = str(_file(tmp_path))
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    with pytest.warns(UserWarning, match=r"replaces the critical_state_friction_angle"):
        result = ht.analysis.friction_angle_from_shear_box(
            fit, soil="cohesionless", critical_state_friction_angle={"Terrace": 30}
        )
    assert result.groups[0]["critical_state_friction_angle"] == 30


def test_cv_missing_names_it_its_key_and_how_to_set_it(tmp_path):
    fit = _fit({"Terrace": 30})
    with pytest.raises(
        HangtuError,
        match=r"needs critical_state_friction_angle, φ′cv, keyed by geology_unit: "
        r"no judgments file.*Pass critical_state_friction_angle=.*p.set_judgments",
    ):
        ht.analysis.friction_angle_from_shear_box(fit, soil="cohesionless")
    other = _file(
        tmp_path,
        "significance_level:\n  project: {significance_level: "
        '0.05, reason: "the usual convention"}\n',
    )
    with pytest.raises(HangtuError, match=r"judgments.yaml has no critical_state"):
        ht.analysis.friction_angle_from_shear_box(
            fit, soil="cohesionless", judgments=other
        )


def test_cv_file_missing_a_unit_names_it(tmp_path):
    fit = _fit({"Fill": 30, "Terrace": 30})
    with pytest.raises(
        HangtuError,
        match=r"The judgments file's critical_state_friction_angle has no "
        r"critical_state_friction_angle, φ′cv, for the geology_unit 'Fill'",
    ):
        ht.analysis.friction_angle_from_shear_box(
            fit, soil="cohesionless", judgments=_file(tmp_path)
        )


def test_cv_one_number_for_several_groups():
    fit = _fit({"Alluvium": 28, "Terrace": 30})
    with pytest.raises(
        HangtuError, match=r"is one number, but the fit has 2 groups.*SPEC §4"
    ):
        ht.analysis.friction_angle_from_shear_box(
            fit, soil="cohesionless", critical_state_friction_angle=32
        )


@pytest.mark.parametrize("value", [0, 90, -5, 120, "32 deg", True, np.nan])
def test_cv_out_of_range(value):
    with pytest.raises(HangtuError, match=r"critical_state_friction_angle="):
        ht.analysis.friction_angle_from_shear_box(
            _fit({"Terrace": 30}),
            soil="cohesionless",
            critical_state_friction_angle={"Terrace": value},
        )


def test_cv_file_entry_without_a_reason(tmp_path):
    text = FILE.replace(', reason: "ring shear, BH02 4.0 m"', "")
    with pytest.raises(HangtuError, match=r"values.Terrace: 'reason' is missing"):
        ht.analysis.friction_angle_from_shear_box(
            _fit({"Terrace": 30}), soil="cohesionless", judgments=_file(tmp_path, text)
        )


def test_cv_mapping_with_an_unknown_unit_warns():
    with pytest.warns(UserWarning, match=r"has values for 'Terace'"):
        ht.analysis.friction_angle_from_shear_box(
            _fit({"Terrace": 30}),
            soil="cohesionless",
            critical_state_friction_angle={"Terrace": 32, "Terace": 31},
        )
