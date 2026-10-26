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


def _power_law(
    df: pd.DataFrame,
    name: str,
    a: float,
    b: float,
    uscs: str | list[str] | None,
    units: Mapping[str, str] | None,
    display_units: str | None,
) -> pd.DataFrame:
    """Return a N60^b, the form of every Vs correlation in Wair et al. (2012)."""
    item = _framework.entry(name)
    values = _framework.inputs(df, item, units)
    with np.errstate(invalid="ignore"):
        velocity = a * values["spt_n60"] ** b
    note = _framework.notes(df, item, values, uscs)
    return _framework.estimate(df, name, velocity, note, display_units, uscs=uscs)


def shear_wave_velocity_imai_tonouchi_1982(
    df: pd.DataFrame,
    *,
    uscs: list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the shear wave velocity Vs of any soil from N60.

    $$
    V_s = 93.7 \, N_{60}^{\,0.31} \ \text{m/s}
    $$

    Imai & Tonouchi (1982), pp. 67-72, in the 60 % form Wair et al. (2012)
    give in PEER Report 2012/08, Table 4.2, Eq. (4.6), p. 28. The source's
    equation, Vs = 97.0 N^0.31 m/s, is on uncorrected Japanese N.

    **Input:** ``spt_n60``, N at 60 % energy. Wair et al. converted the
    source's N assuming the 67 % energy typical of Japanese practice (Seed
    et al. 1985), not a measured one. There is no argument to read another
    column (SPEC §4).

    **Valid for:** all soils, and 0 < N60 ≤ 447: the source's N "from less
    than one bpf to nearly 400 bpf" (§4.1.3, p. 18) at the same 67 %. The
    data are Holocene, Pleistocene and Tertiary soils, alluvium and fill,
    from 386 borings at 250 sites in Japan.

    **Which Vs:** a small-strain property, as measured by seismic tests. A
    G0 or E0 from it is far stiffer than a working-strain E (see
    ``drained_youngs_modulus_aashto_2004``), and hangtu doesn't derive one
    here.

    **Scatter:** n = 1654 pairs, r² = 0.75. FHWA GEC 5 (Loehr et al. 2016,
    p. 8-18) describes the scatter in these relationships as typical.

    **Assumptions:** the 67 % energy, as above. FHWA GEC 5, Table 8-5,
    p. 8-20, repeats this equation but labels it "Tertiary": its notes column
    is shifted a row against Wair et al.'s table, which hangtu follows.

    **Soil type:** the source is for all soils, so hangtu proposes no USCS
    groups and ``uscs="proposed"`` raises. A list of groups reads
    ``uscs_symbol`` and gives no estimate outside them ("not for this
    soil"), or where the symbol is blank ("soil type unknown").

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N60 ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and N60 of 0 or less or above 447 ("below
    range", "above range").

    **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60``.
    uscs : list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups.
        By default no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N60 is a count,
        so none is needed.
    display_units : {"US", "SI"}, optional
        The units of Vs: ft/s for US, m/s for SI. Defaults to
        ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``shear_wave_velocity``, ``correlation_name``
        ("shear_wave_velocity_imai_tonouchi_1982"), ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Imai, T., and Tonouchi, K. (1982). Correlation of N value with S-wave
    velocity and shear modulus. *Proceedings of the 2nd European Symposium
    on Penetration Testing*, Amsterdam, 67-72.

    Wair, B. R., DeJong, J. T., and Shantz, T. (2012). *Guidelines for
    Estimation of Shear Wave Velocity Profiles*. PEER Report 2012/08,
    Pacific Earthquake Engineering Research Center, Berkeley.

    Loehr, J. E., et al. (2016). *Geotechnical Site Characterization*.
    Geotechnical Engineering Circular No. 5, FHWA-NHI-16-072.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> est = correlations.shear_wave_velocity_imai_tonouchi_1982(spt)
    >>> fig, ax = ht.plot.profile(est, "shear_wave_velocity")
    """
    return _power_law(
        df,
        "shear_wave_velocity_imai_tonouchi_1982",
        93.7,
        0.31,
        uscs,
        units,
        display_units,
    )


def shear_wave_velocity_ohta_goto_1978(
    df: pd.DataFrame,
    *,
    uscs: list[str] | None = None,
    units: Mapping[str, str] | None = None,
    display_units: str | None = None,
) -> pd.DataFrame:
    r"""Estimate the shear wave velocity Vs of any Quaternary soil from N60.

    $$
    V_s = 82.1 \, N_{60}^{\,0.35} \ \text{m/s}
    $$

    Ohta & Goto (1978), pp. 167-187, their regression on N alone for
    Quaternary soils, in the 60 % form Wair et al. (2012) give in PEER
    Report 2012/08, Table 4.2, Eq. (4.3), p. 28. The source's equation,
    Vs = 85.3 N^0.35 m/s, is on uncorrected Japanese N.

    **Input:** ``spt_n60``, N at 60 % energy. Wair et al. converted the
    source's N assuming the 67 % energy typical of Japanese practice (Seed
    et al. 1985), not a measured one. There is no argument to read another
    column (SPEC §4).

    **Valid for:** all soils, and 2.23 ≤ N60 ≤ 223: the source's N of about
    2 to 200 bpf (§4.1.2, p. 18) at the same 67 %. The data are 289 pairs,
    mostly from alluvial plains in Japan. The source's Holocene and
    Pleistocene forms need a geologic age and aren't built.

    **Which Vs:** a small-strain property, as measured by seismic tests. A
    G0 or E0 from it is far stiffer than a working-strain E, and hangtu
    doesn't derive one here.

    **Scatter:** r² = 0.52.

    **Assumptions:** the 67 % energy, as above. FHWA GEC 5 (Loehr et al.
    2016), Table 8-5, p. 8-20, labels this equation "Holocene": its notes
    column is shifted a row against Wair et al.'s table, which hangtu
    follows.

    **Soil type:** the source is for all soils, so hangtu proposes no USCS
    groups and ``uscs="proposed"`` raises. A list of groups reads
    ``uscs_symbol`` and gives no estimate outside them ("not for this
    soil"), or where the symbol is blank ("soil type unknown").

    **No estimate** (NaN, with ``correlation_note`` saying why and one
    warning counting them): a blank N60 ("input blank"), a refusal from
    ``spt_refusal`` ("refusal"), and N60 below 2.23 or above 223 ("below
    range", "above range").

    **Judgments taken:** none.

    Parameters
    ----------
    df : pandas.DataFrame
        One row per SPT test with ``spt_n60``.
    uscs : list of str, optional
        Read ``uscs_symbol`` and give no estimate outside these USCS groups.
        By default no soil type is read.
    units : dict, optional
        ``{column: unit}``, overriding ``df.attrs["units"]``. N60 is a count,
        so none is needed.
    display_units : {"US", "SI"}, optional
        The units of Vs: ft/s for US, m/s for SI. Defaults to
        ``ht.settings.display_units``.

    Returns
    -------
    pandas.DataFrame
        A copy of ``df`` with ``shear_wave_velocity``, ``correlation_name``
        ("shear_wave_velocity_ohta_goto_1978"), ``correlation_note`` and
        ``correlation_input`` (blank unless an input was another
        correlation's estimate). No row is dropped or reordered.
        ``df.attrs["correlations"]`` holds every correlation's entry; see
        ``ht.analysis.correlations.describe()``.

    References
    ----------
    Ohta, Y., and Goto, N. (1978). Empirical shear wave velocity equations
    in terms of characteristic soil indexes. *Earthquake Engineering and
    Structural Dynamics*, 6(2), 167-187.

    Wair, B. R., DeJong, J. T., and Shantz, T. (2012). *Guidelines for
    Estimation of Shear Wave Velocity Profiles*. PEER Report 2012/08,
    Pacific Earthquake Engineering Research Center, Berkeley.

    Examples
    --------
    >>> from hangtu.analysis import correlations
    >>> est = correlations.shear_wave_velocity_ohta_goto_1978(spt)
    >>> fig, ax = ht.plot.profile(est, "shear_wave_velocity")
    """
    return _power_law(
        df,
        "shear_wave_velocity_ohta_goto_1978",
        82.1,
        0.35,
        uscs,
        units,
        display_units,
    )
