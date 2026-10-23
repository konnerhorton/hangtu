"""(N1)60: N60 corrected for overburden (docs/work/m13b1-spt-framework.md, Decision 1).

C_N is computed in kPa, with pa = 100 kPa converted with pint, so a σ′v in
psf gives the same result.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu import units as _units
from hangtu._data import numeric_column, rows_text
from hangtu.errors import ColumnError, HangtuError, warn

#: Atmospheric pressure, pa (Youd et al. 2001, p. 300), shared with the correlations.
PA = 100.0  # kPa
#: The largest C_N either method gives (Youd et al. 2001, p. 300).
CAP = 1.7
#: Above this σ′v, C_N "should be estimated by other means" (Youd et al. 2001).
MAX_STRESS = 300.0  # kPa
OUTPUT_COLUMNS = ("spt_overburden_correction", "spt_n1_60")
SOURCE = (
    "Youd et al. (2001), J. Geotech. Geoenviron. Eng. 127(4), 297-313, "
    "Eq. 9 and 10, p. 300"
)

_KILOPASCAL = _units.ureg.kilopascal
_MADE_BY = {
    "spt_n60": "ht.analysis.spt() or p.spt(), with an energy ratio",
    "effective_vertical_stress": "ht.analysis.vertical_stress()",
}


def liao_whitman_1986(stress: np.ndarray) -> np.ndarray:
    """C_N = (pa / σ′v)^0.5, uncapped, with σ′v in kPa."""
    with np.errstate(divide="ignore"):
        return np.sqrt(PA / stress)


def kayen_1992(stress: np.ndarray) -> np.ndarray:
    """C_N = 2.2 / (1.2 + σ′v / pa), uncapped, with σ′v in kPa."""
    return 2.2 / (1.2 + stress / PA)


METHODS = {
    "liao_whitman_1986": (
        liao_whitman_1986,
        "Liao & Whitman (1986), after Youd et al. (2001) Eq. 9",
    ),
    "kayen_1992": (kayen_1992, "Kayen et al. (1992), after Youd et al. (2001) Eq. 10"),
}


def stress_kpa(df: pd.DataFrame, units: Mapping[str, str] | None) -> np.ndarray:
    """Return ``effective_vertical_stress`` in kPa, its units resolved per SPEC §2.6."""
    values = numeric_column(df, "effective_vertical_stress")
    unit = _units.resolve_units(df, ["effective_vertical_stress"], units, analysis=True)
    source = _units.parse_unit(
        unit["effective_vertical_stress"], "effective_vertical_stress"
    )
    return _units.convert(values, source, "stress", _KILOPASCAL)


def check_columns(
    df: pd.DataFrame, columns: list[str], made_by: Mapping[str, str]
) -> None:
    """Raise naming each missing column and the function that adds it."""
    if not isinstance(df, pd.DataFrame):
        raise HangtuError(f"df must be a pandas DataFrame, not {type(df).__name__}.")
    missing = [column for column in columns if column not in df.columns]
    if missing:
        hints = "; ".join(
            f"{column!r} comes from {made_by[column]}" for column in missing
        )
        raise ColumnError(
            f"Column{'s' if len(missing) > 1 else ''} "
            f"{', '.join(map(repr, missing))} not found: {hints}. Run "
            f"{'them' if len(missing) > 1 else 'it'} first."
        )


def spt_n1_60(
    df: pd.DataFrame, *, method: str, units: Mapping[str, str] | None = None
) -> pd.DataFrame:
    r"""Add the overburden correction C_N and (N1)60 to SPT results.

    $$
    (N_1)_{60} = C_N \, N_{60}
    $$

    with $C_N$ by ``method``, $\sigma'_v$ the effective vertical stress at
    the test and $p_a$ = 100 kPa (atmospheric pressure, converted with pint
    for a $\sigma'_v$ in other units):

    - ``"liao_whitman_1986"``: $C_N = (p_a / \sigma'_v)^{0.5}$
      (Liao & Whitman 1986; Youd et al. 2001, Eq. 9, p. 300).
    - ``"kayen_1992"``: $C_N = 2.2 / (1.2 + \sigma'_v / p_a)$
      (Kayen et al. 1992; Youd et al. 2001, Eq. 10, p. 300).

    **There is no default method.** The two differ by up to about 12 %
    between 25 and 300 kPa, and the choice is the engineer's.

    **Cap:** $C_N \le 1.7$ for both methods (Youd et al. 2001, p. 300), so a
    test near the surface gets 1.7.

    **Valid for:** $0 \le \sigma'_v \le 300$ kPa. Youd et al. (2001) fit
    Eq. 9 to about 200 kPa and Eq. 10 to 300 kPa, and above 300 kPa say C_N
    "should be estimated by other means": those rows get a blank C_N and
    (N1)60, counted in a warning. Liao & Whitman between 200 and 300 kPa is
    computed; Youd et al. find it less certain there.

    **Not applied:** the rod-length, borehole-diameter and sampler
    corrections ($C_R$, $C_B$, $C_S$; Youd et al. 2001, Table 2). Apply them
    to N60 first if they matter to the design: they wait until the AGS rod
    and sampler data are read.

    **Refusals** get C_N and (N1)60, as they get N60. Correlations give no
    estimate for them.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60`` (from ``ht.analysis.spt()`` or
        ``p.spt()``) and ``effective_vertical_stress`` (from
        ``ht.analysis.vertical_stress()``), with its units declared.
    method : {"liao_whitman_1986", "kayen_1992"}
        The C_N equation. Required.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. Only
        ``effective_vertical_stress`` needs units.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``spt_overburden_correction`` (C_N) and
        ``spt_n1_60``. No row is dropped or reordered. A blank N60 or
        $\sigma'_v$ gives a blank (N1)60, counted in a warning.
        ``df.attrs["spt_n1_60"]`` records the method, the cap, $p_a$ and the
        source.

    Raises
    ------
    HangtuError
        For a missing column, an unknown method, a negative $\sigma'_v$ or
        missing units.

    References
    ----------
    Youd, T. L., et al. (2001). Liquefaction resistance of soils: summary
    report from the 1996 NCEER and 1998 NCEER/NSF workshops. *J. Geotech.
    Geoenviron. Eng.*, 127(4), 297-313. Eq. 9 and 10, p. 300.

    Liao, S. S. C., and Whitman, R. V. (1986). Overburden correction factors
    for SPT in sand. *J. Geotech. Eng.*, 112(3), 373-377.

    Kayen, R. E., et al. (1992). Evaluation of SPT-, CPT-, and shear
    wave-based methods for liquefaction potential assessment using Loma
    Prieta data. NCEER-92-0019, 177-204.

    Examples
    --------
    >>> spt = ht.analysis.vertical_stress(p.spt(), stratigraphy=p.stratigraphy())
    >>> spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")
    >>> spt[["loca_id", "depth", "spt_n60", "spt_n1_60"]]
    """
    check_columns(df, ["spt_n60", "effective_vertical_stress"], _MADE_BY)
    if method not in METHODS:
        raise HangtuError(
            f"method must be one of {', '.join(map(repr, METHODS))}, not "
            f'{method!r}. Example: method="liao_whitman_1986"'
        )
    n60 = numeric_column(df, "spt_n60")
    stress = stress_kpa(df, units)
    negative = stress < 0
    if negative.any():
        raise HangtuError(
            "Column 'effective_vertical_stress' is negative in rows "
            f"{rows_text(df.index[negative])}. Check the water levels and unit "
            "weights given to ht.analysis.vertical_stress()."
        )

    equation, citation = METHODS[method]
    above = stress > MAX_STRESS
    correction = np.minimum(equation(stress), CAP)
    correction[above] = np.nan
    n1_60 = n60 * correction

    blank = np.isnan(n60) | np.isnan(stress)
    reasons = []
    if blank.any():
        reasons.append(f"{int(blank.sum())} with no N60 or σ′v")
    if above.any():
        reasons.append(
            f"{int(above.sum())} with σ′v above 300 kPa, where Youd et al. (2001) "
            "say C_N should be estimated by other means"
        )
    if reasons:
        count = int((blank | above).sum())
        warn(
            f"(N1)60 is blank for {count} row{'s' if count != 1 else ''}: "
            f"{'; '.join(reasons)}."
        )
    replaced = [column for column in OUTPUT_COLUMNS if column in df.columns]
    if replaced:
        warn(f"Replaced the existing columns {', '.join(map(repr, replaced))}.")

    result = df.copy()
    result["spt_overburden_correction"] = correction
    result["spt_n1_60"] = n1_60
    result.attrs["spt_n1_60"] = {
        "method": method,
        "cap": CAP,
        "pa": f"{PA:g} kPa",
        "max_stress": f"{MAX_STRESS:g} kPa",
        "source": f"{citation}; {SOURCE}",
    }
    return result
