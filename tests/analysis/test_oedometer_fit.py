"""ht.analysis.oedometer_fit() (docs/work/m19b-compressibility.md, AC 1-17).

Golden values are the spec's, hand-calculated from its Derivation: Oikawa's
two least-squares lines in x = log10 σ′v, y = log10(1 + e), crossing at
σ′p = 10^((a2 - a1) / (b1 - b2)); Cc and Cr the negated e-log10 σ′v slopes of
the same groups. Points are (σ′v in kPa, e at the increment's end).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

DATA = Path(__file__).parents[1] / "data" / "ags"
REL = 1e-7
#: 1 psf in kPa: 0.45359237 kg × 9.80665 m/s² / 0.3048² m² (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000

#: BH1-U3 (site_si.ags), in file order: loading, an unload-reload loop, a
#: last load and a second unload.
BH1_U3 = [
    (25, 0.795),
    (50, 0.788),
    (100, 0.776),
    (200, 0.748),
    (400, 0.690),
    (800, 0.612),
    (200, 0.625),
    (50, 0.638),
    (200, 0.630),
    (800, 0.608),
    (1600, 0.520),
    (400, 0.538),
]


def _frame(points, specimen="S1", unit="kPa", **columns):
    """Increments ``(σ′v, e)`` of one specimen, in test order."""
    stress, void_ratio = (
        np.array(values, dtype=float) for values in zip(*points, strict=True)
    )
    df = pd.DataFrame(
        {
            "specimen_id": [specimen] * len(stress),
            "applied_vertical_stress": stress,
            "void_ratio_at_increment_end": void_ratio,
            **columns,
        }
    )
    df.attrs["units"] = {"applied_vertical_stress": unit}
    return df


def _fit(df, **kwargs):
    return ht.analysis.oedometer_fit(df, **kwargs)


def _one(df, **kwargs):
    fit = _fit(df, **kwargs)
    assert len(fit.specimens) == 1
    return fit.specimens[0]


def _project(name, system, tmp_path_factory):
    return ht.Project.from_ags(
        DATA / f"{name}.ags",
        db=tmp_path_factory.mktemp(name) / f"{name}.sqlite",
        overwrite=True,
        display_units=system,
    )


@pytest.fixture(scope="module")
def site_si(tmp_path_factory):
    return _project("site_si", "SI", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def site_us(tmp_path_factory):
    return _project("site_us", "US", tmp_path_factory).oedometer()


@pytest.fixture(scope="module")
def example(tmp_path_factory):
    p = ht.Project.from_ags(
        ht.examples.path("site.ags"),
        db=tmp_path_factory.mktemp("example") / "site.sqlite",
        overwrite=True,
        display_units="US",
    )
    return p.oedometer()


@pytest.fixture(scope="module")
def bh1_u3(site_si):
    return _one(site_si)


def _counts_add_up(record):
    """AC 5: the loading points, the Cs run's unloads and the counts are the rows."""
    used = sum(
        point["reason"] is None and point["load_branch"] == "unloading"
        for point in record["points"]
    )
    left_out = sum(
        record[name]
        for name in record
        if name.startswith("count_")
        and name not in {"count_rows", "count_loading_points"}
        and name not in {"count_loading_after_reload", "count_unload_runs"}
    )
    assert record["count_loading_points"] + used + left_out == record["count_rows"]


# --- AC 1: σ′p by Oikawa ------------------------------------------------------


def test_ac1_splits_and_their_sums_of_squares(bh1_u3):
    splits = bh1_u3["splits"]
    assert [(s["lower_count"], s["upper_count"]) for s in splits] == [(3, 4), (4, 3)]
    assert splits[0]["sum_of_squares"] == pytest.approx(2.9810204e-5, rel=1e-7)
    assert splits[1]["sum_of_squares"] == pytest.approx(1.1316206e-5, rel=1e-7)
    assert bh1_u3["lower_count"] == 4


def test_ac1_lines_and_preconsolidation_stress(bh1_u3):
    lower, upper = bh1_u3["lower_line"], bh1_u3["upper_line"]
    assert lower["intercept"] == pytest.approx(0.272639634, rel=REL)
    assert lower["slope"] == pytest.approx(-0.0124551132, rel=REL)
    assert upper["intercept"] == pytest.approx(0.427715041, rel=REL)
    assert upper["slope"] == pytest.approx(-0.0764759614, rel=REL)
    assert bh1_u3["preconsolidation_stress"] == pytest.approx(264.401656, rel=REL)
    assert bh1_u3["preconsolidation_stress_reason"] is None
    assert bh1_u3["slope_ratio"] == pytest.approx(6.14012574, rel=REL)
    assert bh1_u3["highest_stress_over_preconsolidation_stress"] == pytest.approx(
        6.05139931, rel=REL
    )


# --- AC 2: Cc and Cr ----------------------------------------------------------


def test_ac2_compression_and_recompression_index(bh1_u3):
    assert bh1_u3["compression_index"] == pytest.approx(0.282363888, rel=REL)
    assert bh1_u3["recompression_index"] == pytest.approx(0.0508254999, rel=REL)
    assert bh1_u3["compression_line"]["lowest_stress"] == 400
    assert bh1_u3["compression_line"]["highest_stress"] == 1600
    assert bh1_u3["recompression_line"]["highest_stress"] == 200


def test_ac2_roles_of_the_loading_points(bh1_u3):
    roles = {
        point["applied_vertical_stress"]: point["role"]
        for point in bh1_u3["points"]
        if point["load_branch"] == "loading"
    }
    assert roles == {
        25: "recompression",
        50: "recompression",
        100: "recompression",
        200: "recompression",
        400: "virgin",
        800: "virgin",
        1600: "virgin",
    }


# --- AC 2 (CR), 3 and 4: CR, Cs and Pacheco Silva's check -----------------------


def test_ac2_compression_ratio(bh1_u3):
    assert bh1_u3["void_ratio"] == 0.8
    assert bh1_u3["compression_ratio"] == pytest.approx(0.156868827, rel=REL)
    assert bh1_u3["compression_ratio_reason"] is None


def test_ac3_swelling_index_from_the_first_unload(bh1_u3):
    assert bh1_u3["swelling_index"] == pytest.approx(0.0215925326, rel=REL)
    assert bh1_u3["swelling_index_reason"] is None
    first, second = bh1_u3["unload_runs"]
    assert first["start_stress"] == 800
    assert first["swelling_line"]["count"] == 3
    assert first["notes"] == []
    assert second["start_stress"] == 1600
    assert second["swelling_index"] == pytest.approx(0.0298973529, rel=REL)
    assert second["notes"] == ["2 points: the line passes through both."]
    points = bh1_u3["points"]
    swelling = [p["applied_vertical_stress"] for p in points if p["role"] == "swelling"]
    assert swelling == [200, 50]


def test_ac3_no_unloading():
    record = _one(_frame(BH1_U3[:6]))
    assert np.isnan(record["swelling_index"])
    assert record["swelling_index_reason"] == "no unloading"
    assert record["unload_runs"] == []


def test_ac3_cs_never_reads_a_reload():
    # The second unload starts from a reloading point (800 again): it is the
    # run's start point, while the reload's own slope is never fitted.
    record = _one(_frame([*BH1_U3[:9], (800, 0.608), (400, 0.615), (200, 0.622)]))
    assert record["swelling_index"] == pytest.approx(0.0215925326, rel=REL)
    second = record["unload_runs"][1]
    assert second["start_stress"] == 800
    assert second["swelling_line"]["count"] == 3


def test_ac4_pacheco_silva(bh1_u3):
    construction = bh1_u3["pacheco_silva"]
    assert construction["stress_a"] == pytest.approx(166.247579, rel=REL)
    assert construction["void_ratio_b"] == pytest.approx(0.755466667, rel=REL)
    assert bh1_u3["preconsolidation_stress_pacheco_silva"] == pytest.approx(
        239.040472, rel=REL
    )
    assert bh1_u3["pacheco_silva_reason"] is None


def test_ac4_no_initial_void_ratio(site_si):
    record = _one(site_si.assign(void_ratio=np.nan))
    assert np.isnan(record["preconsolidation_stress_pacheco_silva"])
    assert record["pacheco_silva_reason"] == "no initial void ratio"
    assert np.isnan(record["compression_ratio"])
    assert record["compression_ratio_reason"] == "no initial void ratio"
    assert record["preconsolidation_stress"] == pytest.approx(264.401656, rel=REL)


def test_ac4_construction_outside_the_curve():
    record = _one(_frame(BH1_U3, void_ratio=1.2))
    assert np.isnan(record["preconsolidation_stress_pacheco_silva"])
    assert record["pacheco_silva_reason"].startswith(
        "the construction falls outside the measured curve (σA = "
    )
    assert record["pacheco_silva_reason"].endswith("kPa, loading from 25.0 kPa)")
    assert record["pacheco_silva"]["stress_a"] < 25


def test_ac4_check_blank_with_the_reason_of_a_blank_preconsolidation():
    record = _one(_frame(NO_BREAK, void_ratio=1.25))
    assert np.isnan(record["preconsolidation_stress_pacheco_silva"])
    assert record["pacheco_silva_reason"].startswith("no σ′p: no clear break")
    assert record["compression_ratio_reason"].startswith("no Cc: no clear break")


def test_more_than_one_initial_void_ratio_is_an_error():
    df = _frame(BH1_U3, void_ratio=0.8)
    df.loc[4, "void_ratio"] = 0.81
    with pytest.raises(HangtuError, match="more than one void_ratio"):
        _fit(df)


# --- AC 5: counts ---------------------------------------------------------------


def test_ac5_loading_and_reload_counts(bh1_u3):
    assert bh1_u3["count_loading_points"] == 7
    assert bh1_u3["count_loading_after_reload"] == 1
    after = [p for p in bh1_u3["points"] if p["after_reload"]]
    assert [p["applied_vertical_stress"] for p in after] == [1600]
    assert bh1_u3["count_reloading"] == 2
    assert bh1_u3["count_unloading_not_used"] == 1
    assert bh1_u3["count_rows"] == 12
    _counts_add_up(bh1_u3)


def test_ac5_each_row_counted_once_under_its_first_reason():
    df = _frame(
        [
            (25, 0.795),
            (np.nan, 0.790),  # no stress
            (50, np.nan),  # no e
            (100, 0.776),
            (100, 0.770),  # constant stress
            (200, 0.748),
            (400, 0.690),
            (800, 0.612),
            (1600, 0.520),
        ]
    )
    zero = _frame([(0, 0.800)])
    record = _one(pd.concat([zero, df], ignore_index=True))
    assert record["count_no_applied_stress"] == 1
    assert record["count_no_void_ratio"] == 1
    assert record["count_stress_not_positive"] == 1
    assert record["count_constant_stress"] == 1
    assert record["count_reloading"] == 0
    assert record["count_loading_points"] == 6
    _counts_add_up(record)
    by_row = {p["row"]: p["reason"] for p in record["points"]}
    assert by_row[0] == "count_stress_not_positive"
    assert by_row[2] == "count_no_applied_stress"
    assert by_row[3] == "count_no_void_ratio"
    assert by_row[5] == "count_constant_stress"


# --- AC 8-11: when the crossing isn't a σ′p ---------------------------------


NO_BREAK = [
    *zip(
        [10 * 2**i for i in range(8)],
        [1.200, 1.125, 1.049, 0.974, 0.899, 0.824, 0.748, 0.673],
        strict=True,
    ),
    (320, 0.690),
]


def _blank_preconsolidation(record):
    assert np.isnan(record["preconsolidation_stress"])
    assert np.isnan(record["compression_index"])
    assert np.isnan(record["recompression_index"])
    assert all(
        p["role"] in {"loading", "swelling", "left_out"} for p in record["points"]
    )


def test_ac8_no_clear_break():
    record = _one(_frame(NO_BREAK))
    assert record["lower_count"] == 4
    assert record["slope_ratio"] == pytest.approx(1.16891429, rel=REL)
    _blank_preconsolidation(record)
    assert record["preconsolidation_stress_reason"] == (
        "no clear break: the upper line is 1.17 times as steep as the lower, "
        "at least 2 is needed"
    )
    assert record["swelling_index"] == pytest.approx(0.0282363888, rel=REL)


def test_ac8_upper_line_not_falling():
    points = [(10, 1.0), (20, 0.99), (40, 0.98), (80, 0.98), (160, 0.981), (320, 0.982)]
    record = _one(_frame(points))
    _blank_preconsolidation(record)
    assert record["preconsolidation_stress_reason"] == (
        "no clear break: the upper line isn't falling"
    )


def test_ac9_crossing_outside_the_loading_stresses():
    points = [(10, 1.000), (20, 0.999), (40, 0.998), (80, 0.600), (160, 0.500)]
    record = _one(_frame([*points, (320, 0.400)]))
    assert len(record["splits"]) == 1
    assert record["slope_ratio"] == pytest.approx(133.464616, rel=REL)
    assert record["crossing_stress"] == pytest.approx(7.93570770, rel=REL)
    _blank_preconsolidation(record)
    assert record["preconsolidation_stress_reason"] == (
        "the lines cross at 7.94 kPa, outside the loading stresses (10.0 to 320 kPa)"
    )


def test_ac10_virgin_line_too_short():
    points = [
        (25, 0.795),
        (50, 0.788),
        (100, 0.776),
        (200, 0.766),
        (250, 0.745),
        (300, 0.722),
        (350, 0.702),
    ]
    record = _one(_frame(points))
    assert record["lower_count"] == 4
    assert record["crossing_stress"] == pytest.approx(213.808933, rel=REL)
    assert record["highest_stress_over_preconsolidation_stress"] == pytest.approx(
        1.63697557, rel=REL
    )
    _blank_preconsolidation(record)
    assert record["preconsolidation_stress_reason"] == (
        "the highest loading stress is 1.64 σ′p, at least 2 is needed to define "
        "the virgin line"
    )


def test_ac11_too_few_points():
    record = _one(_frame(BH1_U3[:5]))
    _blank_preconsolidation(record)
    assert record["splits"] == []
    assert record["preconsolidation_stress_reason"] == (
        "6 loading points are needed (3 per line), 5 given"
    )


def test_a_short_virgin_line_is_said_in_the_summary(example):
    points = [(25, 0.795), (50, 0.788), (100, 0.776), (200, 0.766)]
    points += [(300, 0.735), (400, 0.700), (500, 0.672)]
    fit = _fit(_frame(points))
    assert 2 < fit.specimens[0]["highest_stress_over_preconsolidation_stress"] < 3
    assert "highest stress 2.09 σ′p (below 3: a short virgin line)" in str(fit)
    text = str(_fit(example))
    assert "highest stress 3.78 σ′p;" in text
    assert "below 3" not in text


# --- AC 12: ties and order ------------------------------------------------------


def test_ac12_a_tie_takes_the_lower_split():
    # Point-symmetric about the middle point in log10 σ′v-log10(1 + e), so the
    # 3 | 4 and 4 | 3 splits mirror each other.
    y = [0.30, 0.299, 0.297, 0.29, 0.283, 0.281, 0.28]
    points = [(2**i, 10**v - 1) for i, v in enumerate(y)]
    record = _one(_frame(points))
    first, second = (s["sum_of_squares"] for s in record["splits"])
    assert first == pytest.approx(second, rel=1e-9)
    assert record["lower_count"] == 3


def test_ac12_order_of_specimens_doesnt_change_the_result():
    a = _frame(BH1_U3, specimen="A")
    b = _frame(NO_BREAK, specimen="B")
    one = _fit(pd.concat([a, b], ignore_index=True)).to_frame()
    other = _fit(pd.concat([b, a], ignore_index=True)).to_frame()
    assert one["specimen_id"].tolist() == ["A", "B"]
    pd.testing.assert_frame_equal(one, other)


def test_ac12_rows_keep_the_frame_order_within_a_specimen(bh1_u3):
    assert [p["row"] for p in bh1_u3["points"]] == list(range(12))


# --- AC 13: inputs --------------------------------------------------------------


def test_ac13_load_branch_added_with_a_note(site_si, bh1_u3):
    fit = _fit(site_si.drop(columns="load_branch"))
    assert fit.specimens[0]["preconsolidation_stress"] == pytest.approx(
        bh1_u3["preconsolidation_stress"], rel=1e-12
    )
    assert any("load_branch added" in note for note in fit.notes)
    assert not any("load_branch added" in note for note in _fit(site_si).notes)


@pytest.mark.parametrize("column", ["specimen_id", "void_ratio_at_increment_end"])
def test_ac13_missing_column(column):
    with pytest.raises(ColumnError, match=column) as error:
        _fit(_frame(BH1_U3).drop(columns=column))
    assert 'ht.template("oedometer")' in str(error.value)


def test_ac13_blank_specimen_id():
    df = _frame(BH1_U3)
    df.loc[3, "specimen_id"] = None
    with pytest.raises(HangtuError, match="Rows 3 have no specimen_id"):
        _fit(df)


def test_ac13_template_csv_with_blank_columns(tmp_path):
    template = ht.template("oedometer")
    rows = pd.DataFrame(
        {
            "specimen_id": ["S1"] * 12,
            "applied_vertical_stress": [s for s, _ in BH1_U3],
            "void_ratio_at_increment_end": [e for _, e in BH1_U3],
        }
    )
    path = tmp_path / "oedometer.csv"
    pd.concat([template, rows]).to_csv(path, index=False)
    df = ht.read_csv(path, units={"applied_vertical_stress": "kPa"})
    record = _one(df)
    assert record["preconsolidation_stress"] == pytest.approx(264.401656, rel=REL)


def test_unknown_load_branch_is_an_error():
    df = ht.analysis.oedometer_load_branch(_frame(BH1_U3))
    df.loc[2, "load_branch"] = "creep"
    with pytest.raises(HangtuError, match="Rows 2 have load_branch 'creep'"):
        _fit(df)


def test_negative_void_ratio_is_an_error():
    df = _frame(BH1_U3)
    df.loc[1, "void_ratio_at_increment_end"] = -0.1
    with pytest.raises(HangtuError, match="Rows 1 have a negative"):
        _fit(df)


def test_display_units_must_be_known():
    with pytest.raises(HangtuError, match="display_units"):
        _fit(_frame(BH1_U3), display_units="metric")


# --- AC 14: units ---------------------------------------------------------------


def test_ac14_psf_file_gives_the_same_indexes_and_scaled_stress(site_si, site_us):
    si, us = _one(site_si), _one(site_us)
    assert _fit(site_us).unit == "psf"
    assert us["preconsolidation_stress"] * PSF == pytest.approx(
        si["preconsolidation_stress"], rel=1e-9
    )
    for name in ("compression_index", "recompression_index", "swelling_index"):
        assert us[name] == pytest.approx(si[name], rel=1e-9)


def test_ac14_display_units_si_on_the_psf_file(site_si, site_us):
    fit = _fit(site_us, display_units="SI")
    assert fit.unit == "kPa"
    assert fit.specimens[0]["preconsolidation_stress"] == pytest.approx(
        _one(site_si)["preconsolidation_stress"], rel=1e-9
    )


# --- AC 15: the example file ------------------------------------------------------


def test_ac15_example_file(example):
    frame = _fit(example).to_frame().set_index("sample_reference")
    b4, b5 = frame.loc["B-4-U1"], frame.loc["B-5-U2"]
    assert round(b4["preconsolidation_stress"]) == 1624
    assert round(b4["compression_index"], 3) == 0.388
    assert round(b4["recompression_index"], 4) == 0.0382
    assert round(b4["highest_stress_over_preconsolidation_stress"], 2) == 9.85
    assert round(b4["swelling_index"], 4) == 0.0590
    assert round(b4["compression_ratio"], 3) == 0.186
    assert round(b4["preconsolidation_stress_pacheco_silva"]) == 1615
    assert round(b5["preconsolidation_stress"]) == 4232
    assert round(b5["compression_index"], 3) == 0.254
    assert round(b5["recompression_index"], 4) == 0.0326
    assert round(b5["highest_stress_over_preconsolidation_stress"], 2) == 3.78
    assert round(b5["swelling_index"], 4) == 0.0399
    assert round(b5["compression_ratio"], 3) == 0.137
    assert round(b5["preconsolidation_stress_pacheco_silva"]) == 3943


def test_ac15_swelling_pressure_specimen_has_no_loading_branch(example):
    frame = _fit(example).to_frame().set_index("sample_reference")
    swell = frame.loc["B-1-U2"]
    assert swell["test_type"] == "SWELLPRESS"
    assert np.isnan(swell["preconsolidation_stress"])
    assert swell["preconsolidation_stress_reason"] == "no loading branch"
    assert swell["count_no_applied_stress"] == 1


# --- AC 16: the result object -------------------------------------------------------


def test_ac16_result_object(site_si):
    fit = _fit(site_si)
    assert fit.kind == "derived"
    assert fit.function == "oedometer_fit"
    assert fit.unit == "kPa"
    json.dumps(fit.to_dict())
    frame = fit.to_frame()
    assert frame.attrs["units"]["preconsolidation_stress"] == "kPa"
    assert (
        list(frame.columns[:7])
        == [
            "specimen_id",
            "sample_reference",
            "specimen_reference",
            "loca_id",
            "depth",
            "geology_unit",
            "test_type",
        ][: len(fit.identifiers)]
    )
    for column in (
        "preconsolidation_stress",
        "preconsolidation_stress_pacheco_silva",
        "compression_index",
        "recompression_index",
        "swelling_index",
        "compression_ratio",
        "overconsolidation_ratio",
        "normalized_void_ratio_change",
        "sample_quality",
        "count_loading_after_reload",
        "highest_stress_over_preconsolidation_stress",
        "count_unload_runs",
        "preconsolidation_stress_reason",
        "swelling_index_reason",
        "pacheco_silva_reason",
        "overconsolidation_ratio_reason",
        "normalized_void_ratio_change_reason",
        "sample_quality_reason",
    ):
        assert column in frame.columns


def test_ac16_summary(example):
    text = str(_fit(example))
    assert (
        "B-4-U1-C1: σ′p = 1,620 psf (Oikawa; Pacheco Silva 1,620 psf), Cc = 0.388, "
        "Cr = 0.0382, Cs = 0.0590, CR = 0.186"
    ) in text
    assert "unload 1 from 8,000 psf, used: Cs = 0.0590" in text
    assert "7 loading points, 4 on the virgin line, highest stress 9.85 σ′p" in text
    assert "B-1-U2-SW1: σ′p not given: no loading branch" in text
