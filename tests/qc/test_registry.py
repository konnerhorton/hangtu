from hangtu import _config, qc  # noqa: F401  (importing qc registers the rules)
from hangtu.qc._registry import RULES
from hangtu.qc._settings import is_ingest_rule


def test_every_computed_rule_has_code():
    in_yaml = {
        rule_id
        for rule_id in _config.load("qc/rules.yaml")["rules"]
        if not is_ingest_rule(rule_id)
    }
    assert set(RULES) == in_yaml
