"""The readings map (datasets.md §6.15): M16 acceptance criteria 1 and 2."""

import re
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

import hangtu as ht

from .conftest import DATA

MAP = DATA / "readings_map.csv"
MAPPED = pd.read_csv(MAP, dtype=str)


def _map(*changes, drop=()):
    """The good map with rows ``drop`` (0-based) removed and ``changes`` applied:
    each a (row, column, value), a row of None appending a new row."""
    table = MAPPED.drop(index=list(drop)).reset_index(drop=True)
    for row, column, value in changes:
        if row is None:
            table = pd.concat([table, pd.DataFrame([value])], ignore_index=True)
        else:
            table.loc[row, column] = value
    return table


@pytest.mark.parametrize("name", ["site_si", "site_us", "joins"])
def test_stored(fresh, name):
    # AC 1: thirteen rows, kept on open, removed by None.
    p = fresh(name)
    assert p.readings_map is None
    p.set_readings_map(MAP)
    stored = p.readings_map
    assert stored.equals(MAPPED)
    assert ht.Project.open(p.path).readings_map.equals(stored)
    p.set_readings_map(None)
    assert p.readings_map is None


def test_a_dataframe_replaces_the_map(fresh):
    p = fresh()
    p.set_readings_map(MAP)
    p.set_readings_map(MAPPED.iloc[9:])
    assert list(p.readings_map["group"]) == ["XSBS"] * 4


def test_rebuilding_the_database_drops_the_map(fresh):
    # AC 1: from_ags(..., overwrite=True) starts with none.
    p = fresh()
    p.set_readings_map(MAP)
    p = ht.Project.from_ags(DATA / "site_si.ags", db=p.path, overwrite=True)
    assert p.readings_map is None


def test_no_file(fresh, tmp_path):
    p = fresh()
    with pytest.raises(ht.HangtuError, match=r"(?s)No readings map at .*group,dataset"):
        p.set_readings_map(tmp_path / "nope.csv")


def test_a_csv_names_its_lines(fresh, tmp_path):
    # Line 1 is the header, so the map's fourth row is line 5.
    text = MAP.read_text(encoding="utf-8").replace("XTPW_TESN", "XTPW_TEST")
    path = tmp_path / "map.csv"
    path.write_text(text, encoding="utf-8")
    p = fresh()
    with pytest.raises(
        ht.HangtuError,
        match=r"The readings map map\.csv maps heading XTPW_TEST on line 5, which "
        r"group XTPW doesn't have\. Its headings are: LOCA_ID, .*XTPW_PWPE\.",
    ):
        p.set_readings_map(path)


ERRORS = [
    # Columns and cells.
    (
        MAPPED.drop(columns="dataset"),
        r"has no dataset column\. Its columns are group, dataset, heading, column",
    ),
    (
        MAPPED.assign(units="kPa"),
        r"has columns hangtu doesn't read: units",
    ),
    (MAPPED.iloc[:0], r"has no rows"),
    (_map((4, "heading", "")), r"has a blank heading on row 5\."),
    (
        _map((None, None, dict(MAPPED.iloc[1]))),
        r"maps a heading more than once: XTDS XTDS_STRN on rows 2, 14\.",
    ),
    (
        _map((2, "heading", "XTDS_DEVF"), (1, "heading", "XTDS_DEVF"), drop=[]),
        r"maps a heading more than once",
    ),
    (
        _map((None, None, {**dict(MAPPED.iloc[2]), "heading": "XTDS_POIN"})),
        r"maps a column more than once in one group: XTDS deviator_stress on "
        r"rows 3, 14\.",
    ),
    (
        _map((0, "dataset", "shear_box_readings")),
        r"gives group XTDS two datasets: shear_box_readings, triaxial_readings\.",
    ),
    # Names.
    (
        _map(*((r, "dataset", "triaxial") for r in range(3))),
        r"has dataset 'triaxial' on row 1\. The readings datasets are "
        r"triaxial_readings and shear_box_readings\.",
    ),
    (
        _map((2, "column", "shear_stress")),
        r"maps XTDS_DEVF to column 'shear_stress' on row 3, which triaxial_readings "
        r"doesn't read\. Its columns are test_stage, axial_strain, deviator_stress, "
        r"excess_pore_pressure, volumetric_strain\.",
    ),
    # The file.
    (
        _map(*((r, "group", "TRET") for r in range(3))),
        r"names TRET on row 1, a standard AGS group\. The readings map reads "
        r"user-defined groups only\.",
    ),
    (
        _map(*((r, "group", "XTQQ") for r in range(3))),
        r"names group XTQQ on row 1, which the file doesn't have\. Its user-defined "
        r"groups are: XPPT, XSBS, XTDS, XTPW, XTVS\.",
    ),
    (
        _map((5, "heading", "XTPW_PWPF")),
        r"maps heading XTPW_PWPF on row 6, which group XTPW doesn't have\.",
    ),
    (
        _map(drop=[1]),
        r"doesn't map axial_strain for group XTDS\. A triaxial_readings group needs "
        r"test_stage and axial_strain, and at least one of deviator_stress, "
        r"excess_pore_pressure, volumetric_strain\.",
    ),
    (
        _map(drop=[11, 12]),
        r"doesn't map shear_stress or vertical_displacement for group XSBS\.",
    ),
    (
        _map(*((r, "dataset", "triaxial_readings") for r in range(9, 13)))
        .drop(index=[12])
        .assign(
            column=lambda t: t["column"].replace(
                {
                    "horizontal_displacement": "axial_strain",
                    "shear_stress": "deviator_stress",
                }
            )
        ),
        r"sends group XSBS to triaxial_readings, but the file's DICT gives it the "
        r"parent SHBG\. A triaxial_readings group is a child of TREG, TRET, TRIG, "
        r"TRIT\. Check the dataset on rows 10, 11, 12\.",
    ),
    (
        pd.DataFrame(
            {
                "group": ["XPPT"] * 3,
                "dataset": ["shear_box_readings"] * 3,
                "heading": ["LOCA_ID", "XPPT_DPTH", "XPPT_RES"],
                "column": ["test_stage", "horizontal_displacement", "shear_stress"],
            }
        ),
        r"sends group XPPT to shear_box_readings, but the file's DICT gives it the "
        r"parent LOCA\. A shear_box_readings group is a child of SHBG, SHBT\.",
    ),
    # Units: kPa against percent.
    (
        _map((1, "heading", "XTDS_DEVF"), (2, "heading", "XTDS_STRN")),
        r"maps XTDS XTDS_DEVF \(unit 'kPa'\) to axial_strain on row 2, but "
        r"axial_strain is a percent and its unit isn't a percent\.",
    ),
    (
        _map((2, "heading", "XTDS_POIN")),
        r"maps XTDS XTDS_POIN \(no unit\) to deviator_stress on row 3, but "
        r"deviator_stress is a stress and it isn't a number in the file\.",
    ),
]


@pytest.mark.parametrize(("table", "message"), ERRORS)
def test_errors_store_nothing(fresh, table, message):
    # AC 2: each error names what it says; the stored map is unchanged.
    p = fresh()
    p.set_readings_map(MAP)
    with pytest.raises(ht.HangtuError, match=r"The readings map " + message):
        p.set_readings_map(table)
    assert p.readings_map.equals(MAPPED)


def test_a_group_with_no_dict_entry(fresh):
    # defects.ags' XUND has no DICT row (python-ags4 Rule 9).
    p = fresh("defects")
    headings = list(p.table("XUND").columns)
    table = pd.DataFrame(
        {
            "group": ["XUND"] * 3,
            "dataset": ["triaxial_readings"] * 3,
            "heading": headings[-3:],
            "column": ["test_stage", "axial_strain", "deviator_stress"],
        }
    )
    with pytest.raises(
        ht.HangtuError,
        match=r"names group XUND on row 1, which has no entry in the file's DICT "
        r"group.*DICT_PGRP one of TREG, TRET, TRIG, TRIT",
    ):
        p.set_readings_map(table)
    assert p.readings_map is None


@pytest.mark.parametrize(
    ("status", "unit", "message"),
    [
        ("file_unit", "kJ/m3", "hangtu doesn't know its unit, so it's kept as written"),
        ("raw_only", "furlong", "its unit couldn't be read or doesn't fit"),
    ],
)
def test_a_heading_ingest_did_not_convert(fresh, status, unit, message):
    # U005 and raw-only headings: the map never converts a number itself.
    p = fresh()
    with closing(sqlite3.connect(p.path)) as connection, connection:
        connection.execute(
            "UPDATE meta_heading SET status = ?, file_unit = ?, unit = NULL, "
            'quantity = NULL WHERE "group" = ? AND heading = ?',
            (status, unit, "XTDS", "XTDS_DEVF"),
        )
    with pytest.raises(
        ht.HangtuError,
        match=rf"maps XTDS XTDS_DEVF \(unit '{re.escape(unit)}'\) to "
        rf"deviator_stress on row 3, but deviator_stress is a stress and {message}",
    ):
        p.set_readings_map(MAPPED)
