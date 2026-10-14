from hangtu import _config, qc  # noqa: F401  (importing qc registers the rules)
from hangtu.qc._registry import RULES
from hangtu.qc._settings import is_ingest_rule

# Rules in rules.yaml whose code comes in a later build step (plan Builds 7-8).
PENDING = {
    *("P001", "P002", "P003", "P004", "K001"),
    *("C001", "C002"),
}


def test_every_computed_rule_has_code():
    in_yaml = {
        rule_id
        for rule_id in _config.load("qc/rules.yaml")["rules"]
        if not is_ingest_rule(rule_id)
    }
    assert set(RULES) == in_yaml - PENDING
    assert not set(RULES) & PENDING
