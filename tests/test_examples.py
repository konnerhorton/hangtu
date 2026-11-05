"""The example data and scripts (docs/work/m9-release.md, spec §1 and §3)."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

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
    "permeability.csv",
    "rock_triaxial.csv",
    "site.ags",
    "spt.csv",
    "strata.csv",
    "triaxial_readings.csv",
]
CSVS = [
    "atterberg.csv",
    "permeability.csv",
    "rock_triaxial.csv",
    "spt.csv",
    "triaxial_readings.csv",
]
NOT_FINDINGS = {"Metadata", "Summary of data"}


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
    for name in ("site.ags", "strata.csv", "judgments.yaml"):
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
        "permeability.csv, rock_triaxial.csv, site.ags, spt.csv, strata.csv, "
        "triaxial_readings.csv."
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


# --- Triaxial readings (M11 c, spec AC 11) -----------------------------------------

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
    rows = ht.analysis.triaxial_failure_from_readings(
        readings, failure_criterion=criterion
    )
    # The readings are the CU and CDM tests'; the UU stages (M17 a) have none.
    stages = site.triaxial(where={"test_type": ["CU", "CDM"]})
    for column in ["specimen_id", "test_stage", "multistage_test", *AT_FAILURE]:
        pd.testing.assert_series_equal(
            rows[column].reset_index(drop=True),
            stages[column].reset_index(drop=True),
            check_dtype=False,
            obj=column,
        )
