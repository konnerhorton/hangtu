"""``fit()``: probability distributions fitted to a property's values, ranked by AICc.

Spec: docs/work/m15c-fit.md. The rows are chosen by ``_rows``, as ``describe()``
chooses them.
"""

import math
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as _stats

from hangtu._data import text_values
from hangtu.errors import HangtuError, warn
from hangtu.stats import _rows
from hangtu.stats._result import FitResult
from hangtu.stats._rows import COUNTS

#: The candidates, in the order that breaks a tie in AICc (Decision 2).
DISTRIBUTIONS = ("normal", "lognormal", "gamma", "weibull", "beta")
SCIPY_NAMES = {
    "normal": "norm",
    "lognormal": "lognorm",
    "gamma": "gamma",
    "weibull": "weibull_min",
    "beta": "beta",
}
#: Located at 0, so they have no density at or below it.
POSITIVE = ("lognormal", "gamma", "weibull")
#: Fitted parameters per distribution (k in AICc).
PARAMETER_COUNT = 2
#: Fewer uncensored values per group is no fit; fewer than ``FEW`` warns.
MIN_COUNT = 4
FEW = 10
#: A normal fit putting more than this below the lower bound gets a note.
BELOW_BOUND_NOTE = 0.01
BURNHAM_ANDERSON = (
    "AICc ranks the fits within each group (Burnham & Anderson 2004, p. 271): "
    "ΔAICc ≤ 2 is substantial support, 4 to 7 considerably less, above 10 "
    "essentially none, so fits within 2 of the best aren't a clear winner."
)


@dataclass(frozen=True)
class Values:
    """One group's values: measured, and censored on each side."""

    exact: np.ndarray
    #: Known only to be at most these (``<x``).
    left: np.ndarray
    #: Known only to be at least these (a refusal, ``>x``).
    right: np.ndarray

    @property
    def count(self) -> int:
        return self.exact.size + self.left.size + self.right.size

    def all(self) -> np.ndarray:
        return np.concatenate([self.exact, self.left, self.right])


def fit(
    data: pd.DataFrame | pd.Series | Sequence[float] | np.ndarray,
    *,
    value: str | None = None,
    by: str | Sequence[str] | None = None,
    distributions: Sequence[str] | None = None,
    bounds: str | tuple[float | None, float | None] = "auto",
    pool: str | Sequence[str] | None = None,
    include_assumed: bool = False,
    units: str | Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> FitResult:
    r"""Fit probability distributions to measured or estimated values, by group.

    Fits each candidate distribution by maximum likelihood, ranks them by
    AICc and says how much probability each puts beyond a physical bound, so
    the choice of distribution for a property is made on the data and
    recorded. It never selects a design value.

    **Candidates** (each with two fitted parameters, $k = 2$):

    - ``normal``: mean and standard deviation ($n$, not $n - 1$: the
      maximum-likelihood estimates);
    - ``lognormal``: median and σ of ln x, located at 0. A normal fit to the
      logs is this fit, so ``fit()`` has no ``log=``;
    - ``gamma``: shape and scale, located at 0;
    - ``weibull``: shape and scale, located at 0, fitted as the Gumbel
      (minimum) distribution of ln x, which is the same fit;
    - ``beta``: α and β on ``bounds``, fitted when both bounds are given.

    Lognormal, gamma and Weibull have no density at or below 0: a group with
    a value there isn't fitted with them, and a note says so with the count.
    Beta likewise needs every value strictly inside the bounds. A fit that
    fails is left out of its group with SciPy's message in the notes.

    **Ranking** (Burnham & Anderson 2004, pp. 270-272): with $\ln L$ the
    log-likelihood at the fit and $n$ the values fitted,
    $\mathrm{AICc} = 2k - 2\ln L + 2k(k + 1)/(n - k - 1)$;
    $\Delta_i = \mathrm{AICc}_i - \mathrm{AICc}_{\min}$; the Akaike weight
    $w_i = e^{-\Delta_i/2} / \sum_r e^{-\Delta_r/2}$. Fits are ranked 1, 2, …
    within each group; AICc means nothing across groups. As a rough guide,
    Δ ≤ 2 is substantial support, 4 to 7 considerably less, above 10
    essentially none.

    **Bounds:** most properties can't be negative, and a normal fit puts
    some probability there. Each fit reports
    ``probability_below_lower_bound`` $= F(\text{low})$ and
    ``probability_above_upper_bound`` $= 1 - F(\text{high})$, and a normal
    fit with more than 1 % below the lower bound gets a note.

    **At least 4 values per group** (AICc needs $n > k + 1$): a group with
    fewer has no fits, with a warning; one with fewer than 10 is fitted with
    a warning that the ranking says little. No group to fit is an error.

    The SPT N is a count but is fitted as continuous, as is usual.

    **Rows are chosen as by** :func:`describe`: non-plastic, assumed, text,
    blank and band rows are left out and counted; sources aren't pooled
    unawares (``pool=``); the counts add up to the group's rows.

    Parameters
    ----------
    data : pandas.DataFrame, pandas.Series, list or array
        The values. A DataFrame needs ``value=``; a Series is its own value
        (its name is the column). ``by=`` needs a DataFrame.
    value : str
        The column to fit, e.g. ``"undrained_shear_strength"``.
    by : str or list of str, optional
        The column(s) to group by, e.g. ``"geology_unit"``. Each group is
        fitted on its own. Groups are ordered as by :func:`describe`.
    distributions : list of str, optional
        Names from ``"normal"``, ``"lognormal"``, ``"gamma"``, ``"weibull"``
        and ``"beta"``. None fits the first four, and beta too when
        ``bounds`` has two ends.
    bounds : "auto" or (low, high)
        The physical bounds of the value, in its (display) units, either end
        None. ``"auto"`` gives ``(0, None)`` for a column the registry marks
        ``scale: ratio`` (``ht.columns()``), and ``(None, None)`` otherwise.
        Pass ``(0, 100)`` for a percentage: the registry records no upper
        bounds. A value outside the bounds raises.
    pool : str or list of str, optional
        Source columns to pool across on purpose, e.g. ``["source"]``, as
        in :func:`describe`.
    include_assumed : bool
        Fit assumed values with the rest. They are still counted.
    units : str or dict, optional
        The value's unit, e.g. ``"kPa"``, or ``{column: unit}``, as in
        :func:`describe`. A list or array without it is fitted with "(units
        not given)".
    display_units : {"US", "SI"}, optional
        Convert the values to this system's display unit before fitting.
        None keeps the column's unit. Fitted parameters with a unit, and
        ``bounds``, are in these units; AICc shifts with the unit, but its
        differences, the weights and the ranks don't.

    Returns
    -------
    FitResult
        ``.to_frame()`` has one row per group and distribution, ranked.
        ``.distribution(name)`` gives the fitted SciPy distribution.
        ``print(result)`` shows the same numbers with their units and notes.

    Raises
    ------
    ColumnError
        For a missing column, or a column that holds no numbers.
    HangtuError
        For an unknown distribution, beta without two bounds, a value
        outside the bounds, no group with 4 values, rows from different
        sources in one group, or a ``pool=`` column that isn't a source.
    UnitsError
        For a value column whose unit is unknown.

    References
    ----------
    Burnham, K.P. & Anderson, D.R. (2004). Multimodel inference:
    understanding AIC and BIC in model selection. *Sociological Methods &
    Research* 33(2), 261-304.

    Examples
    --------
    >>> strength = p.strength()
    >>> result = ht.stats.fit(strength, value="undrained_shear_strength",
    ...                       by="geology_unit")
    >>> result.to_frame()
    """
    function = "fit()"
    read = _rows.read_input(data, value, by, pool, units, function)
    frame, value = read.frame, read.value
    pooled = _rows.check_pool(pool, read, function)
    numbers, texts = text_values(frame, read.column)
    numbers, unit = _rows.convert(numbers, read, display_units, function)
    low, high = _check_bounds(bounds, value)
    names = _check_distributions(distributions, low, high)
    flags = (
        _rows.read_flags(frame, read.column, function)
        if value is not None
        else _rows.Flags.none(frame)
    )
    reasons, marks = _rows.choose_rows(
        numbers, texts, flags, include_assumed=include_assumed, positive_only=False
    )
    included = reasons == ""
    _check_inside(numbers[included], low, high, read.column)

    keys = _rows.group_keys(frame, read.by)
    _rows.check_sources(frame, keys, included, read, pooled, function)
    groups, notes, too_few, few = [], [], [], []
    for key, rows in keys:
        label = ", ".join(map(str, key.values())) or "All"
        chosen = rows & included
        values = Values(exact=numbers[chosen], left=np.empty(0), right=np.empty(0))
        counts = {
            "count": values.count,
            "count_censored": values.left.size + values.right.size,
            **{
                name: int(marks.get(name, reasons == name)[rows].sum())
                for name in COUNTS
            },
        }
        group = {
            "key": key,
            "counts": counts,
            "fits": [],
            "left_out": {},
            "reason": None,
            "text": _rows.spellings(texts[rows]),
            "sources": {
                column: _rows.breakdown(frame.loc[chosen, column]) for column in pooled
            },
        }
        groups.append(group)
        if values.exact.size < MIN_COUNT:
            group["reason"] = (
                f"fewer than {MIN_COUNT} uncensored values ({values.exact.size})"
            )
            too_few.append(f"{label} ({values.exact.size})")
            continue
        if values.exact.size < FEW:
            few.append(f"{label} ({values.exact.size})")
        group["fits"], group["left_out"] = _fit_group(values, names, low, high)
        notes.extend(_group_notes(group, label, values, low))

    _rows.warn_left_out(reasons, read.column, function)
    _rows.warn_text(texts, read.column, function)
    if len(too_few) == len(groups):
        raise HangtuError(
            f"fit() needs at least {MIN_COUNT} uncensored values of {read.column!r} "
            f"in a group to fit two parameters and rank them by AICc, and no group "
            f"has them: {', '.join(too_few)}. Group more widely, or report the "
            "values themselves."
        )
    if too_few:
        warn(
            f"fit() has fewer than {MIN_COUNT} uncensored values of {read.column!r} "
            f"in: {', '.join(too_few)}. Those groups aren't fitted; their rows in "
            "the result have only the counts."
        )
    if few:
        warn(
            f"fit() has fewer than {FEW} uncensored values of {read.column!r} in: "
            f"{', '.join(few)}. The ranking and the goodness-of-fit check have "
            "little power with so few values: several distributions may fit "
            "equally well."
        )
    return FitResult(
        kind="property",
        function="fit",
        value=value,
        unit=unit,
        notes=tuple(
            _notes(
                notes, groups, read, pooled, include_assumed, unit_given=read.unit_given
            )
        ),
        judgments=dict(frame.attrs.get("judgments", {})),
        hangtu_version=version("hangtu"),
        by=tuple(read.by),
        pooled=tuple(pooled),
        include_assumed=include_assumed,
        bounds=(low, high),
        distributions=names,
        groups=tuple(groups),
    )


def _check_bounds(bounds: Any, value: str | None) -> tuple[float | None, float | None]:
    """Return ``(low, high)``, from the registry's scale for ``"auto"`` (Decision 1)."""
    if isinstance(bounds, str) and bounds == "auto":
        interval, known = _rows.scale(value)
        return (0.0, None) if known and not interval else (None, None)
    try:
        low, high = bounds
        ends = [None if end is None else float(end) for end in (low, high)]
    except (TypeError, ValueError):
        ends = None
    if (
        ends is None
        or any(end is not None and not math.isfinite(end) for end in ends)
        or (None not in ends and ends[0] >= ends[1])
    ):
        raise HangtuError(
            f'fit() bounds must be "auto" or (low, high), each a number or None, '
            f"with low below high, not {bounds!r}. Example: bounds=(0, 100) for "
            "a percentage."
        )
    return ends[0], ends[1]


def _check_distributions(
    distributions: Sequence[str] | None, low: float | None, high: float | None
) -> tuple[str, ...]:
    bounded = low is not None and high is not None
    if distributions is None:
        return tuple(name for name in DISTRIBUTIONS if name != "beta" or bounded)
    names = [distributions] if isinstance(distributions, str) else list(distributions)
    unknown = [name for name in names if name not in DISTRIBUTIONS]
    if unknown or not names:
        raise HangtuError(
            f"fit() doesn't know the distribution {', '.join(map(repr, unknown))}. "
            f"Choose from: {', '.join(DISTRIBUTIONS)}."
            if unknown
            else "fit() needs at least one distribution, from: "
            f"{', '.join(DISTRIBUTIONS)}."
        )
    if "beta" in names and not bounded:
        raise HangtuError(
            "fit() fits beta between two bounds, and bounds has "
            f"{'none' if low is None and high is None else 'one'}. Pass "
            "bounds=(low, high), e.g. bounds=(0, 100) for a percentage."
        )
    return tuple(name for name in DISTRIBUTIONS if name in names)


def _check_inside(
    numbers: np.ndarray, low: float | None, high: float | None, column: str
) -> None:
    """Raise if a value lies outside the bounds: a data error or wrong bounds."""
    outside = np.zeros(numbers.size, bool)
    if low is not None:
        outside |= numbers < low
    if high is not None:
        outside |= numbers > high
    if outside.any():
        listed = ", ".join(f"{x:g}" for x in numbers[outside][:5])
        more = ", …" if outside.sum() > 5 else ""
        raise HangtuError(
            f"fit() found {int(outside.sum())} values of {column!r} outside "
            f"bounds=({_bound(low)}, {_bound(high)}): {listed}{more}. Either the "
            "values are wrong or the bounds are: check them, or pass other bounds=."
        )


def _count(n: int) -> str:
    return f"{int(n)} value" + ("" if n == 1 else "s")


def _bound(end: float | None) -> str:
    return "None" if end is None else f"{end:g}"


def _fit_group(
    values: Values, names: tuple[str, ...], low: float | None, high: float | None
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Fit each distribution to one group, and rank the fits (Decision 6)."""
    everything = values.all()
    fits, left_out = [], {}
    for name in names:
        if name in POSITIVE and (everything <= 0).any():
            below = _count((everything <= 0).sum())
            left_out[name] = f"{below} at or below 0, outside the distribution's range"
            continue
        if name == "beta" and ((everything <= low) | (everything >= high)).any():
            on = _count(((everything <= low) | (everything >= high)).sum())
            left_out[name] = f"{on} on the bounds, outside the distribution's range"
            continue
        try:
            parameters = estimate(name, values, (low, high))
        except Exception as error:  # SciPy raises several kinds
            left_out[name] = f"the fit failed: {error}"
            continue
        distribution = frozen(name, parameters)
        log_likelihood = _log_likelihood(distribution, values)
        if not (
            all(math.isfinite(p) for p in parameters.values())
            and math.isfinite(log_likelihood)
        ):
            left_out[name] = "the fit didn't converge"
            continue
        fits.append(
            _record(name, parameters, distribution, log_likelihood, values, low, high)
        )
    _rank(fits)
    return fits, left_out


def estimate(
    name: str, values: Values, bounds: tuple[float | None, float | None]
) -> dict[str, float]:
    """Return the maximum-likelihood parameters of ``name``, by SciPy's names."""
    x = values.exact
    with warnings.catch_warnings():
        # A failed fit shows as non-finite parameters, checked by the caller.
        warnings.simplefilter("ignore", RuntimeWarning)
        if name == "normal":
            return {"loc": float(x.mean()), "scale": float(x.std())}
        if name == "lognormal":
            logs = np.log(x)
            return {"s": float(logs.std()), "scale": float(np.exp(logs.mean()))}
        if name == "gamma":
            shape, _, scale = _stats.gamma.fit(x, floc=0)
            return {"a": float(shape), "scale": float(scale)}
        if name == "weibull":
            # ln of a Weibull variable is Gumbel (minimum): location ln(scale),
            # scale 1/shape. The same fit, about ten times faster (Decision 7).
            location, scale = _stats.gumbel_l.fit(np.log(x))
            return {"c": float(1 / scale), "scale": float(np.exp(location))}
        low, high = bounds
        a, b, _, _ = _stats.beta.fit(x, floc=low, fscale=high - low)
        return {"a": float(a), "b": float(b), "loc": low, "scale": high - low}


def frozen(name: str, parameters: Mapping[str, float]) -> Any:
    """Return SciPy's frozen distribution for ``name`` at ``parameters``."""
    return getattr(_stats, SCIPY_NAMES[name])(**parameters)


def _log_likelihood(distribution: Any, values: Values) -> float:
    """Return ln L: the values' densities, the censored ones' probabilities."""
    with np.errstate(divide="ignore"):
        return float(
            distribution.logpdf(values.exact).sum()
            + distribution.logcdf(values.left).sum()
            + distribution.logsf(values.right).sum()
        )


def _record(
    name: str,
    parameters: dict[str, float],
    distribution: Any,
    log_likelihood: float,
    values: Values,
    low: float | None,
    high: float | None,
) -> dict[str, Any]:
    n, k = values.count, PARAMETER_COUNT
    aic = 2 * k - 2 * log_likelihood
    return {
        "distribution": name,
        "parameters": parameters,
        "mean": float(distribution.mean()),
        "standard_deviation": float(distribution.std()),
        "median": float(distribution.median()),
        "percentile_5": float(distribution.ppf(0.05)),
        "percentile_95": float(distribution.ppf(0.95)),
        "log_likelihood": log_likelihood,
        "aicc": aic + 2 * k * (k + 1) / (n - k - 1),
        "delta_aicc": math.nan,
        "akaike_weight": math.nan,
        "rank": 0,
        "anderson_darling_statistic": math.nan,
        "anderson_darling_p_value": math.nan,
        "probability_below_lower_bound": (
            math.nan if low is None else float(distribution.cdf(low))
        ),
        "probability_above_upper_bound": (
            math.nan if high is None else float(distribution.sf(high))
        ),
    }


def _rank(fits: list[dict[str, Any]]) -> None:
    """Set Δ AICc, the Akaike weights and the ranks; sort the fits by rank."""
    if not fits:
        return
    best = min(fit["aicc"] for fit in fits)
    for fit in fits:
        fit["delta_aicc"] = fit["aicc"] - best
    total = sum(math.exp(-fit["delta_aicc"] / 2) for fit in fits)
    for fit in fits:
        fit["akaike_weight"] = math.exp(-fit["delta_aicc"] / 2) / total
    # A stable sort keeps the table's order on a tie.
    fits.sort(key=lambda fit: fit["aicc"])
    for rank, fit in enumerate(fits, start=1):
        fit["rank"] = rank


def _group_notes(
    group: dict[str, Any], label: str, values: Values, low: float | None
) -> list[str]:
    notes = []
    by_reason: dict[str, list[str]] = {}
    for name, why in group["left_out"].items():
        by_reason.setdefault(why, []).append(name)
    for why, names in by_reason.items():
        notes.append(f"{label}: {', '.join(names)} not fitted: {why}.")
    for fit in group["fits"]:
        below = fit["probability_below_lower_bound"]
        if fit["distribution"] == "normal" and below > BELOW_BOUND_NOTE:
            notes.append(
                f"{label}: the normal fit puts {below:.1%} below {_bound(low)}, "
                "where the value can't be."
            )
    return notes


def _notes(
    group_notes: list[str],
    groups: list[dict[str, Any]],
    read: _rows.Input,
    pooled: list[str],
    include_assumed: bool,
    unit_given: bool,
) -> list[str]:
    """Return the result's lines under the table."""
    notes = [] if unit_given else ["(units not given)"]
    notes.extend(group_notes)
    for group in groups:
        if group["reason"]:
            label = ", ".join(map(str, group["key"].values())) or "All"
            notes.append(f"{label}: not fitted, {group['reason']}.")
    assumed = sum(group["counts"]["count_assumed"] for group in groups)
    if include_assumed and assumed:
        notes.append(f"Assumed values included: {assumed}.")
    for group in groups:
        label = ", ".join(map(str, group["key"].values()))
        for column in pooled:
            listed = ", ".join(
                f"{value} {count}" for value, count in group["sources"][column].items()
            )
            where = f" in {label}" if read.by else ""
            notes.append(f"Pooled across {column}{where}: {listed}.")
    notes.append(BURNHAM_ANDERSON)
    if read.by:
        notes.append("AICc compares fits within a group, never across groups.")
    return notes
