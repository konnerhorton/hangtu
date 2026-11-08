"""φ′ from SPT (sheet 04; docs/work/m13b1-spt-framework.md, Decision 7)."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis._overburden import PA
from hangtu.analysis.correlations import _framework


def effective_friction_angle_hatanaka_uchida_1996(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the effective friction angle φ′ of sand from (N1)60.

    $$
    \phi' = \left(15.4 \, (N_1)_{60}\right)^{0.5} + 20°
    $$

    Hatanaka & Uchida (1996) Eq. 8 at 60 % energy, as FHWA GEC 5 gives it:
    Loehr et al. (2016), Eq. 7.23, p. 7-55. The source's form,
    $\phi' = (20 N_1)^{0.5} + 20°$ (Eq. 6, p. 3; Eq. 8, p. 7), is for $N_1$
    measured with the Japanese "tombi" trip hammer at 78 % energy, with
    $N_1 = N / (\sigma'_v / 98)^{0.5}$ ($\sigma'_v$ in kPa, Liao & Whitman's
    C_N with no cap); 15.4 = 20 (60 / 78), rounded.

    **Input:** ``spt_n1_60``, from ``ht.analysis.spt_n1_60()``. It is the only
    column read: field N or N60 can't be passed instead, and there is no
    argument to choose another column.

    **Valid for:** relatively clean fine to medium sands, and
    4.55 ≤ (N1)60 ≤ 39, the source's 3.5 ≤ N1 ≤ 30 at 78 % energy
    (Conclusions, p. 8). Not for micaceous sands or gravelly soils (GEC 5,
    p. 7-55). The data are drained triaxial compression tests on in situ
    frozen samples of sands from six sites in Japan, including volcanic
    Shirasu.

    **Scatter:** most of the data within ±3° (p. 7).

    **Assumptions:** φ′ is the peak angle in triaxial compression. NASEM
    (2024, Table 2.2.1) prints the 78 % form against (N1)60, which would
    overstate φ′ by up to about 3°; hangtu follows the source and GEC 5.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside SP, SW, SP-SM and SW-SM, hangtu's reading of "relatively clean"
    sands, not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **Bounded estimates** (``correlation_qualifier`` ``>`` or ``<``, with
    ``correlation_note`` saying why and one warning counting them): φ′ rises
    with (N1)60, so a refusal from ``spt_refusal`` gives at least the
    estimate at its (N1)60 ("at least: refusal"), (N1)60 above 39 at least
    the estimate at 39 (44.5°), and (N1)60 below 4.55 at most the estimate at
    4.55 (28.4°). The input is never extrapolated: a bound is the estimate at
    the range's end.

    **No estimate** (NaN, with ``correlation_note`` saying why and one warning
    counting them): a blank (N1)60 ("input blank"), and a refusal with
    (N1)60 below 4.55 ("refusal"), which bounds nothing.

    **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n1_60``.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. (N1)60 is a
        count, so none is needed.
    display_units : {"US", "SI"}, optional
        Accepted for a common signature; φ′ is in degrees in both.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``effective_friction_angle`` (degrees),
        ``correlation_name``
        ("effective_friction_angle_hatanaka_uchida_1996"),
        ``correlation_qualifier``, ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or
        reordered. ``df.attrs["correlations"]`` holds every correlation's
        entry from ``config/correlations.yaml``; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Hatanaka, M., and Uchida, A. (1996). Empirical correlation between
    penetration resistance and internal friction angle of sandy soils.
    *Soils and Foundations*, 36(4), 1-9.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")
    >>> sand = spt[spt["geology_unit"] == "Terrace"]
    >>> from hangtu.analysis import correlations
    >>> est = correlations.effective_friction_angle_hatanaka_uchida_1996(sand)
    >>> est[["depth", "spt_n1_60", "effective_friction_angle", "correlation_note"]]
    """
    name = "effective_friction_angle_hatanaka_uchida_1996"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    note = _framework.notes(df, item, values, uscs)
    values, bounded = _framework.bound(df, item, values, note)
    with np.errstate(invalid="ignore"):
        angle = np.sqrt(15.4 * values["spt_n1_60"]) + 20.0
    return _framework.estimate(
        df, name, angle, note, display_units, uscs=uscs, bounded=bounded
    )


def effective_friction_angle_kulhawy_mayne_1990(
    df: pd.DataFrame,
    *,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the effective friction angle φ′ of sand from N60 and σ′v.

    $$
    \phi' = \arctan\left[\left(\frac{N_{60}}
        {12.2 + 20.3 \, \sigma'_v / p_a}\right)^{0.34}\right]
    $$

    with $\sigma'_v$ the effective vertical stress at the test and $p_a$ =
    100 kPa (converted with pint, so a $\sigma'_v$ in psf gives the same φ′).
    Kulhawy & Mayne (1990), Eq. 4-11, an approximation of Schmertmann's
    (1975) chart, as FHWA GEC 5 gives it: Loehr et al. (2016), Eq. 7.22 and
    Fig. 7-41, p. 7-54 to 7-55.

    **Inputs:** ``spt_n60`` (from ``ht.analysis.spt()`` or ``p.spt()``) and
    ``effective_vertical_stress`` (from ``ht.analysis.vertical_stress()``),
    with its units. GEC 5 gives the input as N60, not field N or (N1)60: the
    overburden is in the equation. There is no argument to read another N
    column.

    **Valid for:** relatively clean sands, within the chart's axes:
    0 < σ′v ≤ 300 kPa and N60 ≤ 60.

    **Scatter:** none stated.

    **Assumptions:** φ′ is the peak angle. GEC 5 calls the relation
    "somewhat conservative, especially for depths less than 6 ft" (1.8 m);
    shallow tests are not corrected for it.

    **Soil type** is read only with ``uscs=``; by default, pass the rows the
    correlation applies to, as for ``ht.analysis.spt_class()``. With
    ``uscs="proposed"`` it reads ``uscs_symbol`` and gives no estimate
    outside SP, SW, SP-SM and SW-SM, hangtu's reading of "relatively clean"
    sands, not the source's ("not
    for this soil"), or where the symbol is blank ("soil type unknown"). A
    list of groups replaces these.

    **Bounded estimates** (``correlation_qualifier`` ``>``, with
    ``correlation_note`` saying why and one warning counting them): φ′ rises
    with N60 at a given σ′v, so a refusal from ``spt_refusal`` gives at least
    the estimate at its N60 ("at least: refusal"), and N60 above 60 at least
    the estimate at 60. N60 is never extrapolated: a bound is the estimate at
    the range's end.

    **No estimate** (NaN, with ``correlation_note`` saying why and one warning
    counting them): a blank N60 or σ′v ("input blank"), σ′v of 0 or less
    ("below range"), and σ′v above 300 kPa ("above range"), whatever N60 is
    and whether or not it is a refusal. σ′v is never clipped or extrapolated.

    **Judgments taken:** none here; σ′v carries the unit weights and water
    levels of ``vertical_stress()``.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60`` and ``effective_vertical_stress``.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. Only
        ``effective_vertical_stress`` needs units.
    display_units : {"US", "SI"}, optional
        Accepted for a common signature; φ′ is in degrees in both.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for hangtu's, above, or a list of your own. By default
        no soil type is read.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``effective_friction_angle`` (degrees),
        ``correlation_name`` ("effective_friction_angle_kulhawy_mayne_1990"),
        ``correlation_qualifier``, ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or
        reordered. ``df.attrs["correlations"]`` holds every correlation's
        entry from ``config/correlations.yaml``; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> sand = spt[spt["geology_unit"] == "Terrace"]
    >>> from hangtu.analysis import correlations
    >>> est = pd.concat([
    ...     correlations.effective_friction_angle_hatanaka_uchida_1996(sand),
    ...     correlations.effective_friction_angle_kulhawy_mayne_1990(sand),
    ... ])
    >>> fig, ax = ht.plot.profile(
    ...     est, value="effective_friction_angle", color_by="correlation_name"
    ... )
    """
    name = "effective_friction_angle_kulhawy_mayne_1990"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    note = _framework.notes(df, item, values, uscs)
    values, bounded = _framework.bound(df, item, values, note)
    n60 = values["spt_n60"]
    stress = values["effective_vertical_stress"]
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = n60 / (12.2 + 20.3 * stress / PA)
        angle = np.degrees(np.arctan(ratio**0.34))
    return _framework.estimate(
        df, name, angle, note, display_units, uscs=uscs, bounded=bounded
    )
