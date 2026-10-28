"""ht.analysis.phase_relations() (docs/work/m14b-phase-relations.md).

Acceptance criteria are the spec's (AC n). Golden values are hand-calculated
there, with γw = 9.81 kN/m³ and g = 9.80665 m/s².
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import hangtu as ht

DATA = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-6
#: Gs for the field rows, which have no particle density (AC 4).
GS = {"Fill": 2.70, "Alluvium": 2.70}


def _project(tmp_path, name="site_si", display_units="SI"):
    p = ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path / f"{name}.sqlite",
        display_units=display_units,
    )
    p.set_geology_map(DATA / "strata.csv")
    return p


def _density(p):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return p.density()


def _relations(df, **kwargs):
    kwargs.setdefault("display_units", "SI")
    kwargs.setdefault("specific_gravity", GS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ht.analysis.phase_relations(df, **kwargs)


def _csv(**columns):
    df = pd.DataFrame(columns)
    units = {"bulk_unit_weight": "kN/m3"}
    if "dry_unit_weight" in columns:
        units["dry_unit_weight"] = "kN/m3"
    if "particle_density" in columns:
        units["particle_density"] = "Mg/m3"
    return ht.set_units(df, units)


# --- Golden values --------------------------------------------------------------------


def test_measured_specific_gravity(tmp_path):
    # AC 1: BH1-U1, rho 1.95 Mg/m3, w 25 %, rho_s 2.68.
    df = _density(_project(tmp_path))
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.phase_relations(
            df, display_units="SI", specific_gravity=GS
        )
    row = result.iloc[0]
    assert row["specific_gravity"] == pytest.approx(2.679085, rel=REL)
    assert row["specific_gravity_source"] == "measured"
    assert row["void_ratio"] == pytest.approx(0.7179487, rel=REL)
    assert row["porosity"] == pytest.approx(41.79104, rel=REL)
    assert row["degree_of_saturation"] == pytest.approx(93.28956, rel=REL)
    assert row["saturated_unit_weight"] == pytest.approx(19.398075, rel=REL)
    assert row["dry_unit_weight"] == pytest.approx(15.298374, rel=REL)
    assert not row["oversaturated"]
    assert result.attrs["units"]["saturated_unit_weight"] == "kN/m³"
    assert result.attrs["units"]["porosity"] == "%"
    assert result.attrs["phase_relations"] == {
        "water_unit_weight": "9.81 kN/m3",
        "gravity": "9.80665 m/s2",
        "saturation_tolerance": 5,
    }
    assert [str(w.message).split(" ")[1:6] for w in caught] == [
        ["row", "uses", "a", "particle", "density"]
    ]


def test_water_unit_weight_cancels(tmp_path):
    # AC 2: e and n don't depend on gamma_w; Gs = 2.68 x 9.80665 / 10.
    df = _density(_project(tmp_path))
    before = _relations(df).iloc[0]
    ht.settings.water_unit_weight = "10 kN/m3"
    after = _relations(df).iloc[0]
    assert after["void_ratio"] == pytest.approx(before["void_ratio"], rel=1e-12)
    assert after["porosity"] == pytest.approx(before["porosity"], rel=1e-12)
    assert after["specific_gravity"] == pytest.approx(2.628182, rel=REL)


def test_assumed_specific_gravity(tmp_path):
    # AC 3: BH2-U2, rho 2.02, w 18 %, rho_s #2.65, recompacted.
    row = _relations(_density(_project(tmp_path))).iloc[1]
    assert row["specific_gravity"] == pytest.approx(2.649095, rel=REL)
    assert row["specific_gravity_source"] == "assumed"
    assert row["void_ratio"] == pytest.approx(0.5480198, rel=REL)
    assert row["porosity"] == pytest.approx(35.40134, rel=REL)
    assert row["degree_of_saturation"] == pytest.approx(87.01093, rel=REL)
    assert row["sample_condition"] == "RECOMPACTED"


def test_oversaturated_is_flagged_not_corrected():
    # AC 5: gamma 20.0, w 30 %, Gs 2.70 (rho_s = 2.70 x 9.81 / 9.80665).
    df = _csv(
        loca_id=["BH9"],
        depth=[4.0],
        bulk_unit_weight=[20.0],
        water_content=[30.0],
        particle_density=[2.70 * 9.81 / 9.80665],
        particle_density_assumed=[False],
    )
    with pytest.warns(UserWarning, match=r"above 105 % in BH9 at 4 \(highest 112.2"):
        result = ht.analysis.phase_relations(df)
    row = result.iloc[0]
    assert row["void_ratio"] == pytest.approx(0.721655, rel=REL)
    assert row["degree_of_saturation"] == pytest.approx(112.2420, rel=REL)
    assert row["oversaturated"]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        relaxed = ht.analysis.phase_relations(df, saturation_tolerance=15)
    assert not relaxed.iloc[0]["oversaturated"]


def test_us_twin_agrees(tmp_path):
    # AC 6: the US file gives the same e, n and S; unit weights in pcf.
    si = _relations(_density(_project(tmp_path)))
    us_project = _project(tmp_path, "site_us", display_units="US")
    us = _relations(_density(us_project), display_units="US")
    for column in ("specific_gravity", "void_ratio", "porosity"):
        assert np.allclose(us[column], si[column], rtol=1e-9, equal_nan=True)
    assert np.allclose(
        us["degree_of_saturation"], si["degree_of_saturation"], equal_nan=True
    )
    assert us.attrs["units"]["saturated_unit_weight"] == "pcf"
    # 19.398075 kN/m3 / 0.157087 kN/m3 per pcf
    assert us["saturated_unit_weight"].iloc[0] == pytest.approx(123.4862, rel=1e-4)


# --- Inputs and checks ----------------------------------------------------------------


def test_particle_density_needs_its_assumed_flag():
    # AC 9
    df = _csv(bulk_unit_weight=[19.0], water_content=[20.0], particle_density=[2.7])
    with pytest.raises(ht.ColumnError, match="no particle_density_assumed"):
        ht.analysis.phase_relations(df)


def test_a_blank_assumed_flag_reads_as_measured():
    df = _csv(
        bulk_unit_weight=[19.0],
        water_content=[20.0],
        particle_density=[2.7],
        particle_density_assumed=[None],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ht.analysis.phase_relations(df)
    assert result.iloc[0]["specific_gravity_source"] == "measured"


def test_unit_weight_needs_units():
    # AC 9
    df = pd.DataFrame({"bulk_unit_weight": [19.0], "water_content": [20.0]})
    with pytest.raises(ht.UnitsError, match="'bulk_unit_weight' has no units"):
        ht.analysis.phase_relations(df)


def test_missing_columns_are_named():
    with pytest.raises(ht.ColumnError, match="'water_content'"):
        ht.analysis.phase_relations(_csv(bulk_unit_weight=[19.0]))


def test_blanks_are_counted_by_reason():
    # AC 9
    df = _csv(
        bulk_unit_weight=[np.nan, 19.0, 19.0, 0.0],
        water_content=[20.0, np.nan, 20.0, 20.0],
        particle_density=[2.7, 2.7, np.nan, 2.7],
        particle_density_assumed=[False, False, False, False],
        geology_unit=["Fill", "Fill", None, "Fill"],
    )
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.phase_relations(df, specific_gravity={"Fill": 2.7})
    message = str(caught[0].message)
    assert "1 with no bulk unit weight" in message
    assert "1 with no water content" in message
    assert "1 with a blank geology_unit" in message
    assert "1 with a bulk unit weight of 0 or less" in message
    assert result["void_ratio"].isna().all()
    assert result["oversaturated"].isna().all()


def test_a_given_dry_unit_weight_is_checked_and_kept():
    # AC 10: gamma 19.0, w 20 % -> 15.833; 17.0 is off, 15.9 is within 0.294.
    df = _csv(
        loca_id=["A", "B"],
        depth=[1.0, 2.0],
        bulk_unit_weight=[19.0, 19.0],
        water_content=[20.0, 20.0],
        dry_unit_weight=[17.0, 15.9],
        particle_density=[2.7, 2.7],
        particle_density_assumed=[False, False],
    )
    with pytest.warns(UserWarning, match=r"0.294 kN/m3 .* in A at 1\.") as caught:
        result = ht.analysis.phase_relations(df, display_units="SI")
    assert "B at 2" not in str(caught[0].message)
    assert list(result["dry_unit_weight"]) == [17.0, 15.9]


def test_a_blank_dry_unit_weight_is_filled():
    df = _csv(
        bulk_unit_weight=[19.0],
        water_content=[20.0],
        dry_unit_weight=[np.nan],
        particle_density=[2.7],
        particle_density_assumed=[False],
    )
    result = _relations(df)
    assert result.iloc[0]["dry_unit_weight"] == pytest.approx(19.0 / 1.2)


def test_existing_output_columns_are_replaced_with_a_warning():
    df = _csv(
        bulk_unit_weight=[19.0],
        water_content=[20.0],
        void_ratio=[9.9],
        particle_density=[2.7],
        particle_density_assumed=[False],
    )
    with pytest.warns(UserWarning, match="Replaced the existing columns 'void_ratio'"):
        result = ht.analysis.phase_relations(df)
    assert result.iloc[0]["void_ratio"] != 9.9


def test_the_input_is_unchanged(tmp_path):
    df = _density(_project(tmp_path))
    before = df.copy()
    _relations(df)
    pd.testing.assert_frame_equal(df, before)


# --- Feeds the plots ------------------------------------------------------------------


def test_feeds_p01_and_p07(tmp_path):
    # AC 13
    result = _relations(_density(_project(tmp_path)))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fig, _ = ht.plot.profile(result, "void_ratio", preset="void_ratio")
        plt.close(fig)
        fig, _ = ht.plot.geology_unit_comparison(result, "void_ratio")
        plt.close(fig)


# --- The specific_gravity judgment ----------------------------------------------------

JUDGMENTS = """\
specific_gravity:
  by: geology_unit
  values:
    Fill: {specific_gravity: 2.70, reason: "median LPDN, measured"}
    Alluvium: {specific_gravity: 2.70}
"""


def _judgments(tmp_path, text=JUDGMENTS):
    path = tmp_path / "judgments.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_judgment_specific_gravity(tmp_path):
    # AC 4: the field row BH1 at 0.50 m (Fill): rho 1.85, w 15 %, Gs 2.70.
    p = _project(tmp_path)
    p.set_judgments(_judgments(tmp_path))
    result = _relations(_density(p), specific_gravity=None)
    row = result.iloc[2]
    assert (row["loca_id"], row["depth"]) == ("BH1", pytest.approx(0.5))
    assert row["specific_gravity"] == 2.70
    assert row["specific_gravity_source"] == "judgment"
    assert row["void_ratio"] == pytest.approx(0.6789517, rel=REL)
    assert row["porosity"] == pytest.approx(40.43903, rel=REL)
    assert row["degree_of_saturation"] == pytest.approx(59.65078, rel=REL)
    assert row["saturated_unit_weight"] == pytest.approx(19.74298, rel=REL)
    assert row["dry_unit_weight"] == pytest.approx(15.77592, rel=REL)
    record = result.attrs["judgments"]["specific_gravity"]
    assert record["by"] == "geology_unit"
    assert record["values"]["Fill"] == {
        "specific_gravity": "2.7",
        "reason": "median LPDN, measured",
    }


def test_a_judgment_never_replaces_a_particle_density(tmp_path):
    # AC 3: the assumed 2.65 stays, with a judgment of 2.70 for its unit.
    result = _relations(_density(_project(tmp_path)))
    assert list(result["specific_gravity_source"]) == [
        "measured",
        "assumed",
        "judgment",
        "judgment",
    ]
    assert result.iloc[1]["specific_gravity"] == pytest.approx(2.649095, rel=REL)


def test_the_argument_replaces_the_file_with_a_warning(tmp_path):
    # AC 7
    p = _project(tmp_path)
    p.set_judgments(_judgments(tmp_path))
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.phase_relations(
            _density(p), specific_gravity=2.60, display_units="SI"
        )
    assert any("replaces the specific_gravity in" in str(w.message) for w in caught)
    assert list(result["specific_gravity"].iloc[2:]) == [2.60, 2.60]
    assert result.attrs["judgments"]["specific_gravity"]["source"] == "argument"


def test_judgments_argument_and_attached_file(tmp_path):
    # AC 7: judgments= is read; a frame without attrs needs it.
    df = _density(_project(tmp_path))
    with_file = _relations(df, specific_gravity=None, judgments=_judgments(tmp_path))
    assert with_file.iloc[2]["specific_gravity"] == 2.70
    bare = df.copy()
    bare.attrs = {"units": df.attrs["units"]}
    with pytest.raises(ht.HangtuError, match=r"pass judgments=p\.judgments"):
        ht.analysis.phase_relations(bare)


def test_rows_with_particle_density_need_no_judgment():
    # AC 7
    df = _csv(
        bulk_unit_weight=[19.0],
        water_content=[20.0],
        particle_density=[2.7],
        particle_density_assumed=[False],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ht.analysis.phase_relations(df)


def test_a_missing_judgment_names_it(tmp_path):
    # AC 7
    with pytest.raises(ht.HangtuError, match="2 rows have no particle density"):
        ht.analysis.phase_relations(_density(_project(tmp_path)))


def test_a_unit_missing_from_the_file_is_an_error_or_takes_the_project_value(
    tmp_path,
):
    # AC 7
    p = _project(tmp_path)
    only_fill = (
        "specific_gravity:\n  by: geology_unit\n"
        "  values:\n    Fill: {specific_gravity: 2.70}\n"
    )
    p.set_judgments(_judgments(tmp_path, only_fill))
    with pytest.raises(
        ht.HangtuError, match="no value for the geology unit 'Alluvium'"
    ):
        _relations(_density(p), specific_gravity=None)
    p.set_judgments(
        _judgments(
            tmp_path,
            only_fill + "  project: {specific_gravity: 2.65, reason: quartz sands}\n",
        )
    )
    with pytest.warns(UserWarning) as caught:
        result = ht.analysis.phase_relations(_density(p), display_units="SI")
    assert any(
        "project value 2.65 is used for the geology unit 'Alluvium'" in str(w.message)
        for w in caught
    )
    assert result.iloc[3]["specific_gravity"] == 2.65


def test_a_blank_key_is_counted():
    df = _csv(
        bulk_unit_weight=[19.0, 19.0],
        water_content=[20.0, 20.0],
        geology_unit=["Fill", None],
    )
    with pytest.warns(UserWarning, match="1 with a blank geology_unit"):
        result = ht.analysis.phase_relations(df, specific_gravity={"Fill": 2.7})
    assert list(result["specific_gravity_source"]) == ["judgment", None]


def test_an_unused_argument_warns():
    df = _csv(
        bulk_unit_weight=[19.0],
        water_content=[20.0],
        particle_density=[2.7],
        particle_density_assumed=[False],
    )
    with pytest.warns(UserWarning, match="specific_gravity= isn't used"):
        ht.analysis.phase_relations(df, specific_gravity=2.7)


@pytest.mark.parametrize("value", [0, -1, "2.7", True])
def test_a_bad_argument_is_an_error(value):
    df = _csv(bulk_unit_weight=[19.0], water_content=[20.0])
    with pytest.raises(ht.HangtuError, match="must be a positive number"):
        ht.analysis.phase_relations(df, specific_gravity=value)


def test_units_with_no_rows_here_are_not_warned_about():
    df = _csv(bulk_unit_weight=[19.0], water_content=[20.0], geology_unit=["Fill"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ht.analysis.phase_relations(
            df, specific_gravity={"Fill": 2.7, "Terrace": 2.67}, display_units="SI"
        )
