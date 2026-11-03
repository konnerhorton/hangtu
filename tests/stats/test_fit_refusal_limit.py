"""fit(): the SPT refusal upper limit (docs/work/m18a-refusals.md, AC 1-5)."""

import math
import textwrap

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.stats import _fit as fit_module

N60 = [12.0, 18.0, 25.0, 31.0, 40.0]
#: Two refusals at N60 66.7, spt_n 50 (ER 80 %): the Terrace limit of 120
#: blows/ft is 120 x 66.7 / 50 = 160.08 in N60.
REFUSAL, FIELD_N, LIMIT = 66.7, 50.0, 160.08
SCIPY = {
    "normal": (stats.norm, {}),
    "lognormal": (stats.lognorm, {"floc": 0}),
    "gamma": (stats.gamma, {"floc": 0}),
    "weibull": (stats.weibull_min, {"floc": 0}),
}
NAMES = {
    "normal": ["loc", "scale"],
    "lognormal": ["s", "loc", "scale"],
    "gamma": ["a", "loc", "scale"],
    "weibull": ["c", "loc", "scale"],
}


@pytest.fixture(autouse=True)
def _short_bootstrap(monkeypatch):
    monkeypatch.setattr(fit_module, "BOOTSTRAP_SAMPLES", 19)


def terrace(**columns):
    return pd.DataFrame(
        {
            "geology_unit": ["Terrace"] * 7,
            "spt_n": [9.0, 13.5, 18.75, 23.25, 30.0, FIELD_N, FIELD_N],
            "spt_n60": [*N60, REFUSAL, REFUSAL],
            "spt_refusal": [False] * 5 + [True] * 2,
            **columns,
        }
    )


def write(tmp_path, text):
    path = tmp_path / "judgments.yaml"
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def fit(df, **kwargs):
    with pytest.warns(UserWarning, match="fewer than 10"):
        return ht.stats.fit(df, value=kwargs.pop("value", "spt_n60"), **kwargs)


def fits(result):
    return {f["distribution"]: f for f in result.groups[0]["fits"]}


# --- AC 1: without the judgment --------------------------------------------------


def test_without_the_limit_refusals_stay_right_censored_with_a_note():
    result = fit(terrace())
    counts = result.groups[0]["counts"]
    assert (counts["count_censored"], counts["count_interval_censored"]) == (2, 0)
    data = stats.CensoredData(uncensored=N60, right=[REFUSAL, REFUSAL])
    location, _ = stats.norm.fit(data)
    assert fits(result)["normal"]["parameters"]["loc"] == pytest.approx(location)
    assert (
        "The tail above the 2 refusals is the distribution's: they are fitted as "
        "at least their value. Set spt_refusal_upper_limit, in field N per "
        "geology unit, to limit it (the judgments guide)."
    ) in result.notes
    assert "spt_refusal_upper_limit" not in result.judgments


def test_no_note_without_refusals():
    result = fit(terrace(spt_refusal=[False] * 7))
    assert not any("tail above" in note for note in result.notes)


# --- AC 2: the golden case ---------------------------------------------------------


@pytest.mark.parametrize("limit", [120, {"Terrace": 120}])
def test_refusals_fit_between_their_value_and_the_limit(limit):
    result = fit(terrace(), spt_refusal_upper_limit=limit)
    counts = result.groups[0]["counts"]
    assert counts["count_interval_censored"] == 2
    assert (counts["count"], counts["count_censored"]) == (7, 2)
    assert counts["count_at_least"] == 2
    assert np.ravel(result.groups[0]["values"]["interval"]) == pytest.approx(
        [REFUSAL, LIMIT, REFUSAL, LIMIT]
    )
    data = stats.CensoredData(
        uncensored=N60, interval=[[REFUSAL, LIMIT], [REFUSAL, LIMIT]]
    )
    for name, fitted in fits(result).items():
        family, fixed = SCIPY[name]
        expected = dict(zip(NAMES[name], family.fit(data, **fixed), strict=True))
        expected.pop("loc", None) if name != "normal" else None
        for key, value in expected.items():
            assert fitted["parameters"][key] == pytest.approx(value, rel=1e-6), name
        distribution = result.distribution(name)
        log_likelihood = distribution.logpdf(N60).sum() + 2 * math.log(
            distribution.cdf(LIMIT) - distribution.cdf(REFUSAL)
        )
        assert fitted["log_likelihood"] == pytest.approx(log_likelihood, rel=1e-9)
    assert (
        "Terrace: 2 refusals fitted between their spt_n60 and the upper limit "
        "(120 blows/ft as field N, scaled by each row's spt_n60 / spt_n)."
        if isinstance(limit, dict)
        else "All: 2 refusals fitted between their spt_n60 and the upper limit "
        "(120 blows/ft as field N, scaled by each row's spt_n60 / spt_n)."
    ) in result.notes
    assert not any("tail above" in note for note in result.notes)
    assert any("2 between a refusal and its upper limit" in n for n in result.notes)


def test_the_limit_shortens_the_fitted_tail():
    without = result_p99(fit(terrace()))
    with_limit = result_p99(fit(terrace(), spt_refusal_upper_limit=120))
    assert with_limit < without


def result_p99(result):
    return result.distribution("lognormal").ppf(0.99)


def test_the_judgment_from_a_file_is_recorded(tmp_path):
    path = write(
        tmp_path,
        """\
        spt_refusal_upper_limit:
          by: geology_unit
          values:
            Terrace: {spt_n: 120, reason: "50 blows for 5 in, per foot"}
        """,
    )
    result = fit(terrace(), judgments=ht.judgments(path))
    assert result.groups[0]["counts"]["count_interval_censored"] == 2
    record = result.judgments["spt_refusal_upper_limit"]
    assert record["source"] == str(path)
    assert record["by"] == "geology_unit"
    assert record["values"] == {
        "Terrace": {"spt_n": "120", "reason": "50 blows for 5 in, per foot"}
    }
    assert len(record["sha256"]) == 64


def test_the_argument_replaces_the_file_with_a_warning(tmp_path):
    path = write(
        tmp_path,
        "spt_refusal_upper_limit:\n  values:\n    Terrace: {spt_n: 500}\n",
    )
    with pytest.warns(UserWarning, match="replaces the one in judgments.yaml"):
        result = fit(terrace(), spt_refusal_upper_limit=120, judgments=path)
    assert result.judgments["spt_refusal_upper_limit"]["source"] == "argument"
    assert result.groups[0]["values"]["interval"][0][1] == pytest.approx(LIMIT)


# --- AC 3: scaled per row ------------------------------------------------------------


def test_one_limit_scales_to_each_n_column():
    df = terrace(spt_n1_60=[*N60, 80.0, 100.0])
    n60 = fit(df, spt_refusal_upper_limit=120)
    n1_60 = fit(df, value="spt_n1_60", spt_refusal_upper_limit=120)
    field = fit(df, value="spt_n", spt_refusal_upper_limit=120)
    assert np.array(n60.groups[0]["values"]["interval"])[:, 1] == pytest.approx(
        [LIMIT, LIMIT]
    )
    # 120 x 80 / 50 = 192; 120 x 100 / 50 = 240.
    assert np.array(n1_60.groups[0]["values"]["interval"])[:, 1] == pytest.approx(
        [192.0, 240.0]
    )
    assert np.array(field.groups[0]["values"]["interval"])[:, 1] == pytest.approx(
        [120.0, 120.0]
    )


def test_the_capped_n_takes_the_limit_as_it_is():
    # spt_n_capped holds the cap at a refusal, not a scaled N.
    df = terrace(spt_n_capped=[9.0, 13.5, 18.75, 23.25, 30.0, 100.0, 100.0])
    result = fit(df, value="spt_n_capped", spt_refusal_upper_limit=120)
    assert np.array(result.groups[0]["values"]["interval"])[:, 1] == pytest.approx(
        [120.0, 120.0]
    )


# --- AC 4: errors ------------------------------------------------------------------


def test_the_argument_for_another_value_is_an_error():
    df = pd.DataFrame({"undrained_shear_strength": [40.0, 50.0, 60.0, 70.0]})
    df = ht.set_units(df, {"undrained_shear_strength": "kPa"})
    with pytest.raises(ht.HangtuError, match=r"isn't an SPT N column.*Leave it out"):
        ht.stats.fit(df, value="undrained_shear_strength", spt_refusal_upper_limit=120)


def test_a_file_entry_is_ignored_for_another_value(tmp_path):
    path = write(tmp_path, "spt_refusal_upper_limit:\n  values:\n    A: {spt_n: 1}\n")
    df = pd.DataFrame({"undrained_shear_strength": [40.0, 50.0, 60.0, 70.0]})
    df = ht.set_units(df, {"undrained_shear_strength": "kPa"})
    with pytest.warns(UserWarning, match="fewer than 10"):
        result = ht.stats.fit(df, value="undrained_shear_strength", judgments=path)
    assert "spt_refusal_upper_limit" not in result.judgments


def test_n60_without_spt_n_is_an_error():
    with pytest.raises(ht.ColumnError, match=r"no 'spt_n' column"):
        ht.stats.fit(
            terrace().drop(columns="spt_n"),
            value="spt_n60",
            spt_refusal_upper_limit=120,
        )


def test_a_limit_not_above_the_value_names_the_row():
    with pytest.raises(
        ht.HangtuError,
        match=r"isn't above the refusal in rows 5, 6: in row 5, spt_n60 is "
        r"66.7 and the limit 53.36 \(40 blows/ft",
    ):
        ht.stats.fit(terrace(), value="spt_n60", spt_refusal_upper_limit=40)


def test_a_unit_with_refusals_the_entry_doesnt_list_is_an_error(tmp_path):
    df = terrace(geology_unit=["Terrace"] * 6 + ["Alluvium"])
    path = write(
        tmp_path, "spt_refusal_upper_limit:\n  values:\n    Terrace: {spt_n: 120}\n"
    )
    with pytest.raises(
        ht.HangtuError, match=r"has no value for the geology unit 'Alluvium'"
    ):
        ht.stats.fit(df, value="spt_n60", judgments=path)


def test_a_project_entry_fills_an_unlisted_unit_with_a_warning(tmp_path):
    df = terrace(geology_unit=["Terrace"] * 6 + ["Alluvium"])
    path = write(
        tmp_path,
        """\
        spt_refusal_upper_limit:
          project: {spt_n: 100, reason: "hardest logged"}
          values:
            Terrace: {spt_n: 120}
        """,
    )
    with pytest.warns(UserWarning, match=r"project value 100 is used for the geology"):
        result = fit(df, judgments=path)
    # 100 x 66.7 / 50 = 133.4 for the Alluvium refusal.
    assert np.array(result.groups[0]["values"]["interval"])[:, 1] == pytest.approx(
        [LIMIT, 133.4]
    )


def test_an_argument_key_not_in_the_rows_is_an_error():
    with pytest.raises(
        ht.HangtuError, match=r"names 'Teracce', which is not a geology unit"
    ):
        ht.stats.fit(
            terrace(), value="spt_n60", spt_refusal_upper_limit={"Teracce": 120}
        )


@pytest.mark.parametrize("limit", [0, -5, "lots", True])
def test_a_limit_that_isnt_a_positive_number_is_an_error(limit):
    with pytest.raises(ht.HangtuError, match=r"must be a positive number of blows"):
        ht.stats.fit(terrace(), value="spt_n60", spt_refusal_upper_limit=limit)


# --- AC 5: none ----------------------------------------------------------------------


def test_none_keeps_a_unit_right_censored_and_says_so(tmp_path):
    df = terrace(geology_unit=["Terrace"] * 6 + ["Alluvium"])
    path = write(
        tmp_path,
        """\
        spt_refusal_upper_limit:
          values:
            Terrace: {spt_n: 120}
            Alluvium: {spt_n: none, reason: "refusals on cobbles"}
        """,
    )
    result = fit(df, judgments=path)
    counts = result.groups[0]["counts"]
    assert (counts["count_interval_censored"], counts["count_censored"]) == (1, 2)
    assert result.groups[0]["values"]["right"] == [REFUSAL]
    assert (
        "Alluvium: 1 refusal right-censored on purpose: spt_refusal_upper_limit is "
        "none (refusals on cobbles)."
    ) in result.notes
    assert result.judgments["spt_refusal_upper_limit"]["values"]["Alluvium"] == {
        "spt_n": "none",
        "reason": "refusals on cobbles",
    }


def test_positions_approximate_when_a_refusal_lies_below_a_measured_value():
    df = terrace(spt_n60=[*N60[:4], 90.0, REFUSAL, REFUSAL])
    result = fit(df, spt_refusal_upper_limit=120)
    assert any("its positions approximate" in note for note in result.notes)
