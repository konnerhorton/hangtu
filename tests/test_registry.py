import re
import warnings
from importlib.resources import files
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import hangtu as ht
from hangtu import _config

REGISTRY = _config.load("columns.yaml")
COLUMNS = REGISTRY["columns"]
OVERLAY_FIELDS = REGISTRY["fields"]
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
        "modulus",
        "velocity",
        "percent",
        "dimensionless",
        "count",
        "angle",
    }


def _follows_naming_rules(name):
    return (
        re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)*", name) is not None
        and name not in BARE_SYMBOLS
    )


@pytest.mark.parametrize("name", COLUMNS)
def test_column_entry_follows_the_rules(name):
    entry = COLUMNS[name]
    assert _follows_naming_rules(name)
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


@pytest.mark.parametrize("name", OVERLAY_FIELDS)
def test_overlay_field_follows_the_rules(name):
    entry = OVERLAY_FIELDS[name]
    assert _follows_naming_rules(name)
    assert set(entry) == {"description", "type"}
    assert entry["description"]
    assert entry["type"] in {"number", "text", "bool"}


def test_names_are_unique():
    # yaml.safe_load keeps the last of two equal keys, so check the raw file.
    # Column and field names share one namespace.
    text = files("hangtu").joinpath("columns.yaml").read_text(encoding="utf-8")
    names = re.findall(r"^  ([a-z0-9_]+):\s*$", text, flags=re.MULTILINE)
    assert len(names) == len(set(names)) == len(COLUMNS) + len(OVERLAY_FIELDS)


@pytest.mark.parametrize("name", REGISTRY["templates"])
def test_template_columns_are_registered(name):
    columns = REGISTRY["templates"][name]
    assert set(columns) <= set(COLUMNS) | set(OVERLAY_FIELDS)
    assert len(columns) == len(set(columns))


def test_columns_lists_every_column():
    table = ht.columns()
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
    table = ht.columns("spt").set_index("name")
    assert list(table.index) == REGISTRY["templates"]["spt"]
    assert table.loc["depth", ["us_unit", "si_unit"]].tolist() == ["ft", "m"]
    assert table.loc["spt_penetration", ["us_unit", "si_unit"]].tolist() == [
        "in",
        "mm",
    ]
    assert table.loc["spt_n", ["quantity", "us_unit"]].tolist() == ["count", ""]
    assert table.loc["loca_id", "quantity"] == ""


def test_template_is_an_empty_frame_with_typed_columns():
    frame = ht.template("atterberg")
    assert frame.empty
    assert list(frame.columns) == REGISTRY["templates"]["atterberg"]
    assert frame["liquid_limit"].dtype == "float64"
    assert frame["loca_id"].dtype == "object"
    assert frame["non_plastic"].dtype == "bool"


PAIRS = ["depth_top", "depth_base", "elevation_top", "elevation_base"]


@pytest.mark.parametrize(
    ("name", "columns"),
    [
        ("strata", ["geology_unit", *PAIRS]),
        ("ranges", ["low", "high", "label", "source", *PAIRS]),
        ("design_lines", ["label", "depth", "elevation", "value"]),
        (
            "baseline",
            ["geology_unit", "property", "low", "central", "high", "source"],
        ),
    ],
)
def test_overlay_templates_follow_p01_and_p07(name, columns):
    frame = ht.template(name)
    assert list(frame.columns) == columns
    text = {"geology_unit", "label", "source", "property"}
    for column in frame.columns:
        assert frame[column].dtype == ("object" if column in text else "float64")


def test_columns_lists_overlay_fields_only_for_their_template():
    assert "low" not in set(ht.columns()["name"])
    table = ht.columns("ranges").set_index("name")
    assert list(table.index) == REGISTRY["templates"]["ranges"]
    assert table.loc["low", ["quantity", "us_unit", "used_by"]].tolist() == ["", "", ""]
    assert table.loc["depth_top", "us_unit"] == "ft"


def test_template_csv_has_one_header_row(tmp_path):
    path = tmp_path / "spt.csv"
    ht.template("spt").to_csv(path, index=False)
    assert path.read_text().splitlines() == [",".join(REGISTRY["templates"]["spt"])]


@pytest.mark.parametrize("call", [ht.template, ht.columns])
def test_unknown_template_lists_the_templates(call):
    with pytest.raises(ht.ColumnError, match=r"no template named 'sptt'.*spt"):
        call("sptt")


# --- Dataset templates (SPEC §2.6) ------------------------------------------------

DATA = Path(__file__).parent / "data" / "ags"
DATASETS = (
    "spt",
    "atterberg",
    "grain_size",
    "permeability",
    "stratigraphy",
    "particle_density",
    "density",
)
# Columns only hangtu can produce, so a CSV template leaves them out.
ONLY_HANGTU = {
    "source_line",
    "energy_source",
    "spt_n_capped",
    "liquidity_index",
    "consistency_index",
    "plasticity_class_uscs",
    "plasticity_class_bs5930",
    "particle_density_specimen_id",
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    db = tmp_path_factory.mktemp("templates") / "site.sqlite"
    p = ht.Project.from_ags(DATA / "site_us.ags", db=db, display_units="US")
    p.set_geology_map(DATA / "strata.csv")
    return p


@pytest.mark.parametrize("name", DATASETS)
def test_dataset_templates_follow_their_dataset(site, name):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        dataset = getattr(site, name)()
    expected = [column for column in dataset.columns if column not in ONLY_HANGTU]
    assert list(ht.template(name).columns) == expected


def test_filled_templates_feed_the_plots(site, tmp_path):
    read = {}
    for name in DATASETS:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            dataset = getattr(site, name)()
        path = tmp_path / f"{name}.csv"
        dataset[list(ht.template(name).columns)].to_csv(path, index=False)
        units = {
            column: unit
            for column, unit in dataset.attrs["units"].items()
            if column in ht.template(name).columns
        }
        read[name] = ht.read_csv(path, units=units)
    calls = [
        (ht.plot.spt_profile, read["spt"]),
        (ht.plot.spt_histogram, read["spt"]),
        (ht.plot.profile, read["permeability"], "hydraulic_conductivity"),
        (ht.plot.profile, read["atterberg"], "liquid_limit"),
        (ht.plot.geology_unit_comparison, read["atterberg"], "plasticity_index"),
    ]
    for plot, *args in calls:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            fig, _ax = plot(*args)
        plt.close(fig)
