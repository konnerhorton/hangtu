"""Analyses on SPT and lab data, usable without plotting (docs/drafts/analysis.md)."""

from hangtu.analysis._gradation import gradation
from hangtu.analysis._plasticity import plasticity
from hangtu.analysis._spt import spt, spt_class

__all__ = ["gradation", "plasticity", "spt", "spt_class"]
