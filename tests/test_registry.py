import re
from importlib.resources import files

import pytest

import ags_kit as ak
from ags_kit import _config

REGISTRY = _config.load("columns.yaml")
COLUMNS = REGISTRY["columns"]
KINDS = _config.quantity_kinds()

FIELDS = {"description", "type", "quantity", "scale", "label", "ags", "used_by"}
# Bare symbols and abbreviations that CLAUDE.md "Naming" rules out as names.
BARE_SYMBOLS = {"su", "cu", "cc", "k", "ll", "pl", "pi", "li", "ic", "w", "n", "n60"}
BARE_SYMBOLS |= {"er", "unit", "gamma"}


def test_quantity_kinds_match_p00_table():
    assert set(KINDS) == {
        "length",
        "small_length",
        "particle_size",
        "stress",
        "unit_weight",
        "density",
        "hydraulic_conductivity",
        "percent",
        "dimensionless",
        "count",
        "angle",
    }


@pytest.mark.parametrize("name", COLUMNS)
def test_column_entry_follows_the_rules(name):
    entry = COLUMNS[name]
    assert re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)*", name)
    assert name not in BARE_SYMBOLS
    assert set(entry) <= FIELDS
    assert entry["description"]
    assert entry["type"] in {"number", "text", "bool"}
    assert entry["ags"]
    assert all(re.fullmatch(r"P\d\d", plot) for plot in entry["used_by"])
    if entry["type"] == "number":
        assert entry["quantity"] in KINDS
        assert entry["scale"] in {"ratio", "interval"}
        assert entry["label"]
    else:
        assert {"quantity", "scale", "label"}.isdisjoint(entry)


def test_names_are_unique():
    # yaml.safe_load keeps the last of two equal keys, so check the raw file.
    text = files("ags_kit").joinpath("columns.yaml").read_text(encoding="utf-8")
    names = re.findall(r"^  ([a-z0-9_]+):\s*$", text, flags=re.MULTILINE)
    assert len(names) == len(set(names)) == len(COLUMNS)


@pytest.mark.parametrize("name", REGISTRY["templates"])
def test_template_columns_are_registered(name):
    columns = REGISTRY["templates"][name]
    assert set(columns) <= set(COLUMNS)
    assert len(columns) == len(set(columns))


def test_columns_lists_every_column():
    table = ak.columns()
    assert list(table.columns) == [
        "name",
        "description",
        "quantity",
        "us_unit",
        "si_unit",
        "used_by",
    ]
    assert list(table["name"]) == list(COLUMNS)


def test_columns_for_a_template_follows_template_order():
    table = ak.columns("spt").set_index("name")
    assert list(table.index) == REGISTRY["templates"]["spt"]
    assert table.loc["depth", ["us_unit", "si_unit"]].tolist() == ["ft", "m"]
    assert table.loc["spt_penetration", ["us_unit", "si_unit"]].tolist() == [
        "in",
        "mm",
    ]
    assert table.loc["spt_n", ["quantity", "us_unit"]].tolist() == ["count", ""]
    assert table.loc["loca_id", "quantity"] == ""


def test_template_is_an_empty_frame_with_typed_columns():
    frame = ak.template("atterberg")
    assert frame.empty
    assert list(frame.columns) == REGISTRY["templates"]["atterberg"]
    assert frame["liquid_limit"].dtype == "float64"
    assert frame["loca_id"].dtype == "object"
    assert frame["non_plastic"].dtype == "bool"


def test_template_csv_has_one_header_row(tmp_path):
    path = tmp_path / "spt.csv"
    ak.template("spt").to_csv(path, index=False)
    assert path.read_text().splitlines() == [",".join(REGISTRY["templates"]["spt"])]


@pytest.mark.parametrize("call", [ak.template, ak.columns])
def test_unknown_template_lists_the_templates(call):
    with pytest.raises(ak.ColumnError, match=r"no template named 'sptt'.*spt"):
        call("sptt")
