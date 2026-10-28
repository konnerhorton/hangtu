"""Analyses on SPT and lab data, usable without plotting (docs/drafts/analysis.md)."""

from hangtu.analysis import correlations
from hangtu.analysis._add_judgment import add_judgment
from hangtu.analysis._classification import aashto, uscs
from hangtu.analysis._clay_activity import clay_activity
from hangtu.analysis._gradation import gradation
from hangtu.analysis._overburden import spt_n1_60
from hangtu.analysis._phase_relations import phase_relations
from hangtu.analysis._plasticity import plasticity
from hangtu.analysis._spt import spt, spt_class
from hangtu.analysis._summary import summary_by
from hangtu.analysis._vertical_stress import vertical_stress

__all__ = [
    "aashto",
    "add_judgment",
    "clay_activity",
    "correlations",
    "gradation",
    "phase_relations",
    "plasticity",
    "spt",
    "spt_class",
    "spt_n1_60",
    "summary_by",
    "uscs",
    "vertical_stress",
]
