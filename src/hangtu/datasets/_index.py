"""``p.index_properties()``: one row per sample, its tests combined (datasets.md §6.6).

A sample's water content (``LNMC``), Atterberg limits (``LLPL``) and grading
(a ``GRAT`` curve, or a reported grading: ``GRAG`` with no curve, §6.13) can
be on different specimens. For each test, the specimen nearest
the sample's reference depth is used, so no row is multiplied and no other
specimen's values are mixed in.
"""

import warnings
from dataclasses import dataclass, field
from os import PathLike

import numpy as np
import pandas as pd

from hangtu.analysis import aashto, clay_activity, uscs
from hangtu.analysis._fractions import fraction_system
from hangtu.datasets._frame import Build
from hangtu.datasets._lab import (
    classify_plasticity,
    limits,
    specimen_names,
    specimens,
    summarize_curves,
)
from hangtu.datasets._reported import (
    add_values,
    no_system_message,
    reported_fractions,
    reported_rows,
    uscs_blank_message,
)
from hangtu.errors import warn

COLUMNS = [
    "loca_id",
    "sample_reference",
    "ground_level",
    "depth",
    "depth_basis",
    "elevation",
    "water_content",
    "liquid_limit",
    "plastic_limit",
    "plasticity_index",
    "non_plastic",
    "liquidity_index",
    "consistency_index",
    "plasticity_class_uscs",
    "plasticity_class_bs5930",
    "d10",
    "d30",
    "d60",
    "uniformity_coefficient",
    "curvature_coefficient",
    "fines_content",
    "sand_content",
    "gravel_content",
    "cobbles_content",
    "boulders_content",
    "fraction_system",
    "grading_source",
    "uscs_symbol",
    "aashto_group",
    "aashto_group_index",
    "clay_activity",
    "water_content_specimen_id",
    "atterberg_specimen_id",
    "grain_size_specimen_id",
]
#: Columns ``gradation(fractions="astm_uscs")`` gives each grading (§6.6).
GRADATION_COLUMNS = COLUMNS[COLUMNS.index("d10") : COLUMNS.index("fraction_system")]
#: The aashto fractions ``aashto()`` reads, which aren't returned.
AASHTO_FRACTIONS = [
    "silt_clay_content",
    "fine_sand_content",
    "coarse_sand_content",
    "gravel_content",
    "boulders_content",
]
#: The tests, and the column naming each one's chosen specimen.
TESTS = {
    "LNMC": "water_content_specimen_id",
    "LLPL": "atterberg_specimen_id",
    "GRAT": "grain_size_specimen_id",
}
#: The groups, in the order samples are listed (decision 3). Reported
#: gradings (GRAG with no GRAT, §6.13) are grading candidates with the curves.
GROUPS = {"LNMC": "LNMC", "LLPL": "LLPL", "GRAT": "GRAT", "GRAG": "GRAT"}
#: The columns of a combined row, before ``finish()``.
ROW_COLUMNS = [
    "location_id",
    "loca_id",
    "sample_id",
    "sample_reference",
    "depth",
    "depth_basis",
    "water_content",
    "liquid_limit",
    "plastic_limit",
    "plasticity_index",
    "non_plastic",
    *TESTS.values(),
    "grading_source",
    "_grading",
]
#: The AGS key fields of a sample, which every lab row carries.
SAMPLE_KEY = ["LOCA_ID", "SAMP_TOP", "SAMP_TYPE", "SAMP_REF", "SAMP_ID"]
#: Distances closer than this (m) are a tie, so 6.25 - 6.20 and 6.30 - 6.25
#: are equal whatever the floating-point noise.
TIE = 1e-6


@dataclass
class Sample:
    """One sample's specimens of each test, as rows of the specimen tables."""

    first: pd.Series  # the first lab row seen, for the sample's own columns
    tests: dict[str, list[pd.Series]] = field(default_factory=dict)


def index_properties(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the index properties dataset; see ``Project.index_properties``."""
    build = Build(
        path,
        noun=("sample", "samples"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not any(build.has(group) for group in GROUPS):
        return build.finish(
            pd.DataFrame(), COLUMNS, group="LNMC, LLPL, GRAT or GRAG", **common
        )
    tables = {g: _specimens(build, g) for g in GROUPS if build.has(g)}
    points = tables.get("GRAT")
    tables = {g: table.drop_duplicates("_specimen") for g, table in tables.items()}
    reported = Reported(tables.get("GRAG"), build.grag_fraction_system)
    samples = _samples(tables)
    rows, chosen = [], []
    for sample in samples.values():
        row, several = _combine(sample)
        rows.append(row)
        if several:
            chosen.append(tuple(row[column] for column in TESTS.values()))
    frame = pd.DataFrame(rows, columns=ROW_COLUMNS)
    frame["_line"] = _sample_lines(build, frame.pop("sample_id"))
    # Classified before finish(), so where= can name the classes, but its
    # warnings are given for the rows the filters return, like the others.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        classified = _classify(frame, points, reported)
    classified["_row"] = np.arange(len(frame))
    result = build.finish(classified, [*COLUMNS, "_row"], **common)
    _classify(frame.iloc[result.pop("_row").to_numpy()], points, reported)
    _warn_chosen(result, chosen)
    return result


def _specimens(build: Build, group: str) -> pd.DataFrame:
    """Return the rows of ``group`` with their specimen, sample and values, in SI.

    ``_specimen`` tells the specimens apart: the specimen key, or for a sample
    with no ``SAMP`` row (no key), its sample, ``SPEC_REF`` and ``SPEC_DPTH``.
    """
    rows = reported_rows(build) if group == "GRAG" else build.rows(group)
    frame = specimens(build, group, rows)
    frame["sample_id"] = rows.get("sample_id", pd.NA)
    frame["_sample"] = _sample_keys(build, rows)
    frame["_specimen"] = frame["specimen_id"].where(
        frame["specimen_id"].notna(),
        frame["_sample"].astype(str)
        + "/"
        + frame["specimen_reference"].fillna("").astype(str)
        + "@"
        + build.numbers(rows, "SPEC_DPTH").astype(str),
    )
    if group == "LLPL":
        frame = frame.join(limits(build, rows))
    if group == "LNMC":
        frame["water_content"] = build.numbers(rows, "LNMC_MC")
        frame = _one_water_content(frame)
    if group == "GRAT":
        frame["particle_size"] = build.numbers(rows, "GRAT_SIZE")
        frame["percent_passing"] = build.numbers(rows, "GRAT_PERP")
    if group == "GRAG":
        add_values(build, frame, rows)
    frame["_source"] = "reported" if group == "GRAG" else "curve"
    return frame


def _sample_keys(build: Build, rows: pd.DataFrame) -> pd.Series:
    """Each row's sample, by its AGS key fields (decision 3)."""
    parts = [
        build.texts(rows, "LOCA_ID").fillna(""),
        build.numbers(rows, "SAMP_TOP").round(6).astype(str),
        *(build.texts(rows, h).fillna("") for h in SAMPLE_KEY[2:]),
    ]
    return pd.Series(list(zip(*parts, strict=True)), index=rows.index, dtype=object)


def _one_water_content(frame: pd.DataFrame) -> pd.DataFrame:
    """Blank the water content of a specimen with several LNMC rows (§6.2)."""
    counts = frame["_specimen"].map(frame["_specimen"].value_counts())
    several = counts > 1
    if several.any():
        named = ", ".join(
            dict.fromkeys(
                frame.loc[several, "loca_id"].astype(str)
                + " "
                + specimen_names(frame[several])
            )
        )
        warn(
            f"Specimens with more than one water content (LNMC) row: {named}. "
            "Their water_content, liquidity_index and consistency_index are left "
            "blank, since hangtu can't tell which applies. Check LNMC."
        )
    frame["water_content"] = frame["water_content"].where(~several)
    return frame


def _samples(tables: dict[str, pd.DataFrame]) -> dict[tuple, Sample]:
    """Return the samples, in order of their first LNMC, LLPL, GRAT, then GRAG row.

    A reported grading (``GRAG``) is listed with the sample's curves, as one
    test.
    """
    samples: dict[tuple, Sample] = {}
    for group, table in tables.items():
        for _, row in table.iterrows():
            sample = samples.setdefault(row["_sample"], Sample(first=row))
            sample.tests.setdefault(GROUPS[group], []).append(row)
    return samples


def _combine(sample: Sample) -> tuple[dict, bool]:
    """Return the combined row, and whether any test had several specimens."""
    first = sample.first
    waters = sample.tests.get("LNMC", [])
    if len(waters) == 1:
        reference, basis = waters[0]["depth"], waters[0]["depth_basis"]
    else:
        reference, basis = first["_sample_depth"], first["_sample_basis"]
    own = None
    picked: dict[str, pd.Series | None] = {}
    for group in TESTS:
        found = sample.tests.get(group, [])
        pick = _nearest(found, reference, own) if found else None
        picked[group] = pick
        if group == "LNMC" and pick is not None:
            own = pick["_specimen"]
    water, atterberg = picked["LNMC"], picked["LLPL"]
    row = {
        "location_id": first["location_id"],
        "loca_id": first["loca_id"],
        "sample_id": first["sample_id"],
        "sample_reference": first["sample_reference"],
        "depth": reference,
        "depth_basis": basis,
        "water_content": np.nan if water is None else water["water_content"],
    }
    for column in ("liquid_limit", "plastic_limit", "plasticity_index"):
        row[column] = np.nan if atterberg is None else atterberg[column]
    row["non_plastic"] = False if atterberg is None else bool(atterberg["non_plastic"])
    for group, column in TESTS.items():
        pick = picked[group]
        row[column] = None if pick is None else pick["specimen_id"]
    grading = picked["GRAT"]
    row["_grading"] = None if grading is None else grading["_specimen"]
    row["grading_source"] = None if grading is None else grading["_source"]
    several = any(len(found) > 1 for found in sample.tests.values())
    return row, several


def _nearest(found: list[pd.Series], reference: float, own) -> pd.Series:
    """Return the specimen nearest ``reference`` (§6.6, decision 5).

    Then the water content's own specimen, then the lowest ``SPEC_REF`` as
    text, then the lowest specimen key. A specimen with no depth is at the
    sample's lab depth, which ``specimens()`` already gives it.
    """

    def order(specimen: pd.Series) -> tuple:
        distance = abs(specimen["depth"] - reference)
        steps = np.inf if np.isnan(distance) else round(distance / TIE)
        key = specimen["specimen_id"]
        return (
            steps,
            specimen["_specimen"] != own,
            specimen["specimen_reference"] or "",
            np.inf if key is None else int(key),
        )

    return min(found, key=order)


def _sample_lines(build: Build, sample_ids: pd.Series) -> pd.Series:
    """Return the line of each sample's ``SAMP`` row, or blank (decision 7)."""
    if not build.has("SAMP"):
        return pd.Series(pd.NA, index=sample_ids.index, dtype="Int64")
    samp = build.data.table("SAMP").dropna(subset=["sample_id"])
    lines = pd.Series(samp["_line"].to_numpy(), index=samp["sample_id"].astype(int))
    return sample_ids.map(
        lambda key: pd.NA if pd.isna(key) else lines.get(int(key), pd.NA)
    ).astype("Int64")


def _warn_chosen(result: pd.DataFrame, chosen: list[tuple]) -> None:
    """Count the samples, among those returned, where a specimen was chosen."""
    if not chosen or result.empty:
        return
    returned = zip(*(result[column] for column in TESTS.values()), strict=True)
    count = len(set(chosen) & set(returned))
    if count:
        warn(
            f"{count} sample{'s' if count > 1 else ''} had more than one specimen "
            "of a test; the one nearest in depth was used. The *_specimen_id "
            "columns say which."
        )


@dataclass
class Reported:
    """The reported gradings a call can choose, and the project's stated system."""

    table: pd.DataFrame | None
    stated: str | None


def _classify(
    frame: pd.DataFrame, points: pd.DataFrame | None, reported: Reported
) -> pd.DataFrame:
    """Add the plasticity columns, gradings, USCS symbol, AASHTO group and activity.

    Plasticity as ``p.atterberg()`` (§6.2), on the combined row. Only rows
    with a grading are classified: a sample with only a water content or
    limits gets blank symbols without a warning, since no test was run to
    classify it. ``gradation()`` runs three times on the chosen curves, for
    the astm_uscs fractions (returned) and the aashto and iso14688 ones (not
    returned); the later runs' warnings would repeat the first's, so they
    aren't shown. Activity is blank where a curve doesn't reach 0.002 mm, as
    on a sieve-only grading, without a warning (M14 b, Decision 7). A
    reported grading gives the same three systems' fractions by §6.13.
    """
    labels = frame["loca_id"].astype(str) + " " + frame["sample_reference"].astype(str)
    frame = classify_plasticity(frame, labels)
    for column in [*GRADATION_COLUMNS, "aashto_group_index", "clay_activity"]:
        frame[column] = np.nan
    for column in ("fraction_system", "uscs_symbol", "aashto_group"):
        frame[column] = None
    graded = frame["_grading"].notna()
    if not graded.any():
        return frame
    grading, fractions, clay = _curve_values(frame, points)
    oversize = pd.Series(dtype=float)
    unclassified: pd.Index = pd.Index([])
    blank_names: list[str] = []
    if reported.table is not None and not reported.table.empty:
        found = _reported_values(frame, reported)
        grading = pd.concat([grading, found.grading])
        fractions = pd.concat([fractions, found.fractions])
        clay = pd.concat([clay, found.clay])
        oversize, unclassified = found.oversize, found.unclassified
        blank_names = found.blank_names
    on = frame.loc[graded, "_grading"]
    for column in GRADATION_COLUMNS:
        frame.loc[graded, column] = on.map(grading[column]).to_numpy()
    frame.loc[graded, "fraction_system"] = "astm_uscs"

    soils = frame.loc[graded].copy()
    # A reported GRAG_VCRE above 0 is the oversize, though cobbles and
    # boulders are blank (§6.6, uscs_symbol); the returned columns stay blank.
    extra = on.map(oversize).astype(float)
    known = extra.notna().to_numpy()
    soils.loc[known, "cobbles_content"] = extra[known].to_numpy()
    soils.loc[known, "boulders_content"] = 0.0
    skip = on.isin(unclassified).to_numpy()
    symbols = pd.Series(None, index=soils.index, dtype=object)
    if (~skip).any():
        symbols[~skip] = uscs(soils[~skip])["uscs_symbol"].to_numpy()
    frame.loc[graded, "uscs_symbol"] = symbols.to_numpy()
    frame["uscs_symbol"] = frame["uscs_symbol"].astype(object)
    frame["uscs_symbol"] = frame["uscs_symbol"].where(
        frame["uscs_symbol"].notna(), None
    )
    if reported.stated is None:
        count = int((frame.loc[graded, "grading_source"] == "reported").sum())
        if count:
            warn(no_system_message(count))
    elif skip.any():
        warn(uscs_blank_message(int(skip.sum()), reported.stated, blank_names))

    soils = soils[["liquid_limit", "plasticity_index", "non_plastic"]].copy()
    for column in AASHTO_FRACTIONS:
        soils[column] = on.map(fractions[column]).to_numpy()
    soils["fraction_system"] = "aashto"
    no_system = (
        (frame.loc[graded, "grading_source"] == "reported").to_numpy()
        if reported.stated is None
        else np.zeros(len(soils), dtype=bool)
    )
    groups = pd.DataFrame(
        {"aashto_group": None, "aashto_group_index": np.nan}, index=soils.index
    )
    if (~no_system).any():
        with warnings.catch_warnings():
            # plasticity()'s PI above LL, already warned about on these rows.
            warnings.filterwarnings(
                "ignore", message=r"Rows .* have a plasticity_index"
            )
            found_groups = aashto(soils[~no_system])
        groups.loc[~no_system, "aashto_group"] = found_groups["aashto_group"].to_numpy()
        groups.loc[~no_system, "aashto_group_index"] = found_groups[
            "aashto_group_index"
        ].to_numpy()
    frame.loc[graded, "aashto_group"] = groups["aashto_group"].to_numpy()
    frame.loc[graded, "aashto_group_index"] = groups["aashto_group_index"].to_numpy()

    soils = soils[["plasticity_index", "non_plastic"]].copy()
    soils["clay_content"] = on.map(clay).to_numpy()
    soils["fraction_system"] = "iso14688"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # blanks are expected on sieve-only curves
        activity = clay_activity(soils)
    frame.loc[graded, "clay_activity"] = activity["clay_activity"].to_numpy()
    return frame


def _curve_values(
    frame: pd.DataFrame, points: pd.DataFrame | None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Return the chosen curves' gradation, aashto fractions and clay, by specimen."""
    empty = pd.DataFrame(columns=GRADATION_COLUMNS, dtype=float)
    if points is None:
        return (
            empty,
            pd.DataFrame(columns=AASHTO_FRACTIONS, dtype=float),
            (pd.Series(dtype=float)),
        )
    chosen = points[points["_specimen"].isin(frame["_grading"].dropna())]
    curves = pd.DataFrame(
        {
            "loca_id": chosen["loca_id"],
            "specimen_id": chosen["_specimen"],
            "sample_reference": chosen["sample_reference"],
            "specimen_reference": chosen["specimen_reference"],
            "particle_size": chosen["particle_size"],
            "percent_passing": chosen["percent_passing"],
        }
    )
    curves.attrs["units"] = {"particle_size": "mm", "percent_passing": "%"}
    grading = summarize_curves(curves, ["specimen_id"], []).set_index("specimen_id")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fractions = summarize_curves(curves, ["specimen_id"], [], "aashto")
        clay = summarize_curves(curves, ["specimen_id"], [], "iso14688")
    return (
        grading,
        fractions.set_index("specimen_id"),
        clay.set_index("specimen_id")["clay_content"],
    )


@dataclass
class ReportedValues:
    """A call's chosen reported gradings, read for classification (§6.13)."""

    grading: pd.DataFrame  # GRADATION_COLUMNS, by specimen
    fractions: pd.DataFrame  # AASHTO_FRACTIONS
    clay: pd.Series  # iso14688 clay
    oversize: pd.Series  # GRAG_VCRE where it is above 0 and cobbles are blank
    unclassified: pd.Index  # specimens whose USCS fractions have other boundaries
    blank_names: list[str]  # those fractions


def _reported_values(frame: pd.DataFrame, reported: Reported) -> ReportedValues:
    assert reported.table is not None  # the caller checks
    table = reported.table[reported.table["_specimen"].isin(frame["_grading"])]
    table = table.set_index("_specimen")
    stated = reported.stated

    def read(system: str) -> tuple[pd.DataFrame, list[str]]:
        found = reported_fractions(table, fraction_system(system)[1], stated)
        return found.contents, found.other_boundaries

    astm, other = read("astm_uscs")
    grading = astm.copy()
    for column in ("d10", "d30", "d60"):
        grading[column] = np.nan
    grading["uniformity_coefficient"] = table["uniformity_coefficient"]
    grading["curvature_coefficient"] = table["curvature_coefficient"]
    # uscs() needs these three; cobbles and boulders only rescale them.
    other = [name for name in other if name in ("fines", "sand", "gravel")]
    blank = astm[[f"{name}_content" for name in other]].isna().any(axis=1)
    vcre = table["GRAG_VCRE"]
    over = (
        astm["cobbles_content"].isna()
        & astm["boulders_content"].isna()
        & (vcre > 0)
        & (stated is not None)
    )
    return ReportedValues(
        grading=grading[GRADATION_COLUMNS],
        fractions=read("aashto")[0][AASHTO_FRACTIONS],
        clay=read("iso14688")[0]["clay_content"],
        oversize=vcre[over],
        unclassified=astm.index[blank] if stated is not None else table.index,
        blank_names=other,
    )
