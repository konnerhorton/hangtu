"""select(): a fit's value as fitted, and the selection placed (m18e-selection.md).

G2 and G3 are the spec's golden values, hand-calculated: G2 by Hyndman & Fan
definition 7 inverted, G3 from the line t = c′ cos φ′ + s′ sin φ′.
"""

import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import HangtuError

from .conftest import (
    COHESION,
    FIT,
    FITTED,
    G1,
    PHI,
    g3_fit,
    sources,
    triaxial,
)

# --- G2: the selected value's position (AC 3) --------------------------------------


def test_g2_the_selection_within_source_b():
    a, b = sources()
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": G1})
    positions = result.positions()
    assert len(positions) == 1  # the selected source isn't placed against itself
    row = positions.iloc[0]
    assert (row["selected_source"], row["parameter_source"]) == ("A", "B")
    assert row["position"] == "within"
    # 34.868 between x(0) = 33 and x(1) = 35: h = 1.868 / 2, rank = 100 h / 4.
    assert row["percentile_rank"] == pytest.approx(23.35, abs=0.01)
    assert (row["count"], row["minimum"], row["maximum"]) == (5, 33.0, 41.0)
    assert pd.isna(row["difference"])
    assert positions.attrs["units"]["selected_value"] == "deg"


def test_a_given_value_is_placed_against_every_source():
    a, b = sources()
    entry = {"method": "value", "value": "32 deg", "reason": "cautious"}
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": entry})
    positions = result.positions()
    assert positions["parameter_source"].tolist() == ["A", "B"]
    assert positions["position"].tolist() == ["below", "below"]
    assert positions["percentile_rank"].isna().all()


def test_no_value_and_none_have_no_positions():
    a, b = sources()
    result = ht.stats.select(
        a, b, value=PHI, selection={"Sand": {"method": "none", "reason": "x"}}
    )
    assert result.positions().empty


# --- G3: fitted, c′ and φ′ from one fit, and the difference (AC 4) -------------------


def test_g3_phi_and_cohesion_from_one_fit():
    fit = g3_fit()
    phi_selected = ht.stats.select(fit, value=PHI, selection={"Sand": FITTED})
    cohesion_selected = ht.stats.select(fit, value=COHESION, selection={"Sand": FITTED})
    phi_row = phi_selected.to_frame().iloc[0]
    cohesion_row = cohesion_selected.to_frame().iloc[0]
    assert phi_row["value"] == pytest.approx(30.000, abs=0.0005)
    assert cohesion_row["value"] == pytest.approx(5.000, abs=0.0005)
    assert (phi_row["parameter_source"], phi_row["selection_method"]) == (
        FIT,
        "fitted",
    )
    assert phi_row["count"] == 3  # the fit's points
    assert cohesion_selected.unit == "kPa"
    assert "Sand: Mohr-Coulomb fit (CD), fitted: 30 deg (three CD stages)." in (
        phi_selected.notes
    )
    with pytest.raises(HangtuError, match=r"selected by fitted, not by representative"):
        phi_selected.representative("Sand")


def test_g3_the_fits_difference_from_g1():
    a, b = sources()
    result = ht.stats.select(a, b, g3_fit(), value=PHI, selection={"Sand": G1})
    positions = result.positions().set_index("parameter_source")
    fit = positions.loc[FIT]
    assert fit["fit_value"] == pytest.approx(30.000, abs=0.0005)
    assert fit["difference"] == pytest.approx(4.868, abs=0.001)
    assert pd.isna(fit["position"])
    assert pd.isna(fit["minimum"])
    assert fit["source_kind"] == "fit"
    assert positions.loc["B", "position"] == "within"


def test_a_fitted_selection_is_placed_among_the_rows():
    a, b = sources()
    result = ht.stats.select(a, b, g3_fit(), value=PHI, selection={"Sand": FITTED})
    positions = result.positions()
    assert positions["parameter_source"].tolist() == ["A", "B"]
    assert positions["position"].tolist() == ["below", "below"]
    assert positions["selected_value"].iloc[0] == pytest.approx(30.0, abs=0.0005)


def test_a_view_on_one_fitted_value_is_an_error():
    with pytest.raises(
        HangtuError,
        match=r"selects characteristic from 'Mohr-Coulomb fit \(CD\)', which has one "
        r"fitted value.*Choose fitted",
    ):
        ht.stats.select(g3_fit(), value=PHI, selection={"Sand": {**G1, "source": FIT}})


# --- A fit per sample: its values to representative() -------------------------------


def per_sample():
    """Four samples, each three CD stages, φ′ 29-33°, at 3, 4, 5 and 6 m."""
    frames = []
    for i, angle in enumerate([29.0, 31.0, 30.0, 33.0]):
        frame = triaxial([100.0, 200.0, 300.0], angle=angle)
        frame["sample_reference"] = f"S{i + 1}"
        frame["depth"] = 3.0 + i
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    df.attrs["units"] = frames[0].attrs["units"]
    return ht.analysis.mohr_coulomb_fit(
        df, group_by=["geology_unit", "sample_reference"]
    )


def test_a_per_sample_fit_goes_to_representative_from_its_values():
    fit = per_sample()
    result = ht.stats.select(fit, value=PHI, selection={"Sand": {**G1, "source": FIT}})
    direct = ht.stats.representative(
        [29.0, 31.0, 30.0, 33.0],
        method="characteristic",
        estimate="mean",
        side="low",
        distribution="normal",
        units="deg",
    )
    row = result.to_frame().iloc[0]
    assert row["value"] == pytest.approx(direct.groups[0]["value"], rel=1e-6)
    assert row["count"] == 4
    assert result.representative("Sand").groups[0]["counts"]["count"] == 4


def test_fitted_on_a_per_sample_fit_is_an_error():
    with pytest.raises(
        HangtuError, match=r"which has 4 values in this unit.*Choose characteristic"
    ):
        ht.stats.select(per_sample(), value=PHI, selection={"Sand": FITTED})


# --- A line with depth: no position (AC 11, first half) -----------------------------


def test_a_selected_line_has_no_position():
    a, b = sources()
    entry = {**G1, "trend": "depth"}
    result = ht.stats.select(a, b, value=PHI, selection={"Sand": entry})
    positions = result.positions()
    assert positions["parameter_source"].tolist() == ["B"]
    assert pd.isna(positions["position"].iloc[0])
    assert positions["no_position_reason"].iloc[0] == "a line with depth"
    direct = ht.stats.representative(
        a,
        value=PHI,
        by="geology_unit",
        method="characteristic",
        estimate="mean",
        side="low",
        distribution="normal",
        trend="depth",
    ).to_frame()
    row = result.to_frame().iloc[0]
    assert pd.isna(row["value"])
    for name in (
        "line_intercept",
        "line_slope",
        "depth_top",
        "depth_base",
        "value_top",
        "value_base",
    ):
        assert row[name] == pytest.approx(direct[name].iloc[0], rel=1e-12), name
