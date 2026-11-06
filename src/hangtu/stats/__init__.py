"""Statistics of test values (SPEC §5): plain functions returning a result object."""

from hangtu.stats._compare import compare, compare_groups
from hangtu.stats._compare_sources import SourceComparison, compare_sources
from hangtu.stats._crosstab import crosstab
from hangtu.stats._describe import describe
from hangtu.stats._fit import fit
from hangtu.stats._representative import representative
from hangtu.stats._result import (
    CompareGroupsResult,
    CompareResult,
    CrosstabResult,
    DescribeResult,
    FitResult,
    RepresentativeResult,
)
from hangtu.stats._select import SelectionResult, select

__all__ = [
    "CompareGroupsResult",
    "CompareResult",
    "CrosstabResult",
    "DescribeResult",
    "FitResult",
    "RepresentativeResult",
    "SelectionResult",
    "SourceComparison",
    "compare",
    "compare_groups",
    "compare_sources",
    "crosstab",
    "describe",
    "fit",
    "representative",
    "select",
]
