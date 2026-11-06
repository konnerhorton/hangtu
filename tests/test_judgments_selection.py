"""The selection judgment (docs/work/m18e-selection.md, decisions 6-10, AC 1, AC 5)."""

import textwrap

import pytest

import hangtu as ht
from hangtu.errors import HangtuError

EVERY_METHOD = """\
selection:
  effective_friction_angle:
    by: geology_unit
    units: {value: deg}
    values:
      Sand:
        source: "A"
        method: characteristic
        estimate: mean
        side: low
        distribution: normal
        reason: "a mean over a long slip surface"
      Gravel:
        source: "A"
        method: percentile
        percentile: 5
        side: low
        distribution: lognormal
        trend: depth
        reason: "P5 of the fitted distribution"
      Silt:
        source: "A"
        method: standard_deviations
        standard_deviations: 0.5
        side: low
        distribution: normal
        reason: "Schneider's mean less half a standard deviation"
      Terrace:
        source: "Mohr-Coulomb fit (CD, CU)"
        method: fitted
        reason: "three CD and two CU stages"
      Alluvium:
        method: value
        value: 26
        reason: "CU tests on the same deposit, adjacent project"
      Fill:
        method: none
        reason: "removed under the structure"
  spt_n:
    values:
      Terrace: {method: value, value: 30, reason: "lowest N in the bearing zone"}
"""


def write(tmp_path, text, name="judgments.yaml"):
    path = tmp_path / name
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def entry(text):
    """A file with one selection entry, for Sand, of effective_friction_angle."""
    body = textwrap.indent(textwrap.dedent(text), " " * 8)
    return (
        "selection:\n"
        "  effective_friction_angle:\n"
        "    units: {value: deg}\n"
        "    values:\n"
        "      Sand:\n"
        f"{body}"
    )


def test_every_method_opens(tmp_path):
    read = ht.judgments(write(tmp_path, EVERY_METHOD)).read()
    assert read.judgments == {}
    selection = read.selections["effective_friction_angle"]
    assert selection.quantity == "angle"
    assert selection.unit == "deg"
    sand = selection.values["Sand"]
    assert (sand.method, sand.source) == ("characteristic", "A")
    assert sand.inputs == {"side": "low", "distribution": "normal", "estimate": "mean"}
    gravel = selection.values["Gravel"]
    assert gravel.inputs == {
        "side": "low",
        "distribution": "lognormal",
        "trend": "depth",
        "percentile": 5,
    }
    assert selection.values["Silt"].inputs["standard_deviations"] == 0.5
    terrace = selection.values["Terrace"]
    assert (terrace.method, terrace.source, terrace.inputs) == (
        "fitted",
        "Mohr-Coulomb fit (CD, CU)",
        {},
    )
    alluvium = selection.values["Alluvium"]
    assert (alluvium.method, alluvium.value, alluvium.source) == ("value", 26.0, None)
    fill = selection.values["Fill"]
    assert (fill.method, fill.reason) == ("none", "removed under the structure")


def test_a_pure_number_takes_no_units(tmp_path):
    read = ht.judgments(write(tmp_path, EVERY_METHOD)).read()
    spt = read.selections["spt_n"]
    assert (spt.quantity, spt.unit, spt.values["Terrace"].value) == ("count", None, 30)
    with pytest.raises(HangtuError, match=r"spt_n: .*pure number .*no units"):
        ht.judgments(
            write(
                tmp_path,
                """\
                selection:
                  spt_n:
                    units: {value: "1"}
                    values:
                      Terrace: {method: value, value: 30, reason: "lowest N"}
                """,
            )
        )


def test_the_repr_lists_each_selection(tmp_path):
    text = repr(ht.judgments(write(tmp_path, EVERY_METHOD)))
    assert "selection of effective_friction_angle, by geology_unit:" in text
    assert "Terrace: Mohr-Coulomb fit (CD, CU), fitted (three CD" in text
    assert "Alluvium: value 26 deg (CU tests" in text
    assert "Fill: none (removed under the structure)" in text


def test_a_selection_sits_beside_other_judgments(tmp_path):
    path = write(
        tmp_path,
        """\
        critical_state_friction_angle:
          units: {critical_state_friction_angle: deg}
          values:
            Terrace: {critical_state_friction_angle: 32, reason: "ring shear"}
        selection:
          effective_friction_angle:
            values:
              Terrace: {method: none, reason: "not used"}
        """,
    )
    read = ht.judgments(path).read()
    assert set(read.judgments) == {"critical_state_friction_angle"}
    assert set(read.selections) == {"effective_friction_angle"}


# Each error names the file, the parameter, the unit and the field (AC 1).
WHERE = r"judgments\.yaml, selection\.effective_friction_angle, values\.Sand"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            'source: "A"\nmethod: mean\nreason: "x"\n',
            rf"{WHERE}, method: 'mean' isn't a selection method",
        ),
        (
            'source: "A"\nreason: "x"\n',
            rf"{WHERE}: 'method' is missing",
        ),
        (
            'source: "A"\nmethod: characteristic\nestimate: mean\nside: low\n'
            'distribution: normal\npercentile: 5\nreason: "x"\n',
            rf"{WHERE}, percentile: method characteristic doesn't take "
            r"'percentile'.* It belongs to percentile\.",
        ),
        (
            'method: value\nvalue: 30\nsource: "A"\nreason: "x"\n',
            rf"{WHERE}, source: method value doesn't take 'source'",
        ),
        (
            'source: "A"\nmethod: characteristic\nside: low\n'
            'distribution: normal\nreason: "x"\n',
            rf"{WHERE}: representative\(\) with method='characteristic' needs "
            r"estimate=.* each argument is a field of the entry",
        ),
        (
            'source: "A"\nmethod: characteristic\nestimate: mean\n'
            'distribution: normal\nreason: "x"\n',
            rf"{WHERE}: 'side' is missing",
        ),
        (
            'source: "A"\nmethod: percentile\npercentile: 50.5\nside: low\n'
            'distribution: normal\nreason: "x"\n',
            rf"{WHERE}: representative\(\) with side='low' takes a percentile below",
        ),
        (
            'source: "A"\nmethod: standard_deviations\nstandard_deviations: "half"\n'
            'side: low\ndistribution: normal\nreason: "x"\n',
            rf"{WHERE}, standard_deviations: must be a number, not 'half'",
        ),
        (
            'source: "A"\nmethod: characteristic\nestimate: [mean]\nside: low\n'
            'distribution: normal\nreason: "x"\n',
            rf"{WHERE}, estimate: must be text",
        ),
        (
            'method: fitted\nreason: "x"\n',
            rf"{WHERE}: 'source' is missing",
        ),
        (
            'method: fitted\nsource: 3\nreason: "x"\n',
            rf"{WHERE}, source: must be a parameter_source label as text",
        ),
        (
            'method: value\nreason: "x"\n',
            rf"{WHERE}: 'value' is missing",
        ),
        (
            'method: value\nvalue: "26 deg"\nreason: "x"\n',
            rf"{WHERE}, value: must be a number",
        ),
        (
            'method: fitted\nsource: "A"\n',
            rf"{WHERE}: 'reason' is missing",
        ),
        (
            'method: none\nreason: "  "\n',
            rf"{WHERE}: 'reason' is missing",
        ),
    ],
)
def test_an_entry_error_names_where(tmp_path, text, message):
    with pytest.raises(HangtuError, match=message):
        ht.judgments(write(tmp_path, entry(text)))


def test_a_value_without_units_fails_on_open(tmp_path):
    """AC 5, second half."""
    path = write(
        tmp_path,
        """\
        selection:
          effective_friction_angle:
            values:
              Sand: {method: value, value: 26, reason: "adjacent project"}
        """,
    )
    with pytest.raises(HangtuError, match=rf"{WHERE}, value: has no unit.*deg"):
        ht.judgments(path)


def test_a_unit_of_another_dimension_fails(tmp_path):
    path = write(
        tmp_path,
        """\
        selection:
          undrained_shear_strength:
            units: {value: deg}
            values:
              Clay: {method: value, value: 25, reason: "adjacent project"}
        """,
    )
    with pytest.raises(
        HangtuError,
        match=r"judgments\.yaml, selection\.undrained_shear_strength, units\.value: "
        r".*stress",
    ):
        ht.judgments(path)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            "  su:\n    values: {}\n",
            r"selection\.su: 'su' isn't in the column registry",
        ),
        (
            "  geology_unit:\n    values: {}\n",
            r"selection\.geology_unit: 'geology_unit' isn't a numeric column",
        ),
        (
            "  effective_friction_angle:\n    project: {method: none, reason: x}\n",
            r"selection\.effective_friction_angle: a selection takes no project:",
        ),
        (
            "  effective_friction_angle:\n    by: depth\n    values: {}\n",
            r"selection\.effective_friction_angle, by: a selection is keyed by "
            r"geology_unit, not 'depth'",
        ),
        (
            "  effective_friction_angle:\n    units: {value: deg}\n",
            r"selection\.effective_friction_angle: 'values' is missing",
        ),
        (
            "  effective_friction_angle:\n    units: {phi: deg}\n    values: {}\n",
            r"selection\.effective_friction_angle, units: gives the unit of the "
            r"value entries only",
        ),
        (
            "  effective_friction_angle:\n    values:\n      1: {method: none, "
            "reason: x}\n",
            r"values: the key 1 isn't text",
        ),
        (
            "  effective_friction_angle:\n    methods: {}\n",
            r"'methods' isn't a section of a selection",
        ),
    ],
)
def test_a_selection_error_names_the_parameter(tmp_path, body, message):
    with pytest.raises(HangtuError, match=message):
        ht.judgments(write(tmp_path, f"selection:\n{body}"))


def test_the_selection_must_map_parameters(tmp_path):
    with pytest.raises(HangtuError, match=r"selection: must map each parameter"):
        ht.judgments(write(tmp_path, "selection: [effective_friction_angle]\n"))
