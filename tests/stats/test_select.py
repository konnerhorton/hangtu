"""select(): computed and given values (docs/work/m18e-selection.md).

Golden values G1, G4 and G5 are the spec's, hand-calculated: G1 from JRC
Formula 4.5, G4 from pint's psf, G5 from test_representative.py's JRC case.
"""

import hashlib
import math
import textwrap

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.errors import HangtuError

PHI = "effective_friction_angle"
SU = "undrained_shear_strength"
#: 1 psf in kPa (exact): 0.45359237 kg × 9.80665 m/s² / 0.3048² m² / 1000.
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
NO_VALUE = r"select\(\) gives no value"

G1_ENTRY = {
    "source": "A",
    "method": "characteristic",
    "estimate": "mean",
    "side": "low",
    "distribution": "normal",
    "reason": "a mean over a long slip surface",
}


def phi(name, values, unit="Sand"):
    """One correlation's φ′ in one unit, at 1 m spacing."""
    frame = pd.DataFrame(
        {
            "geology_unit": unit,
            "loca_id": "BH01",
            "depth": np.arange(1.0, len(values) + 1),
            "correlation_name": name,
            PHI: values,
        }
    )
    return ht.set_units(frame, {PHI: "deg", "depth": "m"})


def g1_sources():
    """G1's source A and G2's source B, in Sand."""
    return phi("A", [34.0, 36.0, 37.0, 38.0, 40.0]), phi(
        "B", [33.0, 35.0, 36.0, 39.0, 41.0]
    )


def su(test_type, values, unit="Clay", stress="kPa"):
    frame = pd.DataFrame(
        {
            "geology_unit": unit,
            "depth": np.arange(1.0, len(values) + 1),
            "test_type": test_type,
            SU: values,
        }
    )
    return ht.set_units(frame, {SU: stress, "depth": "m"})


def write(tmp_path, text, name="judgments.yaml"):
    path = tmp_path / name
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


G1_FILE = """\
selection:
  effective_friction_angle:
    values:
      Sand:
        source: "A"
        method: characteristic
        estimate: mean
        side: low
        distribution: normal
        reason: "a mean over a long slip surface"
"""


# --- G1 through the file (AC 2) ---------------------------------------------------


def test_g1_a_characteristic_value_through_the_file(tmp_path):
    a, b = g1_sources()
    path = write(tmp_path, G1_FILE)
    result = ht.stats.select(a, b, value=PHI, judgments=path)
    frame = result.to_frame()
    row = frame.iloc[0]
    # x̄ = 37, s = √5, k_n = t(0.95, 4) √(1/5): 37 - 0.95339 × 2.2361.
    k_n = stats.t.ppf(0.95, 4) * math.sqrt(1 / 5)
    assert row["value"] == pytest.approx(37.0 - k_n * math.sqrt(5), rel=1e-9)
    assert row["value"] == pytest.approx(34.868, abs=0.001)
    assert (row["geology_unit"], row["parameter_source"], row["selection_method"]) == (
        "Sand",
        "A",
        "characteristic",
    )
    assert row["count"] == 5
    assert row["selection_reason"] == "a mean over a long slip surface"
    assert pd.isna(row["no_value_reason"])
    assert frame.attrs["units"]["value"] == "deg"
    direct = ht.stats.representative(
        a,
        value=PHI,
        by="geology_unit",
        method="characteristic",
        estimate="mean",
        side="low",
        distribution="normal",
    )
    selected = result.representative("Sand")
    pd.testing.assert_frame_equal(selected.to_frame(), direct.to_frame())
    assert selected.groups[0]["statistics"] == direct.groups[0]["statistics"]
    assert result.kind == "parameter"
    assert result.comparison.to_frame().equals(
        ht.stats.compare_sources(a, b, value=PHI).to_frame()
    )


def test_g1_from_a_projects_categorical_geology_unit(tmp_path):
    a, b = g1_sources()
    for frame in (a, b):
        frame["geology_unit"] = pd.Categorical(
            frame["geology_unit"], categories=["Fill", "Sand", "Clay"]
        )
    result = ht.stats.select(
        a, b, value=PHI, selection={"Sand": G1_ENTRY}, judgments=None
    )
    assert result.to_frame()["value"].iloc[0] == pytest.approx(34.868, abs=0.001)
    assert list(result.to_frame()["geology_unit"]) == ["Sand"]


def test_rows_in_another_unit_are_converted_before_the_method():
    kpa = su("UU", [40.0, 50.0, 60.0])
    psf = su("vane", [800.0, 1000.0, 1300.0, 900.0], stress="psf")
    entry = {
        "source": "vane",
        "method": "characteristic",
        "estimate": "mean",
        "side": "low",
        "distribution": "normal",
        "reason": "vane profile",
    }
    result = ht.stats.select(kpa, psf, value=SU, selection={"Clay": entry})
    in_psf = ht.stats.representative(
        psf,
        value=SU,
        by="geology_unit",
        method="characteristic",
        estimate="mean",
        side="low",
        distribution="normal",
    )
    assert result.unit == "kPa"
    assert result.to_frame()["value"].iloc[0] == pytest.approx(
        in_psf.groups[0]["value"] * PSF, rel=1e-9
    )
    assert result.representative("Clay").unit == "kPa"


# --- G4: a value, converted, and for a unit no source has (AC 5) --------------------


def test_g4_a_value_is_converted_to_the_comparisons_unit(tmp_path):
    path = write(
        tmp_path,
        """\
        selection:
          undrained_shear_strength:
            units: {value: psf}
            values:
              Clay: {method: value, value: 500, reason: "adjacent project, vane"}
              Silt: {method: value, value: 600, reason: "no tests; regional report"}
        """,
    )
    result = ht.stats.select(su("UU", [20.0, 25.0, 30.0]), value=SU, judgments=path)
    frame = result.to_frame()
    assert list(frame["geology_unit"]) == ["Clay", "Silt"]
    assert frame["value"].iloc[0] == pytest.approx(500 * 0.0478803, abs=0.001)
    assert frame["value"].iloc[0] == pytest.approx(23.940, abs=0.001)
    assert frame["value"].iloc[1] == pytest.approx(600 * PSF, rel=1e-9)
    assert frame["selection_method"].tolist() == ["value", "value"]
    assert frame["parameter_source"].isna().all()
    assert frame["count"].isna().all()
    assert "Silt: value: 28.7282 kPa (no tests; regional report)." in result.notes


def test_g4_through_the_argument_as_a_quantity():
    result = ht.stats.select(
        su("UU", [20.0, 25.0, 30.0]),
        value=SU,
        selection={"Clay": {"method": "value", "value": "500 psf", "reason": "x"}},
    )
    assert result.to_frame()["value"].iloc[0] == pytest.approx(23.940, abs=0.001)
    assert result.judgments["selection"]["values"]["Clay"]["value"] == "500 psf"


def test_g4_in_us_units():
    result = ht.stats.select(
        su("UU", [20.0, 25.0, 30.0]),
        value=SU,
        selection={"Clay": {"method": "value", "value": "500 psf", "reason": "x"}},
        display_units="US",
    )
    assert result.unit == "psf"
    assert result.to_frame()["value"].iloc[0] == pytest.approx(500.0, rel=1e-9)


@pytest.mark.parametrize(
    ("given", "message"),
    [
        (26, r"selection=, Clay, value: give the value with its unit as text"),
        ("26 kPa/", r"selection=, Clay, value: "),
        ("26 deg", r"selection=, Clay, value: .*stress"),
    ],
)
def test_an_argument_value_needs_its_unit(given, message):
    with pytest.raises(HangtuError, match=message):
        ht.stats.select(
            su("UU", [20.0, 25.0]),
            value=SU,
            selection={"Clay": {"method": "value", "value": given, "reason": "x"}},
        )


def test_an_argument_entry_is_checked_by_the_files_rules():
    with pytest.raises(HangtuError, match=r"selection=, Clay: 'reason' is missing"):
        ht.stats.select(
            su("UU", [20.0, 25.0]),
            value=SU,
            selection={"Clay": {"method": "none"}},
        )
    with pytest.raises(HangtuError, match=r"selection= maps each geology unit"):
        ht.stats.select(su("UU", [20.0, 25.0]), value=SU, selection=["Clay"])


# --- Units listed, none, and units no source has (AC 6) ----------------------------


def test_a_unit_the_selection_doesnt_list_is_an_error():
    clay, sand = su("UU", [20.0, 25.0]), su("UU", [30.0, 35.0], unit="Sand")
    with pytest.raises(
        HangtuError, match=r"doesn't list 'Sand', which the sources have.*method: none"
    ):
        ht.stats.select(
            clay,
            sand,
            value=SU,
            selection={"Clay": {"method": "none", "reason": "removed"}},
        )


def test_none_lists_the_unit_with_its_reason_and_no_value():
    result = ht.stats.select(
        su("UU", [20.0, 25.0, 30.0]),
        value=SU,
        selection={"Clay": {"method": "none", "reason": "removed under the structure"}},
    )
    row = result.to_frame().iloc[0]
    assert row["selection_method"] == "none"
    assert pd.isna(row["value"])
    assert row["selection_reason"] == "removed under the structure"
    assert pd.isna(row["no_value_reason"])
    assert "Clay: none: no value (removed under the structure)." in result.notes


def test_a_computed_method_for_a_unit_no_source_has_is_an_error():
    entry = {**G1_ENTRY, "source": "UU"}
    with pytest.raises(
        HangtuError,
        match=r"computes 'Gravel' by characteristic from 'UU', but no source",
    ):
        ht.stats.select(
            su("UU", [20.0, 25.0]),
            value=SU,
            selection={
                "Clay": {"method": "none", "reason": "x"},
                "Gravel": entry,
            },
        )


# --- Sources (AC 7) -----------------------------------------------------------------


def test_a_source_not_in_the_comparison_lists_those_in_the_unit():
    a, b = g1_sources()
    with pytest.raises(
        HangtuError, match=r"selects from 'C', which isn't a source.*'A', 'B'"
    ):
        ht.stats.select(
            a, b, value=PHI, selection={"Sand": {**G1_ENTRY, "source": "C"}}
        )


def test_a_shear_box_fit_is_refused_as_by_compare_sources():
    df = pd.DataFrame(
        {
            "geology_unit": "Sand",
            "applied_normal_stress": [50.0, 100.0],
            "peak_shear_stress": [30.0, 59.0],
        }
    )
    df.attrs["units"] = {"applied_normal_stress": "kPa", "peak_shear_stress": "kPa"}
    fit = ht.analysis.shear_box_fit(df, group_by="geology_unit")
    with pytest.raises(
        HangtuError, match=r"ShearBoxFit.*friction_angle_from_shear_box"
    ):
        ht.stats.select(
            fit, value=PHI, selection={"Sand": {"method": "none", "reason": "x"}}
        )


def test_a_row_source_has_no_fitted_value():
    a, b = g1_sources()
    with pytest.raises(
        HangtuError,
        match=r"selects fitted from 'A', a source of rows.*characteristic, percentile",
    ):
        ht.stats.select(
            a,
            b,
            value=PHI,
            selection={"Sand": {"source": "A", "method": "fitted", "reason": "x"}},
        )


def test_the_parameter_must_be_a_registry_column():
    with pytest.raises(HangtuError, match=r"select\(\) value=: 'su' isn't in the"):
        ht.stats.select(su("UU", [20.0]), value="su", selection={})


# --- Resolution and the record (AC 8) -----------------------------------------------


def test_the_record_names_the_file_and_its_sha256(tmp_path):
    a, b = g1_sources()
    path = write(tmp_path, G1_FILE)
    result = ht.stats.select(a, b, value=PHI, judgments=ht.judgments(path))
    record = result.judgments["selection"]
    assert record["source"] == str(path)
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["by"] == "geology_unit"
    assert record["values"]["Sand"] == {
        "method": "characteristic",
        "source": "A",
        "side": "low",
        "distribution": "normal",
        "estimate": "mean",
        "reason": "a mean over a long slip surface",
    }


def test_the_file_the_sources_carry_is_read(tmp_path):
    a, b = g1_sources()
    a.attrs["judgments_file"] = str(write(tmp_path, G1_FILE))
    result = ht.stats.select(a, b, value=PHI)
    assert result.to_frame()["value"].iloc[0] == pytest.approx(34.868, abs=0.001)
    assert result.judgments["selection"]["source"] == a.attrs["judgments_file"]


def test_selection_replaces_the_files_with_a_warning(tmp_path):
    a, b = g1_sources()
    path = write(tmp_path, G1_FILE)
    entry = {"method": "value", "value": "33 deg", "reason": "cautious estimate"}
    with pytest.warns(UserWarning, match=r"selection= replaces the selection of"):
        result = ht.stats.select(
            a, b, value=PHI, selection={"Sand": entry}, judgments=path
        )
    assert result.to_frame()["value"].iloc[0] == 33.0
    assert result.judgments["selection"]["source"] == "argument"
    assert "sha256" not in result.judgments["selection"]


def test_no_selection_anywhere_names_the_parameter_and_shows_an_entry(tmp_path):
    a, b = g1_sources()
    with pytest.raises(
        HangtuError,
        match=r"(?s)no selection of 'effective_friction_angle': no judgments file.*"
        r"selection:\n  effective_friction_angle:\n    values:\n      Sand:\n"
        r'        source: "A"',
    ):
        ht.stats.select(a, b, value=PHI)
    path = write(
        tmp_path, "selection:\n  effective_cohesion:\n    values: {}\n", name="j.yaml"
    )
    with pytest.raises(HangtuError, match=r"j\.yaml' has no selection of it"):
        ht.stats.select(a, b, value=PHI, judgments=path)


# --- Refusals and the refusal limit from the file (AC 9) ---------------------------


def terrace():
    """Five measured N60 and two refusals at 66.7 (field N 50), as in m18a."""
    return pd.DataFrame(
        {
            "geology_unit": ["Terrace"] * 7,
            "source": "SPT",
            "spt_n": [9.0, 13.5, 18.75, 23.25, 30.0, 50.0, 50.0],
            "spt_n60": [12.0, 18.0, 25.0, 31.0, 40.0, 66.7, 66.7],
            "spt_refusal": [False] * 5 + [True] * 2,
        }
    )


def test_refusals_use_the_files_upper_limit_and_record_it(tmp_path):
    path = write(
        tmp_path,
        """\
        spt_refusal_upper_limit:
          values:
            Terrace: {spt_n: 120, reason: "50 blows for 5 in, per foot"}
        selection:
          spt_n60:
            values:
              Terrace:
                source: SPT
                method: characteristic
                estimate: mean
                side: low
                distribution: normal
                reason: "a mean over the pile shaft"
        """,
    )
    result = ht.stats.select(terrace(), value="spt_n60", judgments=path)
    limit = 120 * 66.7 / 50
    values = stats.CensoredData(
        uncensored=[12.0, 18.0, 25.0, 31.0, 40.0],
        interval=[[66.7, limit], [66.7, limit]],
    )
    location, scale = stats.norm.fit(values)
    k_n = stats.t.ppf(0.95, 6) * math.sqrt(1 / 7)
    row = result.to_frame().iloc[0]
    assert row["value"] == pytest.approx(location - k_n * scale, rel=1e-4)
    assert row["count"] == 7
    assert (
        result.representative("Terrace").groups[0]["counts"]["count_interval_censored"]
        == 2
    )
    assert result.judgments["spt_refusal_upper_limit"]["source"] == str(path)


# --- No value, never filled (AC 10) -------------------------------------------------


def test_a_unit_with_no_value_is_listed_and_warned_not_filled():
    uu = su("UU", [40.0])
    vane = su("vane", [30.0, 35.0, 40.0, 45.0])
    entry = {**G1_ENTRY, "source": "UU"}
    with pytest.warns(UserWarning, match=rf"{NO_VALUE} of .* in Clay \(fewer than 2"):
        result = ht.stats.select(uu, vane, value=SU, selection={"Clay": entry})
    row = result.to_frame().iloc[0]
    assert pd.isna(row["value"])
    assert row["no_value_reason"] == "fewer than 2 values (1)"
    assert row["count"] == 1
    assert row["parameter_source"] == "UU"


def test_a_source_with_no_rows_in_the_unit_has_no_value():
    clay = su("UU", [40.0, 45.0])
    sand = su("vane", [30.0, 35.0], unit="Sand")
    with pytest.warns(UserWarning, match=rf"{NO_VALUE} .* in Sand \(no rows in this"):
        result = ht.stats.select(
            clay,
            sand,
            value=SU,
            selection={
                "Clay": {"method": "none", "reason": "x"},
                "Sand": {**G1_ENTRY, "source": "UU"},
            },
        )
    assert result.to_frame()["no_value_reason"].iloc[1] == "no rows in this unit"
    with pytest.raises(HangtuError, match=r"'Sand' is selected by characteristic"):
        result.representative("Sand")


# --- G5: the file and the arguments give one number (AC 12) -------------------------


def test_g5_the_jrc_case_through_the_file(tmp_path):
    """test_representative.py's G1: Coca's c′, Type A, V_X computed: 14.0124 kPa."""
    frame = pd.DataFrame(
        {
            "geology_unit": "Coca",
            "test_type": "CD",
            "effective_cohesion": [27.0, 45.0, 47.0, 46.0, 4.5, 9.5],
        }
    )
    frame = ht.set_units(frame, {"effective_cohesion": "kPa"})
    path = write(
        tmp_path,
        """\
        selection:
          effective_cohesion:
            values:
              Coca:
                source: CD
                method: characteristic
                estimate: mean
                side: low
                distribution: normal
                reason: "JRC Annex I"
        """,
    )
    result = ht.stats.select(frame, value="effective_cohesion", judgments=path)
    assert result.to_frame()["value"].iloc[0] == pytest.approx(
        14.01238734909873, rel=1e-6
    )
