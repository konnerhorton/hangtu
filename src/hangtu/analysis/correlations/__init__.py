"""Published correlations, one function per source (SPEC §4).

Each function reads the one input column its correlation was derived with,
returns a copy of ``df`` with the estimate in the target property's column,
``correlation_name`` and ``correlation_note``, and gives NaN, never an
extrapolated value, where the correlation doesn't apply. A correlation
published as a band gives ``<target>_lower`` and ``<target>_upper``. Every
row carries the source's statistics and advice (``correlation_data_count``,
``correlation_r_squared``, ``correlation_scatter``, ``correlation_advice``).
Each is named target first: ``<target>_<authors>_<year>``. Several estimates
compare with ``pd.concat`` and ``ht.plot.profile(..., color_by="correlation_name")``.
"""

from typing import Any

from hangtu.analysis.correlations._framework import entry
from hangtu.analysis.correlations._friction_angle import (
    effective_friction_angle_hatanaka_uchida_1996,
    effective_friction_angle_kulhawy_mayne_1990,
)
from hangtu.analysis.correlations._stiffness import (
    drained_youngs_modulus_aashto_2004,
    drained_youngs_modulus_kulhawy_mayne_1990,
    shear_wave_velocity_imai_tonouchi_1982,
    shear_wave_velocity_ohta_goto_1978,
)
from hangtu.analysis.correlations._stress_history import (
    at_rest_earth_pressure_coefficient_kulhawy_et_al_1989,
    overconsolidation_ratio_mayne_kemper_1988,
    preconsolidation_stress_mayne_kemper_1988,
)
from hangtu.analysis.correlations._undrained_shear_strength import (
    undrained_shear_strength_stroud_1974,
    undrained_shear_strength_terzaghi_peck_1967,
)

__all__ = [
    "at_rest_earth_pressure_coefficient_kulhawy_et_al_1989",
    "describe",
    "drained_youngs_modulus_aashto_2004",
    "drained_youngs_modulus_kulhawy_mayne_1990",
    "effective_friction_angle_hatanaka_uchida_1996",
    "effective_friction_angle_kulhawy_mayne_1990",
    "overconsolidation_ratio_mayne_kemper_1988",
    "preconsolidation_stress_mayne_kemper_1988",
    "shear_wave_velocity_imai_tonouchi_1982",
    "shear_wave_velocity_ohta_goto_1978",
    "undrained_shear_strength_stroud_1974",
    "undrained_shear_strength_terzaghi_peck_1967",
]


def describe(name: str) -> dict[str, Any]:
    """Return a correlation's entry: its equation, inputs, range and sources.

    The same entry ``df.attrs["correlations"][name]`` holds on a result, for
    when the attrs are lost (after a merge, or a file round trip).

    Parameters
    ----------
    name : str
        The correlation's function name, as in ``correlation_name``.

    Returns
    -------
    dict
        A copy of its entry in ``config/correlations.yaml``: ``target``,
        ``equation``, ``inputs`` (column, variant and unit), ``range``,
        ``applies_to``, ``not_for``, ``notes``, ``sources`` (each with its
        locator) and ``label``. ``scatter`` holds the source's own statistics:
        its ``words``, ``data_count`` (n), ``r_squared`` and
        ``standard_deviation`` (``value``, ``unit`` and ``scale``), each None
        where the source states none. ``advice`` is the source's advice on use
        (``words`` and ``by``, its citation, or "hangtu" for hangtu's own), or
        None. ``evaluations`` lists other databases' checks of the
        correlation: ``bias`` (mean of measured over estimated),
        ``coefficient_of_variation``, ``data_count``, ``database``, ``cite``
        and ``locator``. ``label`` is the text a plot's
        legend shows for the correlation when it colors or marks points by
        ``correlation_name``: the entry's ``label:`` if it has one, else the
        first source's citation, e.g. "Hatanaka & Uchida (1996)".

    Examples
    --------
    >>> name = "effective_friction_angle_hatanaka_uchida_1996"
    >>> ht.analysis.correlations.describe(name)["range"]
    {'spt_n1_60': {'at_least': 4.55, 'at_most': 39.0}}
    """
    return entry(name)
