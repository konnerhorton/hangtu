"""Correlation statistics on the rows (docs/work/m15b-correlation-statistics.md)."""

import pytest

from hangtu import _config
from hangtu.analysis import correlations

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
