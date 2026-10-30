"""Correlation statistics on the rows (docs/work/m15b-correlation-statistics.md)."""

import copy

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config
from hangtu.analysis import correlations
from hangtu.analysis.correlations import _framework

ENTRIES = _config.load("config/correlations.yaml")
SCATTER_KEYS = {"words", "data_count", "r_squared", "standard_deviation"}


def _words(text):
    return " ".join(text.split())


# --- AC 1: the config entry -----------------------------------------------------------


@pytest.mark.parametrize("name", list(ENTRIES))
def test_every_entry_has_scatter_advice_and_evaluations(name):
    item = ENTRIES[name]
    assert {"scatter", "advice", "evaluations"} <= set(item), name
    assert set(item["scatter"]) == SCATTER_KEYS, name
    deviation = item["scatter"]["standard_deviation"]
    if deviation is not None:
        assert set(deviation) == {"value", "unit", "scale"}, name
        assert deviation["scale"] in (None, "arithmetic", "log10", "ln"), name
    if item["advice"] is not None:
        assert set(item["advice"]) == {"words", "by"}, name
    assert isinstance(item["evaluations"], list), name


@pytest.mark.parametrize("name", list(ENTRIES))
def test_each_number_is_in_the_words_and_the_docstring(name):
    scatter = ENTRIES[name]["scatter"]
    docstring = _words(getattr(correlations, name).__doc__)
    deviation = scatter["standard_deviation"]
    numbers = [
        scatter["data_count"],
        scatter["r_squared"],
        None if deviation is None else deviation["value"],
    ]
    for number in numbers:
        if number is not None:
            assert str(number) in scatter["words"], (name, number)
            assert str(number) in docstring, (name, number)


@pytest.mark.parametrize("name", list(ENTRIES))
def test_quoted_advice_is_in_the_docstring(name):
    advice = ENTRIES[name]["advice"]
    if advice is None or advice["by"] == "hangtu":
        return
    assert _words(advice["words"]) in _words(getattr(correlations, name).__doc__)


# --- AC 8: describe() -----------------------------------------------------------------


def test_describe_gives_k0s_evaluation_and_its_notes_dont_repeat_it():
    name = "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989"
    item = correlations.describe(name)
    [evaluation] = item["evaluations"]
    assert evaluation["bias"] == 2.16
    assert evaluation["coefficient_of_variation"] == 0.70
    assert evaluation["data_count"] == 74
    assert evaluation["cite"] == "Ching & Schweckendiek (2021)"
    assert "2.16" not in item["notes"]


# --- AC 2: the statistics on every row ------------------------------------------------

SIGMA_P = "preconsolidation_stress_mayne_kemper_1988"
DEVIATION = "preconsolidation_stress_correlation_standard_deviation"
KPA_TO_PSF = 1000 / 47.880259


def test_the_sources_statistics_are_on_every_row_including_blanks():
    df = pd.DataFrame({"spt_n": [10.0, 0.2, 50.0]})
    with pytest.warns(UserWarning, match="1 below range"):
        out = correlations.preconsolidation_stress_mayne_kemper_1988(df)
    assert out["correlation_data_count"].tolist() == [126.0] * 3
    assert out["correlation_r_squared"].tolist() == [0.699] * 3
    assert (
        out["correlation_scatter"].tolist()
        == ["n = 126, r² = 0.699, S.D. = 4.37 pa"] * 3
    )
    assert out["correlation_advice"].iloc[1] == (
        "hangtu: SPT N is a poor predictor in clay: use the estimate to check "
        "oedometer σ′p, not in its place."
    )


def test_a_correlation_without_statistics_says_so():
    out = correlations.undrained_shear_strength_terzaghi_peck_1967(
        pd.DataFrame({"spt_n": [10.0]})
    )
    row = out.iloc[0]
    assert np.isnan(row["correlation_data_count"])
    assert np.isnan(row["correlation_r_squared"])
    assert row["correlation_scatter"] == "Not stated."
    assert row["correlation_advice"] == (
        '"SPT N-values are generally a poor predictor of undrained shear strength" '
        "(Loehr et al. (2016), p. 7-38)"
    )


def test_a_correlation_without_advice_leaves_it_blank():
    out = correlations.effective_friction_angle_hatanaka_uchida_1996(
        pd.DataFrame({"spt_n1_60": [10.0]})
    )
    assert out["correlation_advice"].iloc[0] is None
    assert out["correlation_scatter"].iloc[0] == "±3° for most of the data"


# --- AC 3-6: the standard deviation on the rows ---------------------------------------


@pytest.fixture
def deviation_entry(monkeypatch):
    """σ′p's entry with a scale set, and a registry column for its deviation."""
    entries = copy.deepcopy(_framework.catalog())

    def set_scale(scale):
        entries[SIGMA_P]["scatter"]["standard_deviation"]["scale"] = scale

    set_scale("arithmetic")
    # A second σ′p correlation, with no standard deviation.
    entries["test_no_deviation"] = copy.deepcopy(entries[SIGMA_P])
    entries["test_no_deviation"]["scatter"]["standard_deviation"] = None
    entries["test_no_deviation"]["label"] = "Test"
    monkeypatch.setattr(_framework, "catalog", lambda: entries)
    column_info = _framework.column_info
    deviation_info = {
        "description": "test",
        "type": "number",
        "quantity": "stress",
        "scale": "ratio",
    }
    monkeypatch.setattr(
        _framework,
        "column_info",
        lambda name: deviation_info if name == DEVIATION else column_info(name),
    )
    return set_scale


def _no_deviation(df):
    item = _framework.entry("test_no_deviation")
    values = _framework.inputs(df, item, None)
    note = _framework.notes(df, item, values)
    sigma = 0.47 * values["spt_n"] * 100.0
    return _framework.estimate(df, "test_no_deviation", sigma, note, "SI")


def test_an_arithmetic_deviation_is_converted_and_blank_without_an_estimate(
    deviation_entry,
):
    df = pd.DataFrame({"spt_n": [10.0, 0.2]})
    with pytest.warns(UserWarning, match="1 below range"):
        si = correlations.preconsolidation_stress_mayne_kemper_1988(
            df, display_units="SI"
        )
    with pytest.warns(UserWarning, match="1 below range"):
        us = correlations.preconsolidation_stress_mayne_kemper_1988(
            df, display_units="US"
        )
    # 4.37 pa, pa = 100 kPa: 437 kPa; 437 / 0.04788026 = 9126.9 psf.
    assert si[DEVIATION].iloc[0] == pytest.approx(437.0)
    assert us[DEVIATION].iloc[0] == pytest.approx(9126.9, abs=0.1)
    assert us[DEVIATION].iloc[0] == pytest.approx(437.0 * KPA_TO_PSF)
    assert np.isnan(si[DEVIATION].iloc[1])
    assert si.attrs["units"][DEVIATION] == si.attrs["units"]["preconsolidation_stress"]
    assert us.attrs["units"][DEVIATION] == "psf"


@pytest.mark.parametrize("scale", [None, "log10", "ln"])
def test_a_deviation_not_known_to_be_arithmetic_stays_off_the_rows(
    deviation_entry, scale
):
    deviation_entry(scale)
    out = correlations.preconsolidation_stress_mayne_kemper_1988(
        pd.DataFrame({"spt_n": [10.0, 20.0]})
    )
    assert out[DEVIATION].isna().all()
    assert "4.37" in out["correlation_scatter"].iloc[0]


def test_results_with_and_without_a_deviation_concatenate_with_their_attrs(
    deviation_entry,
):
    df = ht.set_units(pd.DataFrame({"depth": [3.0], "spt_n": [10.0]}), {"depth": "m"})
    first = correlations.preconsolidation_stress_mayne_kemper_1988(
        df, display_units="SI"
    )
    second = _no_deviation(df)
    assert np.isnan(second[DEVIATION].iloc[0])
    both = pd.concat([first, second], ignore_index=True)
    assert both.attrs["units"] == first.attrs["units"]
    assert DEVIATION in both.attrs["units"]
    assert both.attrs["correlations"] == first.attrs["correlations"]


def test_a_target_without_a_registry_column_gets_none():
    out = correlations.preconsolidation_stress_mayne_kemper_1988(
        pd.DataFrame({"spt_n": [10.0]})
    )
    assert not [column for column in out if column.endswith("_standard_deviation")]


# --- AC 7: re-running replaces them with a warning ------------------------------------


def test_running_on_its_own_result_warns_that_it_replaced_them():
    out = correlations.preconsolidation_stress_mayne_kemper_1988(
        pd.DataFrame({"spt_n": [10.0]})
    )
    with pytest.warns(UserWarning, match="'correlation_advice'"):
        correlations.preconsolidation_stress_mayne_kemper_1988(out)
