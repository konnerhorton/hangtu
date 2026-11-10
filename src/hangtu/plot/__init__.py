"""Plots for geotechnical data.

Every plot takes a DataFrame and returns ``(fig, ax)``; "Plots" in the
documentation lists what they share.
"""

# Shared conventions: docs/plots/README.md; one spec per plot in docs/plots/.

from hangtu.plot import common, style
from hangtu.plot._clogging_diagram import clogging_diagram
from hangtu.plot._distribution_fit import distribution_fit
from hangtu.plot._failure_envelope import failure_envelope
from hangtu.plot._geology_units import (
    geology_unit_comparison,
    geology_unit_comparisons,
)
from hangtu.plot._grain_size import grain_size
from hangtu.plot._hoek_brown_envelope import hoek_brown_envelope
from hangtu.plot._palette import legend_handles, palette_cmap, reset_palette
from hangtu.plot._plasticity_chart import plasticity_chart
from hangtu.plot._profile import profile
from hangtu.plot._representative_profile import representative_profile
from hangtu.plot._shear_box_envelope import shear_box_envelope
from hangtu.plot._spt_histogram import spt_histogram
from hangtu.plot._spt_profile import spt_profile
from hangtu.plot._triaxial_shearing import triaxial_shearing
from hangtu.plot._water_content_profile import water_content_profile

__all__ = [
    "clogging_diagram",
    "common",
    "distribution_fit",
    "failure_envelope",
    "geology_unit_comparison",
    "geology_unit_comparisons",
    "grain_size",
    "hoek_brown_envelope",
    "legend_handles",
    "palette_cmap",
    "plasticity_chart",
    "profile",
    "representative_profile",
    "reset_palette",
    "shear_box_envelope",
    "spt_histogram",
    "spt_profile",
    "style",
    "triaxial_shearing",
    "water_content_profile",
]
