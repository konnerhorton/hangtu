"""Triaxial stresses at failure (datasets.md §6.10; M11 a)."""

#: The AGS pick lists ``TREG_TYPE`` and ``TRIG_TYPE`` (4.2, and 4.0.4's
#: ``UNC``), by what a rule needs to know of a test. A type the lists don't
#: have is none of these.
DRAINED = frozenset({"CD", "CDM", "CIDC", "CADC"})
UNDRAINED = frozenset({"CU", "CUM", "CIUC", "CIUCM", "CAUC", "CAUE", "UUP"})
EXTENSION = frozenset({"CIDE", "CADE", "CAUE"})
MULTISTAGE = frozenset({"CDM", "CUM", "CIUCM", "UUM"})
#: Every type in the two pick lists: ``TREG_TYPE``'s, then ``TRIG_TYPE``'s.
LISTED = DRAINED | UNDRAINED | EXTENSION | {"UU", "UUM", "UNC"}
