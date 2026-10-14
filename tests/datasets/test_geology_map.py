"""The geology map (datasets.md §5.2)."""

import pandas as pd
import pytest

import hangtu as ht

from .conftest import DATA, STRATA


def _csv(tmp_path, text):
    path = tmp_path / "map.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_round_trip(fresh):
    p = fresh()
    assert p.geology_map is None
    p.set_geology_map(STRATA)
    stored = p.geology_map
    assert list(stored["code"]) == ["FILL", "ALV", "TRC"]
    assert list(stored["geology_unit"]) == ["Fill", "Alluvium", "Terrace"]
    assert list(stored["order"]) == [1.0, 2.0, 3.0]
    assert ht.Project.open(p.path).geology_map.equals(stored)


def test_a_dataframe_and_none(fresh):
    p = fresh()
    p.set_geology_map(pd.DataFrame({"code": ["ALV"], "geology_unit": ["Alluvium"]}))
    row = p.geology_map.iloc[0]
    assert (row["code"], row["geology_unit"]) == ("ALV", "Alluvium")
    assert row[["soil_class", "color"]].isna().all()
    p.set_geology_map(None)
    assert p.geology_map is None


def test_a_new_map_replaces_the_old_one(fresh):
    p = fresh()
    p.set_geology_map(STRATA)
    p.set_geology_map(pd.DataFrame({"code": ["X"], "geology_unit": ["Y"]}))
    assert list(p.geology_map["code"]) == ["X"]


def test_codes_are_kept_exactly(fresh, tmp_path):
    # Matched exactly and case-sensitively (SPEC §8.3): no trimming, no NaN.
    p = fresh()
    p.set_geology_map(_csv(tmp_path, "code,geology_unit\nNA,Not applied\nalv ,A\n"))
    assert list(p.geology_map["code"]) == ["NA", "alv "]


def test_rebuilding_the_database_drops_the_map(fresh):
    p = fresh()
    p.set_geology_map(STRATA)
    p = ht.Project.from_ags(DATA / "site_si.ags", db=p.path, overwrite=True)
    assert p.geology_map is None


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("code,unit\nALV,Alluvium\n", r"no geology_unit column .* doesn't read: unit"),
        ("code,geology_unit\nALV,\n", r"blank geology_unit on line 2\."),
        (
            "code,geology_unit\nALV,Alluvium\nALV,Terrace\n",
            r"lists a code more than once: 'ALV' on lines 2, 3",
        ),
        (
            "code,geology_unit,color\nA,Alluvium,tan\nB,Alluvium,red\n",
            r"two colors: 'Alluvium': 'tan', 'red'",
        ),
        (
            "code,geology_unit,soil_class\nA,Alluvium,fine\nB,Alluvium,coarse\n",
            r"two soil classes",
        ),
        ("code,geology_unit,order\nA,Alluvium,1\nB,Alluvium,2\n", r"two orders"),
        ("code,geology_unit,order\nA,Alluvium,first\n", r"order 'first' on line 2"),
        (
            "code,geology_unit,color\nA,Alluvium,not a color\n",
            r"'not a color' \(line 2\)",
        ),
    ],
)
def test_errors(fresh, tmp_path, text, message):
    p = fresh()
    with pytest.raises(ht.HangtuError, match=message):
        p.set_geology_map(_csv(tmp_path, text))
    assert p.geology_map is None  # nothing stored


def test_missing_file(fresh, tmp_path):
    with pytest.raises(ht.HangtuError, match=r"No geology map at .* for example"):
        fresh().set_geology_map(tmp_path / "nope.csv")


def test_dataframe_errors_name_the_row(fresh):
    frame = pd.DataFrame({"code": ["A", "A"], "geology_unit": ["X", "Y"]})
    with pytest.raises(ht.HangtuError, match="'A' on rows 1, 2"):
        fresh().set_geology_map(frame)
