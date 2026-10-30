"""Statistics of test values (SPEC §5): plain functions returning a result object."""

from hangtu.stats._describe import describe
from hangtu.stats._fit import fit
from hangtu.stats._result import DescribeResult, FitResult

__all__ = ["DescribeResult", "FitResult", "describe", "fit"]
