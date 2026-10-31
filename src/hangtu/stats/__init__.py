"""Statistics of test values (SPEC §5): plain functions returning a result object."""

from hangtu.stats._compare import compare, compare_groups
from hangtu.stats._crosstab import crosstab
from hangtu.stats._describe import describe
from hangtu.stats._fit import fit
from hangtu.stats._result import (
    CompareGroupsResult,
    CompareResult,
    CrosstabResult,
    DescribeResult,
    FitResult,
)

__all__ = [
    "CompareGroupsResult",
    "CompareResult",
    "CrosstabResult",
    "DescribeResult",
    "FitResult",
    "compare",
    "compare_groups",
    "crosstab",
    "describe",
    "fit",
]
