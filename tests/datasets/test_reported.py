"""Reading GRAG headings as a stated system's ranges (datasets.md §6.13).

Golden values G1 to G7 of docs/work/grag-fractions.md, on hand-built frames.
"""

import numpy as np
import pandas as pd
import pytest

from hangtu.analysis._fractions import fraction_system
from hangtu.datasets._reported import (
    HEADINGS,
    heading_ranges,
    no_system_message,
    other_boundaries_message,
    reported_fractions,
    uscs_blank_message,
)

N = None
#: GRAG_CLAY, GRAG_SILT, GRAG_FINE, GRAG_SAND, GRAG_GRAV, GRAG_VCRE.
GOLDEN = {
    "G1": [N, N, 33.0, 45.0, 22.0, N],
    "G2": [N, N, 11.0, 39.0, 40.0, 10.0],
    "G3": [N, N, 3.0, 87.0, 10.0, N],
    "G4": [8.0, 20.0, N, 40.0, 32.0, 0.0],
    "G5": [8.0, 25.0, N, 45.0, 22.0, N],
    "G6": [N, N, 31.5, 45.0, 22.0, N],
    "G7": [N, N, 30.0, 45.0, 20.0, N],
}


def _frame(*names):
    rows = [[np.nan if v is None else v for v in GOLDEN[name]] for name in names]
    return pd.DataFrame(rows, columns=list(HEADINGS), index=list(names))


def _read(names, requested, stated):
    return reported_fractions(_frame(*names), fraction_system(requested)[1], stated)


def _values(contents, name):
    return {
        column.removesuffix("_content"): (None if np.isnan(v) else v)
        for column, v in contents.loc[name].items()
    }


def test_astm_uscs_as_stated():
    found = _read(["G1", "G2", "G3", "G5", "G6", "G7"], "astm_uscs", "astm_uscs")
    expected = {
        # Blank VCRE, 22 + 45 + 33 = 100: cobbles and boulders 0 (rule 4).
        "G1": dict(fines=33.0, sand=45.0, gravel=22.0, cobbles=0.0, boulders=0.0),
        # VCRE 10 spans cobbles and boulders, so neither is given (3c).
        "G2": dict(fines=11.0, sand=39.0, gravel=40.0, cobbles=None, boulders=None),
        "G3": dict(fines=3.0, sand=87.0, gravel=10.0, cobbles=0.0, boulders=0.0),
        # FINE blank: SILT 25 + CLAY 8.
        "G5": dict(fines=33.0, sand=45.0, gravel=22.0, cobbles=0.0, boulders=0.0),
        # 98.5 is within 2 of 100.
        "G6": dict(fines=31.5, sand=45.0, gravel=22.0, cobbles=0.0, boulders=0.0),
        # 95 isn't.
        "G7": dict(fines=30.0, sand=45.0, gravel=20.0, cobbles=None, boulders=None),
    }
    for name, values in expected.items():
        assert _values(found.contents, name) == values, name
    # The stated system's own boundaries: nothing is blank for that reason.
    assert (found.other_boundaries, found.blank_rows) == ([], 0)


def test_g1_asked_as_aashto():
    found = _read(["G1"], "aashto", "astm_uscs")
    assert _values(found.contents, "G1") == dict(
        silt_clay=33.0, fine_sand=None, coarse_sand=None, gravel=None, boulders=0.0
    )
    assert found.other_boundaries == ["fine_sand", "coarse_sand", "gravel"]
    assert found.blank_rows == 1


def test_g4_as_iso14688():
    found = _read(["G4"], "iso14688", "iso14688")
    assert _values(found.contents, "G4") == dict(
        clay=8.0, silt=20.0, sand=40.0, gravel=32.0, cobbles=0.0, boulders=0.0
    )
    assert found.other_boundaries == []


def test_g4_asked_as_astm_uscs():
    # No ISO boundary is 0.075 or 4.75 mm; cobbles and boulders lie inside
    # GRAG_VCRE (63 mm and up), which is 0 (rule 3b).
    found = _read(["G4"], "astm_uscs", "iso14688")
    assert _values(found.contents, "G4") == dict(
        fines=None, sand=None, gravel=None, cobbles=0.0, boulders=0.0
    )
    assert found.other_boundaries == ["fines", "sand", "gravel"]
    assert found.blank_rows == 1


@pytest.mark.parametrize("requested", ["astm_uscs", "aashto", "iso14688"])
def test_no_stated_system_leaves_every_fraction_blank(requested):
    found = _read(list(GOLDEN), requested, None)
    assert found.contents.isna().all().all()
    assert list(found.contents.index) == list(GOLDEN)
    assert (found.other_boundaries, found.blank_rows) == ([], 0)


def test_a_system_of_your_own_is_read_by_its_boundaries():
    mine = {
        "name": "two_bands",
        "fractions": [
            {"name": "fines", "lower": 0, "upper": 0.075},
            {"name": "coarse_material", "lower": 0.075, "upper": None},
        ],
    }
    # coarse_material is SAND + GRAV + VCRE, blank where VCRE is blank (G7).
    found = _read(["G1", "G7"], mine, "astm_uscs")
    assert _values(found.contents, "G1") == dict(fines=33.0, coarse_material=67.0)
    assert _values(found.contents, "G7") == dict(fines=30.0, coarse_material=None)
    assert found.other_boundaries == []


def test_heading_ranges_of_iso14688():
    assert heading_ranges("iso14688")["GRAG_VCRE"] == (63.0, np.inf)
    assert heading_ranges("iso14688")["GRAG_FINE"] == (0.0, 0.063)


def test_messages():
    assert no_system_message(3).startswith(
        "3 gradings are reported only as fractions (GRAG), and their fractions "
        "are blank because the project's GRAG fraction system isn't set."
    )
    assert no_system_message(3).endswith(
        'for example p.settings.grag_fraction_system = "astm_uscs".'
    )
    assert no_system_message(1).startswith("1 grading is reported only")
    assert other_boundaries_message(
        3, "astm_uscs", "aashto", ["fine_sand", "coarse_sand", "gravel"]
    ) == (
        "3 gradings are reported as astm_uscs fractions (GRAG), so the aashto "
        "fractions with other boundaries are blank: fine_sand, coarse_sand, gravel."
    )
    assert uscs_blank_message(3, "iso14688", ["fines", "sand", "gravel"]).startswith(
        "3 samples' gradings are reported as iso14688 fractions (GRAG), so their "
        "USCS fractions"
    )
