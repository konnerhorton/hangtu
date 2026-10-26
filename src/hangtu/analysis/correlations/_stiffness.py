"""E and Vs from SPT (sheets 08, 10; docs/work/m13b3-spt-stiffness.md).

The E correlations take their coefficient from the source's soil row, named
by a required ``soil=`` (Decision 3).
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hangtu.analysis._overburden import PA
from hangtu.analysis.correlations import _framework


def _by_soil_row(
    df: pd.DataFrame,
    name: str,
    column: str,
    scale: float,
    soil: str | Mapping[str, str] | None,
    uscs: str | list[str] | None,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> pd.DataFrame:
    """Return C x ``column`` x ``scale``, with C from each row's soil row."""
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    rows = _framework.soil_rows(df, item, soil)
    coefficient = np.array(
        [item["rows"][row]["coefficient"] for row in rows], dtype=float
    )
    note = _framework.notes(df, item, values, uscs, rows)
    return _framework.estimate(
        df,
        name,
        coefficient * values[column] * scale,
        note,
        display_units,
        uscs=uscs,
        soil=soil,
        rows=rows,
    )


def drained_youngs_modulus_aashto_2004(
    df: pd.DataFrame,
    *,
    soil: str | Mapping[str, str] | None = None,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the drained Young's modulus E′ of silt, sand or gravel from (N1)60.

    $$
    E = C \, (N_1)_{60} \ \text{tsf}
    $$

    AASHTO (2004), as Samtani & Nowatzki (2006) give it in FHWA NHI-06-088,
    Table 5-16, p. 5-85, with C by the source's soil row, named by
    ``soil=``:

    - ``"silts"``: "Silts, sandy silts, slightly cohesive mixtures", C = 4;
    - ``"clean_fine_to_medium_sands"``: "Clean fine to medium sands and
      slightly silty sands", C = 7;
    - ``"coarse_sands"``: "Coarse sands and sands with little gravel",
      C = 10;
    - ``"gravels"``: "Sandy gravel and gravels", C = 12.

    The constants are in tsf, as the source gives them (1 tsf = 2000 lbf/ft²
    = 95.76 kPa), converted with pint. Read as ksf, they would halve E.
    Loehr et al. (2016), FHWA GEC 5, Table 8-11, p. 8-26, give the same
    factors in ksi, rounded (0.056, 0.097, 0.139, 0.167).

    **Input:** ``spt_n1_60``, N60 corrected for overburden, from
    ``ht.analysis.spt_n1_60()``. There is no argument to read another column
    (SPEC §4).

    **Valid for:** the soils of the four rows, and (N1)60 > 0. The source gives
    no N range; the lower bound is hangtu's, since a zero modulus is no
    estimate. NHI-06-088 gives the table "for preliminary design" (pp. 5-83
    to 5-84).

    **Which E:** the source's Es, Young's modulus for elastic settlement,
    which GEC 5 (§8.9.1, p. 8-25) gives as an "equivalent modulus" at working
    strains: a drained secant modulus. It is not the small-strain E0 from Vs,
    which is one to two orders of magnitude higher, nor an undrained Eu. For
    the silt row, drained loading is hangtu's reading.

    **Scatter:** not stated. GEC 5 (p. 8-25) calls such relationships "only
    approximate estimates"; "the definition of Es is not always consistent
    for the various correlations" (NHI-06-088, p. 5-84).

    **Assumptions:** none beyond the source's.

    **Soil row** (``soil=``) is required: one row name for every row, or
    ``{geology_unit: row}``. hangtu never infers it. ``uscs=`` checks it and
    never chooses it: with ``uscs="proposed"`` it reads ``uscs_symbol`` and
    gives no estimate outside the row's groups, hangtu's reading of its
    wording ("not for this soil"): ML, CL-ML for silts; SP, SW, SP-SM,
    SW-SM for either sand row (a symbol doesn't say fine or coarse); GP, GW,
    GP-GM, GW-GM for gravels. A blank symbol gives "soil type unknown". A
    list of groups replaces these for every row.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank (N1)60 ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and (N1)60 of 0 or less ("below range").

    **Judgments taken:** the soil row, by argument; it has no default.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n1_60``, and ``geology_unit`` when
        ``soil=`` is a mapping.
    soil : str or dict
        The source's soil row: one of ``"silts"``,
        ``"clean_fine_to_medium_sands"``, ``"coarse_sands"`` or
        ``"gravels"``, or ``{geology_unit: row}``. Required.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for each row's, above, or a list of your own. By
        default no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. (N1)60 is a
        count, so none is needed.
    display_units : {"US", "SI"}, optional
        The units of E: ksf for US, MPa for SI. Defaults to
        ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``drained_youngs_modulus``,
        ``correlation_name`` ("drained_youngs_modulus_aashto_2004"),
        ``correlation_soil`` (each row's soil row), ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    AASHTO (2004). *LRFD Bridge Design Specifications*, with 2006 Interims.
    American Association of State Highway and Transportation Officials,
    Washington, DC.

    Samtani, N. C., and Nowatzki, E. A. (2006). *Soils and Foundations
    Reference Manual*, Vol. I. FHWA NHI-06-088, Federal Highway
    Administration, Washington, DC.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> est = correlations.drained_youngs_modulus_aashto_2004(
    ...     sand, soil={"Terrace": "clean_fine_to_medium_sands"}
    ... )
    >>> fig, ax = ht.plot.profile(est, "drained_youngs_modulus")
    """
    return _by_soil_row(
        df,
        "drained_youngs_modulus_aashto_2004",
        "spt_n1_60",
        1.0,
        soil,
        uscs,
        units,
        display_units,
    )


def drained_youngs_modulus_kulhawy_mayne_1990(
    df: pd.DataFrame,
    *,
    soil: str | Mapping[str, str] | None = None,
    uscs: str | list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the drained Young's modulus E′ of sand from N60.

    $$
    \frac{E}{p_a} = C \, N_{60}
    $$

    with $p_a$ = 100 kPa. Kulhawy & Mayne (1990), EPRI EL-6800,
    Eqs. 5-26a to 5-26c, pp. 5-17 to 5-18, with C by the source's soil row,
    named by ``soil=``:

    | ``soil=`` | The source's wording | C |
    |---|---|---|
    | ``"sands_with_fines"`` | sands with fines | 5 |
    | ``"clean_normally_consolidated_sands"`` | clean NC sands | 10 |
    | ``"clean_overconsolidated_sands"`` | clean OC sands | 15 |

    **Input:** ``spt_n60``, N at 60 % energy, as the source states, not
    corrected for overburden. There is no argument to read another column
    (SPEC §4).

    **Valid for:** sands, and N60 > 0. The source gives no N range; the lower
    bound is hangtu's, since a zero modulus is no estimate.

    **Which E:** given "as a first order estimator", beside Fig. 5-13,
    p. 5-17, "Comparative Plot of Drained Modulus Correlations for Sand": a
    drained, working-strain modulus. It is not the small-strain E0 from Vs,
    nor an undrained Eu.

    **Scatter:** not stated. "All attempts to date which correlate a modulus
    with N show considerable scatter" (p. 5-17).

    **Assumptions:** none beyond the source's.

    **Soil row** (``soil=``) is required: one row name for every row, or
    ``{geology_unit: row}``. hangtu never infers it; whether a sand is
    normally consolidated or overconsolidated is the engineer's reading.
    ``uscs=`` checks it and never chooses it: with ``uscs="proposed"`` it
    reads ``uscs_symbol`` and gives no estimate outside the row's groups,
    hangtu's reading of its wording ("not for this soil"): SM, SC, SP-SM,
    SW-SM, SP-SC, SW-SC for sands with fines; SP, SW for either clean row. A
    blank symbol gives "soil type unknown". A list of groups replaces these
    for every row.

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N60 ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and N60 of 0 or less ("below range").

    **Judgments taken:** the soil row, by argument; it has no default.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60``, and ``geology_unit`` when
        ``soil=`` is a mapping.
    soil : str or dict
        The source's soil row: one of ``"sands_with_fines"``,
        ``"clean_normally_consolidated_sands"`` or
        ``"clean_overconsolidated_sands"``, or ``{geology_unit: row}``.
        Required.
    uscs : "proposed" or list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups:
        ``"proposed"`` for each row's, above, or a list of your own. By
        default no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N60 is a count,
        so none is needed.
    display_units : {"US", "SI"}, optional
        The units of E: ksf for US, MPa for SI. Defaults to
        ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``drained_youngs_modulus``,
        ``correlation_name`` ("drained_youngs_modulus_kulhawy_mayne_1990"),
        ``correlation_soil`` (each row's soil row), ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Kulhawy, F. H., and Mayne, P. W. (1990). *Manual on Estimating Soil
    Properties for Foundation Design*. EPRI EL-6800, Electric Power Research
    Institute, Palo Alto.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> est = correlations.drained_youngs_modulus_kulhawy_mayne_1990(
    ...     sand, soil="sands_with_fines"
    ... )
    >>> fig, ax = ht.plot.profile(est, "drained_youngs_modulus")
    """
    return _by_soil_row(
        df,
        "drained_youngs_modulus_kulhawy_mayne_1990",
        "spt_n60",
        PA,
        soil,
        uscs,
        units,
        display_units,
    )
