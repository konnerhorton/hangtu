"""p.spt() (datasets.md §6.1), against hand-calculated values."""

import warnings

import pandas as pd
import pytest

import hangtu as ht
from hangtu.datasets._spt import COLUMNS

from .conftest import make_files


@pytest.fixture
def site(fresh):
    return fresh("site_si")


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


def test_columns(site):
    df = _quiet(site.spt)
    assert list(df.columns) == [
        *COLUMNS,
        "geology_unit",
        "soil_class",
        "geology_description",
        "source_line",
    ]


def test_golden_depths(site):
    df = _quiet(site.spt)
    # BH1 3.00: increments 75 mm each: 3.00 + 0.150 + 0.300 / 2 = 3.300 m.
    # BH1 6.00: increments 75, 75, 75, 50: 6.00 + 0.150 + 0.125 / 2 = 6.2125 m.
    # BH2 2.00: no increments, NPEN 450: 2.00 + 0.300 = 2.300 m.
    assert list(df["depth"][:3]) == pytest.approx([3.300, 6.2125, 2.300])
    assert list(df["depth_basis"][:3]) == [
        "mid_drive",
        "mid_drive",
        "mid_drive_nominal",
    ]
    # Elevation 12.40 - 3.30 = 9.10 m, and 11.85 - 2.30 = 9.55 m.
    assert df["elevation"][0] == pytest.approx(9.10)
    assert df["elevation"][2] == pytest.approx(9.55)


def test_refusal_keeps_n_as_written(site):
    refusal = _quiet(site.spt).iloc[1]
    assert bool(refusal["spt_refusal"]) is True
    assert refusal["spt_n"] == 50
    assert refusal["spt_n_capped"] == 100
    assert refusal["spt_penetration"] == 275


def test_n60_and_its_source(site):
    df = _quiet(site.spt)
    # BH1 3.00: ISPT_N60 16 as given, not 12 * 80 / 60 = 16.0 recomputed.
    # BH1 6.00: no ISPT_N60, so 50 * 80 / 60 = 66.67 from ISPT_ERAT.
    # BH3: no ER and no N60: blank, with no default (SPEC §4).
    assert list(df["energy_source"]) == [
        "file_n60",
        "file_energy_ratio",
        "file_n60",
        "file_n60",
        None,
    ]
    assert df["spt_n60"][1] == pytest.approx(50 * 80 / 60)
    assert pd.isna(df["spt_n60"][4])


def test_hammer_efficiency(site):
    with pytest.warns(UserWarning, match=r"Energy ratio 70 % used for BH3 \(1 test\)"):
        df = site.spt(hammer_efficiency=70)
    assert df["spt_n60"][4] == pytest.approx(4 * 70 / 60)
    assert df["energy_source"][4] == "hammer_efficiency"
    with (
        ht.settings.override(hammer_efficiency=75),
        pytest.warns(UserWarning, match="Energy ratio 75 % used for BH3"),
    ):
        df = site.spt()
    assert df["spt_n60"][4] == pytest.approx(5.0)
    assert df["energy_source"][4] == "hammer_efficiency"


def test_hammer_efficiency_by_hole(site):
    with pytest.warns(UserWarning) as caught:
        df = site.spt(hammer_efficiency={"BH3": 70, "BH1": 90})
    # BH1 has ISPT_ERAT and ISPT_N60, which win; only BH3's test is filled.
    assert list(df["energy_source"]) == [
        "file_n60",
        "file_energy_ratio",
        "file_n60",
        "file_n60",
        "hammer_efficiency",
    ]
    assert df["spt_n60"][1] == pytest.approx(50 * 80 / 60)
    assert df["spt_n60"][4] == pytest.approx(4 * 70 / 60)
    assert [str(w.message).split(":")[0] for w in caught] == [
        "Energy ratio 70 % used for BH3 (1 test)"
    ]


def test_a_hole_not_in_the_dict_has_no_energy_source(site):
    with pytest.warns(UserWarning, match="aren't in the data: 'BH9'"):
        df = site.spt(hammer_efficiency={"BH9": 70})
    assert df["energy_source"][4] is None
    assert pd.isna(df["spt_n60"][4])


def test_cap(site):
    assert _quiet(site.spt, cap=60)["spt_n_capped"][1] == 60


def test_us_units(fresh):
    df = _quiet(fresh("site_us", display_units="US").spt)
    assert df["depth"][0] == pytest.approx(3.300 / 0.3048)
    assert df["spt_penetration"][0] == pytest.approx(450 / 25.4)
    assert df.attrs["units"]["spt_penetration"] == "in"
    assert df.attrs["units"]["depth"] == "ft"


def test_twins_agree(fresh):
    si = _quiet(fresh("site_si").spt).drop(columns="source_line")
    us = _quiet(fresh("site_us").spt).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_joins_file_depths(fresh):
    with pytest.warns(UserWarning):  # overlap and the incomplete record
        df = fresh("joins").spt()
    by_line = df.set_index("source_line")
    # Hand-calculated in tests/data/ags/_make_files.py, joins_groups().
    assert by_line.loc[45, "depth"] == pytest.approx(2.00)  # on the boundary
    assert by_line.loc[45, "geology_unit"] == "ALV"
    assert by_line.loc[46, "depth"] == pytest.approx(3.05)  # seating refusal
    assert by_line.loc[47, "geology_unit"] == "TRC"  # 4.80 m, in the overlap
    assert pd.isna(by_line.loc[49, "geology_unit"])  # 8.20 m, in the gap
    assert by_line.loc[50, "depth"] == pytest.approx(10.00)
    assert by_line.loc[50, "geology_unit"] == "BED"  # base of the deepest layer
    assert by_line.loc[51, "depth"] == pytest.approx(1.175)
    assert pd.isna(by_line.loc[51, "elevation"])  # J2 has no ground level
    assert by_line.loc[52, "depth"] == pytest.approx(1.30)  # no NPEN
    assert 48 not in by_line.index  # incomplete


def test_no_ispt_group(tmp_path):
    path = tmp_path / "no_spt.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA, make_files.GEOL])
    p = ht.Project.from_ags(path)
    with pytest.warns(UserWarning, match="No ISPT group in no_spt.ags"):
        df = p.spt()
    assert df.empty
    assert "spt_n60" in df.columns
