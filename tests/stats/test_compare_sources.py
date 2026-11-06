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
