"""φ′ from SPT (sheet 04; docs/work/m13b1-spt-framework.md, Decision 7)."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis.correlations import _framework


def hatanaka_uchida_1996(
    df: pd.DataFrame,
    *,
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
    argument to choose another column (SPEC §4).

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

    **Soil type isn't read.** Pass the rows the correlation applies to, as
    for ``ht.analysis.spt_class()``.

    **No estimate** (NaN, with ``correlation_note`` saying why and one warning
    counting them): a blank (N1)60 ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and (N1)60 below 4.55 or above 39 ("below
    range", "above range"). Values are never clipped or extrapolated.

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

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``effective_friction_angle`` (degrees),
        ``correlation_name`` ("hatanaka_uchida_1996") and ``correlation_note``.
        No row is dropped or reordered. ``df.attrs["correlations"]`` holds
        every correlation's entry from ``config/correlations.yaml``; see
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
    >>> est = ht.analysis.correlations.hatanaka_uchida_1996(sand)
    >>> est[["depth", "spt_n1_60", "effective_friction_angle", "correlation_note"]]
    """
    name = "hatanaka_uchida_1996"
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    n1_60 = values["spt_n1_60"]
    with np.errstate(invalid="ignore"):
        angle = np.sqrt(15.4 * n1_60) + 20.0
    note = _framework.notes(df, item, values)
    return _framework.estimate(df, name, angle, note, display_units)
