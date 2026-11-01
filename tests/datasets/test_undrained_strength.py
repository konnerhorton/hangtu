"""p.undrained_strength() (datasets.md §6.11).

Acceptance criteria are those of docs/work/m17a-strength-data.md (AC n). The
golden values are hand-calculated from the test files' values, in
tests/data/ags/_make_files.py: s_u = q_f / 2 for UU and q_u / 2 for
unconfined compression, a vane's or fall cone's s_u as reported, and
S_t = s_u / s_u,r.
"""

import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest

import hangtu as ht

from .conftest import make_files

#: 1 psf in kPa: 0.45359237 × 9.80665 / 0.3048² / 1000 (exact).
PSF = 0.45359237 * 9.80665 / 0.3048**2 / 1000
SCALE = "unconfined_compressive_strength"
IPEN_LEFT_OUT = r"^Left out 2 IPEN results"


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


@pytest.fixture
def site(fresh):
    project = fresh("site_si")
    project.set_geology_map(make_files.HERE / "strata.csv")
    return project


def _rows(df, test_type):
    return df[df["test_type"] == test_type].reset_index(drop=True)


def test_rows_come_by_group_in_file_order(site):
    # AC 1-4 (order): TRIT, LUCT, LVAN, LPEN, LFCN, then IVAN, IPEN.
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    assert list(df["test_type"]) == [
        *["UU"] * 3,
        "unconfined compression",
        "LV",
        "hand penetrometer",
        "fall cone",
        "BOREHOLE",
        "BOREHOLE",
        "hand penetrometer",
        "hand penetrometer",
    ]
    assert list(df["source"]) == ["lab"] * 7 + ["field"] * 4


def test_uu_s_u_is_half_the_deviator_stress(site):
    # AC 1: q_f 120, 124, 118 kPa -> 60, 62, 59; TRIT_CU 60, 62, 59.
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    uu = _rows(df, "UU")
    assert uu["undrained_shear_strength"].tolist() == pytest.approx([60, 62, 59])
    assert uu["reported_undrained_shear_strength"].tolist() == [60, 62, 59]
    assert set(uu["undrained_shear_strength_basis"]) == {"half_deviator_stress"}
    assert uu["cell_pressure"].tolist() == [100, 200, 300]
    triaxial = _quiet(site.triaxial, where={"test_type": "UU"})
    for column in ["depth", "depth_basis", "test_stage", "geology_unit"]:
        assert uu[column].tolist() == triaxial[column].tolist()
    assert not uu["multistage_test"].any()


def test_unconfined_compression_s_u_is_half_q_u(site):
    # AC 2: LUCT_UCS 96 kPa -> 48.
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    row = _rows(df, "unconfined compression").iloc[0]
    assert row["undrained_shear_strength"] == pytest.approx(48)
    assert row["unconfined_compressive_strength"] == 96
    assert (
        row["undrained_shear_strength_basis"] == "half_unconfined_compressive_strength"
    )
    assert row["sample_condition"] == "UNDISTURBED"
    assert row["axial_strain_at_failure"] == pytest.approx(8.5)


def test_vanes_and_fall_cone_give_their_sensitivity(site):
    # AC 3: 42/14 = 3.0 and 55/22 = 2.5 (field), 38/12 (LV), 30/9 (fall cone).
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    field = _rows(df, "BOREHOLE")
    assert field["depth"].tolist() == [3.0, 6.0]
    assert set(field["depth_basis"]) == {"test_depth"}
    assert field["strength_sensitivity"].tolist() == pytest.approx([3.0, 2.5])
    assert set(field["undrained_shear_strength_basis"]) == {"as_reported"}
    lab = _rows(df, "LV").iloc[0]
    assert lab["strength_sensitivity"] == pytest.approx(38 / 12, rel=1e-9)
    cone = _rows(df, "fall cone").iloc[0]
    assert cone["strength_sensitivity"] == pytest.approx(30 / 9, rel=1e-9)
    assert cone["depth"] == pytest.approx(5.30)


def test_hand_penetrometer_in_situ_needs_its_scale(site):
    # AC 4: without the scale the two IPEN rows are left out, with the warning.
    with pytest.warns(UserWarning, match=IPEN_LEFT_OUT) as caught:
        df = site.undrained_strength()
    assert len(caught) == 1
    assert "hand_penetrometer_scale" in str(caught[0].message)
    assert (df["source"] == "field").sum() == 2  # the two vanes
    lab = _rows(df, "hand penetrometer").iloc[0]
    assert lab["undrained_shear_strength"] == 45
    assert lab["undrained_shear_strength_basis"] == "as_reported"


@pytest.mark.parametrize(
    ("scale", "values", "basis"),
    [
        (
            "unconfined_compressive_strength",
            [75, 100],
            "half_hand_penetrometer_reading",
        ),
        ("undrained_shear_strength", [150, 200], "hand_penetrometer_reading"),
    ],
)
def test_hand_penetrometer_in_situ_by_its_scale(site, scale, values, basis):
    # AC 4: 150 and >200 kPa; the bound stays a bound.
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=scale)
    field = df[(df["source"] == "field") & (df["test_type"] == "hand penetrometer")]
    assert field["undrained_shear_strength"].tolist() == pytest.approx(values)
    assert field["qualifier"].tolist() == ["", ">"]
    assert set(field["undrained_shear_strength_basis"]) == {basis}
    assert field["hand_penetrometer_reading"].tolist() == [150, 200]


def test_an_unknown_scale_raises(site):
    with pytest.raises(ht.HangtuError, match="isn't one of"):
        site.undrained_strength(hand_penetrometer_scale="psf")


def test_us_display(fresh):
    # AC 5: 60 kPa = 1253.1261 psf; 48 kPa = 1002.5008 psf.
    project = fresh("site_si", display_units="US")
    df = _quiet(project.undrained_strength, hand_penetrometer_scale=SCALE)
    assert df.attrs["units"]["undrained_shear_strength"] == "psf"
    assert df["undrained_shear_strength"].iloc[0] == pytest.approx(1253.1261, rel=1e-6)
    assert df["undrained_shear_strength"].iloc[3] == pytest.approx(1002.5008, rel=1e-6)
    assert _rows(df, "LV")["strength_sensitivity"].iloc[0] == pytest.approx(38 / 12)


@pytest.mark.parametrize("display_units", ["SI", "US"])
def test_twins_agree(fresh, display_units):
    # AC 6 (undrained half).
    si = fresh("site_si", display_units=display_units)
    us = fresh("site_us", display_units=display_units)
    a = _quiet(si.undrained_strength, hand_penetrometer_scale=SCALE)
    b = _quiet(us.undrained_strength, hand_penetrometer_scale=SCALE)
    numeric = a.select_dtypes("number").columns.drop("source_line")
    np.testing.assert_allclose(
        a[numeric].to_numpy(float), b[numeric].to_numpy(float), rtol=1e-9
    )
    assert a.attrs["units"] == b.attrs["units"]


def test_the_tests_are_not_pooled_unawares(site):
    # AC 7
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    with pytest.raises(ht.HangtuError, match="test_type"):
        ht.stats.describe(df, value="undrained_shear_strength")
    # The lab and in situ hand penetrometers share a test type, not a source.
    with pytest.raises(ht.HangtuError, match="source"):
        ht.stats.describe(df, value="undrained_shear_strength", by="test_type")
    with pytest.warns(UserWarning, match="fewer than 3 values"):
        result = ht.stats.describe(
            df, value="undrained_shear_strength", by=["test_type", "source"]
        )
    assert len(result.to_frame()) == 7


@pytest.fixture
def joins(fresh):
    return fresh("joins")


def _joined(project, **kwargs):
    with pytest.warns(UserWarning) as caught:
        df = project.undrained_strength(**kwargs)
    return df, [str(w.message) for w in caught]


def test_a_flagged_peak_keeps_its_bound_and_blanks_the_sensitivity(joins):
    # AC 8: >120 with 30; 55 with 0: both sensitivities blank, in one warning.
    df, messages = _joined(joins)
    vane = df.set_index("depth")
    assert vane.loc[2.50, "qualifier"] == ">"
    assert vane.loc[2.50, "remolded_qualifier"] == ""
    assert vane.loc[2.50, "undrained_shear_strength"] == 120
    assert np.isnan(vane.loc[2.50, "strength_sensitivity"])
    assert np.isnan(vane.loc[3.00, "strength_sensitivity"])
    assert vane.loc[3.00, "remolded_undrained_shear_strength"] == 0
    assert sum("left blank on 2 rows" in m for m in messages) == 1
    df = ht.set_units(df, df.attrs["units"])
    peak = ht.stats.describe(df, value="undrained_shear_strength", pool="test_type")
    assert peak.to_frame().loc[0, "count_at_least"] == 1
    remolded = ht.stats.describe(
        df, value="remolded_undrained_shear_strength", pool="test_type"
    )
    assert remolded.to_frame().loc[0, "count_at_least"] == 0


def test_a_blank_type_is_named(joins):
    # AC 9
    df, _ = _joined(joins)
    row = df[df["depth"] == 3.50].iloc[0]
    assert row["test_type"] == "in situ vane, type not given"
    assert row["strength_sensitivity"] == pytest.approx(4.0)


def test_an_incomplete_vane_is_left_out_unless_asked(joins):
    # AC 16: IVAN_IVAN blank at 4.00 m.
    df, messages = _joined(joins)
    assert 4.00 not in df["depth"].tolist()
    assert any("IVAN_IVAN" in m and "Left out" in m for m in messages)
    df, _ = _joined(joins, include_incomplete=True)
    row = df[df["depth"] == 4.00].iloc[0]
    assert np.isnan(row["undrained_shear_strength"])
    assert row["remolded_undrained_shear_strength"] == 12


def test_no_group_gives_an_empty_frame(fresh):
    # AC 15 (undrained half): defects.ags has none of the seven groups.
    project = fresh("defects")
    with pytest.warns(
        UserWarning, match="No TRIT, LUCT, LVAN, LPEN, LFCN, IVAN or IPEN"
    ):
        df = project.undrained_strength()
    assert df.empty
    assert "undrained_shear_strength" in df.columns


def test_feeds_the_plots(site):
    # AC 17
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE)
    fig, _ = _quiet(
        ht.plot.profile, df, "undrained_shear_strength", color_by="test_type"
    )
    plt.close(fig)
    fig, _ = _quiet(ht.plot.geology_unit_comparison, df, "undrained_shear_strength")
    plt.close(fig)


def test_common_arguments_filter(site):
    # AC 19
    df = _quiet(
        site.undrained_strength,
        hand_penetrometer_scale=SCALE,
        where={"test_type": "UU"},
    )
    assert len(df) == 3
    df = _quiet(site.undrained_strength, hand_penetrometer_scale=SCALE, holes="BH2")
    assert set(df["loca_id"]) == {"BH2"}
    df = _quiet(
        site.undrained_strength,
        hand_penetrometer_scale=SCALE,
        depth=(0, 2),
        geology="Fill",
    )
    assert set(df["test_type"]) == {"unconfined compression", "hand penetrometer"}
