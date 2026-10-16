"""P05 envelopes (P05 §8, §11, §12)."""

import numpy as np
import pandas as pd
import pytest

import hangtu as ht
from hangtu.errors import ColumnError, HangtuError

CURVE_A = (
    [0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75],
    [4, 12, 30, 55, 75, 90, 100],
)


@pytest.fixture(autouse=True)
def _no_hints():
    ht.settings.hints = False


def curves(*specs, unit="mm"):
    rows = [
        {"specimen_id": name, "particle_size": size, "percent_passing": percent}
        for name, sizes, passing in specs
        for size, percent in zip(sizes, passing, strict=True)
    ]
    return ht.set_units(pd.DataFrame(rows), {"particle_size": unit})


def envelope_table(**changes):
    table = pd.DataFrame(
        {
            "label": ["Filter"] * 3,
            "particle_size": [0.075, 0.425, 4.75],
            "low": [0, 20, 80],
            "high": [5, 45, 100],
        }
    )
    for column, values in changes.items():
        table[column] = values
    return ht.set_units(table, {"particle_size": "mm"})


# --- Envelopes (§8, §12) -----------------------------------------------------


def envelope_edges(ax):
    (band,) = [c for c in ax.collections if c.get_gid() == "envelope"]
    return band.get_paths()[0].vertices


def test_envelope_edges_pass_through_the_table():
    _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), envelopes=envelope_table())
    vertices = {tuple(np.round(v, 6)) for v in envelope_edges(ax)}
    for size, low, high in [(0.075, 0, 5), (0.425, 20, 45), (4.75, 80, 100)]:
        assert (size, low) in vertices
        assert (size, high) in vertices
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert legend[-1] == "Filter"


def test_envelope_rows_are_sorted_by_size_as_rows():
    table = envelope_table().iloc[[2, 0, 1]]
    _, ax = ht.plot.grain_size(pd.DataFrame(), envelopes=table)
    vertices = {tuple(np.round(v, 6)) for v in envelope_edges(ax)}
    assert (0.425, 20) in vertices and (0.425, 45) in vertices


def test_envelope_from_a_csv_path(tmp_path):
    path = tmp_path / "filter.csv"
    envelope_table().to_csv(path, index=False)
    with pytest.warns(UserWarning, match="no units for particle_size"):
        _, ax = ht.plot.grain_size(curves(("A", *CURVE_A)), envelopes=path)
    assert len(envelope_edges(ax))


def test_envelope_in_inches_converted_to_mm():
    table = envelope_table(particle_size=[0.075 / 25.4, 0.425 / 25.4, 4.75 / 25.4])
    table = ht.set_units(table, {"particle_size": "in"})
    _, ax = ht.plot.grain_size(pd.DataFrame(), envelopes=table)
    np.testing.assert_allclose(envelope_edges(ax)[:, 0].min(), 0.075)


def test_envelope_without_any_units_is_an_error():
    table = envelope_table()
    table.attrs = {}
    with pytest.raises(HangtuError, match="no units for particle_size, and neither"):
        ht.plot.grain_size(pd.DataFrame(), envelopes=table)


def test_two_envelopes_and_colors():
    table = pd.concat([envelope_table(), envelope_table(label=["Grout"] * 3)])
    table = ht.set_units(table, {"particle_size": "mm"})
    _, ax = ht.plot.grain_size(
        pd.DataFrame(), envelopes=table, envelope_colors={"Grout": "tan"}
    )
    bands = [c for c in ax.collections if c.get_gid() == "envelope"]
    assert len(bands) == 2
    np.testing.assert_allclose(
        bands[1].get_edgecolor()[0][:3], (0.824, 0.706, 0.549), atol=1e-3
    )


def test_unknown_envelope_color_warns():
    with pytest.warns(UserWarning, match="'Grout', which is not in the envelopes"):
        ht.plot.grain_size(
            pd.DataFrame(), envelopes=envelope_table(), envelope_colors={"Grout": "tan"}
        )


def test_bad_envelope_color_is_an_error():
    with pytest.raises(HangtuError, match="envelope_colors has colors"):
        ht.plot.grain_size(
            pd.DataFrame(),
            envelopes=envelope_table(),
            envelope_colors={"Filter": "not a color"},
        )


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"low": [0, None, 80]}, "blank or non-numeric"),
        ({"high": [5, "x", 100]}, "blank or non-numeric"),
        ({"low": [0, 50, 80]}, r"low above high \(rows 1\)"),
        ({"high": [5, 45, 110]}, "outside 0 to 100"),
        ({"particle_size": [0.075, 0.075, 4.75]}, "same particle size twice"),
        ({"particle_size": [0.075, 0.0, 4.75]}, "0 or less"),
        ({"label": ["Filter", "Filter", "Other"]}, "'Other' has one size"),
    ],
)
def test_envelope_errors(changes, match):
    with pytest.raises(HangtuError, match=match):
        ht.plot.grain_size(pd.DataFrame(), envelopes=envelope_table(**changes))


def test_envelope_blank_label_and_missing_column():
    with pytest.raises(HangtuError, match="have no label"):
        ht.plot.grain_size(
            pd.DataFrame(), envelopes=envelope_table(label=["Filter", None, "Filter"])
        )
    with pytest.raises(ColumnError, match="no 'high' column"):
        ht.plot.grain_size(
            pd.DataFrame(), envelopes=envelope_table().drop(columns="high")
        )
    with pytest.raises(HangtuError, match="envelopes must be a DataFrame"):
        ht.plot.grain_size(pd.DataFrame(), envelopes=[(0.075, 0, 5)])


def test_envelopes_template():
    assert list(ht.template("envelopes").columns) == [
        "label",
        "particle_size",
        "low",
        "high",
    ]
