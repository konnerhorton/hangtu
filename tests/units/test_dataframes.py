import pandas as pd
import pytest

import hangtu as ht
from hangtu.units import needs_units, parse_quantity, resolve_units


@pytest.fixture
def spt():
    return pd.DataFrame(
        {
            "loca_id": ["BH1", "BH1", "BH2"],
            "depth": [5.0, 2.5, 7.5],
            "spt_n": [12, 8, 30],
            "liquid_limit": [40.0, 35.0, 52.0],
        }
    )


def test_set_units_returns_a_new_frame_and_leaves_the_input_alone(spt):
    result = ht.set_units(spt, {"depth": "ft"})
    assert ht.units_of(result) == {"depth": "ft"}
    assert ht.units_of(spt) == {}
    assert result is not spt


def test_set_units_merges_with_declared_units(spt):
    result = ht.set_units(ht.set_units(spt, {"depth": "ft"}), {"liquid_limit": "%"})
    assert ht.units_of(result) == {"depth": "ft", "liquid_limit": "%"}


def test_units_of_returns_a_copy(spt):
    result = ht.set_units(spt, {"depth": "ft"})
    ht.units_of(result)["depth"] = "m"
    assert ht.units_of(result) == {"depth": "ft"}


def test_unknown_column_raises_listing_the_columns(spt):
    with pytest.raises(ht.ColumnError, match=r"\['dpth'\].*loca_id, depth"):
        ht.set_units(spt, {"dpth": "ft"})


def test_wrong_dimension_raises(spt):
    with pytest.raises(ht.UnitsError, match="Column 'depth' is a length"):
        ht.set_units(spt, {"depth": "kPa"})


def test_text_column_has_no_unit(spt):
    with pytest.raises(ht.UnitsError, match="'loca_id' holds text values"):
        ht.set_units(spt, {"loca_id": "m"})


def test_units_must_be_a_dict(spt):
    with pytest.raises(ht.UnitsError, match="must be a dict"):
        ht.set_units(spt, "ft")


def test_pint_only_unit_warns_at_the_users_line(spt):
    with pytest.warns(UserWarning, match="'depth' was read as foot") as record:
        ht.set_units(spt, {"depth": "feet"})
    assert record[0].filename == __file__


def test_unregistered_column_takes_any_known_unit(spt):
    frame = spt.assign(cone_resistance=[1.0, 2.0, 3.0])
    assert ht.units_of(ht.set_units(frame, {"cone_resistance": "MPa"})) == {
        "cone_resistance": "MPa"
    }


def test_read_csv_declares_units_and_passes_pandas_arguments(tmp_path, spt):
    path = tmp_path / "spt.csv"
    spt.to_csv(path, index=False, sep=";")
    result = ht.read_csv(path, units={"depth": "ft"}, sep=";")
    pd.testing.assert_frame_equal(result, spt)
    assert ht.units_of(result) == {"depth": "ft"}


def test_read_csv_without_units(tmp_path, spt):
    path = tmp_path / "spt.csv"
    spt.to_csv(path, index=False)
    assert ht.units_of(ht.read_csv(path)) == {}


@pytest.mark.parametrize(
    "operation",
    [
        lambda df: df[df["depth"] > 3],
        lambda df: df[["loca_id", "depth"]],
        lambda df: df.copy(),
        lambda df: df.sort_values("depth"),
    ],
    ids=["filter", "select", "copy", "sort"],
)
def test_units_survive_common_operations(spt, operation):
    assert ht.units_of(operation(ht.set_units(spt, {"depth": "ft"}))) == {"depth": "ft"}


def test_units_are_lost_after_merge(spt):
    ground = pd.DataFrame({"loca_id": ["BH1", "BH2"], "ground_level": [10.0, 12.0]})
    merged = ht.set_units(spt, {"depth": "ft"}).merge(ground, on="loca_id")
    assert ht.units_of(merged) == {}
    with pytest.warns(UserWarning, match="'depth' has no units"):
        resolve_units(merged, ["depth"])


# --- Resolution order (SPEC §2.6) ------------------------------------------------


def test_explicit_argument_beats_declared_units(spt):
    frame = ht.set_units(spt, {"depth": "ft"})
    assert resolve_units(frame, ["depth"], units={"depth": "m"}) == {"depth": "m"}
    assert resolve_units(frame, ["depth"]) == {"depth": "ft"}


def test_explicit_argument_is_checked(spt):
    with pytest.raises(ht.UnitsError, match="is a length"):
        resolve_units(spt, ["depth"], units={"depth": "psf"})


def test_unitless_kinds_resolve_to_none_without_a_warning(spt):
    assert resolve_units(spt, ["spt_n", "liquid_limit"]) == {
        "spt_n": None,
        "liquid_limit": None,
    }


def test_unknown_units_warn_once_per_column_for_a_plot(spt):
    with pytest.warns(UserWarning) as record:
        result = resolve_units(spt, ["depth", "spt_n"])
    assert result == {"depth": None, "spt_n": None}
    assert len(record) == 1
    assert 'ht.set_units(df, {"depth": "ft"})' in str(record[0].message)
    assert '"(units unknown)"' in str(record[0].message)


def test_unknown_units_raise_for_an_analysis(spt):
    with pytest.raises(ht.UnitsError, match=r"'depth' has no units\. Declare them"):
        resolve_units(spt, ["depth"], analysis=True)


def test_unregistered_column_uses_the_given_quantity(spt):
    frame = spt.assign(moisture=[20.0, 25.0, 30.0])
    assert resolve_units(frame, ["moisture"], quantities={"moisture": "percent"}) == {
        "moisture": None
    }
    with pytest.warns(UserWarning, match='"<unit>"'):
        resolve_units(frame, ["moisture"])


def test_needs_units():
    assert needs_units("depth")
    assert not needs_units("spt_n")
    assert not needs_units("unregistered", "percent")
    assert needs_units("unregistered")


# --- Values given as strings (P00 §4.3 #4) ---------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [("3 m", (3.0, "m")), ("10ft", (10.0, "ft")), ("-1.5e-5 m/s", (-1.5e-5, "m/s"))],
)
def test_parse_quantity(text, expected):
    assert parse_quantity(text) == expected


def test_parse_quantity_checks_the_dimension():
    with pytest.raises(ht.UnitsError, match="is a length"):
        parse_quantity("3 kPa", "length")


@pytest.mark.parametrize("text", ["m", "3", "three m", None])
def test_parse_quantity_needs_a_number_and_a_unit(text):
    with pytest.raises(ht.UnitsError, match="number followed by a unit"):
        parse_quantity(text)


def _read(tmp_path, text, **kwargs):
    path = tmp_path / "data.csv"
    path.write_text(text)
    return ht.read_csv(path, **kwargs)


@pytest.mark.parametrize(
    "cell, sign, number",
    [
        ("<5", "<", 5.0),
        ("> 200", ">", 200.0),
        ("<1e-9", "<", 1e-9),
        ("<.5", "<", 0.5),
        ("< -3", "<", -3.0),
    ],
)
def test_read_csv_reads_a_bound_as_a_number_and_a_qualifier(
    tmp_path, cell, sign, number
):
    df = _read(tmp_path, f"hydraulic_conductivity\n2\n{cell}\n")
    assert df["hydraulic_conductivity"].dtype == "float64"
    assert df["hydraulic_conductivity"].tolist() == [2.0, number]
    assert df["qualifier"].tolist() == ["", sign]


def test_read_csv_puts_a_remolded_bound_in_its_own_qualifier(tmp_path):
    df = _read(
        tmp_path,
        "undrained_shear_strength,remolded_undrained_shear_strength\n>120,<5\n80,10\n",
    )
    assert df["undrained_shear_strength"].tolist() == [120.0, 80.0]
    assert df["remolded_undrained_shear_strength"].tolist() == [5.0, 10.0]
    assert df["qualifier"].tolist() == [">", ""]
    assert df["remolded_qualifier"].tolist() == ["<", ""]
    assert "correlation_qualifier" not in df


def test_read_csv_keeps_a_matching_sign_and_fills_blanks(tmp_path):
    df = _read(tmp_path, "hydraulic_conductivity,qualifier\n<1e-9,<\n3,\n4,>\n")
    assert df["hydraulic_conductivity"].tolist() == [1e-9, 3.0, 4.0]
    assert df["qualifier"].tolist() == ["<", "", ">"]


def test_read_csv_raises_on_a_sign_that_differs_from_the_qualifier(tmp_path):
    with pytest.raises(ht.errors.ColumnError, match=r"Rows 1 .*'qualifier'"):
        _read(tmp_path, "hydraulic_conductivity,qualifier\n2,\n<1e-9,>\n")


def test_read_csv_raises_on_two_bounds_sharing_a_qualifier(tmp_path):
    text = "undrained_shear_strength,hydraulic_conductivity\n>120,<1e-9\n80,<1e-9\n"
    with pytest.raises(ht.errors.ColumnError) as raised:
        _read(tmp_path, text)
    message = str(raised.value)
    assert "Rows 0 " in message
    assert "'undrained_shear_strength' and 'hydraulic_conductivity'" in message


def test_read_csv_leaves_other_text_as_written(tmp_path):
    df = _read(
        tmp_path,
        "plasticity_index,depth,sample_reference\nNP,12 ft,<5\n<5,3,A\n12,4,B\n",
    )
    assert df["plasticity_index"].tolist() == ["NP", 5.0, "12"]
    assert df["qualifier"].tolist() == ["", "<", ""]
    assert df["depth"].tolist() == ["12 ft", "3", "4"]
    assert df["sample_reference"].tolist() == ["<5", "A", "B"]


def test_read_csv_leaves_an_unregistered_column_as_text(tmp_path):
    df = _read(tmp_path, "my_value\n<5\n6\n")
    assert df["my_value"].tolist() == ["<5", "6"]
    assert "qualifier" not in df


def test_read_csv_declares_units_on_a_split_column(tmp_path):
    df = _read(
        tmp_path,
        "hydraulic_conductivity\n<1e-9\n",
        units={"hydraulic_conductivity": "m/s"},
    )
    assert ht.units_of(df) == {"hydraulic_conductivity": "m/s"}


def test_read_csv_bound_is_censored_in_describe(tmp_path):
    df = _read(
        tmp_path,
        "undrained_shear_strength\n80\n>200\n120\n",
        units={"undrained_shear_strength": "kPa"},
    )
    row = ht.stats.describe(df, value="undrained_shear_strength").to_frame().iloc[0]
    assert row["count"] == 3
    assert row["count_at_least"] == 1
    assert row["count_text"] == 0
