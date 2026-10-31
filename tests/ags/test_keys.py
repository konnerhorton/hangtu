"""Location, sample and specimen keys (docs/data/ingest.md §5, AC 4)."""

from pathlib import Path

from hangtu.ags import _dictionary, _keys, _read

DATA = Path(__file__).parents[1] / "data" / "ags"


def _keys_of(path):
    ags = _read.read(path)
    dictionary, _ = _dictionary.for_file(ags)
    return ags, _keys.resolve(ags, dictionary)


def _rewrite(tmp_path, old, new):
    path = tmp_path / "site.ags"
    text = (DATA / "site_si.ags").read_bytes().decode("utf-8")
    assert old in text
    path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
    return path


def test_locations_and_samples_are_numbered_in_file_order():
    _, keys = _keys_of(DATA / "site_si.ags")
    assert keys.columns["LOCA"] == {"location_id": [1, 2, 3]}
    assert keys.columns["SAMP"]["location_id"] == [1, 1, 2, 2, 3, 1, 1]
    assert keys.columns["SAMP"]["sample_id"] == [1, 2, 3, 4, 5, 6, 7]


def test_every_child_row_in_the_good_files_has_its_keys():
    for name in ("site_si.ags", "site_us.ags", "site_v404.ags"):
        _, keys = _keys_of(DATA / name)
        for group, columns in keys.columns.items():
            for column, values in columns.items():
                assert None not in values, (name, group, column)


def test_which_keys_each_group_gets():
    _, keys = _keys_of(DATA / "site_si.ags")
    assert set(keys.columns["ISPT"]) == {"location_id"}
    assert set(keys.columns["FGHS"]) == {"location_id"}  # FGHS → FGHG → LOCA
    assert set(keys.columns["SAMP"]) == {"location_id", "sample_id"}
    assert set(keys.columns["GRAT"]) == {"location_id", "sample_id", "specimen_id"}
    assert set(keys.columns["XPPT"]) == {"location_id"}  # user-defined, parent LOCA
    assert "PROJ" not in keys.columns and "UNIT" not in keys.columns


def test_lab_groups_on_one_specimen_share_its_specimen_id():
    ags, keys = _keys_of(DATA / "site_si.ags")

    def specimen(group, sample):
        row = list(ags.tables[group]["SAMP_ID"]).index(sample)
        return keys.columns[group]["specimen_id"][row]

    assert (
        specimen("LLPL", "BH1-U1")
        == specimen("LNMC", "BH1-U1")
        == specimen("PTST", "BH1-U1")
    )
    assert specimen("LLPL", "BH1-U1") != specimen("LLPL", "BH2-U2")
    grat = keys.columns["GRAT"]["specimen_id"]
    assert len(set(grat)) == 1 and grat[0] == specimen("GRAG", "BH3-B1")


def test_specimen_table():
    _, keys = _keys_of(DATA / "site_si.ags")
    first = keys.specimens[0]
    assert first == {
        "specimen_id": 1,
        "sample_id": 1,
        "SPEC_REF": "1",
        "SPEC_DPTH": "1.60",
    }
    ids = [s["specimen_id"] for s in keys.specimens]
    assert ids == list(range(1, len(ids) + 1))
    combos = {(s["sample_id"], s["SPEC_REF"], s["SPEC_DPTH"]) for s in keys.specimens}
    assert len(combos) == len(ids)


def test_key_text_is_matched_exactly(tmp_path):
    # LLPL's first row writes SAMP_TOP as "1.5"; SAMP has "1.50".
    path = _rewrite(
        tmp_path,
        '"DATA","BH1","1.50","1","U","BH1-U1","1","1.60","48"',
        '"DATA","BH1","1.5","1","U","BH1-U1","1","1.60","48"',
    )
    _, keys = _keys_of(path)
    assert keys.columns["LLPL"]["sample_id"][0] is None
    assert keys.columns["LLPL"]["specimen_id"][0] is None
    assert keys.columns["LLPL"]["location_id"][0] == 1


def test_an_orphan_sample_has_null_keys_and_a_python_ags4_finding():
    ags, keys = _keys_of(DATA / "defects.ags")
    row = list(ags.tables["LLPL"]["SAMP_ID"]).index("BH2-D9")
    assert keys.columns["LLPL"]["sample_id"][row] is None
    assert keys.columns["LLPL"]["specimen_id"][row] is None
    assert keys.columns["LLPL"]["location_id"][row] == 2
    line = ags.tables["LLPL"]["_line"][row]
    assert any(f.rule == "V10c" and f.line == line for f in ags.findings)
    assert all(s["sample_id"] is not None for s in keys.specimens)


def test_user_defined_group_with_no_dict_entry_gets_only_location_id():
    _, keys = _keys_of(DATA / "defects.ags")
    assert keys.columns["XUND"] == {"location_id": [1]}


def test_groups_4_2_removed_get_keys_from_their_own_dictionary():
    _, keys = _keys_of(DATA / "site_v404.ags")
    assert set(keys.columns["IPRT"]) == {"location_id"}  # IPRT → IPRG → LOCA
    assert set(keys.columns["RUCS"]) == {"location_id", "sample_id", "specimen_id"}
