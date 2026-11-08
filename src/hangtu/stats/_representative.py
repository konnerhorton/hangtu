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

from hangtu import units as _units
from hangtu.analysis._line_fit import line_fit
from hangtu.errors import ColumnError, HangtuError, warn
from hangtu.stats import _fit, _refusal_limit, _rows
from hangtu.stats._result import CURVE_POINTS, RepresentativeResult, trend_at

FUNCTION = "representative()"
METHODS = ("characteristic", "percentile", "standard_deviations")
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
    "percentile": ("percentile",),
    "standard_deviations": ("standard_deviations",),
}
REQUIRED = {method: inputs[:1] for method, inputs in INPUTS.items()}
#: Each method's fields as a selection judgment writes them, under
#: representative()'s argument names (docs/analysis/judgments.md §5.9).
FIELDS = {
    method: ("side", "distribution", "trend", *inputs)
    for method, inputs in INPUTS.items()
}
EXAMPLES = {
    "characteristic": (
        'method="characteristic", estimate="mean", side="low", distribution="normal"'
    ),
    "percentile": (
        'method="percentile", percentile=5, side="low", distribution="normal"'
    ),
    "standard_deviations": (
        'method="standard_deviations", standard_deviations=0.5, side="low", '
        'distribution="normal"'
    ),
}
#: Fewer values in a group gives it no value, or no line (spec decision 11).
MIN_COUNT = 2
MIN_TREND_COUNT = 3
#: The one-sided confidence of EC7's characteristic value (Formula 4.5).
CONFIDENCE = 0.95
#: The note on a group with censored values, by method (intent decision 2).
CENSORED = {
    "characteristic": (
        "so the mean and standard deviation are the censored maximum-likelihood "
        "fit's (the standard deviation with n, not n - 1), and EC7's k_n factors "
        "assume complete data."
    ),
    "percentile": "fitted as censored by maximum likelihood, as by fit().",
    "standard_deviations": (
        "so the mean and standard deviation are the censored maximum-likelihood "
        "fit's (the standard deviation with n, not n - 1)."
    ),
}


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
    percentile: float | None = None,
    standard_deviations: float | None = None,
    pool: str | Sequence[str] | None = None,
    include_assumed: bool = False,
    spt_refusal_upper_limit: float | str | Mapping[str, float | str] | None = None,
    judgments: Any = None,
    units: str | Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> RepresentativeResult:
    r"""Compute a parameter's representative value per group, in one named view.

    One calculation, one view per call: the view and every judgment it needs
    are arguments, none has a default, and the result records them
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

    **Percentile** (``method="percentile"``): the ``percentile``-th
    percentile of the normal or lognormal distribution :func:`fit` fits to
    the group by maximum likelihood (the standard deviation with $n$,
    censored values as censored), so it matches P08:
    $x_p = \hat{\mu} + z_p \hat{\sigma}$ for a normal fit, with $z_p$ the
    normal quantile (``quantile_factor``), and $\exp(\hat{m} + z_p
    \hat{s}_{\ln})$ for a lognormal one. It has no allowance for the
    uncertainty of a small sample, unlike EC7's fractile. ``side`` must agree
    with it: a percentile below 50 for ``"low"``, above for ``"high"``. The
    empirical percentile of the values is :func:`describe`'s.

    **Standard deviations** (``method="standard_deviations"``):
    $\bar{x} \mp k s$, with $k$ = ``standard_deviations``, above 0, and
    $\bar{x}$ and $s$ as for the characteristic value (lognormal:
    $\exp(m \mp k s_{\ln})$). Schneider's $k = 0.5$ (JRC Equation 20,
    p. 64) and the simplified fractile's $k = 1.75$ (Equation 23, p. 65) are
    values of $k$, not methods of their own.

    **Trends** (``trend="depth"`` or ``"elevation"``): a least-squares line
    $\hat{x}(z) = a_0 + a_1 z$ per group, with the residual standard
    deviation $s_e$ (with $n - 2$), as Bond & Harris (2008) give it in the
    JRC report (Equations 39-43, pp. 83-85):

    - characteristic, ``estimate="mean"``: the confidence band,
      $\hat{x}(z) \mp t_{0.95,\,n-2}\, s_e \sqrt{1/n + (z - \bar{z})^2 /
      \sum (z_i - \bar{z})^2}$;
    - characteristic, ``estimate="fractile"``: the prediction band, the same
      with $\sqrt{1 + 1/n + \dots}$;
    - percentile: $\hat{x}(z) + z_p s_e$; standard deviations:
      $\hat{x}(z) \mp k s_e$.

    The bands curve away from the data's center, so a line is given over its
    group's depths (elevations) only, never beyond. It needs at least 3
    values at 2 or more depths; ``coefficient_of_variation=`` and Type C
    are errors with a trend, since the report gives neither (p. 82).
    Lognormal: the line is through $\ln x$ and transformed back (§5.2.4,
    p. 86), so its mean is the median of $x$. Censored values and values
    with no depth (elevation) are left out of the line and counted
    (``count_censored``, ``count_blank_depth`` or
    ``count_blank_elevation``), with a warning and a note on which way the
    censored ones move it; ``count`` is then the values on the line. The
    line assumes a scatter that is the same at every depth, random and
    normal (p. 86): that isn't tested, and the result keeps the residuals
    (``groups[i]["line"]``) to look at.

    **Censored values** (refusals, ``>`` and ``<`` values, a refusal under
    ``spt_refusal_upper_limit``): in a group with any, $\bar{x}$ and $s$ (or
    $m$ and $s_{\ln}$) are the censored maximum-likelihood normal (or
    lognormal) fit's, as :func:`fit` gives it, so they aren't biased low at
    their limits. That $s$ is with $n$, and EC7's $k_n$ factors assume
    complete data; a note says so. $n$ counts every value, censored or not.
    A percentile is always of that fit.

    **Rows are chosen as by** :func:`fit`: non-plastic, assumed, text and
    blank rows, and bands, are left out and counted; sources aren't pooled
    unawares (``pool=``); the counts add up to the group's rows.

    **Warnings:** a value at or below 0 from a normal
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
    method : {"characteristic", "percentile", "standard_deviations"}
        The view: EC7's characteristic value, a percentile of the fitted
        distribution, or the mean less (or plus) a multiple of the standard
        deviation.
    side : {"low", "high"}
        The cautious side: ``"low"`` where a lower value is unfavorable (a
        strength), ``"high"`` where a higher one is (a load, a
        compressibility).
    distribution : {"normal", "lognormal"}
        The distribution the values are taken to follow.
    trend : {None, "depth", "elevation"}
        None: one value per group, constant with depth. ``"depth"`` or
        ``"elevation"``: a line with that column, which needs its unit like
        the value (``units=`` or ``attrs["units"]``); ``display_units=``
        converts it too.
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
    percentile : float
        For ``method="percentile"``: between 0 and 100, e.g. ``5``.
    standard_deviations : float
        For ``method="standard_deviations"``: the multiple $k$, above 0,
        e.g. ``0.5``.
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
        ``.to_frame()`` has one row per group, with ``value``, or for a
        trend the line's coefficients and its value at the top and base of
        the group's values.
        ``print(result)`` shows it with the inputs and the notes.

    Raises
    ------
    HangtuError
        For a missing or unknown view, side or distribution; an input the
        method needs left out, or one of another method given; an input out
        of range; ``trend=`` with ``coefficient_of_variation=`` or Type C;
        and the input errors of :func:`fit`.
    ColumnError
        For a missing column (the value's, or the trend's depth or
        elevation), or one that holds no numbers.
    UnitsError
        For a value column, or a trend's depth or elevation, whose unit is
        unknown.

    References
    ----------
    Bond, A. & Harris, A. (2008). *Decoding Eurocode 7*. Taylor & Francis,
    as the JRC report gives it (Equations 39-43).

    Orr, T., Sorgatz, J., Estaire, J. et al. (2025). *Determination of
    representative values from derived values for verification with limit
    states with EN 1997*. JRC, EUR 40260, doi:10.2760/0980105 (CC BY 4.0),
    which quotes EN 1997-1:2024.

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
        "percentile": percentile,
        "standard_deviations": standard_deviations,
    }
    method, side, distribution = check_view(method, side, distribution, trend, inputs)
    gamma2, capped = _sensitivity(inputs)
    inputs["sensitivity_index"] = gamma2
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
    # A trend's depth (elevation), or for a constant the column its design
    # lines are drawn against, when the data has one (spec decision 10).
    column = trend or next((c for c in TRENDS if c in read.frame.columns), None)
    vertical, vertical_unit = _vertical(read, column, trend, units, display_units)
    sign = -1.0 if side == "low" else 1.0
    groups, notes, at_or_below_zero = [], [], []
    left_out_of_trend = {"count_censored": 0, f"count_blank_{trend}": 0}
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
        if trend is not None:
            assert vertical is not None  # a trend's column is required
            line, record["counts"], record["reason"] = _trend(
                group, found.numbers, vertical, trend, method, sign, lognormal, inputs
            )
            for name in left_out_of_trend:
                left_out_of_trend[name] += record["counts"][name]
            if values.censored:
                notes.append(_censored_from_trend(group))
            if line is None:
                continue
            record["line"] = line
            record["vertical_range"] = (line["top"], line["base"])
            record["statistics"] = _trend_statistics(line, trend, method)
            ends = np.linspace(line["top"], line["base"], CURVE_POINTS)
            if not lognormal and trend_at(line, ends).min() <= 0:
                at_or_below_zero.append(group.label)
            continue
        record["vertical_range"] = _range(vertical, group.chosen, column)
        if values.count < MIN_COUNT:
            record["reason"] = f"fewer than {MIN_COUNT} values ({values.count})"
            continue
        if method == "percentile":
            assert percentile is not None  # required for the method
            outcome = _percentile(values, distribution, percentile)
        else:
            moments = _moments(values, lognormal)
            outcome = (
                None
                if moments is None
                else _characteristic(moments, values.count, sign, lognormal, inputs)
                if method == "characteristic"
                else _standard_deviations(moments, sign, lognormal, standard_deviations)
            )
        if outcome is None or not math.isfinite(outcome[0]):
            record["reason"] = (
                "the censored maximum-likelihood fit failed"
                if values.censored
                else "the fit failed"
            )
            continue
        result, record["statistics"] = outcome
        if not lognormal and result <= 0:
            at_or_below_zero.append(group.label)
        record["value"] = result
        if values.censored:
            notes.append(
                f"{group.label}: {values.censored} of {values.count} values "
                f"censored, {CENSORED[method]}"
            )

    _rows.warn_left_out(found.reasons, read.column, FUNCTION)
    censored, blank = left_out_of_trend.values()
    if censored or blank:
        listed = " and ".join(
            text
            for count, text in (
                (censored, f"{censored} censored values (count_censored)"),
                (blank, f"{blank} values with no {trend} (count_blank_{trend})"),
            )
            if count
        )
        warn(
            f"{FUNCTION} left {listed} of {read.column!r} out of the trend: a "
            f"line is fitted to measured values at a known {trend} only. The "
            "notes say which way censored values move it."
        )
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
            f"{FUNCTION} gives a {method.replace('_', ' ')} value of "
            f"{read.column!r} at or "
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
            _notes(
                notes, groups, found, include_assumed, lognormal, inputs, capped, trend
            )
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
        vertical=column,
        vertical_unit=vertical_unit,
        estimate=estimate,
        coefficient_of_variation=coefficient_of_variation,
        coefficient_of_variation_case=(
            None
            if method != "characteristic"
            else 2
            if coefficient_of_variation is None
            else 3
        ),
        scale_of_fluctuation=scale_of_fluctuation,
        failure_length=failure_length,
        sensitivity_index=gamma2,
        percentile=percentile,
        standard_deviations=standard_deviations,
        groups=tuple(groups),
    )


def check_view(
    method: Any, side: Any, distribution: Any, trend: Any, inputs: dict[str, Any]
) -> tuple[str, str, str]:
    """Check the view and its judgments (spec decision 1, criterion 1).

    It needs no data, so the judgments file's ``selection`` entries are
    checked by it when the file is opened (docs/analysis/judgments.md §5.9).
    ``inputs`` maps each name in ``INPUTS`` to its value or None.
    """
    example = EXAMPLES["characteristic"]
    for name, given, choices in (
        ("method", method, METHODS),
        ("side", side, SIDES),
        ("distribution", distribution, DISTRIBUTIONS),
    ):
        if given is None:
            raise HangtuError(
                f"{FUNCTION} needs {name}=, one of {_listed(choices)}: it is a "
                f"judgment, so it has no default. Example: {example}"
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
                f"judgment, so it has no default. Example: "
                f"{EXAMPLES[method]}"
            )
    if method == "characteristic":
        _check_characteristic(inputs, trend)
    elif method == "percentile":
        level = _number("percentile", inputs["percentile"])
        if not 0 < level < 100:
            raise HangtuError(
                f"{FUNCTION} percentile= is between 0 and 100, not {level:g}. "
                "Example: percentile=5"
            )
        if (side == "low") != (level < 50):
            raise HangtuError(
                f"{FUNCTION} with side={side!r} takes a percentile "
                f"{'below' if side == 'low' else 'above'} 50, not {level:g}: a "
                f'{side} P{level:g} is a slip. Example: side="low", percentile=5, '
                'or side="high", percentile=95.'
            )
    else:
        _positive("standard_deviations", inputs["standard_deviations"])
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
            "judgments, with no default. Example: "
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


def _characteristic(
    moments: tuple[float, float],
    n: int,
    sign: float,
    lognormal: bool,
    inputs: dict[str, Any],
) -> tuple[float, dict[str, float]]:
    """Return EC7's characteristic value and its statistics (spec decisions 3, 4)."""
    center, spread = moments
    assumed = inputs["coefficient_of_variation"]
    gamma2 = inputs["sensitivity_index"]
    if assumed is None:
        factor = float(_stats.t.ppf(CONFIDENCE, n - 1))
    else:
        factor = float(_stats.norm.ppf(CONFIDENCE))
    coefficient = factor * math.sqrt(gamma2 + 1 / n)
    if lognormal:
        deviation = spread if assumed is None else math.sqrt(math.log1p(assumed**2))
        result = math.exp(center + sign * coefficient * deviation)
        statistics = {
            "geometric_mean": math.exp(center),
            "geometric_standard_deviation": math.exp(deviation),
            "coefficient_of_variation": (
                math.sqrt(math.expm1(spread**2)) if assumed is None else assumed
            ),
        }
    else:
        result = (
            center + sign * coefficient * spread
            if assumed is None
            else center * (1 + sign * coefficient * assumed)
        )
        statistics = {
            "mean": center,
            "standard_deviation": spread,
            "coefficient_of_variation": _variation(center, spread, assumed),
        }
    return result, {
        **statistics,
        "quantile_factor": factor,
        "statistical_coefficient": coefficient,
        "sensitivity_index": gamma2,
    }


def _percentile(
    values: _fit.Values, distribution: str, level: float
) -> tuple[float, dict[str, float]] | None:
    """Return the percentile of ``fit()``'s maximum-likelihood fit (spec decision 5)."""
    try:
        parameters = _fit.estimate(distribution, values, (None, None))
    except Exception:  # SciPy raises several kinds
        return None
    if not all(math.isfinite(p) for p in parameters.values()):
        return None
    with np.errstate(all="ignore"):
        result = float(_fit.frozen(distribution, parameters).ppf(level / 100))
    statistics = (
        {
            "geometric_mean": parameters["scale"],
            "geometric_standard_deviation": math.exp(parameters["s"]),
        }
        if distribution == "lognormal"
        else {
            "mean": parameters["loc"],
            "standard_deviation": parameters["scale"],
            "coefficient_of_variation": _variation(
                parameters["loc"], parameters["scale"], None
            ),
        }
    )
    return result, {
        **statistics,
        "quantile_factor": float(_stats.norm.ppf(level / 100)),
    }


def _standard_deviations(
    moments: tuple[float, float], sign: float, lognormal: bool, multiple: Any
) -> tuple[float, dict[str, float]]:
    """Return the mean less (or plus) k standard deviations (spec decision 6)."""
    center, spread = moments
    if lognormal:
        return math.exp(center + sign * multiple * spread), {
            "geometric_mean": math.exp(center),
            "geometric_standard_deviation": math.exp(spread),
        }
    return center + sign * multiple * spread, {
        "mean": center,
        "standard_deviation": spread,
        "coefficient_of_variation": _variation(center, spread, None),
    }


def _variation(center: float, spread: float, assumed: float | None) -> float:
    """Return V_X: as assumed, else s / x̄ (NaN for a mean of 0)."""
    if assumed is not None:
        return assumed
    return spread / center if center else math.nan


def _moments(values: _fit.Values, lognormal: bool) -> tuple[float, float] | None:
    """Return the center and spread: of x, or of ln x when ``lognormal``.

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
        center, spread = math.log(parameters["scale"]), parameters["s"]
    else:
        center, spread = parameters["loc"], parameters["scale"]
    if not (math.isfinite(center) and math.isfinite(spread)):
        return None
    return center, spread


def _vertical(
    read: _rows.Input,
    column: str | None,
    trend: str | None,
    units: str | Mapping[str, str] | None,
    display_units: str | None,
) -> tuple[np.ndarray | None, str | None]:
    """Return each row's depth (elevation) and its unit, converted as the values are.

    A trend needs its column and the column's unit; a constant reads them for
    its design lines when the data has them, and never guesses a unit. A
    blank or text cell is NaN, left out of the line and counted.
    """
    frame = read.frame
    if trend is not None and trend not in frame.columns:
        raise ColumnError(
            f"{FUNCTION} with trend={trend!r} needs the column {trend!r}, which the "
            f"data doesn't have. Available columns: "
            f"{', '.join(map(str, frame.columns)) or 'none'}. Add it, or use "
            "trend=None for one value per group."
        )
    if column is None:
        return None, None
    explicit = (
        {column: units[column]}
        if isinstance(units, Mapping) and column in units
        else {}
    )
    if trend is not None:
        unit = _units.resolve_units(frame, [column], explicit, analysis=True)[column]
    else:
        unit = explicit.get(column, _units.units_of(frame).get(column))
    vertical = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    if display_units is not None and unit is not None:
        return _units.to_display(vertical, unit, "length", display_units)
    return vertical, unit


def _range(
    vertical: np.ndarray | None, chosen: np.ndarray, column: str | None
) -> tuple[float, float] | None:
    """Return a constant group's shallowest and deepest value, None without depths."""
    if vertical is None:
        return None
    z = vertical[chosen]
    z = z[np.isfinite(z)]
    if not z.size:
        return None
    return (
        (float(z.min()), float(z.max()))
        if column == "depth"
        else (
            float(z.max()),
            float(z.min()),
        )
    )


def _trend(
    group: _fit.Group,
    numbers: np.ndarray,
    vertical: np.ndarray,
    trend: str,
    method: str,
    sign: float,
    lognormal: bool,
    inputs: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, int], str | None]:
    """Fit a group's line with depth (elevation): the line, the counts, the reason.

    Bond & Harris (2008) as the JRC gives it (Equations 39-43, pp. 83-85;
    spec decisions 7-9). Censored values and values with no depth are left
    out, so ``count`` is the values on the line.
    """
    on_line = group.exact & np.isfinite(vertical)
    counts = {
        **group.counts,
        "count": int(on_line.sum()),
        f"count_blank_{trend}": int((group.exact & ~on_line).sum()),
    }
    z = vertical[on_line]
    y = np.log(numbers[on_line]) if lognormal else numbers[on_line]
    n = len(z)
    if n < MIN_TREND_COUNT:
        return (
            None,
            counts,
            f"fewer than {MIN_TREND_COUNT} values with a {trend} ({n}) for a line",
        )
    line = line_fit(z, y, x_name=trend)
    if line.no_fit_reason is not None:
        return None, counts, f"no line: {line.no_fit_reason}"
    residuals = np.array(line.residuals)
    deviation = math.sqrt(float(np.sum(residuals**2)) / (n - 2))
    if method == "characteristic":
        factor = float(_stats.t.ppf(CONFIDENCE, n - 2))
        band = "confidence" if inputs["estimate"] == "mean" else "prediction"
        multiple = sign * factor
    elif method == "percentile":
        factor = float(_stats.norm.ppf(inputs["percentile"] / 100))
        band, multiple = None, factor
    else:
        factor, band = math.nan, None
        multiple = sign * float(inputs["standard_deviations"])
    shallow, deep = (z.min(), z.max()) if trend == "depth" else (z.max(), z.min())
    return (
        {
            "intercept": line.intercept,
            "slope": line.slope,
            "count": n,
            "mean_vertical": float(z.mean()),
            "sum_of_squares": float(np.sum((z - z.mean()) ** 2)),
            "residual_standard_deviation": deviation,
            "r_squared": line.r_squared,
            "band": band,
            "quantile_factor": factor,
            "multiple": multiple,
            "lognormal": lognormal,
            "top": float(shallow),
            "base": float(deep),
            "vertical": [float(v) for v in z],
            "residuals": [float(r) for r in residuals],
        },
        counts,
        None,
    )


def _trend_statistics(
    line: dict[str, Any], trend: str, method: str
) -> dict[str, float]:
    """Return a trend group's columns of ``to_frame()``."""
    top, base = trend_at(line, [line["top"], line["base"]])
    return {
        "line_intercept": line["intercept"],
        "line_slope": line["slope"],
        "residual_standard_deviation": line["residual_standard_deviation"],
        "r_squared": line["r_squared"],
        **(
            {}
            if method == "standard_deviations"
            else {"quantile_factor": line["quantile_factor"]}
        ),
        f"{trend}_top": line["top"],
        f"{trend}_base": line["base"],
        "value_top": float(top),
        "value_base": float(base),
    }


def _censored_from_trend(group: _fit.Group) -> str:
    """Say which way leaving out a group's censored values moves its line.

    Spec decision 8.
    """
    values = group.values
    at_least = values.right.size + len(values.interval)
    at_most = values.left.size
    lower = (
        "lower than the data, so a low-side line is more cautious and a high-side "
        "line less"
    )
    higher = (
        "higher than the data, so a low-side line is less cautious and a high-side "
        "line more"
    )
    if at_least and at_most:
        effect = (
            f"the {at_least} at least their value pull the line {lower}; the "
            f"{at_most} at most their value pull it {higher}"
        )
    elif at_least:
        effect = f"they are at least their value, so the line is {lower}"
    else:
        effect = f"they are at most their value, so the line is {higher}"
    return (
        f"{group.label}: {values.censored} censored values left out of the "
        f"trend; {effect}."
    )


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
    trend: str | None,
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
    if trend is not None:
        notes.append(
            f"Trend: a least-squares line on {trend} (Bond & Harris 2008, JRC "
            "Equations 39-43, pp. 83-85), given over each group's values only. "
            "It assumes the scatter about the line is the same at every "
            f"{trend}, random and normal (JRC p. 86); that isn't tested, so "
            "look at the residuals."
        )
    if lognormal:
        notes.append(
            "Lognormal: the formulae are applied to ln x and transformed back "
            "(JRC Annex IV)."
            if trend is None
            else "Lognormal: the line is fitted to ln x and transformed back "
            "(JRC §5.2.4, p. 86), so its mean is the median of x."
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
