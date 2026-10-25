"""ht.analysis.add_judgment() (docs/work/m13b2-spt-strength-history.md, AC 7)."""

import hashlib

import numpy as np
import pandas as pd
import pytest

import hangtu as ht

NAN = np.nan
FILE = """\
plasticity_index:
  by: geology_unit
  units: {plasticity_index: "%"}
  values:
    Alluvium: {plasticity_index: 28, reason: "median of 9 tests"}
    Lacustrine: {plasticity_index: 40}
"""


def write(tmp_path, text=FILE):
    path = tmp_path / "judgments.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def rows(**columns):
    data = {"geology_unit": ["Alluvium", "Lacustrine", "Alluvium"], **columns}
    return pd.DataFrame(data)


def test_the_file_gives_each_row_its_units_value(tmp_path):
    path = write(tmp_path)
    out = ht.analysis.add_judgment(rows(), "plasticity_index", judgments=path)
    assert out["plasticity_index"].tolist() == [28.0, 40.0, 28.0]
    record = out.attrs["judgments"]["plasticity_index"]
    assert record["source"] == str(path)
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["by"] == "geology_unit"
    assert record["values"] == {
        "Alluvium": {"plasticity_index": "28 %", "reason": "median of 9 tests"},
        "Lacustrine": {"plasticity_index": "40 %"},
    }


def test_value_wins_over_the_file_and_a_column(tmp_path):
    df = rows(plasticity_index=[10.0, NAN, NAN])
    with pytest.warns(UserWarning) as caught:
        out = ht.analysis.add_judgment(
            df,
            "plasticity_index",
            value={"Alluvium": 20, "Lacustrine": 35},
            judgments=write(tmp_path),
        )
    assert [str(w.message) for w in caught] == [
        "value= replaces the plasticity_index in judgments.yaml.",
        "value= replaces the plasticity_index on 1 rows that already had one in "
        "the 'plasticity_index' column.",
    ]
    assert out["plasticity_index"].tolist() == [20.0, 35.0, 20.0]
    assert out.attrs["judgments"]["plasticity_index"]["source"] == "argument"


def test_one_value_for_every_row():
    out = ht.analysis.add_judgment(rows(), "plasticity_index", value=25)
    assert out["plasticity_index"].tolist() == [25.0] * 3
    assert out.attrs["judgments"]["plasticity_index"]["values"] == {
        "all": {"plasticity_index": "25"}
    }


def test_a_column_keeps_its_filled_rows_and_the_file_fills_its_blanks(tmp_path):
    df = rows(plasticity_index=[30.0, NAN, 28.0])
    with pytest.warns(UserWarning) as caught:
        out = ht.analysis.add_judgment(
            df, "plasticity_index", judgments=write(tmp_path)
        )
    assert [str(w.message) for w in caught] == [
        "The 'plasticity_index' column differs from judgments.yaml on 1 of its 2 "
        "filled rows; the column is used there. Clear those cells to use the file."
    ]
    assert out["plasticity_index"].tolist() == [30.0, 40.0, 28.0]
    record = out.attrs["judgments"]["plasticity_index"]
    assert record["from_column"] == 2
    assert record["values"] == {"Lacustrine": {"plasticity_index": "40 %"}}


def test_a_full_column_needs_no_file():
    df = rows(plasticity_index=[30.0, 41.0, 28.0])
    out = ht.analysis.add_judgment(df, "plasticity_index")
    assert out["plasticity_index"].tolist() == [30.0, 41.0, 28.0]
    assert out.attrs["judgments"]["plasticity_index"] == {
        "source": "the 'plasticity_index' column on the rows"
    }


def test_a_full_column_is_compared_with_the_file_without_a_lookup_error(tmp_path):
    df = rows(plasticity_index=[30.0, 41.0, 28.0], geology_unit=["Fill"] * 3)
    out = ht.analysis.add_judgment(df, "plasticity_index", judgments=write(tmp_path))
    assert out["plasticity_index"].tolist() == [30.0, 41.0, 28.0]


def test_a_missing_judgment_raises_naming_it():
    with pytest.raises(ht.HangtuError, match=r"need a plasticity_index.*SPEC §4"):
        ht.analysis.add_judgment(rows(), "plasticity_index")


def test_a_file_without_it_raises_naming_the_file(tmp_path):
    path = write(
        tmp_path,
        "water_level:\n  units: {depth: m}\n  project: {depth: 3, reason: x}\n",
    )
    with pytest.raises(
        ht.HangtuError, match=r"judgments.yaml' has no plasticity_index"
    ):
        ht.analysis.add_judgment(rows(), "plasticity_index", judgments=path)


def test_a_unit_the_file_does_not_list_raises(tmp_path):
    df = rows(geology_unit=["Alluvium", "Fill", "Fill"])
    with pytest.raises(ht.HangtuError, match=r"no value for the geology unit 'Fill'"):
        ht.analysis.add_judgment(df, "plasticity_index", judgments=write(tmp_path))


def test_the_project_value_fills_an_unlisted_unit_with_a_warning(tmp_path):
    text = FILE.replace(
        "  values:", '  project: {plasticity_index: 25, reason: "all tests"}\n  values:'
    )
    df = rows(geology_unit=["Alluvium", "Fill", "Lacustrine"])
    with pytest.warns(
        UserWarning, match=r"project value 25 % is used for the geology unit 'Fill'"
    ):
        out = ht.analysis.add_judgment(
            df, "plasticity_index", judgments=write(tmp_path, text)
        )
    assert out["plasticity_index"].tolist() == [28.0, 25.0, 40.0]


def test_a_value_key_missing_for_a_row_raises():
    with pytest.raises(
        ht.HangtuError, match=r"^value= has no value for the geology unit 'Lacustrine'"
    ):
        ht.analysis.add_judgment(rows(), "plasticity_index", value={"Alluvium": 20})


def test_a_blank_key_raises_naming_the_rows(tmp_path):
    df = rows(geology_unit=["Alluvium", None, "Alluvium"])
    with pytest.raises(ht.ColumnError, match=r"Rows 1 have a blank 'geology_unit'"):
        ht.analysis.add_judgment(df, "plasticity_index", judgments=write(tmp_path))


@pytest.mark.parametrize("bad", [-1, "28", True, float("nan")])
def test_a_value_must_be_a_number_of_zero_or_more(bad):
    with pytest.raises(ht.HangtuError, match=r"must be a number of 0 or more"):
        ht.analysis.add_judgment(rows(), "plasticity_index", value=bad)


def test_the_file_rejects_a_negative_pi(tmp_path):
    with pytest.raises(ht.HangtuError, match=r"must be a number of 0 or more"):
        ht.judgments(write(tmp_path, FILE.replace("28", "-28")))


def test_other_judgments_are_not_taken():
    with pytest.raises(
        ht.HangtuError, match=r"takes 'plasticity_index', not 'unit_weight'"
    ):
        ht.analysis.add_judgment(rows(), "unit_weight", value=19)


def test_the_input_is_unchanged(tmp_path):
    df = rows(plasticity_index=[30.0, NAN, 28.0])
    before = df.copy()
    with pytest.warns(UserWarning):
        ht.analysis.add_judgment(df, "plasticity_index", judgments=write(tmp_path))
    pd.testing.assert_frame_equal(df, before)
