import pytest

from hangtu import _config
from hangtu.ags._dictionary import standard
from hangtu.errors import HangtuError, UnitsError
from hangtu.qc._registry import INGEST_RULES, THRESHOLDS
from hangtu.qc._settings import DICTIONARY_VERSIONS, load


def _default_rules():
    return _config.load("qc/rules.yaml")["rules"]


def test_defaults_load():
    settings = load()
    g002 = settings.rule("G002")
    assert g002.title == "Gap in the geology log"
    assert g002.severity == "warning"
    assert g002.enabled is True
    assert g002.overridden is False
    assert g002.thresholds["depth_tolerance"].text == "0.01 m"
    assert g002.thresholds["depth_tolerance"].value == pytest.approx(0.01)
    l005 = settings.rule("L005").thresholds
    assert l005["neighbor_count"].value == 5
    assert l005["search_radius"].value == pytest.approx(200)
    k001 = settings.rule("K001").thresholds
    assert k001["lowest_hydraulic_conductivity"].value == pytest.approx(1e-12)
    assert settings.rule("A003").thresholds["highest_liquid_limit"].value == 150
    assert settings.rule("L004").thresholds["inclination_tolerance"].value == 2


def test_every_rule_has_title_and_severity():
    for rule_id, entry in _default_rules().items():
        assert entry["title"], rule_id
        if rule_id in ("V*", "VLOG"):
            assert entry["severity"] is None  # kept as stored at ingest
        else:
            assert entry["severity"] in ("error", "warning", "info"), rule_id


def test_yaml_and_code_name_the_same_thresholds():
    in_yaml = {
        rule_id: set(entry["thresholds"])
        for rule_id, entry in _default_rules().items()
        if entry.get("thresholds")
    }
    in_code = {rule_id: set(names) for rule_id, names in THRESHOLDS.items()}
    assert in_yaml == in_code


def test_ingest_rules_are_in_yaml():
    assert set(INGEST_RULES) <= set(_default_rules())


def test_default_min_fields_are_in_the_dictionaries():
    settings = load()
    for group, lists in settings.min_fields.items():
        for heading in lists["required"] + lists["recommended"]:
            assert any(
                (group, heading) in standard(v).headings for v in DICTIONARY_VERSIONS
            ), (group, heading)


def test_spec_key_anchor_is_written_out():
    llpl = load().min_fields["LLPL"]["required"]
    assert llpl == (
        "LOCA_ID",
        "SAMP_TOP",
        "SAMP_REF",
        "SAMP_TYPE",
        "SAMP_ID",
        "SPEC_REF",
        "SPEC_DPTH",
        "LLPL_LL",
        "LLPL_PL",
    )
    assert load().min_fields["LNMC"]["recommended"] == ()


def test_threshold_in_feet_equals_meters():
    feet = load(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}})
    meters = load(rules={"G002": {"thresholds": {"depth_tolerance": "0.01524 m"}}})
    in_feet = feet.rule("G002").thresholds["depth_tolerance"]
    assert in_feet.value == pytest.approx(
        meters.rule("G002").thresholds["depth_tolerance"].value
    )
    assert in_feet.text == "0.05 ft"  # kept as given for report.rules
    assert feet.rule("G002").overridden is True


def test_hydraulic_conductivity_in_cm_per_second():
    settings = load(
        rules={"K001": {"thresholds": {"highest_hydraulic_conductivity": "10 cm/s"}}}
    )
    threshold = settings.rule("K001").thresholds["highest_hydraulic_conductivity"]
    assert threshold.value == pytest.approx(0.1)


def test_override_merges_key_by_key():
    settings = load(rules={"L005": {"thresholds": {"neighbor_count": 3}}})
    l005 = settings.rule("L005")
    assert l005.thresholds["neighbor_count"].value == 3
    assert l005.thresholds["search_radius"].text == "200 m"
    assert l005.severity == "warning"
    assert l005.overridden is True
    assert settings.rule("L004").overridden is False


def test_severity_and_enabled_overrides():
    settings = load(rules={"A004": {"enabled": False}, "S003": {"severity": "warning"}})
    assert settings.rule("A004").enabled is False
    assert settings.rule("A004").overridden is True
    assert settings.rule("S003").severity == "warning"


def test_same_value_is_not_overridden():
    settings = load(rules={"G002": {"thresholds": {"depth_tolerance": "10 mm"}}})
    assert settings.rule("G002").overridden is False


def test_file_and_dict_give_the_same_settings(tmp_path):
    override = {
        "G002": {"thresholds": {"depth_tolerance": "0.05 ft"}},
        "A004": {"enabled": False},
    }
    path = tmp_path / "qc.yaml"
    path.write_text(
        "rules:\n"
        "  G002:\n"
        "    thresholds:\n"
        "      depth_tolerance: 0.05 ft\n"
        "  A004:\n"
        "    enabled: false\n",
        encoding="utf-8",
    )
    from_file, from_dict = load(rules=path), load(rules=override)
    assert from_file.rule("G002") == from_dict.rule("G002")
    assert from_file.rule("A004") == from_dict.rule("A004")
    without_top_key = tmp_path / "bare.yaml"
    without_top_key.write_text("A004:\n  enabled: false\n", encoding="utf-8")
    assert load(rules=str(without_top_key)).rule("A004").enabled is False


def test_min_fields_override_replaces_a_list():
    settings = load(min_fields={"LOCA": {"recommended": ["LOCA_TYPE"]}})
    assert settings.min_fields["LOCA"]["recommended"] == ("LOCA_TYPE",)
    assert settings.min_fields["LOCA"]["required"] == (
        "LOCA_ID",
        "LOCA_GL",
        "LOCA_FDEP",
    )


def test_min_fields_override_adds_a_group():
    settings = load(min_fields={"CONG": {"required": ["CONG_TYPE"]}})
    assert settings.min_fields["CONG"] == {
        "required": ("CONG_TYPE",),
        "recommended": (),
    }


def test_v_star_sets_every_v_rule():
    settings = load(rules={"V*": {"severity": "info"}})
    assert settings.rule("V10a").severity == "info"
    assert settings.rule("V10a").overridden is True
    assert settings.rule("VLOG").severity == "info"


def test_single_v_rule_wins_over_v_star():
    settings = load(
        rules={
            "V*": {"severity": "info"},
            "V10a": {"severity": "error", "enabled": False},
        }
    )
    assert settings.rule("V10a").severity == "error"
    assert settings.rule("V10a").enabled is False
    assert settings.rule("V4").severity == "info"
    assert settings.rule_ids[-1] == "V10a"  # listed after the rules.yaml rules


def test_v_rule_without_override_keeps_stored_severity():
    settings = load()
    assert settings.rule("V10a").severity is None
    assert settings.rule("V10a").overridden is False


# Each error in qc.md §2, with its message.


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"No QC rules file at .*nope\.yaml"):
        load(rules=tmp_path / "nope.yaml")


def test_bad_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("rules:\n  G002: [\n", encoding="utf-8")
    with pytest.raises(HangtuError, match=r"isn't valid YAML at line"):
        load(rules=path)


def test_unknown_rule():
    with pytest.raises(
        HangtuError, match=r"'G009' doesn't exist\. The rules are .*G002"
    ):
        load(rules={"G009": {"enabled": False}})


def test_unknown_key():
    with pytest.raises(
        HangtuError,
        match=r"G002 has no setting 'tolerance'\. The settings are enabled, severity, "
        r"thresholds",
    ):
        load(rules={"G002": {"tolerance": "0.05 ft"}})


def test_unknown_threshold():
    with pytest.raises(
        HangtuError,
        match=r"G002 has no threshold 'tolerance'\. Its thresholds are depth_tolerance",
    ):
        load(rules={"G002": {"thresholds": {"tolerance": "0.05 ft"}}})


def test_threshold_on_a_rule_without_any():
    with pytest.raises(HangtuError, match=r"L001 has no threshold 'x'\. It has no"):
        load(rules={"L001": {"thresholds": {"x": 1}}})


def test_threshold_on_an_ingest_rule():
    with pytest.raises(HangtuError, match=r"U001 is raised at ingest"):
        load(rules={"U001": {"thresholds": {"x": 1}}})


def test_unknown_severity():
    with pytest.raises(
        HangtuError, match=r"severity 'fatal'\. Use one of error, warning, info"
    ):
        load(rules={"G002": {"severity": "fatal"}})


def test_enabled_must_be_a_bool():
    with pytest.raises(HangtuError, match=r"enabled must be true or false"):
        load(rules={"G002": {"enabled": "no"}})


def test_wrong_dimension():
    with pytest.raises(
        UnitsError, match=r"G002, threshold depth_tolerance: .*is a length"
    ):
        load(rules={"G002": {"thresholds": {"depth_tolerance": "2 deg"}}})


def test_percent_is_not_an_angle():
    with pytest.raises(
        UnitsError, match=r"L004, threshold inclination_tolerance is an"
    ):
        load(rules={"L004": {"thresholds": {"inclination_tolerance": "2 %"}}})


def test_plain_number_for_a_length():
    with pytest.raises(
        UnitsError, match=r'depth_tolerance needs a unit.*depth_tolerance: "0\.01 m"'
    ):
        load(rules={"G002": {"thresholds": {"depth_tolerance": 0.05}}})


def test_unit_on_a_count():
    with pytest.raises(
        UnitsError, match=r"neighbor_count is a count and takes a plain"
    ):
        load(rules={"L005": {"thresholds": {"neighbor_count": "5 m"}}})


def test_unknown_min_fields_group():
    with pytest.raises(
        HangtuError, match=r"group .LOCX.*Did you mean LOCA.*The dictionary groups are"
    ):
        load(min_fields={"LOCX": {"required": ["LOCX_ID"]}})


def test_unknown_min_fields_heading():
    with pytest.raises(
        HangtuError,
        match=r"heading 'LOCA_XYZ' in LOCA.*The headings of LOCA are LOCA_ID",
    ):
        load(min_fields={"LOCA": {"required": ["LOCA_XYZ"]}})


def test_unknown_min_fields_list():
    with pytest.raises(HangtuError, match=r"no list 'optional'"):
        load(min_fields={"LOCA": {"optional": ["LOCA_TYPE"]}})
