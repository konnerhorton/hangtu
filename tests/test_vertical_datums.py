import pandas as pd
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


# --- from_locations (ingest.md §7) ---------------------------------------------


def _loca(*rows, local=False):
    """LOCA as (LOCA_ID, LOCA_GL, LOCA_DATM[, LOCA_LOCZ])."""
    columns = ["LOCA_ID", "LOCA_GL", "LOCA_DATM"] + (["LOCA_LOCZ"] if local else [])
    return pd.DataFrame([list(row) for row in rows], columns=columns)


def test_one_known_datum_in_every_hole_is_the_project_datum():
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88"], ["BH2", 11.0, "NAVD88"])
    )
    assert found.datum == "NAVD88"
    assert found.reason is None
    assert found.names == {"NAVD88": ("BH1", "BH2")}


def test_spellings_are_stored_as_the_short_name():
    # AC 2.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD 88"], ["BH2", 11.0, "navd88"])
    )
    assert found.datum == "NAVD88"


def test_holes_with_no_ground_level_are_ignored():
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88"], ["BH2", None, None], ["BH3", None, "NGVD29"])
    )
    assert found.datum == "NAVD88"
    assert found.names == {"NAVD88": ("BH1",)}


def test_a_blank_datum_sets_nothing():
    # AC 3.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88"], ["BH2", 11.0, " "], ["BH3", 12.0, None])
    )
    assert (found.datum, found.reason, found.holes) == (None, "blank", ("BH2", "BH3"))


def test_a_local_level_sets_nothing():
    # AC 3. Its LOCA_DATM may be the local level's datum, so it isn't a name.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88", None], ["BH2", 11.0, "SD", 2.5], local=True)
    )
    assert (found.datum, found.reason, found.holes) == (None, "local_level", ("BH2",))
    assert found.names == {"NAVD88": ("BH1",)}


def test_different_datums_set_nothing():
    # AC 3.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88"], ["BH2", 11.0, "NGVD 29"], ["BH3", 9.0, "NAVD88"])
    )
    assert (found.datum, found.reason) == (None, "different")
    assert found.names == {"NAVD88": ("BH1", "BH3"), "NGVD29": ("BH2",)}


def test_a_name_not_in_the_table_sets_nothing():
    # AC 2. Unknown names are grouped by their normalized text.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "Anytown datum"], ["BH2", 11.0, "ANYTOWN DATUM"])
    )
    assert (found.datum, found.reason) == (None, "unknown")
    assert found.names == {"Anytown datum": ("BH1", "BH2")}


def test_reasons_are_checked_in_order():
    # A blank comes before two datums.
    found = vertical_datums.from_locations(
        _loca(["BH1", 10.0, "NAVD88"], ["BH2", 11.0, "NGVD29"], ["BH3", 9.0, None])
    )
    assert found.reason == "blank"


@pytest.mark.parametrize(
    "loca",
    [
        pd.DataFrame({"LOCA_ID": ["BH1"], "LOCA_GL": [10.0]}),  # no LOCA_DATM
        _loca(["BH1", 10.0, None], ["BH2", 11.0, None]),  # all blank
        _loca(["BH1", None, "NAVD88"]),  # no hole with a ground level
        pd.DataFrame(),  # no LOCA
    ],
)
def test_nothing_to_read(loca):
    assert vertical_datums.from_locations(loca) == vertical_datums.FileDatum()


def test_same_compares_known_names_by_short_name_and_others_by_text():
    assert vertical_datums.same("NAVD 88", "North American Vertical Datum of 1988")
    assert vertical_datums.same("Site datum", "site-datum")
    assert not vertical_datums.same("NAVD88", "NGVD29")
