"""Analyses on SPT and lab data, usable without plotting (docs/drafts/analysis.md)."""

from hangtu.analysis._classification import aashto, uscs
from hangtu.analysis._gradation import gradation
from hangtu.analysis._overburden import spt_n1_60
from hangtu.analysis._plasticity import plasticity
from hangtu.analysis._spt import spt, spt_class
from hangtu.analysis._vertical_stress import vertical_stress

__all__ = [
    "aashto",
    "gradation",
    "plasticity",
    "spt",
    "spt_class",
    "spt_n1_60",
    "uscs",
    "vertical_stress",
]
