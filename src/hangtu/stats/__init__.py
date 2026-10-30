"""Statistics of test values (SPEC §5): plain functions returning a result object."""

from hangtu.stats._compare import compare
from hangtu.stats._describe import describe
from hangtu.stats._fit import fit
from hangtu.stats._result import CompareResult, DescribeResult, FitResult

__all__ = ["CompareResult", "DescribeResult", "FitResult", "compare", "describe", "fit"]
