"""compare_sources(): docs/work/m18d-sources-compared.md, AC 5-9.

G2 and G3 are the spec's, hand-calculated with Python and NumPy from the
values below, not from the implementation.
"""

import json
import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError, UnitsError

REL = 1e-6
PHI = "effective_friction_angle"
SU = "undrained_shear_strength"
HATANAKA = "effective_friction_angle_hatanaka_uchida_1996"
KULHAWY = "effective_friction_angle_kulhawy_mayne_1990"
STROUD = "undrained_shear_strength_stroud_1974"
BAND = r"left out 1 rows of 'effective_friction_angle' that give only a range"
#: 1 psf in kPa (exact): 0.45359237 kg × 9.80665 m/s² / 0.3048² m² / 1000.
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000


def _compare(*sources, **kwargs):
    """Compare, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return ht.stats.compare_sources(*sources, **kwargs)


def _spt_phi():
    """G2's correlations A and B in one frame, as an SPT frame holds them."""
    a = [31.2, 34.8, 36.1, 33.0, 38.4, 35.5, 32.7, 37.9]
    b = [34.0, 36.5, 39.2, 35.1, 41.0, 37.3, np.nan, np.nan]
    alluvium = [30.1, 31.5, 29.8]
    df = pd.DataFrame(
        {
            "loca_id": [f"BH{i % 4 + 1:02d}" for i in range(19)],
            "geology_unit": ["Terrace"] * 16 + ["Alluvium"] * 3,
            "depth": np.linspace(1.5, 19.5, 19),
            PHI: [*a, *b, *alluvium],
            f"{PHI}_lower": [np.nan] * 14 + [33.0, np.nan] + [np.nan] * 3,
            f"{PHI}_upper": [np.nan] * 14 + [38.0, np.nan] + [np.nan] * 3,
            "correlation_name": [HATANAKA] * 8 + [KULHAWY] * 8 + [HATANAKA] * 3,
            "correlation_qualifier": [""] * 4 + [">"] + [""] * 14,
        }
    )
    df.attrs["units"] = {PHI: "deg", f"{PHI}_lower": "deg", f"{PHI}_upper": "deg"}
    return df


def _su():
    """G3: UU and field vane in kPa."""
    df = pd.DataFrame(
        {
            "geology_unit": "Alluvium",
            "source": ["lab"] * 4 + ["field"] * 3,
            "test_type": ["UU"] * 4 + ["in situ vane"] * 3,
            SU: [42.0, 55.0, 61.0, 48.0, 58.0, 71.0, 66.0],
        }
    )
    df.attrs["units"] = {SU: "kPa"}
    return df


def _stroud():
    """G3: Stroud (1974) estimates in psf."""
    df = pd.DataFrame(
        {
            "geology_unit": "Alluvium",
            SU: [1200.0, 1500.0, 1350.0],
            "correlation_name": STROUD,
        }
    )
    df.attrs["units"] = {SU: "psf"}
    return df


def _row(result, unit, source):
    frame = result.to_frame()
    rows = frame[
        (frame["geology_unit"] == unit) & (frame["parameter_source"] == source)
    ]
    assert len(rows) == 1, rows
    return rows.iloc[0]


def _counts_add_up(result, frames):
    """AC 5: count plus the counts left out are each source's rows in the unit."""
    frame = result.to_frame()
    counted = ["count_at_least", "count_at_most"]
    left_out = [c for c in frame.columns if c.startswith("count_") and c not in counted]
    left_out.remove("count_points")
    for _, row in frame.iterrows():
        total = sum(
            int(
                (
                    (f["geology_unit"] == row["geology_unit"])
                    & (_label(f) == row["parameter_source"].split(" (source")[0])
                ).sum()
            )
            for f in frames
        )
        assert row["count"] + row[left_out].sum() == total, row


def _label(frame):
    columns = [c for c in ("source", "test_type", "correlation_name") if c in frame]
    return frame[columns].astype(str).agg(", ".join, axis=1)


# --- AC 5: G2 correlations A and B, G3 ----------------------------------------------


def test_g2_two_correlations_in_one_frame():
    df = _spt_phi()
    with pytest.warns(UserWarning, match=BAND):
        result = ht.stats.compare_sources(df, value=PHI, percentiles=(25, 75))
    a = _row(result, "Terrace", HATANAKA)
    assert a["count"] == 8
    assert a["count_at_least"] == 1
    assert a["mean"] == pytest.approx(34.95, rel=REL)
    assert a["standard_deviation"] == pytest.approx(2.540529, rel=REL)
    assert a["coefficient_of_variation"] == pytest.approx(0.072690, rel=1e-5)
    assert a["median"] == pytest.approx(35.15, rel=REL)
    assert a["percentile_25"] == pytest.approx(32.925, rel=REL)
    assert a["percentile_75"] == pytest.approx(36.55, rel=REL)
    b = _row(result, "Terrace", KULHAWY)
    assert b["count"] == 6
    assert b["count_range"] == 1
    assert b["count_blank"] == 1
    assert b["mean"] == pytest.approx(37.183333, rel=REL)
    assert b["standard_deviation"] == pytest.approx(2.591846, rel=REL)
    assert b["percentile_25"] == pytest.approx(35.45, rel=REL)
    assert b["median"] == pytest.approx(36.9, rel=REL)
    assert b["percentile_75"] == pytest.approx(38.725, rel=REL)
    assert result.unit == "deg"
    _counts_add_up(result, [df])


def test_g2_default_percentiles_blank_below_their_floor():
    with pytest.warns(UserWarning, match=BAND):
        result = ht.stats.compare_sources(_spt_phi(), value=PHI)
    a = _row(result, "Terrace", HATANAKA)
    assert np.isnan(a["percentile_5"]) and np.isnan(a["percentile_95"])
    assert a["percentile_25"] == pytest.approx(32.925, rel=REL)
    assert "P5/P95 need 20 values" in str(result)


def test_g3_tests_and_a_correlation_in_another_unit():
    uu, stroud = _su(), _stroud()
    result = _compare(uu, stroud, value=SU)
    assert result.unit == "kPa"
    row = _row(result, "Alluvium", "lab, UU")
    assert row["count"] == 4
    assert row["mean"] == pytest.approx(51.5, rel=REL)
    assert row["standard_deviation"] == pytest.approx(8.266398, rel=REL)
    assert row["percentile_25"] == pytest.approx(46.5, rel=REL)
    assert row["median"] == pytest.approx(51.5, rel=REL)
    assert row["percentile_75"] == pytest.approx(56.5, rel=REL)
    vane = _row(result, "Alluvium", "field, in situ vane")
    assert vane["count"] == 3
    assert vane["mean"] == pytest.approx(65.0, rel=REL)
    assert vane["standard_deviation"] == pytest.approx(6.557439, rel=REL)
    assert np.isnan(vane["percentile_25"]) and np.isnan(vane["percentile_75"])
    correlated = _row(result, "Alluvium", STROUD)
    assert correlated["minimum"] == pytest.approx(57.456311, rel=REL)
    assert correlated["maximum"] == pytest.approx(71.820388, rel=REL)
    assert correlated["mean"] == pytest.approx(64.638350, rel=REL)
    assert correlated["standard_deviation"] == pytest.approx(7.182039, rel=REL)
    _counts_add_up(result, [uu, stroud])


# --- AC 9: units ---------------------------------------------------------------------


def test_g3_in_us_units():
    result = _compare(_su(), _stroud(), value=SU, display_units="US")
    assert result.unit == "psf"
    assert _row(result, "Alluvium", "lab, UU")["mean"] == pytest.approx(
        1075.600, abs=1e-3
    )
    assert _row(result, "Alluvium", STROUD)["mean"] == pytest.approx(1350.0, rel=REL)
    assert result.to_frame().attrs["units"]["mean"] == "psf"


def test_the_first_sources_unit_is_used():
    result = _compare(_stroud(), _su(), value=SU)
    assert result.unit == "psf"
    assert _row(result, "Alluvium", "lab, UU")["mean"] == pytest.approx(
        51.5 / PSF, rel=REL
    )


def test_units_argument_applies_to_every_frame():
    uu, stroud = _su(), _stroud()
    uu.attrs, stroud.attrs = {}, {}
    result = _compare(uu, stroud, value=SU, units={SU: "kPa"})
    assert result.unit == "kPa"
    assert _row(result, "Alluvium", STROUD)["mean"] == pytest.approx(1350.0, rel=REL)
    assert _row(result, "Alluvium", "lab, UU")["mean"] == pytest.approx(51.5, rel=REL)


def test_a_frame_without_a_unit_names_its_position():
    stroud = _stroud()
    stroud.attrs = {}
    with pytest.raises(
        UnitsError, match=r"compare_sources\(\) source 2 \(a DataFrame\)"
    ):
        ht.stats.compare_sources(_su(), stroud, value=SU)


def test_angles_are_in_degrees():
    df = pd.DataFrame({"geology_unit": "Terrace", PHI: [0.6, 0.62]})
    df.attrs["units"] = {PHI: "radian"}
    with pytest.warns(UserWarning, match="read as radian"):
        result = ht.stats.compare_sources(df, value=PHI)
    assert result.unit == "deg"
    assert _row(result, "Terrace", "(no source given)")["minimum"] == pytest.approx(
        np.degrees(0.6), rel=REL
    )


# --- AC 7: labels --------------------------------------------------------------------


def test_labels_join_the_source_columns_in_registry_order():
    df = _su()
    df["correlation_name"] = None
    df.loc[0, "test_type"] = None
    df.loc[0, "source"] = ""
    result = _compare(df, value=SU)
    assert [s["parameter_source"] for s in result.sources] == [
        "(no source given)",
        "lab, UU",
        "field, in situ vane",
    ]
    assert {s["source_kind"] for s in result.sources} == {"rows"}


def test_a_repeated_label_takes_its_position():
    uu = _su()
    result = _compare(uu, _stroud(), uu, value=SU)
    labels = [s["parameter_source"] for s in result.sources]
    assert labels == [
        "lab, UU",
        "field, in situ vane",
        STROUD,
        "lab, UU (source 3)",
        "field, in situ vane (source 3)",
    ]
    assert _row(result, "Alluvium", "lab, UU (source 3)")["mean"] == pytest.approx(
        51.5, rel=REL
    )


def test_errors_name_what_to_do():
    with pytest.raises(HangtuError, match=r"needs at least one source"):
        ht.stats.compare_sources(value=SU)
    with pytest.raises(
        ColumnError, match=r"source 1 \(a DataFrame\): .*'geology_unit'"
    ):
        ht.stats.compare_sources(_su().drop(columns="geology_unit"), value=SU)
    other = _su().rename(columns={SU: "remolded_undrained_shear_strength"})
    with pytest.raises(ColumnError, match=r"source 2 \(a DataFrame\): .*'undrained_sh"):
        ht.stats.compare_sources(_su(), other, value=SU)
    with pytest.raises(HangtuError, match=r"source 2 is a list"):
        ht.stats.compare_sources(_su(), [1, 2], value=SU)
    with pytest.raises(HangtuError, match=r"display_units must be"):
        ht.stats.compare_sources(_su(), value=SU, display_units="metric")


# --- AC 8: nothing dropped ----------------------------------------------------------


def test_every_unit_and_source_is_listed():
    with pytest.warns(UserWarning, match=BAND):
        result = ht.stats.compare_sources(_spt_phi(), value=PHI)
    frame = result.to_frame()
    assert list(frame["geology_unit"]) == ["Alluvium", "Alluvium", "Terrace", "Terrace"]
    empty = _row(result, "Alluvium", KULHAWY)
    assert empty["count"] == 0
    assert empty["no_value_reason"] == "no rows in this unit"
    assert np.isnan(empty["mean"])
    assert _row(result, "Terrace", KULHAWY)["no_value_reason"] is None


def test_all_rows_left_out():
    df = _su()
    df.loc[df["test_type"] == "UU", SU] = np.nan
    result = _compare(df, value=SU)
    row = _row(result, "Alluvium", "lab, UU")
    assert row["count"] == 0
    assert row["count_blank"] == 4
    assert row["no_value_reason"] == "all 4 rows left out"


def test_blank_unit_last_and_by_none():
    df = _su()
    df.loc[0, "geology_unit"] = None
    df.loc[1, "geology_unit"] = "Clay"
    result = _compare(df, value=SU)
    assert list(dict.fromkeys(result.to_frame()["geology_unit"])) == [
        "Alluvium",
        "Clay",
        "(blank)",
    ]
    together = _compare(_su(), value=SU, by=None)
    assert list(together.to_frame().columns[:2]) == ["parameter_source", "source_kind"]
    assert together.to_frame()["count"].tolist() == [4, 3]


# --- the views ----------------------------------------------------------------------


def test_frame_columns_text_and_dict():
    result = _compare(_su(), _stroud(), value=SU, percentiles=(25, 75))
    frame = result.to_frame()
    assert list(frame.columns) == [
        "geology_unit",
        "parameter_source",
        "source_kind",
        "count",
        "mean",
        "standard_deviation",
        "coefficient_of_variation",
        "minimum",
        "percentile_25",
        "median",
        "percentile_75",
        "maximum",
        "count_at_least",
        "count_at_most",
        "count_non_plastic",
        "count_assumed",
        "count_range",
        "count_text",
        "count_blank",
        "count_points",
        "r_squared",
        "lowest_normal_stress",
        "highest_normal_stress",
        "shallowest_depth",
        "deepest_depth",
        "no_value_reason",
    ]
    assert frame.attrs["units"]["mean"] == "kPa"
    assert "count" not in frame.attrs["units"]
    assert result.kind == "property"
    record = json.loads(json.dumps(result.to_dict()))
    assert record["function"] == "compare_sources"
    text = str(result)
    assert text.splitlines()[:2] == [
        "undrained_shear_strength (kPa), sources compared by geology_unit",
        "Alluvium",
    ]
    assert "never pooled" in text
    assert repr(result) == text


def test_names_are_registered():
    registered = set(ht.columns()["name"])
    assert {"parameter_source", "source_kind"} <= registered
    frame = _compare(_su(), value=SU).to_frame()
    statistics = {"count", "mean", "standard_deviation", "coefficient_of_variation"}
    statistics |= {"minimum", "median", "maximum", "percentile_5", "percentile_25"}
    statistics |= {"percentile_75", "percentile_95", "r_squared", "count_points"}
    statistics |= {"lowest_normal_stress", "highest_normal_stress", "no_value_reason"}
    statistics |= {"shallowest_depth", "deepest_depth"}
    statistics |= {c for c in frame.columns if c.startswith("count_")}
    for column in frame.columns:
        assert column in registered or column in statistics, column


# --- step 5: fit sources (AC 5-8) -----------------------------------------------------

CONVERTED = "shear box, converted (Kulhawy & Mayne 1990)"
NEGATIVE = r"the free line's intercept is negative"
STRESSES = [
    "minor_principal_stress_at_failure",
    "major_principal_stress_at_failure",
    "effective_minor_principal_stress_at_failure",
    "effective_major_principal_stress_at_failure",
]


def _triaxial_frame(points, **columns):
    """CD stages with effective (σ′3, σ′1) and totals 300 kPa above them."""
    minor, major = (np.array(v, dtype=float) for v in zip(*points, strict=True))
    df = pd.DataFrame(
        {
            STRESSES[0]: minor + 300,
            STRESSES[1]: major + 300,
            STRESSES[2]: minor,
            STRESSES[3]: major,
            "test_type": "CD",
            **columns,
        }
    )
    df.attrs["units"] = {**dict.fromkeys(STRESSES, "kPa"), "depth": "m"}
    return df


def _mohr_coulomb(group_by="geology_unit"):
    """G2's triaxial fit: φ′ 36° in Terrace at 4.0-9.0 m; one stage in Alluvium."""
    df = _triaxial_frame(
        [(50, 192.592), (100, 385.184), (200, 770.368), (100, 400.0)],
        geology_unit=["Terrace"] * 3 + ["Alluvium"],
        depth=[4.0, 6.5, 9.0, 3.0],
    )
    # σ′1 is rounded to 3 decimals, so the free intercept is a hair below 0.
    with pytest.warns(UserWarning, match=r"intercept is negative") as caught:
        fit = ht.analysis.mohr_coulomb_fit(df, group_by=group_by)
    assert len(caught) == 1, [str(w.message) for w in caught]
    return fit


def _conversion():
    """G2's shear box: τ = σn tan 30°, cohesionless, φ′cv 32° → 30.5777°."""
    df = pd.DataFrame(
        {
            "geology_unit": "Terrace",
            "applied_normal_stress": [50.0, 100.0, 200.0],
            "peak_shear_stress": [28.867513, 57.735027, 115.470054],
            "depth": [5.0, 5.0, 5.0],
        }
    )
    df.attrs["units"] = {
        "applied_normal_stress": "kPa",
        "peak_shear_stress": "kPa",
        "depth": "m",
    }
    with pytest.warns(UserWarning, match=NEGATIVE):
        fit = ht.analysis.shear_box_fit(df, group_by="geology_unit", cohesion=0)
    return ht.analysis.friction_angle_from_shear_box(
        fit, soil="cohesionless", critical_state_friction_angle={"Terrace": 32}
    )


def _g2(**kwargs):
    with pytest.warns(UserWarning, match=BAND):
        return ht.stats.compare_sources(
            _spt_phi(), _mohr_coulomb(), _conversion(), value=PHI, **kwargs
        )


def test_g2_fit_values_and_their_columns():
    result = _g2(percentiles=(25, 75))
    assert [s["parameter_source"] for s in result.sources] == [
        HATANAKA,
        KULHAWY,
        "Mohr-Coulomb fit (CD)",
        CONVERTED,
    ]
    fit = _row(result, "Terrace", "Mohr-Coulomb fit (CD)")
    assert fit["source_kind"] == "fit"
    assert fit["count"] == 1
    assert fit["mean"] == pytest.approx(36.0, abs=1e-3)
    assert fit["median"] == pytest.approx(36.0, abs=1e-3)
    assert np.isnan(fit["standard_deviation"])
    assert fit["count_points"] == 3
    assert fit["r_squared"] == pytest.approx(1.0, abs=1e-9)
    assert fit["shallowest_depth"] == 4.0
    assert fit["deepest_depth"] == 9.0
    assert fit["lowest_normal_stress"] < fit["highest_normal_stress"]
    converted = _row(result, "Terrace", CONVERTED)
    assert converted["mean"] == pytest.approx(30.5777, abs=1e-4)
    assert converted["count_points"] == 3
    assert converted["shallowest_depth"] == converted["deepest_depth"] == 5.0
    record = next(
        r
        for r in result.rows
        if r["parameter_source"] == CONVERTED and r["key"]["geology_unit"] == "Terrace"
    )
    assert record["line_kind"] == "through_origin"
    frame = result.to_frame()
    assert frame.attrs["units"]["shallowest_depth"] == "m"
    assert frame.attrs["units"]["lowest_normal_stress"] == "kPa"
    assert frame.attrs["units"]["mean"] == "deg"
    json.loads(json.dumps(result.to_dict()))


def test_g2_positions():
    result = _g2()
    positions = result.positions().set_index(["fit_source", "parameter_source"])
    a = positions.loc[("Mohr-Coulomb fit (CD)", HATANAKA)]
    assert a["position"] == "within"
    assert a["percentile_rank"] == pytest.approx(69.0476, abs=1e-3)
    assert a["count"] == 8
    b = positions.loc[("Mohr-Coulomb fit (CD)", KULHAWY)]
    assert b["position"] == "within"
    assert b["percentile_rank"] == pytest.approx(32.8571, abs=1e-3)
    # H&F 7 at the rank gives the fit's value again.
    df = _spt_phi()
    terrace = df[df["geology_unit"] == "Terrace"]
    for name, rank in (
        (HATANAKA, a["percentile_rank"]),
        (KULHAWY, b["percentile_rank"]),
    ):
        values = terrace.loc[terrace["correlation_name"] == name, PHI].dropna()
        assert np.percentile(values, rank, method="linear") == pytest.approx(
            36.0, abs=1e-3
        )
    for name in (HATANAKA, KULHAWY):
        below = positions.loc[(CONVERTED, name)]
        assert below["position"] == "below"
        assert np.isnan(below["percentile_rank"])
    assert set(result.positions()["geology_unit"]) == {"Terrace"}
    assert result.positions().attrs["units"]["fit_value"] == "deg"
    assert "Mohr-Coulomb fit (CD) 36.0 is within" in str(result)


def test_g2_alluvium_lists_every_source_with_its_reason():
    result = _g2()
    assert _row(result, "Alluvium", HATANAKA)["count"] == 3
    assert _row(result, "Alluvium", KULHAWY)["no_value_reason"] == (
        "no rows in this unit"
    )
    fitted = _mohr_coulomb().groups[0]
    assert fitted["key"] == {"geology_unit": "Alluvium"}
    reason = fitted["fits"][0]["no_fit_reason"]
    assert reason
    fit = _row(result, "Alluvium", "Mohr-Coulomb fit (CD)")
    assert fit["count"] == 0
    assert fit["no_value_reason"] == reason
    assert _row(result, "Alluvium", CONVERTED)["no_value_reason"] == (
        "no rows in this unit"
    )


def test_a_rank_under_four_values_is_blank():
    df = _spt_phi()
    df = df[~((df["geology_unit"] == "Terrace") & (df.index % 8 > 2))]
    result = _compare(df, _mohr_coulomb(), value=PHI)
    placed = result.positions().set_index("parameter_source")
    assert placed.loc[HATANAKA, "count"] == 3
    assert placed.loc[HATANAKA, "position"] == "within"
    assert np.isnan(placed.loc[HATANAKA, "percentile_rank"])


def test_percentile_rank_ties_take_the_middle():
    from hangtu.stats._compare_sources import percentile_rank

    assert percentile_rank(np.array([1.0, 2.0, 2.0, 2.0, 3.0]), 2.0) == 50.0
    assert percentile_rank(np.array([1.0, 2.0, 3.0, 4.0]), 1.0) == 0.0
    assert percentile_rank(np.array([1.0, 2.0, 3.0, 4.0]), 4.0) == 100.0
    assert percentile_rank(np.array([1.0, 2.0, 3.0, 5.0]), 4.0) == pytest.approx(
        250 / 3
    )


def test_a_per_sample_fit_is_summarized_like_rows():
    angles = {"S1": 34.0, "S2": 36.0, "S3": 37.0}
    points, samples = [], []
    for sample, angle in angles.items():
        ratio = (1 + np.sin(np.radians(angle))) / (1 - np.sin(np.radians(angle)))
        points += [(50, 50 * ratio), (150, 150 * ratio)]
        samples += [sample, sample]
    df = _triaxial_frame(
        points, geology_unit="Terrace", sample_reference=samples, depth=np.arange(6.0)
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 2 points per fit
        fit = ht.analysis.mohr_coulomb_fit(
            df, group_by=["geology_unit", "sample_reference"]
        )
    result = _compare(fit, value=PHI)
    row = _row(result, "Terrace", "Mohr-Coulomb fit (CD)")
    assert row["count"] == 3
    assert row["mean"] == pytest.approx(np.mean(list(angles.values())), abs=1e-6)
    assert row["standard_deviation"] == pytest.approx(
        np.std(list(angles.values()), ddof=1), abs=1e-6
    )
    assert row["count_points"] == 6
    assert np.isnan(row["r_squared"])
    assert (row["shallowest_depth"], row["deepest_depth"]) == (0.0, 5.0)
    assert result.positions().empty


def test_cohesion_from_a_fit_in_us_units():
    result = _compare(_mohr_coulomb(), value="effective_cohesion", display_units="US")
    row = _row(result, "Terrace", "Mohr-Coulomb fit (CD)")
    assert row["mean"] == pytest.approx(0.0, abs=1e-3)
    assert result.unit == "psf"
    assert result.stress_unit == "psf"
    assert result.depth_unit == "ft"
    assert row["shallowest_depth"] == pytest.approx(4.0 / 0.3048, rel=REL)


def test_g3_has_no_positions():
    result = _compare(_su(), _stroud(), value=SU)
    assert result.positions().empty
    assert list(result.positions().columns) == [
        "geology_unit",
        "fit_source",
        "parameter_source",
        "fit_value",
        "count",
        "minimum",
        "maximum",
        "position",
        "percentile_rank",
    ]


def test_fit_source_errors_name_what_to_do():
    df = pd.DataFrame(
        {"applied_normal_stress": [50.0, 100.0], "peak_shear_stress": [30.0, 59.0]}
    )
    df.attrs["units"] = {"applied_normal_stress": "kPa", "peak_shear_stress": "kPa"}
    shear_box = ht.analysis.shear_box_fit(df)
    for value in (PHI, "effective_cohesion"):
        with pytest.raises(HangtuError, match=r"friction_angle_from_shear_box\(fit"):
            ht.stats.compare_sources(shear_box, value=value, by=None)
    triaxial = _triaxial_frame(
        [(50, 192.592), (100, 385.184), (200, 770.368)], geology_unit="Terrace"
    )
    total = ht.analysis.mohr_coulomb_fit(
        triaxial, stress="total", group_by="geology_unit", cohesion=0
    )
    with pytest.raises(HangtuError, match=r"total stress MohrCoulombFit.*stress="):
        ht.stats.compare_sources(total, value=PHI)
    from hangtu.analysis import HoekBrownFit

    with pytest.raises(HangtuError, match=r"HoekBrownFit.*intact rock"):
        ht.stats.compare_sources(object.__new__(HoekBrownFit), value=PHI)
    with pytest.raises(HangtuError, match=r"effective_friction_angle only"):
        ht.stats.compare_sources(_conversion(), value="effective_cohesion")
    with pytest.raises(
        HangtuError,
        match=r"gives effective_friction_angle and effective_cohesion, not "
        r"'undrained_shear_strength'",
    ):
        ht.stats.compare_sources(_mohr_coulomb(), value=SU)
    with pytest.raises(
        HangtuError,
        match=r"source 1 was fitted with no group_by.*no geology_unit.*"
        r"group_by=\['geology_unit'\]",
    ):
        ht.stats.compare_sources(
            ht.analysis.mohr_coulomb_fit(triaxial, cohesion=0), value=PHI
        )
    with pytest.raises(HangtuError, match=r"source 2 is a dict"):
        ht.stats.compare_sources(_su(), {}, value=SU)
