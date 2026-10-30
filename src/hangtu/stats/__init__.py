"""Statistics of test values (SPEC §5): plain functions returning a result object."""

from hangtu.stats._compare import compare, compare_groups
from hangtu.stats._describe import describe
from hangtu.stats._fit import fit
from hangtu.stats._result import (
    CompareGroupsResult,
    CompareResult,
    DescribeResult,
    FitResult,
)

__all__ = [
    "CompareGroupsResult",
    "CompareResult",
    "DescribeResult",
    "FitResult",
    "compare",
    "compare_groups",
    "describe",
    "fit",
]
