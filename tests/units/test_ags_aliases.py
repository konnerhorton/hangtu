"""AGS4 dictionary unit strings in the alias table (docs/data/ingest.md §7)."""

import pytest

from hangtu import units
from hangtu.ags import _dictionary, _read

DATE_AND_TIME = ("DT", "T")


def _dictionary_units():
    found = set()
    for version in _read.VERSIONS:
        for heading in _dictionary.standard(version).headings.values():
            if heading.unit and heading.type not in DATE_AND_TIME:
                found.add(heading.unit)
    return sorted(found)


@pytest.mark.parametrize("text", _dictionary_units())
def test_every_dictionary_unit_is_an_alias(text):
    unit, from_alias = units._lookup(text)
    assert unit is not None and from_alias


def test_aliases_read_as_expected():
    assert units._lookup("Bar")[0] == units._lookup("bar")[0] == units.ureg.Unit("bar")
    assert units._lookup("m2/yr")[0] == units.ureg.Unit("meter**2 / year")
    assert units._lookup("kg/m3")[0] == units.ureg.Unit("kilogram / meter**3")
    assert units._lookup("µS/cm")[0] == units._lookup("uS/cm")[0]


def test_date_and_time_formats_are_not_aliases():
    # pint reads "hh:mm" as hectohours times millimeters (plan decision 6).
    for text in ("hh:mm", "hh:mm:ss", "mm:ss", "yyyy-mm-dd"):
        assert text not in units._aliases
