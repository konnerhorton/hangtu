"""s_u from SPT (sheet 05; docs/work/m13b2-spt-strength-history.md, Decision 1)."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis._overburden import PA
from hangtu.analysis.correlations import _framework


def undrained_shear_strength_terzaghi_peck_1967(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate a band of undrained shear strength s_u of clay from field N.

    Terzaghi & Peck (1967), p. 347, as Kulhawy & Mayne (1990) give it in
    EPRI EL-6800, Table 4-10, p. 4-54, with $p_a$ = 100 kPa:

    | N (blows/ft) | s_u / p_a |
    |---|---|
    | 0 to < 2 | 0 to 0.125 |
    | 2 to < 4 | 0.125 to 0.25 |
    | 4 to < 8 | 0.25 to 0.5 |
    | 8 to < 15 | 0.5 to 1 |
    | 15 to < 30 | 1 to 2 |
    | 30 or more | above 2 (open) |

    Each class includes its lower N, as ``ht.analysis.spt_class(...,
    table="cohesive")`` does with the same boundaries, so the band and the
    consistency class of a test agree. The source gives the lowest class as
    "< 1/8"; its lower bound of 0 is hangtu's, since s_u can't be negative.

    **A band, not a value.** The estimate is the band, in
    ``undrained_shear_strength_lower`` and ``undrained_shear_strength_upper``;
    ``undrained_shear_strength`` stays blank, since the source gives no
    central value and hangtu doesn't invent one. ``ht.plot.profile()`` draws
    each band as a bar at its depth, and the open class as a caret ▷ at its
    lower bound.

    **Input:** ``spt_n``, field N as measured. The table predates energy
    correction: its N values "have not all been standardized to the same
    energy level" (EPRI, p. 4-53), so N60 isn't read and isn't converted to
    the hammers of the time. There is no argument to read another column
    (SPEC §4).

    **Valid for:** clays, and N of 0 or more. The table was "developed
    primarily using unconfined compression tests" (EPRI, p. 4-53).

    **Scatter:** not stated. FHWA GEC 5 (Loehr et al. 2016, p. 7-38): "SPT
    N-values are generally a poor predictor of undrained shear strength".
    Use the band to check measured s_u, not in its place.

    **Assumptions:** EPRI's straight-line fit through the table,
    s_u/p_a ≈ 0.06 N (Eq. 4-59, p. 4-53), isn't built, so one table isn't
    counted twice when correlations are compared.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside CL and CH, hangtu's reading of "clays", not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **No estimate** (NaN in all three columns, with ``correlation_note``
    saying why and one warning counting them): a blank N ("input blank"), a
    refusal from ``spt_refusal`` ("refusal"), and N below 0 ("below range").

    **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n``.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N is a count, so
        none is needed.
    display_units : {"US", "SI"}, optional
        The units of the band: psf for US, kPa for SI. Defaults to
        ``ht.settings.display_units``.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``undrained_shear_strength`` (blank),
        ``undrained_shear_strength_lower`` and
        ``undrained_shear_strength_upper`` (blank for N of 30 or more),
        ``correlation_name``
        ("undrained_shear_strength_terzaghi_peck_1967"),
        ``correlation_note`` and ``correlation_input`` (blank unless an
        input was another correlation's estimate). No row is dropped or
        reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Terzaghi, K., and Peck, R. B. (1967). *Soil Mechanics in Engineering
    Practice*, 2nd ed. Wiley, New York.

    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> clay = spt[spt["geology_unit"] == "Alluvium"]
    >>> est = correlations.undrained_shear_strength_terzaghi_peck_1967(clay)
    >>> fig, ax = ht.plot.profile(est, "undrained_shear_strength")
    """
    name = "undrained_shear_strength_terzaghi_peck_1967"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    n = values["spt_n"]
    starts = np.array([band["spt_n"] for band in item["bands"]], dtype=float)
    lowers = np.array([band["lower"] for band in item["bands"]], dtype=float)
    uppers = np.array(
        [np.nan if band["upper"] is None else band["upper"] for band in item["bands"]]
    )
    known = np.isfinite(n) & (n >= starts[0])
    index = np.searchsorted(starts, np.where(known, n, starts[0]), side="right") - 1
    lower = np.where(known, lowers[index] * PA, np.nan)
    upper = np.where(known, uppers[index] * PA, np.nan)
    note = _framework.notes(df, item, values, uscs)
    central = np.full(len(df), np.nan)
    return _framework.estimate(
        df, name, central, note, display_units, uscs=uscs, lower=lower, upper=upper
    )


def undrained_shear_strength_stroud_1974(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the undrained shear strength s_u of clay from N60 and PI.

    $$
    s_u = f_1 \, N_{60} \, p_a / 100
    $$

    with $p_a$ = 100 kPa, so $s_u = f_1 N_{60}$ in kPa. Stroud (1974), as
    FHWA GEC 5 gives it: Loehr et al. (2016), Eq. 7.19, p. 7-38. GEC 5 gives
    two values of $f_1$, 4.5 for PI ≳ 30 and 5.5 for PI ≅ 15, and nothing
    between them, so:

    | PI | Estimate |
    |---|---|
    | 30 or more | $s_u$ = 4.5 $N_{60}$ kPa |
    | 15 to < 30 | the band 4.5 $N_{60}$ to 5.5 $N_{60}$ kPa, no central value |
    | below 15 | none ("below range") |

    **Nothing is interpolated.** For 15 ≤ PI < 30, the band is in
    ``undrained_shear_strength_lower`` and ``undrained_shear_strength_upper``,
    and ``undrained_shear_strength`` stays blank; ``ht.plot.profile()`` draws
    it as a bar. For PI ≥ 30 the bounds are blank and the value is the
    estimate.

    **Inputs:** ``spt_n60`` (from ``ht.analysis.spt()`` or ``p.spt()``) and
    ``plasticity_index`` (from ``ht.analysis.add_judgment()``). PI is rarely
    tested at the SPT depth, so it is a judgment by geology unit; the nearest
    Atterberg test isn't used. There is no argument to read another column
    (SPEC §4).

    **Valid for:** clays with PI of 15 or more. No N range is stated.

    **Scatter:** not stated. GEC 5 (p. 7-38) gives these as "somewhat lower
    bound values", and says "SPT N-values are generally a poor predictor of
    undrained shear strength". Use the estimate to check measured s_u, not
    in its place.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside CL and CH, hangtu's reading of "clays", not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N60 or PI ("input blank"), a refusal
    from ``spt_refusal`` ("refusal"), and PI below 15 ("below range").

    **Judgments taken:** none here; PI is the judgment, put on the rows by
    ``add_judgment()`` and recorded in ``df.attrs["judgments"]``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60`` and ``plasticity_index``.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N60 and PI need
        none.
    display_units : {"US", "SI"}, optional
        The units of s_u: psf for US, kPa for SI. Defaults to
        ``ht.settings.display_units``.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``undrained_shear_strength``,
        ``undrained_shear_strength_lower`` and
        ``undrained_shear_strength_upper``, ``correlation_name``
        ("undrained_shear_strength_stroud_1974"), ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Stroud, M. A. (1974). The standard penetration test in insensitive clays
    and soft rocks. *Proceedings, European Symposium on Penetration Testing
    (ESOPT-II)*, Vol. 2, pp. 367-375.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> clay = ht.analysis.add_judgment(clay, "plasticity_index")
    >>> est = correlations.undrained_shear_strength_stroud_1974(clay)
    """
    name = "undrained_shear_strength_stroud_1974"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    n60 = values["spt_n60"]
    index = values["plasticity_index"]
    (low_range, high_range) = item["bands"]
    high = index >= high_range["plasticity_index"]
    middle = (index >= low_range["plasticity_index"]) & ~high
    scale = n60 * PA / 100.0
    central = np.where(high, high_range["lower"] * scale, np.nan)
    lower = np.where(middle, low_range["lower"] * scale, np.nan)
    upper = np.where(middle, low_range["upper"] * scale, np.nan)
    note = _framework.notes(df, item, values, uscs)
    return _framework.estimate(
        df, name, central, note, display_units, uscs=uscs, lower=lower, upper=upper
    )
