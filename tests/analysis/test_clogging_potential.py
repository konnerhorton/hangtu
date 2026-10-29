"""Clay clogging potential (docs/work/m12-clogging-diagram.md, Spec)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config
from hangtu.errors import ColumnError, HangtuError

NAN = np.nan
# The golden table (Spec, "Golden values"): w, LL, PL, Ic, zone.
GOLDEN = [
    (30, 60, 25, 30 / 35, "high"),
    (8, 50, 20, 42 / 30, "medium-high"),
    (20, 35, 20, 15 / 15, "medium"),
    (32, 60, 20, 28 / 40, "medium"),
    (20, 40, 20, 20 / 20, "high"),  # on PI = 20
    (8, 60, 20, 52 / 40, "high"),  # on Ic = 1.3
    (30, 60, 20, 30 / 40, "high"),  # on Ic = 0.75
    (36, 60, 20, 24 / 40, "medium"),  # on Ic = 0.6, medium against low
    (20, 28, 20, 8 / 8, "low"),
    (8, 40, 20, 32 / 20, None),  # Ic > 1.5
    (50, 40, 20, -10 / 20, None),  # Ic < 0.3
    (25, 100, 25, 75 / 75, None),  # PI > 70
    (30, 30, 30, NAN, None),  # PI = 0
    (25, NAN, NAN, NAN, None),  # NP
    (31, 40, 20, 9 / 20, "low"),
    (34, 40, 20, 6 / 20, "low"),  # on the bottom axis
]


def golden_frame():
    frame = pd.DataFrame(
        GOLDEN, columns=["water_content", "liquid_limit", "plastic_limit", "ic", "z"]
    )
    frame["non_plastic"] = [False] * 13 + [True] + [False] * 2
    frame["specimen_id"] = [f"S{i}" for i in range(1, 17)]
    return frame.drop(columns=["ic", "z"])


def run(frame, **kwargs):
    with pytest.warns(UserWarning, match="clogging_potential is blank"):
        return ht.analysis.clogging_potential(frame, **kwargs)


def test_golden_values():
    # Criteria 1 and 4: Ic as plasticity() gives it, and the zone of each row,
    # with boundaries going to the higher zone.
    result = run(golden_frame())
    expected = pd.DataFrame(GOLDEN, columns=["w", "ll", "pl", "ic", "zone"])
    np.testing.assert_allclose(
        result["consistency_index"], expected["ic"], rtol=0, atol=1e-9
    )
    assert result["clogging_potential"].tolist() == expected["zone"].tolist()


def test_rows_order_and_input_unchanged():
    frame = golden_frame()
    before = frame.copy()
    result = run(frame)
    pd.testing.assert_frame_equal(frame, before)
    assert result["specimen_id"].tolist() == frame["specimen_id"].tolist()
    pd.testing.assert_index_equal(result.index, frame.index)
    expected = ht.analysis.plasticity(frame)
    np.testing.assert_allclose(
        result["plasticity_index"], expected["plasticity_index"], equal_nan=True
    )


def test_warning_counts_blank_rows_by_reason():
    with pytest.warns(UserWarning) as caught:
        ht.analysis.clogging_potential(golden_frame())
    (message,) = [str(w.message) for w in caught]
    assert "1 non-plastic; 1 a plasticity index of 0; 3 outside the diagram" in message


def test_no_warning_when_every_row_is_placed():
    result = ht.analysis.clogging_potential(golden_frame().iloc[:9])
    assert result["clogging_potential"].notna().all()


def test_no_water_content_column_is_an_error():
    frame = golden_frame().drop(columns="water_content")
    with pytest.raises(ColumnError, match=r"no 'water_content'.*p\.atterberg\(\)"):
        ht.analysis.clogging_potential(frame)


def test_blank_water_content_is_counted():
    frame = golden_frame().iloc[:2].copy()
    frame.loc[0, "water_content"] = NAN
    with pytest.warns(UserWarning, match="1 no water content"):
        result = ht.analysis.clogging_potential(frame)
    assert result["clogging_potential"].tolist() == [None, "medium-high"]


def test_a_given_consistency_index_is_kept():
    frame = golden_frame().iloc[:1].drop(columns="water_content")
    frame["consistency_index"] = 1.4
    result = ht.analysis.clogging_potential(frame)
    assert result["clogging_potential"].tolist() == ["medium-high"]


# --- zones= (criterion 9) ------------------------------------------------------

SQUARE = pd.DataFrame(
    {
        "label": ["sticky"] * 4,
        "plasticity_index": [0.0, 100.0, 100.0, 0.0],
        "consistency_index": [-1.0, -1.0, 2.0, 2.0],
    }
)


def test_user_zones_replace_the_method(tmp_path):
    path = tmp_path / "zones.csv"
    SQUARE.to_csv(path, index=False)
    frame = golden_frame()
    for zones in (SQUARE, path, str(path)):
        result = run(frame, zones=zones)
        # No box with user zones: rows 10-12 are in the square too.
        assert set(result["clogging_potential"].dropna()) == {"sticky"}
        assert result["clogging_potential"].notna().sum() == 14


def test_user_zone_with_two_vertices_is_an_error():
    with pytest.raises(HangtuError, match="Zone 'sticky' has 2 vertices"):
        ht.analysis.clogging_potential(golden_frame(), zones=SQUARE.iloc[:2])


def test_unknown_method_is_an_error():
    with pytest.raises(HangtuError, match="no clogging method named 'thewes'"):
        ht.analysis.clogging_potential(golden_frame(), method="thewes")


def test_template_columns():
    assert list(ht.template("clogging_zones").columns) == [
        "label",
        "plasticity_index",
        "consistency_index",
    ]


# --- the config against spec §4 (criterion 2) --------------------------------


def test_config_matches_the_spec_table():
    config = _config.load("config/clogging_methods.yaml")["thewes_burger_2004"]
    assert config["axes"] == {
        "plasticity_index": [0, 70],
        "consistency_index": [0.3, 1.5],
    }
    zones = {zone["name"]: zone["vertices"] for zone in config["zones"]}
    assert list(zones) == ["low", "medium", "medium-high", "high"]
    assert zones == {
        "low": [[0, 0.3], [70, 0.3], [70, 0.6], [10, 0.6], [10, 1.5], [0, 1.5]],
        "medium": [
            [10, 0.6],
            [70, 0.6],
            [70, 0.75],
            [20, 0.75],
            [20, 1.5],
            [10, 1.5],
        ],
        "medium-high": [[20, 1.3], [70, 1.3], [70, 1.5], [20, 1.5]],
        "high": [[20, 0.75], [70, 0.75], [70, 1.3], [20, 1.3]],
    }
