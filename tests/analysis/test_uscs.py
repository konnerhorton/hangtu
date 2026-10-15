"""ht.analysis.uscs(): USCS group symbols (docs/drafts/analysis.md §2.6, §2.9)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError


def soils(**columns):
    columns.setdefault("fraction_system", "astm_uscs")
    return pd.DataFrame(columns)


def symbol(**columns):
    return ht.analysis.uscs(soils(**columns))["uscs_symbol"].tolist()


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        # Gravel 60, sand 35, fines 5 (CL), Cu 5, Cc 2.
        (dict(gravel_content=[60], sand_content=[35], fines_content=[5],
              uniformity_coefficient=[5], curvature_coefficient=[2],
              plasticity_class_uscs=["CL"]), "GW-GC"),
        (dict(gravel_content=[60], sand_content=[35], fines_content=[5],
              uniformity_coefficient=[3.9], curvature_coefficient=[2],
              plasticity_class_uscs=["CL"]), "GP-GC"),
        # Curve A: Cu 5.63 < 6, so a poorly graded sand.
        (dict(gravel_content=[0], sand_content=[96], fines_content=[4],
              uniformity_coefficient=[5.633], curvature_coefficient=[1.004]), "SP"),
        (dict(gravel_content=[0], sand_content=[96], fines_content=[4],
              uniformity_coefficient=[6.5], curvature_coefficient=[1.5]), "SW"),
        (dict(gravel_content=[0], sand_content=[96], fines_content=[4],
              uniformity_coefficient=[8], curvature_coefficient=[3.5]), "SP"),
        (dict(gravel_content=[0], sand_content=[80], fines_content=[20],
              plasticity_class_uscs=["ML"]), "SM"),
        (dict(gravel_content=[0], sand_content=[80], fines_content=[20],
              plasticity_class_uscs=["CL-ML"]), "SC-SM"),
        (dict(gravel_content=[70], sand_content=[10], fines_content=[20],
              plasticity_class_uscs=["CH"]), "GC"),
        (dict(gravel_content=[70], sand_content=[10], fines_content=[20],
              plasticity_class_uscs=["CL-ML"]), "GC-GM"),
        # Equal gravel and sand: not "more than half" of the coarse fraction.
        (dict(gravel_content=[45], sand_content=[45], fines_content=[10],
              uniformity_coefficient=[10], curvature_coefficient=[2],
              plasticity_class_uscs=["MH"]), "SW-SM"),
        # CL-ML fines count as C in a dual symbol.
        (dict(gravel_content=[0], sand_content=[88], fines_content=[12],
              uniformity_coefficient=[3], curvature_coefficient=[2],
              plasticity_class_uscs=["CL-ML"]), "SP-SC"),
        (dict(gravel_content=[10], sand_content=[40], fines_content=[50],
              plasticity_class_uscs=["CL"]), "CL"),
    ],
)  # fmt: skip
def test_symbol_golden_values(columns, expected):
    assert symbol(**columns) == [expected]


def test_cobbles_are_left_out_before_classifying():
    # Gravel 45, sand 37, fines 8, cobbles 10 % of the whole sample. Of the part
    # finer than 75 mm: 50.0, 41.1 and 8.9, so a gravel with a dual symbol.
    got = symbol(
        gravel_content=[45],
        sand_content=[37],
        fines_content=[8],
        cobbles_content=[10],
        boulders_content=[0],
        uniformity_coefficient=[20],
        curvature_coefficient=[1.5],
        plasticity_class_uscs=["ML"],
    )
    assert got == ["GW-GM"]


def test_rescaling_moves_fines_across_twelve_percent():
    # Fines 11.5 % of the whole, 12.8 % of the part finer than 75 mm: not dual.
    got = symbol(
        gravel_content=[40],
        sand_content=[38.5],
        fines_content=[11.5],
        cobbles_content=[10],
        plasticity_class_uscs=["ML"],
    )
    assert got == ["GM"]


def test_cu_and_cc_from_the_d_values():
    got = symbol(
        gravel_content=[0],
        sand_content=[96],
        fines_content=[4],
        d10=[0.1],
        d30=[0.3],
        d60=[0.9],
    )
    # Cu = 9, Cc = 0.09 / 0.09 = 1, on the limit (0.9999999999999999 in floats).
    assert got == ["SW"]


def test_class_from_the_limits_when_no_class_column():
    got = symbol(
        gravel_content=[10],
        sand_content=[30],
        fines_content=[60],
        liquid_limit=[45.0],
        plasticity_index=[25.0],
    )
    assert got == ["CL"]


def test_end_to_end_from_a_curve():
    df = pd.DataFrame(
        {
            "loca_id": "BH1",
            "specimen_id": "A",
            "particle_size": [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
            "percent_passing": [4, 12, 30, 55, 75, 90, 100],
        }
    )
    summary = ht.analysis.gradation(ht.set_units(df, {"particle_size": "mm"}))
    assert ht.analysis.uscs(summary)["uscs_symbol"].tolist() == ["SP"]


# --- Blanks ------------------------------------------------------------------------


def test_blanks_are_counted_by_reason():
    df = soils(
        gravel_content=[0, 0, 0, np.nan],
        sand_content=[92, 80, 10, np.nan],
        fines_content=[8, 20, 90, np.nan],
    )
    with pytest.warns(UserWarning, match="blank for 4 of 4") as record:
        out = ht.analysis.uscs(df)
    assert out["uscs_symbol"].isna().all()
    message = str(record[0].message)
    assert "1 with no Cu or Cc" in message
    assert "2 with no plasticity class" in message
    assert "1 with no fractions" in message


# --- fraction_system ----------------------------------------------------------------


def test_missing_fraction_system_asks_for_it():
    df = soils(gravel_content=[0], sand_content=[96], fines_content=[4])
    df = df.drop(columns="fraction_system")
    with pytest.raises(ColumnError, match=r'df\["fraction_system"\] = "astm_uscs"'):
        ht.analysis.uscs(df)


def test_wrong_fraction_system_is_an_error():
    df = soils(
        gravel_content=[0],
        sand_content=[96],
        fines_content=[4],
        fraction_system="aashto",
    )
    with pytest.raises(HangtuError, match="have fraction_system 'aashto'"):
        ht.analysis.uscs(df)


def test_missing_fractions_list_the_columns():
    with pytest.raises(ColumnError, match="'gravel_content' not found"):
        ht.analysis.uscs(soils(sand_content=[96], fines_content=[4]))


def test_rows_and_input_are_kept():
    df = soils(
        gravel_content=[0, 70],
        sand_content=[80, 10],
        fines_content=[20, 20],
        plasticity_class_uscs=["ML", "CH"],
    )
    df.index = [5, 2]
    before = df.copy()
    out = ht.analysis.uscs(df)
    assert out.index.tolist() == [5, 2]
    assert out["uscs_symbol"].tolist() == ["SM", "GC"]
    pd.testing.assert_frame_equal(df, before)
