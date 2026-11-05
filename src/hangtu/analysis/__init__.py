"""Analyses on SPT and lab data, usable without plotting (docs/drafts/analysis.md)."""

from hangtu.analysis import correlations
from hangtu.analysis._add_judgment import add_judgment
from hangtu.analysis._classification import aashto, uscs
from hangtu.analysis._clay_activity import clay_activity
from hangtu.analysis._clogging import clogging_potential
from hangtu.analysis._gradation import gradation
from hangtu.analysis._hoek_brown_fit import HoekBrownFit, hoek_brown_fit
from hangtu.analysis._mohr_coulomb import MohrCoulombFit, mohr_coulomb_fit
from hangtu.analysis._overburden import spt_n1_60
from hangtu.analysis._phase_relations import phase_relations
from hangtu.analysis._plasticity import plasticity
from hangtu.analysis._shear_box_fit import ShearBoxFit, shear_box_fit
from hangtu.analysis._spt import spt, spt_class
from hangtu.analysis._triaxial import triaxial_failure_stresses
from hangtu.analysis._triaxial_readings import triaxial_failure_from_readings
from hangtu.analysis._undrained import undrained_shear_strength_from_tests
from hangtu.analysis._vertical_stress import vertical_stress

__all__ = [
    "HoekBrownFit",
    "MohrCoulombFit",
    "ShearBoxFit",
    "aashto",
    "add_judgment",
    "clay_activity",
    "clogging_potential",
    "correlations",
    "gradation",
    "hoek_brown_fit",
    "mohr_coulomb_fit",
    "phase_relations",
    "plasticity",
    "shear_box_fit",
    "spt",
    "spt_class",
    "spt_n1_60",
    "triaxial_failure_from_readings",
    "triaxial_failure_stresses",
    "undrained_shear_strength_from_tests",
    "uscs",
    "vertical_stress",
]
