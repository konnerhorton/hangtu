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
from hangtu.stats._positions import plotting_positions
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
#: Parametric bootstrap of the Anderson-Darling p-value (Decision 7): 999
#: samples give a standard error of about 0.007 at p = 0.05. The seed is fixed,
#: so the same data give the same p-value.
BOOTSTRAP_SAMPLES = 999
SEED = 20261030
ANDERSON_DARLING = (
    "Anderson-Darling p-values are by parametric bootstrap (999 samples from "
    "each fit, refitted): a small one (below 0.05, say) is evidence against the "
    "distribution; a large one is not evidence for it, least of all below 10 "
    "values."
)
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
    - ``weibull``: shape and scale, located at 0; without censored values,
      fitted as the Gumbel (minimum) distribution of ln x, the same fit;
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

    **Goodness of fit** (Anderson-Darling): for each fit,
    $A^2 = -n - \frac{1}{n}\sum_{i=1}^{n} (2i - 1)[\ln F(x_{(i)}) +
    \ln(1 - F(x_{(n+1-i)}))]$ with $F$ the fitted CDF and $x_{(i)}$ the
    values in order (NIST/SEMATECH e-Handbook of Statistical Methods,
    §1.3.5.14). Published critical values exist only for some distributions,
    and they assume the parameters weren't estimated from the same data, so
    the p-value is a parametric bootstrap instead, as in SciPy's
    ``scipy.stats.goodness_of_fit``: 999 samples of $n$ values drawn from the
    fit, each refitted the same way, and $p$ = (1 + the number with $A^2$ at
    least the observed) / 1000. The seed is fixed, so the same data give the
    same p-value. A small p-value (below 0.05, say) is evidence against the
    distribution; a large one is not evidence for it, least of all with few
    values. It is reported, not turned into a pass or fail.

    **At least 4 uncensored values per group** (AICc needs $n > k + 1$): a
    group with fewer has no fits, with a warning; one with fewer than 10 is
    fitted with a warning that the ranking says little. A group whose values
    are all equal has no spread to fit. No group to fit is an error.

    The SPT N is a count but is fitted as continuous, as is usual.

    **Censored values are fitted as censored**, not at their limits
    (Helsel et al. 2020, §12.7): a refusal (``spt_refusal``) or a ``>``
    value (``qualifier``) is known only to be at least the value the column
    holds, a ``<`` value at most. Each enters the likelihood as the
    probability beyond its limit, $1 - F(c)$ or $F(c)$, through SciPy's
    ``CensoredData``, and every candidate is fitted to the same censored
    data, so their AICc compare. They are counted (``count_censored``,
    ``count_at_least``, ``count_at_most``) and the notes give the share.
    With any censored value in a group there is no Anderson-Darling check:
    its p-value assumes complete data. Judge the fit on P08's Q-Q panel.
    A band (``<value>_lower``/``_upper`` with no value) is the spread of a
    correlation's coefficient, not a censored measurement, so it is left
    out and counted (``count_range``).

    **Rows are chosen as by** :func:`describe`: non-plastic, assumed, text
    and blank rows are left out and counted; sources aren't pooled
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

    Helsel, D.R., Hirsch, R.M., Ryberg, K.R., Archfield, S.A. & Gilroy,
    E.J. (2020). *Statistical Methods in Water Resources*. USGS Techniques
    and Methods 4-A3, §12.7, pp. 356-357.

    NIST/SEMATECH *e-Handbook of Statistical Methods*, §1.3.5.14,
    Anderson-Darling test. It cites Stephens (1974); the bootstrap with
    estimated parameters follows SciPy's ``goodness_of_fit`` documentation
    until the primary papers are checked.

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
        # Decision 3: refusals and ">" are right-censored, "<" left-censored.
        right = chosen & marks["count_at_least"]
        left = chosen & marks["count_at_most"] & ~right
        values = Values(
            exact=numbers[chosen & ~left & ~right],
            left=numbers[left],
            right=numbers[right],
        )
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
            "positions": None,
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
        if np.ptp(values.all()) == 0:
            group["reason"] = (
                f"all {values.count} values are {values.exact[0]:g}, so there is "
                "no spread to fit"
            )
            continue
        if values.exact.size < FEW:
            few.append(f"{label} ({values.exact.size})")
        group["fits"], group["left_out"] = _fit_group(values, names, low, high)
        if not group["fits"]:
            group["reason"] = "no distribution could be fitted"
        positions = plotting_positions(values.exact, values.left, values.right)
        if positions is not None:
            group["positions"] = {
                "values": positions[0].tolist(),
                "probabilities": positions[1].tolist(),
            }
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
    if not any(group["fits"] for group in groups):
        reasons = "; ".join(
            f"{', '.join(map(str, group['key'].values())) or 'All'}: {group['reason']}"
            for group in groups
        )
        raise HangtuError(
            f"fit() could fit no group of {read.column!r}: {reasons}. Check the "
            "values, or report them themselves."
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
        record = _record(
            name, parameters, distribution, log_likelihood, values, low, high
        )
        if not values.left.size and not values.right.size:
            statistic = anderson_darling(name, parameters, values.exact)
            record["anderson_darling_statistic"] = statistic
            record["anderson_darling_p_value"] = _anderson_darling_p_value(
                name, distribution, statistic, values.exact.size, (low, high)
            )
        fits.append(record)
    _rank(fits)
    return fits, left_out


def estimate(
    name: str, values: Values, bounds: tuple[float | None, float | None]
) -> dict[str, float]:
    """Return the maximum-likelihood parameters of ``name``, by SciPy's names."""
    x = values.exact
    censored = bool(values.left.size or values.right.size)
    if name in CLOSED_FORM and not censored:
        return {key: float(value) for key, value in _closed_form(name, x).items()}
    # Decision 3: censored values enter by maximum likelihood, as CensoredData.
    data = (
        _stats.CensoredData(uncensored=x, left=values.left, right=values.right)
        if censored
        else x
    )
    with warnings.catch_warnings():
        # A failed fit shows as non-finite parameters, checked by the caller.
        warnings.simplefilter("ignore", RuntimeWarning)
        if name == "normal":
            location, scale = _stats.norm.fit(data)
            return {"loc": float(location), "scale": float(scale)}
        if name == "lognormal":
            sigma, _, scale = _stats.lognorm.fit(data, floc=0)
            return {"s": float(sigma), "scale": float(scale)}
        if name == "gamma":
            shape, _, scale = _stats.gamma.fit(data, floc=0)
            return {"a": float(shape), "scale": float(scale)}
        if name == "weibull" and not censored:
            # ln of a Weibull variable is Gumbel (minimum): location ln(scale),
            # scale 1/shape. The same fit, about ten times faster for the
            # bootstrap, and exact where weibull_min's stops short (Decision 7).
            location, scale = _stats.gumbel_l.fit(np.log(x))
            return {"c": float(1 / scale), "scale": float(np.exp(location))}
        if name == "weibull":
            # With censoring, gumbel_l falls back to a generic optimizer that
            # stops short of weibull_min's; there is no bootstrap to speed up.
            shape, _, scale = _stats.weibull_min.fit(data, floc=0)
            return {"c": float(shape), "scale": float(scale)}
        low, high = bounds
        a, b, _, _ = _stats.beta.fit(data, floc=low, fscale=high - low)
        return {"a": float(a), "b": float(b), "loc": low, "scale": high - low}


#: Fitted in closed form without censoring (Decision 2).
CLOSED_FORM = ("normal", "lognormal")


def _closed_form(name: str, x: np.ndarray) -> dict[str, np.ndarray]:
    """Fit normal or lognormal along the last axis: one fit per row of ``x``."""
    if name == "normal":
        return {"loc": x.mean(axis=-1), "scale": x.std(axis=-1)}
    logs = np.log(x)
    return {"s": logs.std(axis=-1), "scale": np.exp(logs.mean(axis=-1))}


def anderson_darling(
    name: str, parameters: Mapping[str, Any], values: np.ndarray
) -> Any:
    """Return A² of ``values`` against distribution ``name`` at ``parameters``.

    The formula is in ``fit()``'s docstring (NIST/SEMATECH e-Handbook,
    §1.3.5.14). With 2-D ``values`` and a parameter array per row, it
    returns one A² per row. It doesn't freeze the distribution, which costs
    more than the statistic.
    """
    x = np.sort(np.atleast_2d(values), axis=-1)
    n = x.shape[-1]
    weights = 2 * np.arange(1, n + 1) - 1
    columns = {
        key: np.reshape(np.asarray(value, float), (-1, 1))
        for key, value in parameters.items()
    }
    distribution = getattr(_stats, SCIPY_NAMES[name])
    with np.errstate(divide="ignore", invalid="ignore"):
        total = (
            weights
            * (
                distribution.logcdf(x, **columns)
                + distribution.logsf(x[:, ::-1], **columns)
            )
        ).sum(axis=-1)
    statistic = -n - total / n
    return float(statistic[0]) if np.ndim(values) == 1 else statistic


def _anderson_darling_p_value(
    name: str,
    distribution: Any,
    statistic: float,
    n: int,
    bounds: tuple[float | None, float | None],
) -> float:
    """Return the share of refitted bootstrap samples with A² at least ``statistic``.

    Each sample is drawn from the fit and refitted with the same routine, so
    the estimated parameters are accounted for. A sample whose refit fails is
    left out of both counts.
    """
    random = np.random.default_rng(SEED)
    samples = distribution.rvs(size=(BOOTSTRAP_SAMPLES, n), random_state=random)
    if name in CLOSED_FORM:
        parameters = _closed_form(name, samples)
    else:
        parameters = _estimates(name, samples, bounds)
    refits = anderson_darling(name, parameters, samples)
    valid = np.isfinite(refits)
    return float((1 + (refits[valid] >= statistic).sum()) / (1 + valid.sum()))


def _estimates(
    name: str, samples: np.ndarray, bounds: tuple[float | None, float | None]
) -> dict[str, np.ndarray]:
    """Refit each sample with ``estimate()``; NaN parameters where a refit fails."""
    empty = np.empty(0)
    rows = []
    for sample in samples:
        try:
            rows.append(estimate(name, Values(sample, empty, empty), bounds))
        except Exception:  # SciPy raises several kinds
            rows.append({})
    keys = next((row.keys() for row in rows if row), ())
    return {key: np.array([row.get(key, np.nan) for row in rows]) for key in keys}


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
    censored = values.left.size + values.right.size
    if censored:
        sides = [
            f"{values.right.size} at least (refusal or '>')"
            if values.right.size
            else "",
            f"{values.left.size} at most ('<')" if values.left.size else "",
        ]
        notes.append(
            f"{label}: {censored} of {values.count} values censored "
            f"({censored / values.count:.0%}: {', '.join(filter(None, sides))}), "
            "fitted as censored by maximum likelihood, not at their limits."
        )
        notes.append(
            f"{label}: no Anderson-Darling check: {_count(censored)} are censored; "
            "judge the fit on the Q-Q plot."
        )
        if values.left.size and values.right.size:
            notes.append(
                f"{label}: no plotting positions: values are censored both ways, "
                "so the Q-Q plot can't place them. The fits and AICc stand."
            )
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
    if any(
        math.isfinite(fit["anderson_darling_p_value"])
        for group in groups
        for fit in group["fits"]
    ):
        notes.append(ANDERSON_DARLING)
    if read.by:
        notes.append("AICc compares fits within a group, never across groups.")
    return notes
