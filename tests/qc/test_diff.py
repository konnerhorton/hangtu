import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError
from hangtu.qc._diff import COLUMNS

from .conftest import DATA, group, make_files


def _changes(project, group, heading=None):
    return set(project.diff(group, heading=heading)["change"])


def test_columns(projects):
    assert list(projects["site_si"].diff("ISPT").columns) == COLUMNS


def test_one_row_per_cell_in_file_order(projects):
    p = projects["site_si"]
    df = p.diff("ISPT")
    raw = p.table("ISPT", raw=True)
    assert len(df) == len(raw) * (len(raw.columns) - 1)
    assert list(df["_line"]) == sorted(df["_line"])
    assert list(df["heading"].iloc[: len(raw.columns) - 1]) == list(raw.columns[1:])


def test_converted_on_the_us_file(projects):
    df = projects["site_us"].diff("ISPT", heading="ISPT_TOP")
    first = df.iloc[0]
    assert first["change"] == "converted"
    assert first["text"] == "9.842519685"
    assert first["file_unit"] == "ft"
    assert first["value"] == pytest.approx(3.0)
    assert first["unit"] == "m"
    assert first["display_value"] == pytest.approx(3.0 / 0.3048)
    assert first["display_unit"] == "ft"


def test_pcf_density_converted(projects):
    df = projects["site_us"].diff("PTST", heading="PTST_BDEN")
    assert set(df["change"]) == {"converted"}
    assert df["value"].iloc[0] == pytest.approx(1.85)
    assert df["file_unit"].iloc[0] == "pcf"


def test_same_unit_is_unchanged(projects):
    df = projects["site_si"].diff("ISPT", heading=["ISPT_TOP", "ISPT_ERAT"])
    assert set(df["change"]) == {"unchanged", "blank"}  # one ERAT is blank
    assert set(df.query("text != ''")["change"]) == {"unchanged"}


def test_flagged(projects):
    df = projects["site_si"].diff("LLPL", heading="LLPL_PL")
    np_row = df.query("text == 'NP'").iloc[0]
    assert np_row["change"] == "flagged"
    assert np_row["flag"] == "NP"
    lt = projects["site_si"].diff("FGHG", heading="FGHG_ILUG").iloc[0]
    assert (lt["change"], lt["flag"], lt["bound"]) == ("flagged", "LT", 1.0)


def test_reformatted(projects):
    assert "reformatted" in _changes(projects["site_si"], "LOCA", "LOCA_LAT")  # DMS
    assert _changes(projects["site_si"], "GRAG", "GRAG_SUFF") == {"reformatted"}  # YN
    assert _changes(projects["site_v404"], "IPRT", "IPRT_TIME") == {"reformatted"}  # T
    # Dates already in ISO 8601 are unchanged.
    assert _changes(projects["site_si"], "LOCA", "LOCA_STAR") == {"unchanged"}


def test_date_rewritten_to_iso_is_reformatted(build, monkeypatch):
    monkeypatch.setitem(make_files.UNIT_DESCRIPTIONS, "dd/mm/yyyy", "day month year")
    loca = group(
        "LOCA",
        [("LOCA_ID", "ID", ""), ("LOCA_STAR", "DT", "dd/mm/yyyy")],
        [["BH1", "01/09/2026"]],
    )
    row = build(loca).diff("LOCA", heading="LOCA_STAR").iloc[0]
    assert (row["text"], row["value"], row["change"]) == (
        "01/09/2026",
        "2026-09-01",
        "reformatted",
    )


def test_not_converted(projects):
    df = projects["defects"].diff("LOCA", heading="LOCA_FDEP")
    assert set(df["change"]) == {"not_converted"}
    assert df["value"].isna().all()


def test_blank(projects):
    row = projects["site_si"].diff("ISPT", heading="ISPT_ERAT").iloc[-1]
    assert (row["text"], row["change"]) == ("", "blank")


def test_changed_only(projects):
    df = projects["site_us"].diff("ISPT", changed_only=True)
    assert set(df["change"]) <= {"flagged", "not_converted", "converted", "reformatted"}
    assert "ISPT_NVAL" in set(df["heading"])  # the refusal is flagged
    assert "ISPT_REP" not in set(df["heading"])  # text is unchanged


def test_key_headings_only_if_named(projects):
    df = projects["site_si"].diff("ISPT", heading=["ISPT_NVAL"])
    assert set(df["heading"]) == {"ISPT_NVAL"}
    assert df["loca_id"].iloc[0] == "BH1"


def test_unknown_group_lists_groups(projects):
    with pytest.raises(HangtuError, match=r"no group 'XXXX'\. Groups: PROJ, TRAN"):
        projects["site_si"].diff("XXXX")


def test_unknown_heading_lists_headings(projects):
    with pytest.raises(
        HangtuError, match=r"ISPT has no heading 'ISPT_X'\. Headings: LOCA_ID, ISPT_TOP"
    ):
        projects["site_si"].diff("ISPT", heading=["ISPT_TOP", "ISPT_X"])


def test_display_follows_project_settings(tmp_path):
    project = ht.Project.from_ags(
        DATA / "site_us.ags", db=tmp_path / "si.sqlite", display_units="SI"
    )
    ht.settings.display_units = "US"  # the session's choice doesn't apply
    row = project.diff("ISPT", heading="ISPT_TOP").iloc[0]
    assert row["display_value"] == pytest.approx(3.0)
    assert row["display_unit"] == "m"
    k = project.diff("PTST", heading="PTST_K").iloc[0]
    assert k["display_unit"] == "m/s"
    assert pd.notna(k["display_value"])
