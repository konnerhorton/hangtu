"""p.triaxial_readings() and p.shear_box_readings() (datasets.md §6.16, §6.17).

M16 acceptance criteria 3, 4-7 end to end, and 9-13. The readings are the
spec's tables, in tests/data/ags/_make_files.py.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.registry import template

from .conftest import DATA

MAP = DATA / "readings_map.csv"
INTERPOLATED = r"interpolated in strain"
DASH = chr(0x2013)  # an en dash, as the warnings write line ranges
PSF = 20.8854342  # psf per kPa
BH1_Q = [
    (0.0, 0), (2.0, 100), (4.0, 150), (6.0, 170), (8.5, 180),
    (10.0, 176), (12.0, 170), (11.8, 80), (11.6, 5),
]  # fmt: skip
BH1_DU = [(0.0, 0), (3.0, 40), (7.0, 56), (10.0, 64), (12.0, 66), (11.7, 60)]
BH2_D1 = [
    (0.00, 38 * 0, 0.00), (0.50, 20, 0.05), (1.00, 30, 0.15), (2.10, 38, 0.30),
    (4.00, 34, 0.25), (8.00, 31, 0.10), (12.00, 30, -0.40),
]  # fmt: skip


@pytest.fixture
def mapped(fresh):
    """A project from a test file with the readings map set."""

    def build(name="site_si", **settings):
        p = fresh(name, **settings)
        p.set_readings_map(MAP)
        return p

    return build


def quiet(call, *args, **kwargs):
    """Call, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def stage(df, specimen, test_stage="1"):
    return df[(df["specimen_id"] == specimen) & (df["test_stage"] == test_stage)]


# --- AC 3: triaxial rows ----------------------------------------------------------


def test_ac3_triaxial_rows(mapped):
    p = mapped()
    df = quiet(p.triaxial_readings)
    rows = stage(df, "7")  # BH1-U3 specimen 1
    assert len(rows) == 15
    q, du = rows.iloc[:9], rows.iloc[9:]
    assert list(zip(q["axial_strain"], q["deviator_stress"], strict=True)) == BH1_Q
    assert list(zip(du["axial_strain"], du["excess_pore_pressure"], strict=True)) == (
        BH1_DU
    )
    assert q[["excess_pore_pressure", "volumetric_strain"]].isna().all().all()
    assert du[["deviator_stress", "volumetric_strain"]].isna().all().all()
    assert (rows["test_type"] == "CU").all()
    assert (rows["test_stage"] == "1").all()
    assert (rows["cell_pressure"] == 400).all()
    assert (rows["back_pressure"] == 300).all()
    assert (rows["effective_consolidation_stress"] == 100).all()
    assert (rows["failure_criterion"] == "Maximum deviator stress").all()
    assert rows["reported_failure_reading"].isna().all()
    # Each reading's own line, in file order.
    assert list(rows["source_line"]) == [*range(325, 334), *range(359, 365)]
    with pytest.warns(UserWarning, match="back pressure"):
        stage_row = stage(p.triaxial(), "7").iloc[0]
    for column in ["loca_id", "depth", "depth_basis", "elevation", "geology_unit"]:
        assert (rows[column] == stage_row[column]).all(), column
    # Stages in p.triaxial()'s order.
    stages = list(dict.fromkeys(zip(df["specimen_id"], df["test_stage"], strict=True)))
    with pytest.warns(UserWarning, match="back pressure"):
        tret = p.triaxial().query("test_type != 'UU'")
    assert stages == list(zip(tret["specimen_id"], tret["test_stage"], strict=True))


def test_ac3_columns_are_the_template_and_source_line(mapped):
    df = quiet(mapped().triaxial_readings)
    assert list(df.columns) == [*template("triaxial_readings").columns, "source_line"]
    df = quiet(mapped().shear_box_readings)
    assert list(df.columns) == [*template("shear_box_readings").columns, "source_line"]


# --- AC 4-6 end to end ---------------------------------------------------------------


def test_ac4_failure_from_ags_readings_is_p_triaxial(mapped):
    p = mapped()
    with pytest.warns(UserWarning, match=INTERPOLATED) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            p.triaxial_readings(), failure_criterion="max_deviator_stress"
        )
    assert len(record) == 1
    message = str(record[0].message)
    assert "7 stage 1 (excess_pore_pressure)" in message
    assert "10 stage 3 (volumetric_strain)" in message
    with pytest.warns(UserWarning, match="back pressure"):
        reported = p.triaxial()
    for specimen, test_stage in [("7", "1"), ("10", "3")]:
        got, lab = (
            stage(rows, specimen, test_stage),
            stage(reported, specimen, test_stage),
        )
        for column in [
            "axial_strain_at_failure",
            "deviator_stress_at_failure",
            "pore_pressure_at_failure",
            "volumetric_strain_at_failure",
        ]:
            assert got[column].to_numpy() == pytest.approx(
                lab[column].to_numpy(), rel=1e-9, nan_ok=True
            ), (specimen, column)
    # BH1-U3: Δu 60 interpolated, so u_f 360; BH2-U2 drained: u_f 300, εv 3.4.
    assert stage(rows, "7")["pore_pressure_at_failure"].item() == pytest.approx(360)
    bh2 = stage(rows, "10", "3")
    assert bh2["volumetric_strain_at_failure"].item() == pytest.approx(3.4, rel=1e-9)
    assert bh2["pore_pressure_at_failure"].item() == 300


def test_ac5_max_stress_ratio(mapped):
    readings = mapped().triaxial_readings(where={"specimen_id": "7"})
    with pytest.warns(UserWarning, match=INTERPOLATED):
        rows = ht.analysis.triaxial_failure_from_readings(
            readings, failure_criterion="max_stress_ratio"
        )
    assert rows["axial_strain_at_failure"].item() == 12.0
    assert rows["deviator_stress_at_failure"].item() == 170
    assert rows["pore_pressure_at_failure"].item() == pytest.approx(366, rel=1e-9)


def test_ac6_paths_and_tails(mapped):
    readings = mapped().triaxial_readings(where={"specimen_id": "7"})
    _, ax, _ = ht.plot.triaxial_shearing(
        readings,
        space="s_t",
        failure_criterion="max_deviator_stress",
        display_units="SI",
    )
    (path,) = [line for line in ax.lines if line.get_gid() == "stress_path"]
    assert len(path.get_xdata()) == 7
    assert [path.get_xdata()[1], path.get_ydata()[1]] == pytest.approx(
        [123.333333333, 50], rel=1e-9
    )
    _, ax, _ = ht.plot.triaxial_shearing(
        readings,
        failure_criterion="max_deviator_stress",
        second_axis="excess_pore_pressure",
        display_units="SI",
    )
    (curve,) = [line for line in ax.lines if line.get_gid() == "reading_curve"]
    assert (curve.get_xdata()[-1], curve.get_ydata()[-1]) == (11.6, 5)
    twin = next(a for a in ax.get_shared_x_axes().get_siblings(ax) if a is not ax)
    (line,) = [line for line in twin.lines if line.get_gid() == "second_axis_line"]
    assert (line.get_xdata()[-1], line.get_ydata()[-1]) == (11.7, 60)


# --- AC 7: the edge cases in joins.ags ------------------------------------------------


def test_ac7_readings_left_out(mapped):
    p = mapped("joins")
    with pytest.warns(UserWarning) as record:
        df = p.triaxial_readings()
    messages = [str(w.message) for w in record]
    assert len(messages) == 3
    assert (
        f"Left out 2 readings of XTDS with no stage in TRET (lines 179{DASH}180)"
        in messages[0]
    )
    assert "Left out 1 reading of XTPW with a flagged value (line 189)" in messages[1]
    assert "Left out 1 reading of XTDS with a blank stage or strain" in messages[2]
    assert "(line 178)" in messages[2]
    j1 = stage(df, "18")
    assert list(j1["source_line"]) == [*range(172, 178), 186, 187, 188]
    with pytest.warns(UserWarning) as record:
        kept = p.triaxial_readings(include_incomplete=True)
    assert len(record) == 2  # the stage and flag warnings; the reading is kept
    assert list(stage(kept, "18")["source_line"]) == [
        *range(172, 179),
        186,
        187,
        188,
    ]
    assert np.isnan(stage(kept, "18")["axial_strain"].iloc[6])


def test_ac7_failure_from_joins_readings(mapped):
    with pytest.warns(UserWarning):
        readings = mapped("joins").triaxial_readings(where={"specimen_id": "18"})
    with pytest.warns(UserWarning) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            readings, failure_criterion="max_deviator_stress"
        )
    messages = [str(w.message) for w in record]
    assert len(messages) == 1 and "decreases" in messages[0]
    assert rows["axial_strain_at_failure"].item() == 3.0
    assert rows["deviator_stress_at_failure"].item() == 90
    assert np.isnan(rows["pore_pressure_at_failure"].item())
    with pytest.warns(UserWarning) as record:
        rows = ht.analysis.triaxial_failure_from_readings(
            readings, failure_criterion="max_stress_ratio"
        )
    assert len(record) == 2
    assert rows["axial_strain_at_failure"].item() == 1.9
    assert rows["deviator_stress_at_failure"].item() == 85
    assert rows["pore_pressure_at_failure"].item() == pytest.approx(324, rel=1e-9)


# --- AC 9-13 ------------------------------------------------------------------------


def test_ac9_shear_box_rows(mapped):
    p = mapped()
    rows = stage(quiet(p.shear_box_readings), "14")  # BH2-D1 S1
    assert len(rows) == 7
    assert (rows["test_type"] == "SMALL SBOX").all()
    assert (rows["applied_normal_stress"] == 50).all()
    got = zip(
        rows["horizontal_displacement"],
        rows["shear_stress"],
        rows["vertical_displacement"],
        strict=True,
    )
    assert [tuple(map(float, r)) for r in got] == pytest.approx(BH2_D1, rel=1e-9)
    assert list(rows["source_line"]) == list(range(392, 399))
    us = stage(quiet(p.shear_box_readings, display_units="US"), "14").iloc[3]
    assert us["horizontal_displacement"] == pytest.approx(2.10 / 25.4, rel=1e-6)
    assert us["shear_stress"] == pytest.approx(38 * PSF, rel=1e-6)


@pytest.mark.parametrize("units", ["SI", "US"])
@pytest.mark.parametrize("dataset", ["triaxial_readings", "shear_box_readings"])
def test_ac10_twins(mapped, units, dataset):
    si = quiet(getattr(mapped("site_si"), dataset), display_units=units)
    us = quiet(getattr(mapped("site_us"), dataset), display_units=units)
    pd.testing.assert_frame_equal(
        si.drop(columns=["source_line", "sample_reference"]),
        us.drop(columns=["source_line", "sample_reference"]),
        rtol=1e-9,
    )


@pytest.mark.parametrize(
    ("dataset", "noun"),
    [("triaxial_readings", "triaxial"), ("shear_box_readings", "shear box")],
)
def test_ac11_no_map(fresh, dataset, noun):
    with pytest.warns(UserWarning) as record:
        df = getattr(fresh(), dataset)()
    assert [str(w.message) for w in record] == [
        f"No readings map for this project, so there are no {noun} readings. Set "
        "one with p.set_readings_map(path)."
    ]
    assert df.empty
    assert list(df.columns) == [*template(dataset).columns, "source_line"]


def test_ac11_no_group_for_the_dataset(fresh):
    p = fresh()
    p.set_readings_map(pd.read_csv(MAP, dtype=str).query("group == 'XSBS'"))
    with pytest.warns(UserWarning) as record:
        df = p.triaxial_readings()
    assert [str(w.message) for w in record] == [
        "The readings map names no triaxial_readings group."
    ]
    assert df.empty


def test_ac11_no_curve_groups_and_no_map(fresh):
    with pytest.warns(UserWarning, match="No readings map") as record:
        fresh("site_v404").triaxial_readings()
    assert len(record) == 1


def test_ac12_common_arguments(mapped):
    p = mapped()
    df = quiet(p.triaxial_readings, holes=["BH2"])
    assert set(df["specimen_id"]) == {"10"}
    assert len(df) == 21
    df = quiet(p.triaxial_readings, depth=(5.1, 5.2))
    assert set(df["specimen_id"]) == {"8"}
    df = quiet(p.triaxial_readings, where={"test_stage": "3"})
    assert set(zip(df["specimen_id"], df["test_stage"], strict=True)) == {("10", "3")}
    assert len(df) == 9
    all_rows = quiet(p.triaxial_readings)
    unit = all_rows["geology_unit"].iloc[0]
    df = quiet(p.triaxial_readings, geology=unit)
    assert len(df) == (all_rows["geology_unit"] == unit).sum()


def test_ac13_units(mapped):
    p = mapped()
    for dataset in ["triaxial_readings", "shear_box_readings"]:
        df = quiet(getattr(p, dataset), display_units="US")
        numeric = [
            c for c in df.select_dtypes("number").columns if c not in ("source_line",)
        ]
        assert set(numeric) <= set(df.attrs["units"]), dataset
    triaxial = quiet(p.triaxial_readings).attrs["units"]
    assert triaxial["axial_strain"] == "%"
    assert triaxial["deviator_stress"] == "kPa"
    shear = quiet(p.shear_box_readings, display_units="US").attrs["units"]
    assert shear["horizontal_displacement"] == "in"
    assert shear["vertical_displacement"] == "in"


# --- M19 (c2): p.oedometer_readings() (datasets.md §6.18) ----------------------------
# Increment 4's readings are the c2 spec's golden table (its AC 1 and AC 10).
INCREMENT_4 = [
    (0, 0.267), (0.1, 0.306), (0.25, 0.317), (0.5, 0.330), (1, 0.348),
    (2, 0.374), (4, 0.410), (8, 0.460), (15, 0.511), (30, 0.552),
    (60, 0.565), (120, 0.568), (240, 0.570), (480, 0.573), (1440, 0.578),
]  # fmt: skip


def test_oedometer_readings_carry_their_increment(mapped):
    p = mapped()
    df = quiet(p.oedometer_readings)
    assert list(df.columns) == [*template("oedometer_readings").columns, "source_line"]
    assert list(dict.fromkeys(df["test_stage"])) == ["2", "3", "4", "5", "6"]
    assert len(df) == 5 * 15
    rows = df[df["test_stage"] == "4"]
    got = zip(rows["elapsed_time"], rows["vertical_displacement"], strict=True)
    assert [tuple(map(float, r)) for r in got] == pytest.approx(INCREMENT_4, rel=1e-12)
    increment = quiet(p.oedometer).set_index("test_stage").loc["4"]
    for column in [
        "loca_id",
        "specimen_id",
        "test_type",
        "load_branch",
        "applied_vertical_stress",
        "void_ratio_at_increment_start",
        "void_ratio_at_increment_end",
        "specimen_height",
        "void_ratio",
        "reported_coefficient_of_consolidation_root_time",
        "reported_coefficient_of_consolidation_log_time",
        "depth",
    ]:
        assert (rows[column] == increment[column]).all(), column
    first = rows.iloc[0]
    assert (first["load_branch"], first["applied_vertical_stress"]) == ("loading", 200)
    assert (first["void_ratio_at_increment_start"], first["specimen_height"]) == (
        0.776,
        20.0,
    )
    assert first["reported_coefficient_of_consolidation_root_time"] == 2.1
    assert list(rows["source_line"]) == sorted(rows["source_line"])
    assert df.attrs["units"]["elapsed_time"] == "min"
    assert df.attrs["units"]["vertical_displacement"] == "mm"


@pytest.mark.parametrize("units", ["SI", "US"])
def test_oedometer_readings_twins(mapped, units):
    si = quiet(mapped("site_si").oedometer_readings, display_units=units)
    us = quiet(mapped("site_us").oedometer_readings, display_units=units)
    pd.testing.assert_frame_equal(
        si.drop(columns=["source_line", "sample_reference"]),
        us.drop(columns=["source_line", "sample_reference"]),
        rtol=1e-9,
    )
    if units == "US":
        assert us.attrs["units"]["elapsed_time"] == "min"
        assert us.attrs["units"]["vertical_displacement"] == "in"
        row = us[us["test_stage"] == "4"].iloc[7]
        assert row["vertical_displacement"] == pytest.approx(0.460 / 25.4, rel=1e-9)
        assert row["elapsed_time"] == 8


def test_oedometer_readings_left_out_with_no_increment(mapped):
    # joins.ags: two readings of an increment "3" that CONS doesn't have.
    p = mapped("joins")
    with pytest.warns(UserWarning) as record:
        df = p.oedometer_readings()
    messages = [str(w.message) for w in record]
    assert len(messages) == 1
    assert "Left out 2 readings of XCOT with no stage in CONS" in messages[0]
    assert messages[0].endswith(
        "from the oedometer readings: their specimen and stage must match a row "
        "of that group. Without its stage a reading has nothing to be read "
        "against, so include_incomplete=True doesn't keep it."
    )
    assert list(df["test_stage"]) == ["1"] * 4 + ["2"] * 2
    first = df[df["test_stage"] == "1"]
    assert list(first["elapsed_time"]) == [0.0, 1.0, 4.0, 60.0]
    assert (first["applied_vertical_stress"] == 5).all()
    assert (first["void_ratio_at_increment_end"] == 0.897).all()
    # Increment "2" is incomplete in CONS (a blank CONS_INCE), so p.oedometer()
    # leaves it out; its readings still get its values.
    with pytest.warns(UserWarning, match="CONS_INCE"):
        assert "2" not in set(p.oedometer()["test_stage"])
    second = df[df["test_stage"] == "2"]
    assert (second["applied_vertical_stress"] == 10).all()
    assert (second["load_branch"] == "loading").all()
    assert second["void_ratio_at_increment_end"].isna().all()


def test_oedometer_readings_incomplete(mapped, tmp_path):
    # A blank time is incomplete: left out with a warning unless kept.
    text = (DATA / "site_si.ags").read_bytes().decode("utf-8")
    old = '"OED1","5.20","4","7","4.00","0.410"'
    assert old in text
    path = tmp_path / "blank.ags"
    path.write_bytes(text.replace(old, '"OED1","5.20","4","7","","0.410"').encode())
    p = ht.Project.from_ags(path, display_units="SI", grag_fraction_system="astm_uscs")
    p.set_readings_map(MAP)
    with pytest.warns(UserWarning) as record:
        df = p.oedometer_readings()
    assert len(record) == 1
    assert (
        "Left out 1 reading of XCOT with a blank increment, time or displacement"
        in (str(record[0].message))
    )
    assert (df["test_stage"] == "4").sum() == 14
    kept = quiet(p.oedometer_readings, include_incomplete=True)
    assert (kept["test_stage"] == "4").sum() == 15


def test_oedometer_readings_convert_from_the_stored_time_unit(tmp_path):
    # A time heading in s is stored in minutes on ingest (ingest.md §7) and read
    # from its stored unit, so the readings are the same as in min.
    text = (DATA / "site_si.ags").read_bytes().decode("utf-8")
    start = text.index('\r\n"GROUP","XCOT"') + 2
    end = text.index("\r\n\r\n", start)
    lines = text[start:end].split("\r\n")
    lines[2] = lines[2].replace('"min","mm"', '"s","mm"')
    for i in range(4, len(lines)):
        cells = lines[i].split(",")
        cells[-2] = f'"{float(cells[-2].strip(chr(34))) * 60:.1f}"'
        lines[i] = ",".join(cells)
    dict_old = (
        '"XCOT_TIME","OTHER","2DP","Elapsed time since the load was applied","min"'
    )
    assert dict_old in text
    text = text[:start] + "\r\n".join(lines) + text[end:]
    text = text.replace(dict_old, dict_old.replace('"min"', '"s"'))
    path = tmp_path / "seconds.ags"
    path.write_bytes(text.encode("utf-8"))
    p = ht.Project.from_ags(path, display_units="SI", grag_fraction_system="astm_uscs")
    p.set_readings_map(MAP)
    rows = quiet(p.oedometer_readings, where={"test_stage": "4"})
    assert list(rows["elapsed_time"]) == pytest.approx([t for t, _ in INCREMENT_4])


def test_oedometer_readings_no_map(fresh):
    with pytest.warns(UserWarning) as record:
        df = fresh().oedometer_readings()
    assert [str(w.message) for w in record] == [
        "No readings map for this project, so there are no oedometer readings. Set "
        "one with p.set_readings_map(path)."
    ]
    assert df.empty
    assert list(df.columns) == [*template("oedometer_readings").columns, "source_line"]
