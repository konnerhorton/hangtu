"""p.density() and p.particle_density() (datasets.md §6.8, §6.9).

Acceptance criteria are those of docs/work/m14a-density-data.md (AC n).
"""

import warnings

import pandas as pd
import pytest

import hangtu as ht

from .conftest import make_files


def _quiet(call, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return call(*args, **kwargs)


# --- p.particle_density() ------------------------------------------------------------


def test_particle_density_measured_and_assumed(fresh):
    # AC 4: "2.68" is measured; "#2.65" is assumed, with its number kept.
    df = _quiet(fresh("site_si").particle_density)
    assert list(df["loca_id"]) == ["BH1", "BH2"]
    assert list(df["particle_density"]) == pytest.approx([2.68, 2.65])
    assert list(df["particle_density_assumed"]) == [False, True]
    assert list(df["test_type"]) == ["SMALL PYK", "SMALL PYK"]
    assert (df["depth"].iloc[0], df["depth_basis"].iloc[0]) == (
        pytest.approx(1.65),
        "spec_depth",
    )
    assert df.attrs["units"]["particle_density"] == "Mg/m3"


def test_particle_density_in_us_units(fresh):
    # 2.68 Mg/m3 / (0.45359237 kg / 0.3048^3 m3 / 1000) = 167.307 pcf.
    df = _quiet(fresh("site_us", display_units="US").particle_density)
    assert df.attrs["units"]["particle_density"] == "pcf"
    assert df["particle_density"].iloc[0] == pytest.approx(167.307, rel=1e-5)


def test_particle_density_twins_agree(fresh):
    # AC 9.
    si = _quiet(fresh("site_si").particle_density).drop(columns="source_line")
    us = _quiet(fresh("site_us").particle_density).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_particle_density_filters_on_the_flag(fresh):
    df = _quiet(fresh("site_si").particle_density, where={"loca_id": "BH2"})
    assert list(df["particle_density_assumed"]) == [True]


def test_no_lpdn_group(tmp_path):
    # AC 11.
    path = tmp_path / "none.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No LPDN group in none.ags"):
        df = ht.Project.from_ags(path).particle_density()
    assert df.empty and "particle_density_assumed" in df.columns
    assert str(df["particle_density_assumed"].dtype) == "boolean"


# --- p.density() ---------------------------------------------------------------------
# Golden values: gamma = rho * 9.80665 (standard gravity, exact). In US units,
# 1 pcf = 0.45359237 kg / 0.3048^3 m3 = 0.0160185 Mg/m3, and as a unit weight
# 0.157087 kN/m3; both give the same number of pcf (P00 §4.3 #1).


@pytest.fixture
def site(fresh):
    project = fresh("site_si")
    project.set_geology_map(make_files.HERE / "strata.csv")
    return project


def test_lab_row(site):
    # AC 1: rho 1.95, rho_d 1.56 Mg/m3, w 25 %: 1.95 * 9.80665 = 19.12297 and
    # 1.56 * 9.80665 = 15.29837 kN/m3.
    df = _quiet(site.density)
    lab = df.iloc[0]
    assert lab["bulk_unit_weight"] == pytest.approx(19.12297, rel=1e-6)
    assert lab["dry_unit_weight"] == pytest.approx(15.29837, rel=1e-6)
    assert lab["water_content"] == pytest.approx(25.0)
    assert (lab["source"], lab["test_type"]) == ("lab", "LINEAR")
    assert lab["sample_condition"] == "UNDISTURBED"
    assert (lab["depth"], lab["depth_basis"]) == (pytest.approx(1.60), "spec_depth")
    assert (lab["sample_reference"], lab["geology_unit"]) == ("BH1-U1", "Fill")
    assert df.attrs["units"]["bulk_unit_weight"] == "kN/m3"


def test_us_display(fresh):
    # AC 2: 19.12297 / 0.157087 = 121.735 and 15.29837 / 0.157087 = 97.388 pcf.
    df = _quiet(fresh("site_us", display_units="US").density)
    assert df.attrs["units"]["bulk_unit_weight"] == "pcf"
    lab = df.iloc[0]
    assert lab["bulk_unit_weight"] == pytest.approx(121.735, rel=1e-4)
    assert lab["dry_unit_weight"] == pytest.approx(97.388, rel=1e-4)


def test_field_row(site):
    # AC 3: BH1, ground level 12.40 m, at 0.50 m: elevation 11.90 m;
    # 1.85 * 9.80665 = 18.14230 kN/m3.
    df = _quiet(site.density)
    field = df[df["source"] == "field"].iloc[0]
    assert (field["loca_id"], field["depth"]) == ("BH1", pytest.approx(0.50))
    assert field["elevation"] == pytest.approx(11.90)
    assert field["depth_basis"] == "test_depth"
    assert field["bulk_unit_weight"] == pytest.approx(18.14230, rel=1e-6)
    assert pd.isna(field["dry_unit_weight"])
    assert field["water_content"] == pytest.approx(15.0)
    assert field["test_type"] == "SAND"
    for column in ("specimen_id", "sample_reference", "specimen_reference"):
        assert field[column] is None


def test_recompacted_and_stabilized_are_kept(site):
    # AC 6.
    df = _quiet(site.density)
    assert list(df["sample_condition"].fillna("-")) == [
        "UNDISTURBED",
        "RECOMPACTED",
        "-",
        "-",
    ]
    assert list(df["stabilizer_content"].fillna(-1)) == [-1, -1, -1, 3.0]
    in_situ = df[df["sample_condition"] != "RECOMPACTED"]
    assert len(in_situ) == 3  # a pandas filter keeps the field rows


def test_density_twins_agree(fresh):
    # AC 9.
    si = _quiet(fresh("site_si").density).drop(columns="source_line")
    us = _quiet(fresh("site_us").density).drop(columns="source_line")
    pd.testing.assert_frame_equal(si, us, rtol=1e-9)


def test_incomplete_record(fresh):
    # AC 10: J1-D2's LDEN row (line 103) has no LDEN_BDEN.
    project = fresh("joins")
    with pytest.warns(UserWarning) as record:
        df = project.density()
    messages = [str(w.message) for w in record]
    assert any(m.startswith("Left out 1 of 4 LDEN records") for m in messages)
    assert "LDEN_BDEN on line 103" in next(m for m in messages if "Left out" in m)
    assert "J1-D2" not in set(df["sample_reference"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kept = project.density(include_incomplete=True)
    row = kept[kept["sample_reference"] == "J1-D2"].iloc[0]
    assert pd.isna(row["bulk_unit_weight"])
    assert row["dry_unit_weight"] == pytest.approx(1.60 * 9.80665)


def test_no_density_groups(tmp_path):
    # AC 11.
    path = tmp_path / "none.ags"
    make_files.write_file(path, "4.2", [make_files.LOCA])
    with pytest.warns(UserWarning, match="No LDEN or IDEN group in none.ags"):
        df = ht.Project.from_ags(path).density()
    assert df.empty and "bulk_unit_weight" in df.columns


def test_feeds_the_plots(fresh):
    # AC 12: no warning, in pcf.
    project = fresh("site_us", display_units="US")
    project.set_geology_map(make_files.HERE / "strata.csv")
    df = _quiet(project.density)
    _, ax = _quiet(ht.plot.profile, df, "bulk_unit_weight")
    assert "pcf" in ax.get_xlabel()
    _, ax = _quiet(ht.plot.geology_unit_comparison, df, "bulk_unit_weight")
    assert "pcf" in ax.get_xlabel() + ax.get_ylabel()


def test_common_arguments(site):
    # AC 14.
    assert list(_quiet(site.density, depth=(0, 1))["depth"]) == pytest.approx(
        [0.50, 0.40]
    )
    assert list(_quiet(site.density, holes=["BH2"])["source"]) == ["lab", "field"]
    assert len(_quiet(site.density, geology=["Fill"])) == 2
    assert list(_quiet(site.density, where={"source": "field"})["loca_id"]) == [
        "BH1",
        "BH2",
    ]


# --- Particle density by sample (datasets.md §6.8) -----------------------------------


def _ids(project):
    """``{(sample_reference, SPEC_REF): specimen_id}`` of the LPDN specimens."""
    rho_s = _quiet(project.particle_density)
    return {
        (row.sample_reference, row.specimen_reference): row.specimen_id
        for row in rho_s.itertuples()
    }


def test_particle_density_joined_by_sample(fresh):
    # AC 5, joins.ags (tests/data/ags/_make_files.py, joins_groups()):
    # J1-U1's density specimen is at 1.20; LPDN 5 is at 1.10 (0.10 away) and
    # 6 at 1.25 (0.05 away, #2.65): 6 is used, and stays assumed.
    # J1-U3's is at 6.25; E at 6.30 and D at 6.20 are both 0.05 away, and E has
    # the lower specimen key: D (2.71) is used, by the lower SPEC_REF.
    # J2-U1 has no LPDN: blank.
    project = fresh("joins")
    with pytest.warns(UserWarning) as record:
        df = project.density()
    messages = [str(w.message) for w in record]
    assert (
        "2 samples had more than one particle density specimen; the one nearest "
        "in depth was used. particle_density_specimen_id says which."
    ) in messages
    ids = _ids(project)
    by_sample = df.set_index("sample_reference")
    j1_u1, j1_u3, j2_u1 = (by_sample.loc[s] for s in ("J1-U1", "J1-U3", "J2-U1"))
    assert j1_u1["particle_density"] == pytest.approx(2.65)
    assert str(j1_u1["particle_density_assumed"]) == "True"
    assert j1_u1["particle_density_specimen_id"] == ids["J1-U1", "6"]
    assert j1_u3["particle_density"] == pytest.approx(2.71)
    assert str(j1_u3["particle_density_assumed"]) == "False"
    assert j1_u3["particle_density_specimen_id"] == ids["J1-U3", "D"]
    assert pd.isna(j2_u1["particle_density"])
    assert pd.isna(j2_u1["particle_density_assumed"])
    assert j2_u1["particle_density_specimen_id"] is None


def test_the_warning_counts_only_returned_samples(fresh):
    project = fresh("joins")
    with pytest.warns(UserWarning) as record:
        project.density(depth=(6, 7))
    messages = [str(w.message) for w in record]
    assert any(m.startswith("1 sample had more than one") for m in messages)


def test_one_specimen_per_sample_and_field_rows(site):
    # The good files: one LPDN specimen per sample, so no warning (_quiet).
    df = _quiet(site.density)
    ids = _ids(site)
    assert list(df["particle_density"].iloc[:2]) == pytest.approx([2.68, 2.65])
    assert list(df["particle_density_assumed"].iloc[:2]) == [False, True]
    assert list(df["particle_density_specimen_id"].iloc[:2]) == [
        ids["BH1-U1", "2"],
        ids["BH2-U2", "2"],
    ]
    field = df[df["source"] == "field"]
    assert field["particle_density"].isna().all()
    assert field["particle_density_assumed"].isna().all()
    assert field["particle_density_specimen_id"].isna().all()
