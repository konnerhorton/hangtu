"""ht.analysis.correlations (docs/work/m13b1-spt-framework.md, AC 2, 3, 5 and 6)."""

import inspect
import re

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu import _config
from hangtu.analysis import correlations

# AC 2, by hand: φ′ = (15.4 (N1)60)^0.5 + 20. (N1)60 by Liao & Whitman, then by Kayen.
HATANAKA_UCHIDA = [
    (28.284, 40.87),
    (10.000, 32.41),
    (21.213, 38.07),
    (8.500, 31.44),
    (25.882, 39.96),
    (20.625, 37.82),
    (7.586, 30.81),
]
FUNCTIONS = {"hatanaka_uchida_1996": correlations.hatanaka_uchida_1996}


def frame(**columns):
    return pd.DataFrame(columns)


def test_hatanaka_uchida_golden_values():
    n1_60, expected = zip(*HATANAKA_UCHIDA, strict=True)
    out = correlations.hatanaka_uchida_1996(frame(spt_n1_60=list(n1_60)))
    assert out["effective_friction_angle"].tolist() == pytest.approx(
        list(expected), abs=0.005
    )
    assert (out["correlation_name"] == "hatanaka_uchida_1996").all()
    assert out["correlation_note"].isna().all()
    assert out.attrs["units"] == {"effective_friction_angle": "°"}


def test_hatanaka_uchida_range_ends_are_inside():
    out = correlations.hatanaka_uchida_1996(frame(spt_n1_60=[4.55, 39.0]))
    assert out["effective_friction_angle"].notna().all()


def test_no_estimate_gives_nan_with_the_reason_and_one_warning():
    df = frame(
        spt_n1_60=[4.0, 40.0, np.nan, 20.0, 20.0, np.nan],
        spt_refusal=[False, False, False, True, False, True],
    )
    with pytest.warns(UserWarning) as caught:
        out = correlations.hatanaka_uchida_1996(df)
    # A blank input comes before a refusal.
    assert out["correlation_note"].tolist() == [
        "below range",
        "above range",
        "input blank",
        "refusal",
        None,
        "input blank",
    ]
    assert out["effective_friction_angle"].isna().tolist() == [
        True, True, True, True, False, True,
    ]  # fmt: skip
    assert [str(w.message) for w in caught] == [
        "hatanaka_uchida_1996 gave no estimate for 5 of 6 rows (2 input blank, "
        "1 refusal, 1 below range, 1 above range; see 'correlation_note'). Its "
        "range is 4.55 ≤ spt_n1_60 ≤ 39; outside it the estimate is blank, never "
        "extrapolated."
    ]


def test_no_row_is_dropped_or_reordered_and_the_input_is_unchanged():
    df = frame(loca_id=["B", "A", "C"], spt_n1_60=[10.0, 2.0, 20.0])
    df.index = [7, 3, 5]
    before = df.copy()
    with pytest.warns(UserWarning, match="1 below range"):
        out = correlations.hatanaka_uchida_1996(df)
    assert out.index.tolist() == [7, 3, 5]
    assert out["loca_id"].tolist() == ["B", "A", "C"]
    pd.testing.assert_frame_equal(df, before)


def test_existing_output_columns_are_replaced_with_a_warning():
    df = frame(spt_n1_60=[10.0], effective_friction_angle=[30.0])
    with pytest.warns(UserWarning, match="Replaced the existing columns"):
        out = correlations.hatanaka_uchida_1996(df)
    assert out["effective_friction_angle"][0] == pytest.approx(32.41, abs=0.005)


# --- AC 3: the wrong variant is an error ----------------------------------------------


def test_n60_without_n1_60_is_an_error_naming_what_adds_it():
    df = frame(spt_n=[10.0], spt_n60=[12.0])
    with pytest.raises(
        ht.ColumnError, match=r"'spt_n1_60' not found.*ht\.analysis\.spt_n1_60\("
    ):
        correlations.hatanaka_uchida_1996(df)


@pytest.mark.parametrize("name", list(FUNCTIONS))
def test_no_argument_chooses_the_input_column(name):
    parameters = set(inspect.signature(FUNCTIONS[name]).parameters)
    assert parameters == {"df", "units", "display_units"}


# --- AC 5: what's recorded ------------------------------------------------------------


def test_attrs_hold_every_entry_and_describe_returns_the_same():
    out = correlations.hatanaka_uchida_1996(frame(spt_n1_60=[10.0]))
    recorded = out.attrs["correlations"]
    assert set(recorded) == set(_config.load("config/correlations.yaml"))
    assert recorded["hatanaka_uchida_1996"] == correlations.describe(
        "hatanaka_uchida_1996"
    )
    entry = recorded["hatanaka_uchida_1996"]
    assert entry["inputs"] == {
        "spt_n1_60": {"variant": "(N1)60, N60 corrected for overburden", "unit": None}
    }
    assert entry["range"] == {"spt_n1_60": {"at_least": 4.55, "at_most": 39.0}}


def test_describe_returns_a_copy():
    correlations.describe("hatanaka_uchida_1996")["range"].clear()
    assert correlations.describe("hatanaka_uchida_1996")["range"]


def test_describe_an_unknown_name_lists_the_correlations():
    with pytest.raises(ht.HangtuError, match=r"no correlation named 'wolff_1989'.*"):
        correlations.describe("wolff_1989")


def test_outputs_from_one_input_concatenate_with_their_attrs():
    df = ht.set_units(frame(depth=[3.0], spt_n1_60=[10.0]), {"depth": "m"})
    first = correlations.hatanaka_uchida_1996(df)
    second = correlations.hatanaka_uchida_1996(df)
    both = pd.concat([first, second], ignore_index=True)
    assert both.attrs["units"] == {"depth": "m", "effective_friction_angle": "°"}
    assert both.attrs["correlations"] == first.attrs["correlations"]


# --- AC 6: the config and the docstrings agree ----------------------------------------


def _drift(name, docstring):
    """Return what the entry states and the docstring doesn't."""
    text = " ".join(docstring.split())
    entry = correlations.describe(name)
    expected = []
    for source in entry["sources"]:
        expected += [source["cite"], *source["locators"]]
    for bounds in entry["range"].values():
        expected += [f"{bound:g}" for bound in bounds.values()]
    return [item for item in expected if item not in text]


def test_every_entry_has_a_function():
    assert set(_config.load("config/correlations.yaml")) == set(FUNCTIONS)
    assert set(correlations.__all__) == {*FUNCTIONS, "describe"}


@pytest.mark.parametrize("name", list(FUNCTIONS))
def test_the_docstring_names_the_sources_locators_and_range(name):
    assert _drift(name, FUNCTIONS[name].__doc__) == []


def test_the_drift_test_fails_when_a_docstring_changes():
    docstring = correlations.hatanaka_uchida_1996.__doc__
    changed = re.sub(r"4\.55", "4.5", docstring)
    changed = changed.replace("Eq. 7.23", "Eq. 7.32")
    assert _drift("hatanaka_uchida_1996", changed) == ["Eq. 7.23, p. 7-55", "4.55"]
