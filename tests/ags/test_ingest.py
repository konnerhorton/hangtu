"""The ingest pipeline in memory (docs/data/ingest.md §3)."""

from pathlib import Path

import pytest

from hangtu import ags

DATA = Path(__file__).parents[1] / "data" / "ags"


@pytest.fixture(scope="module")
def site():
    return ags.ingest(DATA / "site_si.ags")


def test_canonical_columns_are_keys_then_headings(site):
    assert list(site.canonical["SAMP"])[:3] == ["location_id", "sample_id", "LOCA_ID"]
    assert list(site.canonical["LOCA"])[:2] == ["location_id", "LOCA_ID"]
    assert list(site.canonical["PROJ"]) == ["PROJ_ID", "PROJ_NAME"]


def test_canonical_values_are_typed(site):
    loca = site.canonical["LOCA"]
    assert loca["LOCA_GL"] == [12.40, 11.85, 13.10]
    assert loca["LOCA_STAR"][0] == "2026-09-01"
    assert loca["LOCA_LAT"][0] == pytest.approx(37.793361, rel=1e-7)
    assert loca["LOCA_LAT"][2] is None
    assert site.canonical["GRAG"]["GRAG_SUFF"] == [1, 0]
    assert site.canonical["LNMC"]["LNMC_MC"] == [32.0, 41.0, 12.0]
    assert site.canonical["FGHS"]["FGHS_STTM"][0] == "2026-09-03T10:15:00"


def test_sql_types(site):
    types = site.sql_types["LOCA"]
    assert (types["location_id"], types["LOCA_ID"], types["LOCA_GL"]) == (
        "INTEGER",
        "TEXT",
        "REAL",
    )
    assert site.sql_types["GRAG"]["GRAG_SUFF"] == "INTEGER"
    assert site.sql_types["LOCA"]["LOCA_STAR"] == "TEXT"


def test_flags_carry_their_group(site):
    assert ("ISPT", "ISPT_NVAL", 2, "REFUSAL") in [
        (group, f.heading, f.row, f.flag) for group, f in site.flags
    ]


def test_specimen_depth_is_in_canonical_units():
    si = ags.ingest(DATA / "site_si.ags").specimens
    us = ags.ingest(DATA / "site_us.ags").specimens
    assert si[0]["SPEC_DPTH"] == 1.60
    assert [s["SPEC_DPTH"] for s in us] == pytest.approx(
        [s["SPEC_DPTH"] for s in si], rel=1e-9
    )


def test_findings_from_every_step():
    found = ags.ingest(DATA / "defects.ags").findings
    assert {f.rule for f in found} >= {
        "V000",
        "V9",
        "V10c",
        "U001",
        "U002",
        "U003",
        "U004",
        "T001",
    }
    assert {f.rule for f in ags.ingest(DATA / "site_v404.ags").findings} == {"M001"}
    assert ags.ingest(DATA / "site_si.ags").findings == []
