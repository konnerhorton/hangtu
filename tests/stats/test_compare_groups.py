"""compare_groups(): Welch's ANOVA, Kruskal-Wallis and the pairs (m15d, AC 4-7, 12)."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import hangtu as ht
from hangtu.errors import HangtuError

VALUE = "undrained_shear_strength"


def _run(frame, **kwargs):
    kwargs.setdefault("significance_level", 0.05)
    return ht.stats.compare_groups(frame, value=VALUE, by="geology_unit", **kwargs)


def _frame(values):
    frame = pd.DataFrame(
        {
            "geology_unit": [key for key, items in values.items() for _ in items],
            VALUE: [float(v) for items in values.values() for v in items],
        }
    )
    return ht.set_units(frame, {VALUE: "kPa"})


@pytest.fixture
def result(three_groups):
    with pytest.warns(UserWarning, match=r"fewer than 5 .* C \(4\)"):
        return _run(three_groups)


def test_welch_anova_by_hand(result):
    # AC 4: W, its degrees of freedom and p from Delacre et al.'s eqs. 7-9.
    overall = result.overall().iloc[0]
    assert overall["welch_f_statistic"] == pytest.approx(11.98457980, abs=5e-9)
    assert overall["welch_degrees_of_freedom_numerator"] == 2
    assert overall["welch_degrees_of_freedom_denominator"] == pytest.approx(
        7.98204548, abs=5e-9
    )
    assert overall["welch_p_value"] == pytest.approx(0.00394381, abs=5e-9)
    # The degrees of freedom reproduce SciPy's p.
    assert stats.f.sf(
        overall["welch_f_statistic"], 2, overall["welch_degrees_of_freedom_denominator"]
    ) == pytest.approx(overall["welch_p_value"], rel=1e-9)


def test_games_howell(result):
    # AC 4: equal to tukey_hsd(equal_var=False) to 1e-6.
    frame = result.to_frame().set_index(["group_1", "group_2"])
    assert frame.loc[("A", "B"), "games_howell_p_value"] == pytest.approx(
        0.00449133, abs=1e-6
    )
    assert frame.loc[("A", "C"), "games_howell_p_value"] == pytest.approx(
        0.98361561, abs=1e-6
    )
    assert frame.loc[("B", "C"), "games_howell_p_value"] == pytest.approx(
        0.00420186, abs=1e-6
    )
    assert frame.loc[("A", "B"), "difference_lower"] == pytest.approx(
        -26.6216109, abs=1e-6
    )
    assert frame.loc[("A", "B"), "difference_upper"] == pytest.approx(
        -6.2450558, abs=1e-6
    )
    assert frame.loc[("A", "B"), "difference"] == pytest.approx(17.4 - 203 / 6)


def test_kruskal_wallis_and_dunn(result):
    # AC 5: H 10.1475, p 0.00625891; Dunn z and Holm-adjusted p.
    overall = result.overall().iloc[0]
    assert overall["kruskal_wallis_statistic"] == pytest.approx(10.1475, rel=1e-9)
    assert overall["kruskal_wallis_degrees_of_freedom"] == 2
    assert overall["kruskal_wallis_p_value"] == pytest.approx(0.00625891, abs=5e-9)
    frame = result.to_frame()
    assert frame["dunn_z_statistic"].tolist() == pytest.approx(
        [-2.6957037, 0.15, 2.6846788], abs=5e-8
    )
    assert frame["dunn_p_value"].tolist() == pytest.approx(
        [0.02107204, 0.88076462, 0.02107204], abs=5e-9
    )


def test_kruskal_wallis_with_ties_on_helsel_table_7_4():
    # AC 7: the tie-corrected H 2.6890049, p 0.44209903 (Helsel: 0.44).
    frame = _frame(
        {
            "Summer": [6, 12, 15, 18, 21, 24],
            "Fall": [5, 8.5, 11, 14, 19.5, 22],
            "Winter": [2, 4, 8.5, 13, 16, 19.5],
            "Spring": [1, 3, 7, 10, 17, 23],
        }
    )
    overall = _run(frame).overall().iloc[0]
    assert overall["kruskal_wallis_statistic"] == pytest.approx(2.6890049, abs=5e-8)
    assert overall["kruskal_wallis_p_value"] == pytest.approx(0.44209903, abs=5e-9)


def test_pairs_are_in_group_order_with_their_statistics(result):
    frame = result.to_frame()
    assert list(zip(frame["group_1"], frame["group_2"], strict=True)) == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]
    assert frame["count_1"].tolist() == [5, 5, 6]
    assert frame["mean_2"].tolist() == pytest.approx([203 / 6, 17, 17])
    assert frame["confidence_level"].tolist() == pytest.approx([0.95] * 3)


def test_two_groups_match_welch(helsel):
    # AC: W = t², Games-Howell's p = Welch's p, with a note pointing to compare().
    industrial, residential = helsel
    frame = _frame({"Industrial": industrial, "Residential": residential})
    result = _run(frame)
    overall = result.overall().iloc[0]
    assert overall["welch_f_statistic"] == pytest.approx(0.029044191616**2, rel=1e-9)
    assert result.to_frame().iloc[0]["games_howell_p_value"] == pytest.approx(
        0.9773249, abs=5e-8
    )
    assert any("compare() adds the Brunner-Munzel" in note for note in result.notes)


def test_a_group_of_one_is_left_out_with_a_warning(three_groups):
    # AC 12: one group of 1 among four.
    frame = pd.concat([three_groups, _frame({"D": [50]})], ignore_index=True)
    frame = ht.set_units(frame, {VALUE: "kPa"})
    with pytest.warns(UserWarning) as record:
        result = _run(frame)
    messages = [str(w.message) for w in record]
    assert any(
        "left 1 group" in m and "D: fewer than 2 values (1)" in m for m in messages
    )
    groups = result.groups_frame()
    assert groups["geology_unit"].tolist() == ["A", "B", "C", "D"]
    assert groups["reason_not_tested"].tolist()[3] == "fewer than 2 values (1)"
    assert len(result.to_frame()) == 3
    assert result.overall().iloc[0]["kruskal_wallis_degrees_of_freedom"] == 2
    assert "D: not tested, fewer than 2 values (1)." in result.notes


def test_three_groups_of_one_is_an_error():
    # AC 12
    frame = _frame({"A": [1, 2, 3], "B": [4], "C": [5], "D": [6]})
    with pytest.raises(HangtuError, match=r"needs at least 2 groups .* has 1"):
        _run(frame)


def test_by_is_required(three_groups):
    with pytest.raises(HangtuError, match="needs by="):
        ht.stats.compare_groups(three_groups, value=VALUE, significance_level=0.05)


def test_log_reports_ratios(three_groups):
    with pytest.warns(UserWarning, match="fewer than 5"):
        result = _run(three_groups, log=True)
    frame = result.to_frame()
    assert "ratio" in frame.columns and "difference" not in frame.columns
    assert "geometric_mean_1" in frame.columns
    row = frame.iloc[0]
    assert row["ratio"] == pytest.approx(
        row["geometric_mean_1"] / row["geometric_mean_2"]
    )
    assert "A / B" in str(result)
    # Ranks don't change on a log scale.
    with pytest.warns(UserWarning, match="fewer than 5"):
        plain = _run(three_groups)
    assert frame["dunn_p_value"].tolist() == pytest.approx(
        plain.to_frame()["dunn_p_value"].tolist()
    )


def test_the_note_names_a_pair_whose_tests_disagree():
    steady = [9.5, 9.6, 9.7, 9.8, 9.9, 10.1, 10.2, 10.3, 10.4, 10.5]
    split = [9.0, 9.2, 9.4, 9.6, 9.8, 20, 20.5, 21, 21.5, 22]
    result = _run(_frame({"A": steady, "B": split}))
    assert any(
        note.startswith("A and B: Games-Howell finds the means differ")
        and "Dunn's test doesn't find" in note
        and note.endswith("Look at the values (P07).")
        for note in result.notes
    )
    with pytest.warns(UserWarning, match="fewer than 5"):
        agreeing = _run(_frame({"A": [12, 15, 18, 20, 22], "C": [14, 16, 17, 21]}))
    assert not any(note.startswith("A and C") for note in agreeing.notes)


def test_the_note_on_the_overall_tests(result):
    assert result.notes[0].startswith("Welch's ANOVA finds the means differ")
    assert result.notes[1].startswith("The Kruskal-Wallis test finds")
    assert any("family-wise, adjusted for the 3 pairs" in note for note in result.notes)
    assert any(
        note.startswith("Both tests assume independent") for note in result.notes
    )


def test_no_spread_in_a_group_leaves_the_parametric_tests_blank():
    frame = _frame({"A": [5, 5, 5, 5, 5], "B": [1, 2, 3, 4, 6], "C": [7, 8, 9, 10, 11]})
    result = _run(frame)
    assert np.isnan(result.overall().iloc[0]["welch_p_value"])
    assert result.to_frame()["games_howell_p_value"].isna().all()
    assert not np.isnan(result.overall().iloc[0]["kruskal_wallis_p_value"])
    assert any("No Welch's ANOVA or Games-Howell" in note for note in result.notes)


def test_units_scale_the_differences_and_leave_the_tests(three_groups):
    # AC 13 for compare_groups(): psf to kPa.
    psf = ht.set_units(three_groups.copy(), {VALUE: "psf"})
    with pytest.warns(UserWarning, match="fewer than 5"):
        in_psf = _run(psf).to_frame()
    with pytest.warns(UserWarning, match="fewer than 5"):
        in_kpa = _run(psf, display_units="SI").to_frame()
    assert in_kpa["difference_lower"].tolist() == pytest.approx(
        (in_psf["difference_lower"] * 0.04788026).tolist(), rel=1e-6
    )
    for name in ("games_howell_p_value", "dunn_z_statistic", "dunn_p_value"):
        assert in_kpa[name].tolist() == pytest.approx(in_psf[name].tolist(), rel=1e-9)
