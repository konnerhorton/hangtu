"""The example data and scripts (docs/work/m9-release.md, spec §1 and §3)."""

import importlib.util
import os
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from python_ags4 import AGS4

import hangtu as ht

ROOT = Path(__file__).parents[1]
# The installed package's copy, not src/, so the release workflow's wheel test
# (which deletes src/) checks the files the wheel ships.
DATA = Path(ht.examples.__file__).parent / "data"
FILES = [
    "atterberg.csv",
    "judgments.yaml",
    "oedometer.csv",
    "oedometer_readings.csv",
    "permeability.csv",
    "readings_map.csv",
    "rock_triaxial.csv",
    "shear_box.csv",
    "shear_box_readings.csv",
    "site.ags",
    "spt.csv",
    "strata.csv",
    "strength.csv",
    "triaxial.csv",
    "triaxial_readings.csv",
]
CSVS = [
    "atterberg.csv",
    "oedometer.csv",
    "oedometer_readings.csv",
    "permeability.csv",
    "rock_triaxial.csv",
    "shear_box.csv",
    "shear_box_readings.csv",
    "spt.csv",
    "strength.csv",
    "triaxial.csv",
    "triaxial_readings.csv",
]
NOT_FINDINGS = {"Metadata", "Summary of data"}
INTERPOLATED = r"interpolated in strain"
READING_UNITS = dict.fromkeys(
    [
        "effective_consolidation_stress",
        "back_pressure",
        "cell_pressure",
        "deviator_stress",
        "excess_pore_pressure",
    ],
    "psf",
)


def _load_generator():
    script = ROOT / "tests" / "data" / "_make_examples.py"
    spec = importlib.util.spec_from_file_location("_make_examples", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    db = tmp_path_factory.mktemp("example") / "site.sqlite"
    p = ht.Project.from_ags(
        DATA / "site.ags", db=db, display_units="US", vertical_datum="NAVD88"
    )
    p.set_geology_map(DATA / "strata.csv")
    return p


def test_site_passes_python_ags4(capsys):
    errors = AGS4.check_file(DATA / "site.ags")
    capsys.readouterr()  # python-ags4 prints progress notes
    assert {rule for rule in errors if rule not in NOT_FINDINGS} == set()


def test_qc_finds_only_the_planted_defects(site):
    findings = site.qc().findings
    assert not (findings["severity"] == "error").any()
    warnings = findings[findings["severity"] == "warning"]
    assert sorted(zip(warnings["rule_id"], warnings["loca_id"], strict=True)) == [
        ("A002", "B-3"),
        ("G002", "B-4"),
    ]


def test_generator_reproduces_the_shipped_files(tmp_path):
    _load_generator().main(tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == FILES
    for name in ("site.ags", "strata.csv", "judgments.yaml", "readings_map.csv"):
        assert (tmp_path / name).read_bytes() == (DATA / name).read_bytes(), name
    # The CSV files go through pandas' writer, so compare what they hold.
    for name in CSVS:
        made, shipped = pd.read_csv(tmp_path / name), pd.read_csv(DATA / name)
        pd.testing.assert_frame_equal(made, shipped, obj=name)


# --- ht.examples ------------------------------------------------------------------


def test_names_and_paths():
    assert ht.examples.names() == FILES
    for name in FILES:
        path = ht.examples.path(name)
        assert path.is_file()
        assert path.read_bytes() == (DATA / name).read_bytes()


def test_unknown_name_lists_the_files():
    with pytest.raises(ht.HangtuError) as caught:
        ht.examples.path("site.csv")
    assert str(caught.value) == (
        "No example file 'site.csv'. Files: atterberg.csv, judgments.yaml, "
        "oedometer.csv, oedometer_readings.csv, permeability.csv, readings_map.csv, "
        "rock_triaxial.csv, shear_box.csv, shear_box_readings.csv, site.ags, spt.csv, "
        "strata.csv, strength.csv, triaxial.csv, triaxial_readings.csv."
    )


@pytest.mark.parametrize(
    ("name", "value"), [("spt", "spt_n"), ("atterberg", "plasticity_index")]
)
def test_csv_and_ags_hold_the_same_tests(site, name, value):
    from_ags = getattr(site, name)()
    from_csv = ht.read_csv(ht.examples.path(f"{name}.csv"), units={"depth": "ft"})
    key = ["loca_id", "depth", value]
    pd.testing.assert_frame_equal(
        from_csv[key], from_ags[key].reset_index(drop=True), check_dtype=False
    )


@pytest.mark.parametrize(
    ("name", "dataset", "value"),
    [
        ("triaxial", "triaxial", "deviator_stress_at_failure"),
        ("shear_box", "shear_box", "peak_shear_stress"),
        # The CSV keeps only the s_u that is an input; the next test checks
        # the s_u worked out from it against the project's.
        ("strength", "undrained_strength", "deviator_stress_at_failure"),
        ("oedometer", "oedometer", "void_ratio_at_increment_end"),
    ],
)
def test_test_csvs_hold_the_projects_tests(site, name, dataset, value):
    # M18 (d), decision 20: the tests compared, written from site.ags.
    from_ags = getattr(site, dataset)()
    from_csv = ht.read_csv(
        ht.examples.path(f"{name}.csv"), dtype={"specimen_reference": str}
    )
    key = ["loca_id", "sample_reference", "specimen_reference", "depth", value]
    ags = from_ags[key].reset_index(drop=True)
    ags = ags.mask(ags.isna(), np.nan)  # a field test's blank sample is None
    # site.ags stores psf through a conversion; the CSV has 6 figures.
    pd.testing.assert_frame_equal(
        from_csv[key], ags, check_dtype=False, check_exact=False
    )
    # A lab specimen is named by its sample and reference; a field test has none.
    lab = from_csv["sample_reference"].notna()
    named = from_csv["sample_reference"] + "-" + from_csv["specimen_reference"]
    assert (from_csv.loc[lab, "specimen_id"] == named[lab]).all()
    assert from_csv.loc[~lab, "specimen_id"].isna().all()


# Each test CSV through the analysis its template feeds, with the units the
# file is in (it is written from site.ags, in US units; the rock in MPa).
# permeability.csv feeds plots only.
FEET = dict.fromkeys(
    ["depth", "ground_level", "elevation", "depth_top", "depth_base"], "ft"
)
DEGREES = dict.fromkeys(
    [
        "reported_effective_friction_angle",
        "reported_peak_friction_angle",
        "reported_residual_friction_angle",
    ],
    "deg",
)
TRIAXIAL_STRESSES = [
    "effective_consolidation_stress",
    "effective_vertical_consolidation_stress",
    "effective_radial_consolidation_stress",
    "back_pressure",
    "cell_pressure",
    "deviator_stress_at_failure",
    "pore_pressure_at_failure",
    "reported_effective_cohesion",
    "reported_intact_compressive_strength",
]
SHEAR_BOX_STRESSES = [
    "applied_normal_stress",
    "normal_stress_at_peak",
    "normal_stress_at_residual",
    "peak_shear_stress",
    "residual_shear_stress",
    "reported_peak_cohesion",
    "reported_residual_cohesion",
]
STRENGTH_STRESSES = [
    "undrained_shear_strength",
    "remolded_undrained_shear_strength",
    "reported_undrained_shear_strength",
    "cell_pressure",
    "deviator_stress_at_failure",
    "unconfined_compressive_strength",
    "hand_penetrometer_reading",
]
OEDOMETER_READING_UNITS = {
    "applied_vertical_stress": "psf",
    "specimen_height": "in",
    "reported_coefficient_of_consolidation_root_time": "ft2/yr",
    "reported_coefficient_of_consolidation_log_time": "ft2/yr",
    "elapsed_time": "min",
    "vertical_displacement": "in",
}
EXAMPLE_ANALYSES = {
    "atterberg.csv": ({}, ht.analysis.plasticity),
    "spt.csv": ({"spt_penetration": "in"}, ht.analysis.spt),
    "triaxial.csv": (
        dict.fromkeys(TRIAXIAL_STRESSES, "psf"),
        lambda df: ht.analysis.mohr_coulomb_fit(
            ht.analysis.triaxial_failure_stresses(df),
            group_by=["geology_unit", "test_type"],
        ),
    ),
    "rock_triaxial.csv": (
        dict.fromkeys(TRIAXIAL_STRESSES, "MPa"),
        lambda df: ht.analysis.hoek_brown_fit(
            ht.analysis.triaxial_failure_stresses(df), failure_modes=["Shear"]
        ),
    ),
    "triaxial_readings.csv": (
        READING_UNITS,
        ht.analysis.triaxial_failure_from_readings,
    ),
    "shear_box.csv": (
        dict.fromkeys(SHEAR_BOX_STRESSES, "psf"),
        lambda df: ht.analysis.shear_box_fit(
            df, group_by=["geology_unit", "test_type"]
        ),
    ),
    "strength.csv": (
        dict.fromkeys(STRENGTH_STRESSES, "psf"),
        ht.analysis.undrained_shear_strength_from_tests,
    ),
    "oedometer.csv": (
        {"applied_vertical_stress": "psf"},
        ht.analysis.oedometer_load_branch,
    ),
    "oedometer_readings.csv": (
        OEDOMETER_READING_UNITS,
        ht.analysis.consolidation_coefficient_from_readings,
    ),
}


def read_example(name, units):
    columns = pd.read_csv(DATA / name, nrows=0).columns
    declared = {c: u for c, u in {**FEET, **DEGREES, **units}.items() if c in columns}
    text = {"specimen_id": str, "specimen_reference": str, "test_stage": str}
    dtype = {c: t for c, t in text.items() if c in columns}
    return ht.read_csv(ht.examples.path(name), units=declared, dtype=dtype)


def test_every_test_csv_has_its_analysis():
    # The shear box readings feed no analysis yet.
    plots_only = {"permeability.csv", "shear_box_readings.csv"}
    assert set(EXAMPLE_ANALYSES) == set(CSVS) - plots_only


@pytest.mark.parametrize("name", sorted(EXAMPLE_ANALYSES))
def test_example_csv_passes_its_analysis(name):
    units, analysis = EXAMPLE_ANALYSES[name]
    df = read_example(name, units)
    if name == "atterberg.csv":
        # The PI planted for the QC example (A002) is warned about, not refused.
        with pytest.warns(UserWarning, match=r"Rows 7 have a plasticity_index"):
            result = analysis(df)
    elif name == "triaxial_readings.csv":
        # Δu and ε_v at failure come from their own readings (M16).
        with pytest.warns(UserWarning, match=INTERPOLATED):
            result = analysis(df)
    else:
        result = analysis(df)
    # A fit gives a result object; its table has a row per group fitted.
    table = result if isinstance(result, pd.DataFrame) else result.to_frame()
    assert len(table)


def test_strength_csv_gives_the_projects_undrained_strength(site):
    units, analysis = EXAMPLE_ANALYSES["strength.csv"]
    from_csv = analysis(read_example("strength.csv", units))
    from_ags = site.undrained_strength()
    for column in ["undrained_shear_strength", "undrained_shear_strength_basis"]:
        pd.testing.assert_series_equal(
            from_csv[column],
            from_ags[column].reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            obj=column,
        )


def test_the_sources_compared_are_in_the_example_site(site):
    # M18 (d), decision 20: Terrace φ′ from CD triaxial and shear box tests,
    # Alluvium s_u from four kinds of test.
    triaxial = site.triaxial(where={"test_type": "CD"})
    assert set(triaxial["geology_unit"]) == {"Terrace"}
    assert triaxial["loca_id"].nunique() == 4 and len(triaxial) == 12
    shear_box = site.shear_box(where={"geology_unit": "Terrace"})
    assert shear_box["sample_reference"].nunique() == 4
    strength = site.undrained_strength()
    assert set(strength["geology_unit"]) == {"Alluvium"}
    counts = strength.groupby(["source", "test_type"]).size().to_dict()
    assert counts == {
        ("field", "BOREHOLE"): 11,
        ("lab", "LV"): 6,
        ("lab", "UU"): 11,
        ("lab", "hand penetrometer"): 6,
    }


# --- The example scripts (spec §3, §4) ----------------------------------------------


@pytest.mark.parametrize(
    ("script", "outputs"),
    [
        ("csv_to_plot.py", ["csv_example.pdf"]),
        (
            "ags_qc_plot.py",
            ["site.sqlite", "qc_report.csv", "qc_report_rules.csv", "ags_example.pdf"],
        ),
    ],
)
def test_example_runs_clean(tmp_path, script, outputs):
    # Run as a user would: a fresh Python, default warning filters, any folder.
    env = {**os.environ, "MPLBACKEND": "Agg"}
    env.pop("PYTHONWARNINGS", None)
    done = subprocess.run(
        [sys.executable, str(ROOT / "examples" / script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert done.returncode == 0, done.stderr
    assert done.stderr == ""  # no warning, no traceback
    for name in outputs:
        assert (tmp_path / name).is_file(), name
    assert "Wrote" in done.stdout


# --- Triaxial readings (M11 c, spec AC 11; M16, AC 16) ----------------------------

AT_FAILURE = [
    "deviator_stress_at_failure",
    "pore_pressure_at_failure",
    "axial_strain_at_failure",
    "volumetric_strain_at_failure",
]


@pytest.mark.parametrize("criterion", ["max_deviator_stress", None])
def test_readings_end_at_the_example_stages(site, criterion):
    readings = ht.read_csv(
        ht.examples.path("triaxial_readings.csv"),
        units=READING_UNITS,
        dtype={"specimen_id": str, "test_stage": str, "specimen_reference": str},
    )
    if criterion is not None:
        # Picked by the criterion, not by the lab's mark the file carries.
        readings = readings.drop(columns="reported_failure_reading")
    # Each quantity has rows of its own, so Δu and ε_v at failure are another
    # row's: the same value, at the same strain.
    with pytest.warns(UserWarning, match=INTERPOLATED):
        rows = ht.analysis.triaxial_failure_from_readings(
            readings, failure_criterion=criterion
        )
    stages = site.triaxial()
    # The CSV names a specimen by its sample and reference.
    named = stages["sample_reference"] + "-" + stages["specimen_reference"]
    stages = stages.assign(specimen_id=named)
    for column in ["specimen_id", "test_stage", "multistage_test", *AT_FAILURE]:
        pd.testing.assert_series_equal(
            rows[column].reset_index(drop=True),
            stages[column].reset_index(drop=True),
            check_dtype=False,
            obj=column,
        )


def test_the_example_site_has_readings_for_every_stage(tmp_path):
    # M16 AC 16: through the example's readings map.
    p = ht.Project.from_ags(
        DATA / "site.ags", db=tmp_path / "site.sqlite", display_units="US"
    )
    p.set_readings_map(ht.examples.path("readings_map.csv"))
    for readings, stages in (
        (p.triaxial_readings(), p.triaxial()),
        (p.shear_box_readings(), p.shear_box()),
    ):
        key = ["specimen_id", "test_stage"]
        assert readings[key].drop_duplicates().values.tolist() == (
            stages[key].values.tolist()
        )


@pytest.mark.parametrize(
    "name", ["triaxial_readings", "shear_box_readings", "oedometer_readings"]
)
def test_readings_csvs_are_the_datasets_template_columns(name):
    from_csv = pd.read_csv(DATA / f"{name}.csv", nrows=0)
    assert list(from_csv.columns) == list(ht.template(name).columns)


# --- Oedometer (M19 a) ------------------------------------------------------------


def test_oedometer_tests_in_the_example_site(site):
    # AC 16: two incremental-load tests and a swelling pressure test.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        df = site.oedometer()
    specimens = df.drop_duplicates("specimen_id")
    assert specimens["sample_reference"].tolist() == ["B-1-U2", "B-4-U1", "B-5-U2"]
    assert specimens["test_type"].tolist() == ["SWELLPRESS", "OEDOMETER", "OEDOMETER"]
    assert set(df["geology_unit"]) == {"Alluvium"}
    tests = df[df["test_type"] == "OEDOMETER"]
    assert tests.groupby("specimen_id")["test_stage"].count().tolist() == [12, 12]
    for _, test in tests.groupby("specimen_id"):
        assert set(test["load_branch"]) == {"loading", "unloading", "reloading"}
    swelling = df.loc[df["test_type"] == "SWELLPRESS", "swelling_pressure"]
    assert swelling.tolist() == [pytest.approx(420, rel=1e-9)]  # psf, through kPa


def test_oedometer_csv_is_the_datasets_template_columns(site):
    # AC 16: oedometer.csv read back equals the dataset in its template columns.
    columns = list(ht.template("oedometer").columns)
    text = {"specimen_reference": str, "test_stage": str}
    from_csv = ht.read_csv(ht.examples.path("oedometer.csv"), dtype=text)
    assert list(from_csv.columns) == columns
    from_ags = site.oedometer()
    key = [
        "loca_id",
        "depth",
        "test_stage",
        "applied_vertical_stress",
        "void_ratio_at_increment_start",
        "void_ratio_at_increment_end",
        "reported_coefficient_of_volume_compressibility",
        "swelling_pressure",
    ]
    pd.testing.assert_frame_equal(
        from_csv[key],
        from_ags[key].mask(from_ags[key].isna(), np.nan),
        check_dtype=False,
        check_exact=False,
    )


# --- Settlement-time readings (M19 c2) ----------------------------------------------

#: The example's increment too fast for the standard's reading times.
FAST = ("B-5-U2-C1", "3")


def test_the_example_site_has_readings_for_every_loading_increment(tmp_path):
    p = ht.Project.from_ags(
        DATA / "site.ags", db=tmp_path / "site.sqlite", display_units="US"
    )
    p.set_readings_map(ht.examples.path("readings_map.csv"))
    readings = p.oedometer_readings()
    increments = p.oedometer()
    with_cv = increments[
        increments["reported_coefficient_of_consolidation_root_time"].notna()
    ]
    key = ["specimen_id", "test_stage"]
    assert readings[key].drop_duplicates().values.tolist() == (
        with_cv[key].values.tolist()
    )
    assert set(readings["load_branch"]) == {"loading"}
    assert readings.groupby(key).size().tolist() == [15] * 12


def test_oedometer_readings_csv_gives_cv_on_all_but_the_fast_increment():
    df = read_example("oedometer_readings.csv", OEDOMETER_READING_UNITS)
    rows = ht.analysis.consolidation_coefficient_from_readings(df)
    assert len(rows) == 12
    fast = (rows["specimen_id"] == FAST[0]) & (rows["test_stage"] == FAST[1])
    for method in ("root_time", "log_time"):
        cv = rows[f"coefficient_of_consolidation_{method}"]
        reason = rows[f"coefficient_of_consolidation_{method}_reason"]
        assert cv[~fast].notna().all(), method
        assert reason[~fast].isna().all(), method
        assert cv[fast].isna().all(), method
    reasons = rows.loc[fast].iloc[0]
    assert reasons["coefficient_of_consolidation_log_time_reason"] == (
        "fewer than 3 pairs of times in the ratio 1:4 before the inflexion"
    )
    assert reasons["coefficient_of_consolidation_root_time_reason"] == (
        "fewer than 3 readings in the first half of the increment's movement"
    )
    # Near the lab's root time c_v (it generated them), not equal to it: the
    # readings scatter. Both in ft²/yr.
    rows = ht.analysis.consolidation_coefficient_from_readings(df, display_units="US")
    ratio = (
        rows["coefficient_of_consolidation_root_time"]
        / rows["reported_coefficient_of_consolidation_root_time"]
    )[~fast]
    assert ratio.between(0.5, 2.5).all()
    assert not np.allclose(ratio, ratio.iloc[0], rtol=0.05)
