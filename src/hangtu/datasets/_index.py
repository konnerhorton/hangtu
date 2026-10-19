"""``p.index_properties()``: one row per sample, its tests combined (datasets.md §6.6).

A sample's water content (``LNMC``), Atterberg limits (``LLPL``) and grading
(``GRAT``) can be on different specimens. For each test, the specimen nearest
the sample's reference depth is used, so no row is multiplied and no other
specimen's values are mixed in.
"""

from dataclasses import dataclass, field
from os import PathLike

import numpy as np
import pandas as pd

from hangtu.datasets._frame import Build
from hangtu.datasets._lab import limits, specimen_names, specimens
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
    "water_content_specimen_id",
    "atterberg_specimen_id",
    "grain_size_specimen_id",
]
#: The test groups, in the order samples are listed (decision 3), and the
#: column naming each one's chosen specimen.
TESTS = {
    "LNMC": "water_content_specimen_id",
    "LLPL": "atterberg_specimen_id",
    "GRAT": "grain_size_specimen_id",
}
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
    if not any(build.has(group) for group in TESTS):
        return build.finish(
            pd.DataFrame(), COLUMNS, group="LNMC, LLPL or GRAT", **common
        )
    tables = {group: _specimens(build, group) for group in TESTS if build.has(group)}
    samples = _samples(tables)
    rows, chosen = [], []
    for sample in samples.values():
        row, several = _combine(sample)
        rows.append(row)
        if several:
            chosen.append(tuple(row[column] for column in TESTS.values()))
    frame = pd.DataFrame(rows, columns=ROW_COLUMNS)
    frame["_line"] = _sample_lines(build, frame.pop("sample_id"))
    result = build.finish(frame, COLUMNS, **common)
    _warn_chosen(result, chosen)
    return result


def _specimens(build: Build, group: str) -> pd.DataFrame:
    """One row per specimen of ``group``: its depth, sample and values, in SI."""
    rows = build.rows(group)
    frame = specimens(build, group, rows)
    frame["sample_id"] = rows.get("sample_id", pd.NA)
    frame["_sample"] = _sample_keys(build, rows)
    frame["_specimen"] = frame["specimen_id"].where(
        frame["specimen_id"].notna(),
        frame["specimen_reference"].fillna("").astype(str)
        + "@"
        + build.numbers(rows, "SPEC_DPTH").astype(str),
    )
    if group == "LLPL":
        frame = frame.join(limits(build, rows))
    if group == "LNMC":
        frame["water_content"] = build.numbers(rows, "LNMC_MC")
        frame = _one_water_content(frame)
    return frame.drop_duplicates("_specimen")


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
    """Return the samples, in order of their first LNMC, then LLPL, then GRAT row."""
    samples: dict[tuple, Sample] = {}
    for group, table in tables.items():
        for _, row in table.iterrows():
            sample = samples.setdefault(row["_sample"], Sample(first=row))
            sample.tests.setdefault(group, []).append(row)
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
        picked[group] = _nearest(found, reference, own) if found else None
        if group == "LNMC" and picked[group] is not None:
            own = picked[group]["_specimen"]
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
        row[column] = None if picked[group] is None else picked[group]["specimen_id"]
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
