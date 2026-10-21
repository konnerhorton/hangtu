import pytest

import hangtu as ht
from hangtu import vertical_datums


@pytest.mark.parametrize(
    "text",
    [
        "NAVD88",
        "NAVD 88",
        "navd-88",
        "navd_88",
        "North American Vertical Datum 1988",  # EPSG's name
        "North American Vertical Datum of 1988",  # a spelling
    ],
)
def test_names_of_navd88_match_its_short_name(text):
    assert vertical_datums.match(text) == "NAVD88"


@pytest.mark.parametrize("text", ["NAVD1988x", "MSL", "Site datum", "NAVD"])
def test_names_not_in_the_table_match_nothing(text):
    assert vertical_datums.match(text) is None


def test_every_entry_has_a_name_and_an_epsg_code():
    for short_name in ("NAVD88", "NGVD29", "CGVD28", "CGVD2013", "ODN"):
        entry = vertical_datums._datums[short_name]
        assert entry["name"]
        assert isinstance(entry["epsg"], int)


def test_add_vertical_datum_makes_a_name_match():
    ht.add_vertical_datum("ATD", name="Anytown datum")
    assert vertical_datums.match("anytown datum") == "ATD"
    assert vertical_datums.match("ATD") == "ATD"


def test_added_datum_lasts_for_the_session_only():
    # The autouse fixture resets the table after each test.
    assert vertical_datums.match("Anytown datum") is None


@pytest.mark.parametrize("short_name", ["NAVD88", "navd 88"])
def test_add_vertical_datum_rejects_an_existing_short_name(short_name):
    message = f'"{short_name}" already names the vertical datum NAVD88'
    with pytest.raises(ht.HangtuError, match=message):
        ht.add_vertical_datum(short_name, name="Another datum")


def test_add_vertical_datum_rejects_a_spelling_another_datum_has():
    with pytest.raises(ht.HangtuError, match="NGVD29"):
        ht.add_vertical_datum("X", name="X datum", spellings=["NGVD 1929"])


def test_add_vertical_datum_rejects_a_blank_name():
    with pytest.raises(ht.HangtuError, match="non-empty"):
        ht.add_vertical_datum("ATD", name=" ")
