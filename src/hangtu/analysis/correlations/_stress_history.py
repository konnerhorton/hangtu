"""σ′p, OCR and K0 from SPT (sheets 06, 07; docs/work/m13b2-spt-strength-history.md).

All three were derived on field N, before energy correction was practice, so
they read ``spt_n`` (Decision 4).
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis._overburden import PA
from hangtu.analysis.correlations import _framework


def _normalized_n(values: dict[str, np.ndarray]) -> np.ndarray:
    """N pa / σ′v0, the term OCR's and K0's ranges are given on (Decision 5)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return values["spt_n"] * PA / values["effective_vertical_stress"]


def preconsolidation_stress_mayne_kemper_1988(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the preconsolidation stress σ′p of clay from field N.

    $$
    \sigma'_p = 0.47 \, N \, p_a
    $$

    with $p_a$ = 100 kPa, so $\sigma'_p$ = 47 N kPa. Mayne & Kemper (1988),
    p. 144, as Kulhawy & Mayne (1990) give it in EPRI EL-6800, Fig. 3-9,
    p. 3-10.

    **Input:** ``spt_n``, field N as measured. The data predate energy
    correction, so N60 isn't read and isn't converted to the hammers of the
    time. There is no argument to read another column (SPEC §4).

    **Valid for:** clays, and 0.5 ≤ N ≤ 200, the chart's N axis.

    **Scatter:** n = 126, r² = 0.699, S.D. = 4.37 pa, on 49 intact and 2
    fissured clays; the fissured clays plot above the trend. SPT N is a poor
    predictor in clay: use the estimate to check oedometer σ′p, not in its
    place.

    **Assumptions:** σ′p and OCR are two regressions on different data
    (0.47 here, 0.58 for OCR), so they are two correlations; an OCR is not
    derived from this σ′p.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside CL and CH, hangtu's reading of "clays", not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and N below 0.5 or above 200 ("below
    range", "above range").

    **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n``.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N is a count, so
        none is needed.
    display_units : {"US", "SI"}, optional
        The units of σ′p: psf for US, kPa for SI. Defaults to
        ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``preconsolidation_stress``,
        ``correlation_name`` ("preconsolidation_stress_mayne_kemper_1988"),
        ``correlation_note`` and ``correlation_input`` (blank unless an input
        was another correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Mayne, P. W., and Kemper, J. B. (1988). Profiling OCR in stiff clays by
    CPT and SPT. *Geotechnical Testing Journal*, 11(2), 139-147.

    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> est = correlations.preconsolidation_stress_mayne_kemper_1988(clay)
    >>> fig, ax = ht.plot.profile(est, "preconsolidation_stress")
    """
    name = "preconsolidation_stress_mayne_kemper_1988"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    stress = 0.47 * values["spt_n"] * PA
    note = _framework.notes(df, item, values, uscs)
    return _framework.estimate(df, name, stress, note, display_units, uscs=uscs)


def overconsolidation_ratio_mayne_kemper_1988(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the overconsolidation ratio OCR of clay from field N and σ′v0.

    $$
    \mathrm{OCR} = 0.58 \, \frac{N \, p_a}{\sigma'_{v0}}
    $$

    with $\sigma'_{v0}$ the effective vertical stress at the test and $p_a$
    = 100 kPa (converted with pint, so a $\sigma'_{v0}$ in psf gives the same
    OCR). Mayne & Kemper (1988), p. 143, as Kulhawy & Mayne (1990) give it in
    EPRI EL-6800, Fig. 3-18, p. 3-18.

    **Inputs:** ``spt_n``, field N as measured, and
    ``effective_vertical_stress`` (from ``ht.analysis.vertical_stress()``),
    with its units. The data predate energy correction, so N60 isn't read.
    There is no argument to read another column (SPEC §4).

    **Valid for:** clays, and 1 ≤ N pa/σ′v0 ≤ 100, the chart's axis (OCR 1
    to 50); σ′v0 must be greater than 0.

    **Scatter:** n = 112, r² = 0.661, S.D. = 3.82, on 48 intact and 3
    fissured clays. SPT N is a poor predictor in clay: use the estimate to
    check oedometer OCR, not in its place.

    **Assumptions:** a separate regression from σ′p's (0.58 here, 0.47 for
    σ′p), on different data; OCR isn't σ′p / σ′v0 from that correlation.
    σ′v0 carries the unit weights and water levels of ``vertical_stress()``;
    a σ′v0 too high gives an OCR too low, which is unconservative for
    settlement.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside CL and CH, hangtu's reading of "clays", not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N or σ′v0 ("input blank"), a refusal
    from ``spt_refusal`` ("refusal"), σ′v0 of 0 or less or N pa/σ′v0 below 1
    ("below range"), and N pa/σ′v0 above 100 ("above range").

    **Judgments taken:** none here; σ′v0 carries those of
    ``vertical_stress()``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n`` and ``effective_vertical_stress``.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. Only
        ``effective_vertical_stress`` needs units.
    display_units : {"US", "SI"}, optional
        Accepted for a common signature; OCR is dimensionless.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``overconsolidation_ratio``,
        ``correlation_name`` ("overconsolidation_ratio_mayne_kemper_1988"),
        ``correlation_note`` and ``correlation_input`` (blank unless an input
        was another correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Mayne, P. W., and Kemper, J. B. (1988). Profiling OCR in stiff clays by
    CPT and SPT. *Geotechnical Testing Journal*, 11(2), 139-147.

    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> clay = ht.analysis.vertical_stress(clay, stratigraphy=p.stratigraphy())
    >>> est = correlations.overconsolidation_ratio_mayne_kemper_1988(clay)
    >>> fig, ax = ht.plot.profile(est, "overconsolidation_ratio", log=True)
    """
    name = "overconsolidation_ratio_mayne_kemper_1988"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    values["normalized_n"] = _normalized_n(values)
    ratio = 0.58 * values["normalized_n"]
    note = _framework.notes(df, item, values, uscs)
    return _framework.estimate(df, name, ratio, note, display_units, uscs=uscs)


def at_rest_earth_pressure_coefficient_kulhawy_et_al_1989(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the at-rest earth pressure coefficient K0 of clay from field N.

    $$
    K_0 = 0.073 \, \frac{N \, p_a}{\sigma'_{v0}}
    $$

    with $\sigma'_{v0}$ the effective vertical stress at the test and $p_a$
    = 100 kPa (converted with pint). Kulhawy et al. (1989), p. 129, as
    Kulhawy & Mayne (1990) give it in EPRI EL-6800, Eq. 3-31, p. 3-27, and
    Fig. 3-30, p. 3-28.

    **Inputs:** ``spt_n``, field N as measured, and
    ``effective_vertical_stress`` (from ``ht.analysis.vertical_stress()``),
    with its units. EPRI gives the input as N, not N60: some later sources
    write N60, but the data predate energy correction. There is no argument
    to read another column (SPEC §4).

    **Valid for:** clays, and 0 < N pa/σ′v0 ≤ 60, the chart's axis; σ′v0
    must be greater than 0.

    **Scatter:** n = 57, r² = 0.771, S.D. = 0.43, on 13 intact and 5
    fissured clays.

    **Bias:** large. Ching & Schweckendiek (2021), evaluating
    0.073 N60/(σ′v0/p_a) on the TC304 clay database CLAY/12/3997 (n = 74),
    Table 5.2, p. 178, found the mean of measured over predicted K0 to be
    b = 2.16, with COV δ = 0.70 (§5.1, p. 176): measured K0 averaged about
    twice the estimate. The estimate is likely low; don't use it for design
    without measured K0.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside CL and CH, hangtu's reading of "clays", not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N or σ′v0 ("input blank"), a refusal
    from ``spt_refusal`` ("refusal"), σ′v0 or N pa/σ′v0 of 0 or less ("below
    range"), and N pa/σ′v0 above 60 ("above range").

    **Judgments taken:** none here; σ′v0 carries those of
    ``vertical_stress()``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n`` and ``effective_vertical_stress``.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. Only
        ``effective_vertical_stress`` needs units.
    display_units : {"US", "SI"}, optional
        Accepted for a common signature; K0 is dimensionless.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``at_rest_earth_pressure_coefficient``,
        ``correlation_name``
        ("at_rest_earth_pressure_coefficient_kulhawy_et_al_1989"),
        ``correlation_note`` and ``correlation_input`` (blank unless an input
        was another correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Kulhawy, F. H., Jackson, C. S., and Mayne, P. W. (1989). First-order
    estimation of K0 in sands and clays. *Foundation Engineering: Current
    Principles and Practices*, ASCE, New York, 121-134.

    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Ching, J., and Schweckendiek, T. (2021). Chapter 5 of ISSMGE TC304,
    *State-of-the-art review of inherent variability and transformation
    uncertainty in geotechnical properties*.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> clay = ht.analysis.vertical_stress(clay, stratigraphy=p.stratigraphy())
    >>> est = correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989(
    ...     clay
    ... )
    """
    name = "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    values["normalized_n"] = _normalized_n(values)
    coefficient = 0.073 * values["normalized_n"]
    note = _framework.notes(df, item, values, uscs)
    return _framework.estimate(df, name, coefficient, note, display_units, uscs=uscs)
