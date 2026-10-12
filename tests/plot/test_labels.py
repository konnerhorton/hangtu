import pytest

from hangtu.plot.common import axis_label


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (("Elevation", "ft", "NAVD88"), "Elevation (ft, NAVD88)"),
        (("Depth", "m"), "Depth (m)"),
        (("Liquid limit, LL", "%"), "Liquid limit, LL (%)"),
        (("SPT N60",), "SPT N60"),
        (("Bulk unit weight, γ", "kN/m³"), "Bulk unit weight, γ (kN/m³)"),
        (("Elevation", None, "NAVD88"), "Elevation (NAVD88)"),
    ],
)
def test_axis_label(arguments, expected):
    assert axis_label(*arguments) == expected


def test_unknown_units_replace_the_unit():
    assert axis_label("k", unknown=True) == "k (units unknown)"
    assert axis_label("Elevation", "ft", "NAVD88", unknown=True) == (
        "Elevation (units unknown, NAVD88)"
    )
