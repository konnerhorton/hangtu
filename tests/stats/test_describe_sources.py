"""describe(): rows from different sources, and pool= (m15a, Decision 5)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

STROUD = "undrained_shear_strength_stroud_1974"
TERZAGHI = "undrained_shear_strength_terzaghi_peck_1967"


def _estimates(names=(STROUD, TERZAGHI), per=4):
    rows = len(names) * per
    df = pd.DataFrame(
        {
            "geology_unit": ["Alluvium"] * rows,
            "undrained_shear_strength": np.arange(10.0, 10.0 + rows),
            "correlation_name": [name for name in names for _ in range(per)],
        }
    )
    return ht.set_units(df, {"undrained_shear_strength": "kPa"})


def test_two_correlations_in_one_unit_raise():
    # AC 11
    with pytest.raises(HangtuError) as error:
        ht.stats.describe(
            _estimates(), value="undrained_shear_strength", by="geology_unit"
        )
    message = str(error.value)
    assert "different sources in group 'Alluvium'" in message
    assert f"'{STROUD}' (4 rows)" in message
    assert f"'{TERZAGHI}' (4 rows)" in message
    assert "by=['geology_unit', 'correlation_name']" in message
    assert "pool=['correlation_name']" in message


def test_group_by_the_source():
    frame = ht.stats.describe(
        _estimates(),
        value="undrained_shear_strength",
        by=["geology_unit", "correlation_name"],
    ).to_frame()
    assert frame["correlation_name"].tolist() == [STROUD, TERZAGHI]
    assert frame["count"].tolist() == [4, 4]


def test_pool_on_purpose():
    result = ht.stats.describe(
        _estimates(),
        value="undrained_shear_strength",
        by="geology_unit",
        pool=["correlation_name"],
    )
    assert len(result.to_frame()) == 1
    assert result.pooled == ("correlation_name",)
    assert result.groups[0]["sources"] == {"correlation_name": {STROUD: 4, TERZAGHI: 4}}
    assert (
        f"Pooled across correlation_name in Alluvium: {STROUD} 4, {TERZAGHI} 4."
        in result.notes
    )
    assert result.to_dict()["pooled"] == ["correlation_name"]


def test_measured_and_estimated_rows_mix():
    df = _estimates()
    df.loc[:3, "correlation_name"] = None
    with pytest.raises(HangtuError, match=r"'\(blank\)' \(4 rows\)"):
        ht.stats.describe(df, value="undrained_shear_strength")


def test_blank_estimates_beside_measured_values_dont_mix():
    df = _estimates()
    df.loc[4:, "undrained_shear_strength"] = np.nan
    df.loc[:3, "correlation_name"] = ""
    row = ht.stats.describe(df, value="undrained_shear_strength").to_frame().iloc[0]
    assert row["count"] == 4 and row["count_blank"] == 4


def test_lab_and_field_permeability_raise(fresh):
    permeability = fresh("site_si").permeability()
    with pytest.raises(HangtuError) as error:
        ht.stats.describe(permeability, value="hydraulic_conductivity")
    message = str(error.value)
    assert "source: 'lab' (2 rows),\n" in message
    assert "'field' (1 rows)" in message
    assert "test_type: '(blank)' (2 rows)" in message
    result = ht.stats.describe(
        permeability,
        value="hydraulic_conductivity",
        log=True,
        pool=["source", "test_type"],
    )
    assert "Pooled across source: lab 2, field 1." in result.notes


def test_two_spellings_of_a_test_type_are_both_listed():
    df = pd.DataFrame(
        {
            "undrained_shear_strength": [30, 35, 40, 45],
            "test_type": ["UU", "UU", "uu ", "Torvane"],
        }
    )
    with pytest.raises(HangtuError) as error:
        ht.stats.describe(df, value="undrained_shear_strength", units="kPa")
    message = str(error.value)
    assert "'UU' (2 rows)" in message
    assert "'uu' (1 rows)" in message
    assert "'Torvane' (1 rows)" in message


def test_a_source_in_by_isnt_checked():
    df = pd.DataFrame(
        {"water_content": [20, 25, 30, 35], "source": ["lab", "lab", "field", "field"]}
    )
    with pytest.warns(UserWarning, match="fewer than 3"):
        frame = ht.stats.describe(df, value="water_content", by="source").to_frame()
    assert frame["source"].tolist() == ["field", "lab"]


def test_pool_needs_a_source_column():
    with pytest.raises(HangtuError, match="'geology_unit' isn't one"):
        ht.stats.describe(
            _estimates(), value="undrained_shear_strength", pool="geology_unit"
        )


def test_pool_cant_also_be_by():
    with pytest.raises(HangtuError, match="also summarize or group by"):
        ht.stats.describe(
            _estimates(),
            value="undrained_shear_strength",
            by="correlation_name",
            pool="correlation_name",
        )


def test_pool_needs_the_column():
    with pytest.raises(ColumnError, match="no such column"):
        ht.stats.describe(
            _estimates(), value="undrained_shear_strength", pool="test_type"
        )


def test_pool_and_by_need_a_dataframe():
    with pytest.raises(HangtuError, match="only with a DataFrame"):
        ht.stats.describe([1, 2, 3], pool="source")
