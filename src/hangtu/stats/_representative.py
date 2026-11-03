"""``representative()``: a parameter's representative value per group (SPEC §5).

Spec: docs/work/m18b-representative-values.md. The rows are read as ``fit()``
reads them (``_fit.read_groups``), so refusals, ``>`` and ``<`` values are
censored and enter through the censored maximum-likelihood fit.
"""

import math
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as _stats

from hangtu.errors import HangtuError, warn
from hangtu.stats import _fit, _refusal_limit, _rows
from hangtu.stats._result import RepresentativeResult

FUNCTION = "representative()"
METHODS = ("characteristic",)
SIDES = ("low", "high")
DISTRIBUTIONS = ("normal", "lognormal")
TRENDS = ("depth", "elevation")
#: The estimate a characteristic value is (EC7 Types A, B and C), and its Γ².
ESTIMATES = {"mean": 0.0, "fractile": 1.0, "intermediate": None}
#: Each method's inputs, and which of them a call must give (spec decision 1).
INPUTS = {
    "characteristic": (
        "estimate",
        "coefficient_of_variation",
        "scale_of_fluctuation",
        "failure_length",
        "sensitivity_index",
    ),
}
REQUIRED = {"characteristic": ("estimate",)}
EXAMPLES = {
    "characteristic": (
        'method="characteristic", estimate="mean", side="low", distribution="normal"'
    ),
}
#: Fewer values in a group gives it no value (spec decision 11).
MIN_COUNT = 2
#: The one-sided confidence of EC7's characteristic value (Formula 4.5).
CONFIDENCE = 0.95
COMPLETE_DATA = (
    "the mean and standard deviation are the censored maximum-likelihood fit's "
    "(the standard deviation with n, not n - 1), and EC7's k_n factors assume "
    "complete data."
)


def representative(
    data: pd.DataFrame | pd.Series | Sequence[float] | np.ndarray,
    *,
    value: str | None = None,
    by: str | Sequence[str] | None = None,
    method: str | None = None,
    side: str | None = None,
    distribution: str | None = None,
    trend: str | None = None,
    estimate: str | None = None,
    coefficient_of_variation: float | None = None,
    scale_of_fluctuation: float | None = None,
    failure_length: float | None = None,
    sensitivity_index: float | None = None,
    pool: str | Sequence[str] | None = None,
    include_assumed: bool = False,
    spt_refusal_upper_limit: float | str | Mapping[str, float | str] | None = None,
    judgments: Any = None,
    units: str | Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> RepresentativeResult:
    r"""Compute a parameter's representative value per group, in one named view.

    One calculation, one view per call: the view and every judgment it needs
    are arguments, none has a default (SPEC §4), and the result records them
    with the statistics behind each value. Two views of the same rows are two
    calls, and both read the same statistics.

    **Characteristic value** (``method="characteristic"``), EN 1997-1:2024
    Formula 4.5 as the JRC report restates it (Orr et al. 2025, p. 55), with
    $\mp$ meaning $-$ for ``side="low"`` and $+$ for ``"high"``:

    - $V_X$ computed from the data (Case 2, ``coefficient_of_variation=None``):
      $X_k = \bar{x} \mp k_n s$, with $k_n = t_{0.95,\,n-1}\sqrt{\Gamma^2 +
      1/n}$;
    - $V_X$ assumed (Case 3, ``coefficient_of_variation=`` a number):
      $X_k = \bar{x}(1 \mp k_n V_X)$, with $k_n = N_{95}\sqrt{\Gamma^2 + 1/n}$
      and $N_{95} = 1.645$, the normal distribution's 95 % quantile (computed,
      not Table 13's rounded 1.64). The same formula serves Case 1, $V_X$
      known from prior experience: give it the same way.

    $\bar{x}$ is the sample mean and $s$ the sample standard deviation, with
    $n - 1$ (Formula A.4); $k_n$ is from Table 13 and Equation 18 (p. 58).
    $\Gamma^2$ sets the estimate (``estimate=``):

    - ``"mean"`` (Type A): $\Gamma^2 = 0$, the mean at 95 % confidence, for a
      failure that averages over a large volume (a long slip surface, a pile
      shaft);
    - ``"fractile"`` (Type B): $\Gamma^2 = 1$, the 5 % (or 95 %) fractile at
      95 % confidence, for a local failure;
    - ``"intermediate"`` (Type C): $\Gamma^2 = \min(\theta / L,\ 1)$
      (Equation 17, p. 57, capped at 1 as the report's text adopts), from the
      scale of fluctuation $\theta$ (``scale_of_fluctuation``) and the length
      of the failure surface $L$ (``failure_length``), or given directly as
      ``sensitivity_index`` between 0 and 1. $\theta$ and $L$ are in the same
      length unit, whichever it is: only their ratio enters. SPT spacing
      can't resolve the vertical $\theta$, so take it from published values
      or a CPT.

    **Lognormal** (``distribution="lognormal"``): the formulae are applied to
    $\ln x$ and transformed back (the JRC's Annex IV, pp. 160-162):
    $X_k = \exp(m \mp k_n s_{\ln})$, with $m$ and $s_{\ln}$ the mean and
    standard deviation of $\ln x$; with $V_X$ assumed,
    $s_{\ln} = \sqrt{\ln(1 + V_X^2)}$. Values at or below 0 are left out and
    counted (``count_not_positive``). The report's other route, Annex V
    (Equations 72-74), takes the parameters from the moments of $x$; it isn't
    offered. The result gives the geometric mean $e^m$ and geometric
    standard deviation $e^{s_{\ln}}$.

    **Censored values** (refusals, ``>`` and ``<`` values, a refusal under
    ``spt_refusal_upper_limit``): in a group with any, $\bar{x}$ and $s$ (or
    $m$ and $s_{\ln}$) are the censored maximum-likelihood normal (or
    lognormal) fit's, as :func:`fit` gives it, so they aren't biased low at
    their limits. That $s$ is with $n$, and EC7's $k_n$ factors assume
    complete data; a note says so. $n$ counts every value, censored or not.

    **Rows are chosen as by** :func:`fit`: non-plastic, assumed, text and
    blank rows, and bands, are left out and counted; sources aren't pooled
    unawares (``pool=``); the counts add up to the group's rows.

    **Warnings:** a characteristic value at or below 0 from a normal
    distribution (the data may be lognormal, JRC §5.1.3), and
    ``hydraulic_conductivity`` with a normal distribution, for which
    Formula 4.5 should not be used (Table A.1, note 2, p. 57). A group with
    fewer than 2 values has no value, with the reason.

    Parameters
    ----------
    data : pandas.DataFrame, pandas.Series, list or array
        The values. A DataFrame needs ``value=``; a Series is its own value.
        ``by=`` needs a DataFrame.
    value : str
        The column, e.g. ``"undrained_shear_strength"``.
    by : str or list of str, optional
        The column(s) to group by, e.g. ``"geology_unit"``.
    method : {"characteristic"}
        The view.
    side : {"low", "high"}
        The cautious side: ``"low"`` where a lower value is unfavorable (a
        strength), ``"high"`` where a higher one is (a load, a
        compressibility).
    distribution : {"normal", "lognormal"}
        The distribution the values are taken to follow.
    trend : None
        None: one value per group, constant with depth.
    estimate : {"mean", "fractile", "intermediate"}
        For ``method="characteristic"``: Type A, B or C.
    coefficient_of_variation : float, optional
        For ``method="characteristic"``: $V_X$ assumed (Case 3) or known
        (Case 1), e.g. ``0.4``. None computes it from the data (Case 2).
    scale_of_fluctuation, failure_length : float
        For ``estimate="intermediate"``: $\theta$ and $L$, in one length
        unit, both above 0.
    sensitivity_index : float
        For ``estimate="intermediate"``: $\Gamma^2$ directly, from 0 to 1,
        instead of $\theta$ and $L$.
    pool : str or list of str, optional
        Source columns to pool across on purpose, as in :func:`describe`.
    include_assumed : bool
        Include assumed values. They are still counted.
    spt_refusal_upper_limit : float, "none" or dict, optional
        For an SPT N column: the most a refusal could be, in field N, as in
        :func:`fit`. None reads it from ``judgments=``, then the Project's
        file; not found anywhere, refusals are taken as at least their value.
    judgments : Judgments or path, optional
        The judgments file to read ``spt_refusal_upper_limit`` from.
    units : str or dict, optional
        The value's unit, e.g. ``"kPa"``, as in :func:`describe`.
    display_units : {"US", "SI"}, optional
        Convert the values to this system's display unit first.

    Returns
    -------
    RepresentativeResult
        ``.to_frame()`` has one row per group, with ``value``.
        ``print(result)`` shows it with the inputs and the notes.

    Raises
    ------
    HangtuError
        For a missing or unknown view, side or distribution; an input the
        method needs left out, or one of another method given; an input out
        of range; ``trend=`` with ``coefficient_of_variation=`` or Type C;
        and the input errors of :func:`fit`.
    ColumnError
        For a missing column, or one that holds no numbers.
    UnitsError
        For a value column whose unit is unknown.

    References
    ----------
    Orr, T., Sorgatz, J., Estaire, J. et al. (2025). *Determination of
    characteristic values of ground properties in the second generation of
    Eurocode 7*. JRC, EUR 40260 (CC BY 4.0), which quotes EN 1997-1:2024.

    Examples
    --------
    >>> strength = p.strength()
    >>> result = ht.stats.representative(
    ...     strength, value="undrained_shear_strength", by="geology_unit",
    ...     method="characteristic", estimate="mean", side="low",
    ...     distribution="normal")
    >>> result.to_frame()
    """
    inputs = {
        "estimate": estimate,
        "coefficient_of_variation": coefficient_of_variation,
        "scale_of_fluctuation": scale_of_fluctuation,
        "failure_length": failure_length,
        "sensitivity_index": sensitivity_index,
    }
    method, side, distribution = _check(method, side, distribution, trend, inputs)
    if trend is not None:
        raise HangtuError(f"{FUNCTION} trend= is not built yet (M18 (b), step 4).")
    gamma2, capped = _sensitivity(inputs)
    lognormal = distribution == "lognormal"
    found = _fit.read_groups(
        data,
        value,
        by,
        pool,
        include_assumed,
        spt_refusal_upper_limit,
        judgments,
        units,
        display_units,
        FUNCTION,
        positive_only=lognormal,
    )
    read = found.read
    sign = -1.0 if side == "low" else 1.0
    assumed = coefficient_of_variation
    groups, notes, at_or_below_zero = [], [], []
    for group in found.groups:
        record: dict[str, Any] = {
            "key": group.key,
            "counts": group.counts,
            "statistics": {},
            "value": math.nan,
            "reason": None,
            "sources": {
                column: _rows.breakdown(read.frame.loc[group.chosen, column])
                for column in found.pooled
            },
        }
        groups.append(record)
        values = group.values
        if values.count < MIN_COUNT:
            record["reason"] = f"fewer than {MIN_COUNT} values ({values.count})"
            continue
        moments = _moments(values, lognormal)
        if moments is None:
            record["reason"] = "the censored maximum-likelihood fit failed"
            continue
        centre, spread = moments
        n = values.count
        if assumed is None:
            factor = float(_stats.t.ppf(CONFIDENCE, n - 1))
        else:
            factor = float(_stats.norm.ppf(CONFIDENCE))
        coefficient = factor * math.sqrt(gamma2 + 1 / n)
        if lognormal:
            deviation = spread if assumed is None else math.sqrt(math.log1p(assumed**2))
            result = math.exp(centre + sign * coefficient * deviation)
            statistics = {
                "geometric_mean": math.exp(centre),
                "geometric_standard_deviation": math.exp(deviation),
                "coefficient_of_variation": (
                    math.sqrt(math.expm1(spread**2)) if assumed is None else assumed
                ),
            }
        else:
            result = (
                centre + sign * coefficient * spread
                if assumed is None
                else centre * (1 + sign * coefficient * assumed)
            )
            statistics = {
                "mean": centre,
                "standard_deviation": spread,
                "coefficient_of_variation": (
                    assumed
                    if assumed is not None
                    else spread / centre
                    if centre
                    else math.nan
                ),
            }
            if result <= 0:
                at_or_below_zero.append(group.label)
        record["statistics"] = {
            **statistics,
            "quantile_factor": factor,
            "statistical_coefficient": coefficient,
            "sensitivity_index": gamma2,
        }
        record["value"] = result
        if values.censored:
            notes.append(
                f"{group.label}: {values.censored} of {n} values censored, so "
                + COMPLETE_DATA
            )

    _rows.warn_left_out(found.reasons, read.column, FUNCTION)
    _rows.warn_text(found.texts, read.column, FUNCTION)
    not_positive = int((found.reasons == "count_not_positive").sum())
    if not_positive:
        warn(
            f'{FUNCTION} with distribution="lognormal" left out {not_positive} '
            f"values of {read.column!r} at or below 0: a lognormal distribution "
            "has no place for them. They are counted in count_not_positive."
        )
    if at_or_below_zero:
        warn(
            f"{FUNCTION} gives a characteristic value of {read.column!r} at or "
            f"below 0 from a normal distribution in: {', '.join(at_or_below_zero)}. "
            'The data may be lognormal (JRC §5.1.3): try distribution="lognormal".'
        )
    if read.value == "hydraulic_conductivity" and not lognormal:
        warn(
            f"{FUNCTION}: Formula 4.5 should not be used for hydraulic "
            "conductivity with a normal distribution (EN 1997-1:2024 Table A.1, "
            'note 2). Use distribution="lognormal".'
        )
    return RepresentativeResult(
        kind="parameter",
        function="representative",
        value=read.value,
        unit=found.unit,
        notes=tuple(
            _notes(notes, groups, found, include_assumed, lognormal, inputs, capped)
        ),
        judgments={
            **read.frame.attrs.get("judgments", {}),
            **(
                {}
                if found.limits.record is None
                else {_refusal_limit.NAME: found.limits.record}
            ),
        },
        hangtu_version=version("hangtu"),
        by=tuple(read.by),
        pooled=tuple(found.pooled),
        include_assumed=include_assumed,
        display_units=display_units,
        method=method,
        side=side,
        distribution=distribution,
        trend=trend,
        estimate=estimate,
        coefficient_of_variation=coefficient_of_variation,
        coefficient_of_variation_case=(
            None if method != "characteristic" else 2 if assumed is None else 3
        ),
        scale_of_fluctuation=scale_of_fluctuation,
        failure_length=failure_length,
        sensitivity_index=gamma2,
        groups=tuple(groups),
    )


def _check(
    method: Any, side: Any, distribution: Any, trend: Any, inputs: dict[str, Any]
) -> tuple[str, str, str]:
    """Check the view and its judgments (spec decision 1, criterion 1)."""
    example = EXAMPLES["characteristic"]
    for name, given, choices in (
        ("method", method, METHODS),
        ("side", side, SIDES),
        ("distribution", distribution, DISTRIBUTIONS),
    ):
        if given is None:
            raise HangtuError(
                f"{FUNCTION} needs {name}=, one of {_listed(choices)}: it is a "
                f"judgment, so it has no default (SPEC §4). Example: {example}"
            )
        if given not in choices:
            raise HangtuError(
                f"{FUNCTION} doesn't know {name}={given!r}. Choose from "
                f"{_listed(choices)}. Example: {example}"
            )
    if trend is not None and trend not in TRENDS:
        raise HangtuError(
            f"{FUNCTION} doesn't know trend={trend!r}. Choose from "
            f"{_listed(TRENDS)}, or None for one value per group."
        )
    allowed = INPUTS[method]
    others = [
        name
        for name, given in inputs.items()
        if given is not None and name not in allowed
    ]
    if others:
        raise HangtuError(
            f"{FUNCTION} with method={method!r} doesn't take "
            f"{', '.join(f'{name}=' for name in others)}: its inputs are "
            f"{', '.join(f'{name}=' for name in allowed)}. Leave "
            f"{'it' if len(others) == 1 else 'them'} out, or choose the method "
            "that uses it."
        )
    for name in REQUIRED[method]:
        if inputs[name] is None:
            raise HangtuError(
                f"{FUNCTION} with method={method!r} needs {name}=: it is a "
                f"judgment, so it has no default (SPEC §4). Example: "
                f"{EXAMPLES[method]}"
            )
    if method == "characteristic":
        _check_characteristic(inputs, trend)
    return method, side, distribution


def _check_characteristic(inputs: dict[str, Any], trend: Any) -> None:
    estimate = inputs["estimate"]
    if estimate not in ESTIMATES:
        raise HangtuError(
            f"{FUNCTION} doesn't know estimate={estimate!r}. Choose from "
            f"{_listed(ESTIMATES)} (EC7 Types A, B and C)."
        )
    for name in ("coefficient_of_variation", "scale_of_fluctuation", "failure_length"):
        if inputs[name] is not None:
            _positive(name, inputs[name])
    local = ("scale_of_fluctuation", "failure_length", "sensitivity_index")
    given = [name for name in local if inputs[name] is not None]
    if estimate != "intermediate":
        if given:
            raise HangtuError(
                f"{FUNCTION} takes {', '.join(f'{name}=' for name in given)} only "
                f'with estimate="intermediate" (Type C); estimate={estimate!r} '
                f"fixes Γ² at {ESTIMATES[estimate]:g}. Leave "
                f"{'it' if len(given) == 1 else 'them'} out."
            )
    elif inputs["sensitivity_index"] is not None:
        if len(given) > 1:
            raise HangtuError(
                f"{FUNCTION} takes Γ² either as sensitivity_index= or from "
                "scale_of_fluctuation= and failure_length=, not both. Give one."
            )
        index = _number("sensitivity_index", inputs["sensitivity_index"])
        if not 0 <= index <= 1:
            raise HangtuError(
                f"{FUNCTION} sensitivity_index= is Γ², from 0 to 1, not {index:g}. "
                "Example: sensitivity_index=0.3"
            )
    elif len(given) < 2:
        missing = [name for name in local[:2] if inputs[name] is None]
        raise HangtuError(
            f'{FUNCTION} with estimate="intermediate" (Type C) needs '
            f"{' and '.join(f'{name}=' for name in missing)}, θ and L in one "
            "length unit, or sensitivity_index= for Γ² directly. They are "
            "judgments, with no default (SPEC §4). Example: "
            "scale_of_fluctuation=1.0, failure_length=10.0"
        )
    if trend is not None:
        if inputs["coefficient_of_variation"] is not None:
            raise HangtuError(
                f"{FUNCTION} gives a trend only with the standard deviation from "
                "the data (JRC, pp. 83-85), so not with coefficient_of_variation=. "
                "Leave it out, or use trend=None."
            )
        if estimate == "intermediate":
            raise HangtuError(
                f'{FUNCTION} doesn\'t give estimate="intermediate" (Type C) on a '
                "trend: the JRC report leaves it beyond its scope (p. 82). Use "
                '"mean" or "fractile", or trend=None.'
            )


def _sensitivity(inputs: dict[str, Any]) -> tuple[float, bool]:
    """Return Γ² and whether θ/L was capped at 1 (spec decision 4)."""
    estimate = inputs["estimate"]
    if estimate is None:
        return math.nan, False
    fixed = ESTIMATES[estimate]
    if fixed is not None:
        return fixed, False
    if inputs["sensitivity_index"] is not None:
        return float(inputs["sensitivity_index"]), False
    ratio = float(inputs["scale_of_fluctuation"]) / float(inputs["failure_length"])
    return min(ratio, 1.0), ratio > 1


def _moments(values: _fit.Values, lognormal: bool) -> tuple[float, float] | None:
    """Return the centre and spread: of x, or of ln x when ``lognormal``.

    The sample's (spread with n - 1) without censoring; with it, the censored
    maximum-likelihood fit's (intent decision 2), None if that fails.
    """
    if not values.censored:
        x = np.log(values.exact) if lognormal else values.exact
        return float(x.mean()), float(x.std(ddof=1))
    name = "lognormal" if lognormal else "normal"
    try:
        parameters = _fit.estimate(name, values, (None, None))
    except Exception:  # SciPy raises several kinds
        return None
    if lognormal:
        centre, spread = math.log(parameters["scale"]), parameters["s"]
    else:
        centre, spread = parameters["loc"], parameters["scale"]
    if not (math.isfinite(centre) and math.isfinite(spread)):
        return None
    return centre, spread


def _number(name: str, given: Any) -> float:
    if isinstance(given, bool) or not isinstance(given, int | float):
        raise HangtuError(f"{FUNCTION} {name}= is a number, not {given!r}.")
    if not math.isfinite(given):
        raise HangtuError(f"{FUNCTION} {name}= must be finite, not {given!r}.")
    return float(given)


def _positive(name: str, given: Any) -> None:
    if _number(name, given) <= 0:
        raise HangtuError(f"{FUNCTION} {name}= must be above 0, not {given!r}.")


def _listed(choices: Any) -> str:
    return ", ".join(f'"{choice}"' for choice in choices)


def _notes(
    group_notes: list[str],
    groups: list[dict[str, Any]],
    found: _fit.Groups,
    include_assumed: bool,
    lognormal: bool,
    inputs: dict[str, Any],
    capped: bool,
) -> list[str]:
    """Return the result's lines under the table."""
    read = found.read
    notes = [] if read.unit_given else ["(units not given)"]
    notes.extend(group_notes)
    notes.extend(found.limits.notes)
    for group in groups:
        if group["reason"]:
            label = ", ".join(map(str, group["key"].values())) or "All"
            notes.append(f"{label}: no value, {group['reason']}.")
    if capped:
        ratio = inputs["scale_of_fluctuation"] / inputs["failure_length"]
        notes.append(
            f"θ/L = {ratio:g} is above 1, so Γ² = 1, the most it can be "
            "(JRC Equation 17, p. 57): the estimate is the fractile's."
        )
    if lognormal:
        notes.append(
            "Lognormal: the formulae are applied to ln x and transformed back "
            "(JRC Annex IV)."
        )
    assumed = sum(group["counts"]["count_assumed"] for group in groups)
    if include_assumed and assumed:
        notes.append(f"Assumed values included: {assumed}.")
    for group in groups:
        label = ", ".join(map(str, group["key"].values()))
        for column in found.pooled:
            listed = ", ".join(
                f"{value} {count}" for value, count in group["sources"][column].items()
            )
            where = f" in {label}" if read.by else ""
            notes.append(f"Pooled across {column}{where}: {listed}.")
    return notes
