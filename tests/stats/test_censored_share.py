"""Values the censored values drive (docs/work/reliability-guards.md, AC 5, 6 and 8)."""

import warnings

import pandas as pd

import hangtu as ht
from hangtu.stats import _fit

#: The warning from representative() when censored values drive a value.
MOSTLY = "rests on censored values"


def friction(values, qualifiers):
    df = pd.DataFrame({"effective_friction_angle": values, "qualifier": qualifiers})
    return ht.set_units(df, {"effective_friction_angle": "deg"})


def representative(df, **kwargs):
    kwargs.setdefault("method", "characteristic")
    kwargs.setdefault("side", "low")
    kwargs.setdefault("distribution", "normal")
    kwargs.setdefault("estimate", "mean")
    return ht.stats.representative(df, value="effective_friction_angle", **kwargs)


def caught(function, *args, **kwargs):
    with warnings.catch_warnings(record=True) as found:
        warnings.simplefilter("always")
        result = function(*args, **kwargs)
    return result, [str(w.message) for w in found]


def test_more_than_half_censored_warns_and_notes():
    df = friction([30.0, 32.0, 34.0, 40.0, 40.0, 40.0, 40.0], [None] * 3 + [">"] * 4)
    result, messages = caught(representative, df)
    assert any(MOSTLY in m and "4 of 7 values censored" in m for m in messages)
    assert any(
        n.startswith("All: 4 of 7 values censored;") and "so the value rests" in n
        for n in result.notes
    )


def test_half_or_fewer_censored_does_not_warn_on_the_count():
    df = friction([30.0, 32.0, 34.0, 36.0, 40.0, 40.0, 40.0], [None] * 4 + [">"] * 3)
    result, messages = caught(representative, df)
    assert result.groups[0]["value"] < 36.0
    assert not any(MOSTLY in m for m in messages)


def test_a_high_value_above_every_measured_one_warns():
    # Three measured values, two "at least" far above: the high mean+k·s view
    # lands above the largest measured value with only 2 of 5 censored.
    df = friction([30.0, 31.0, 32.0, 45.0, 45.0], [None] * 3 + [">"] * 2)
    result, messages = caught(
        representative,
        df,
        method="standard_deviations",
        side="high",
        standard_deviations=1,
        estimate=None,
    )
    assert result.groups[0]["value"] > 32.0
    assert any(MOSTLY in m and "above every measured value" in m for m in messages)


def test_a_low_value_below_every_measured_one_warns_when_left_censored():
    df = friction([20.0, 20.0, 20.0, 30.0, 31.0, 32.0], ["<"] * 3 + [None] * 3)
    result, messages = caught(representative, df)
    assert result.groups[0]["value"] < 30.0
    assert any("below every measured value" in m for m in messages)


def test_the_usual_low_side_of_right_censored_values_does_not_warn():
    # A low characteristic value inside the measured values, 1 of 6 censored.
    df = friction([30.0, 32.0, 34.0, 36.0, 38.0, 45.0], [None] * 5 + [">"])
    result, messages = caught(representative, df)
    assert result.groups[0]["value"] < 38.0
    assert not any(MOSTLY in m for m in messages)
    # The 5th percentile below every measured value, 1 of 6 censored "at least".
    df = friction([30.0, 40.0, 50.0, 60.0, 70.0, 80.0], [None] * 5 + [">"])
    result, messages = caught(
        representative, df, method="percentile", percentile=5, estimate=None
    )
    assert result.groups[0]["value"] < 30.0
    assert not any(MOSTLY in m for m in messages)


def test_fit_warns_when_most_values_are_censored():
    values = [30.0, 32.0, 34.0, 36.0] + [40.0] * 5
    df = friction(values, [None] * 4 + [">"] * 5)
    result, messages = caught(ht.stats.fit, df, value="effective_friction_angle")
    assert any("more than half the values" in m for m in messages)
    assert any("5 of 9 values censored, so the fits rest" in n for n in result.notes)


def test_the_values_are_unchanged(monkeypatch):
    df = friction([30.0, 32.0, 34.0, 40.0, 40.0, 40.0, 40.0], [None] * 3 + [">"] * 4)
    result, _ = caught(representative, df)
    monkeypatch.setattr(_fit, "censoring_concerns", lambda values, value=None: [])
    plain, messages = caught(representative, df)
    assert not any(MOSTLY in m for m in messages)
    assert result.groups[0]["value"] == plain.groups[0]["value"]
