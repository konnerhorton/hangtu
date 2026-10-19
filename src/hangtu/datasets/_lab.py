"""Lab datasets: ``p.atterberg()`` and ``p.grain_size()`` (datasets.md §6.2, §6.3)."""

import warnings
from os import PathLike

import numpy as np
import pandas as pd

from hangtu.analysis import gradation, plasticity
from hangtu.analysis._fractions import content_column, fraction_system
from hangtu.analysis._gradation import _check_d_values
from hangtu.datasets import _joins
from hangtu.datasets._frame import Build
from hangtu.errors import warn

#: Columns every lab dataset starts with.
SPECIMEN_COLUMNS = [
    "loca_id",
    "specimen_id",
    "sample_reference",
    "specimen_reference",
    "ground_level",
    "depth",
    "depth_basis",
    "elevation",
]
ATTERBERG_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "depth_top",
    "depth_base",
    "liquid_limit",
    "plastic_limit",
    "plasticity_index",
    "non_plastic",
    "water_content",
    "liquidity_index",
    "consistency_index",
    "plasticity_class_uscs",
    "plasticity_class_bs5930",
]
#: Columns ``ht.analysis.plasticity()`` adds or fills in.
PLASTICITY_COLUMNS = [
    "plasticity_index",
    "liquidity_index",
    "consistency_index",
    "plasticity_class_uscs",
    "plasticity_class_bs5930",
]
GRAIN_SIZE_COLUMNS = [
    *SPECIMEN_COLUMNS,
    "particle_size",
    "percent_passing",
    "qualifier",
]


def specimens(build: Build, group: str, rows: pd.DataFrame) -> pd.DataFrame:
    """Return the specimen columns of lab ``rows``, in SI (§6.2, "Lab depth").

    Depth is ``SPEC_DPTH``, else the sample's midpoint, else its top, with the
    sample's top and base read from ``SAMP``. ``depth_top`` and ``depth_base``
    are the specimen's ``SPEC_DPTH`` and ``SPEC_BASE`` when both are given.
    ``_sample_depth`` and ``_sample_basis`` are the sample's own lab depth,
    without ``SPEC_DPTH`` (§6.6); ``finish()`` leaves them out.
    """
    samples = build.samples()
    sample_id = rows["sample_id"] if "sample_id" in rows else pd.Series(pd.NA)
    known = sample_id.notna() & sample_id.isin(samples.index)
    at = sample_id[known].astype(int).to_numpy()
    top = build.numbers(rows, "SAMP_TOP")
    top[known] = samples.loc[at, "SAMP_TOP"].to_numpy()
    base = pd.Series(np.nan, index=rows.index, dtype=float)
    base[known] = samples.loc[at, "SAMP_BASE"].to_numpy()
    specimen_depth = build.numbers(rows, "SPEC_DPTH")
    specimen_base = build.numbers(rows, "SPEC_BASE")
    depth, basis = _joins.lab_depth(specimen_depth, top, base)
    no_specimen = pd.Series(np.nan, index=rows.index, dtype=float)
    sample_depth, sample_basis = _joins.lab_depth(no_specimen, top, base)
    both = specimen_depth.notna() & specimen_base.notna()
    specimen_id = (
        rows["specimen_id"]
        if "specimen_id" in rows
        else pd.Series(pd.NA, index=rows.index)
    )
    return pd.DataFrame(
        {
            "location_id": rows["location_id"],
            "loca_id": build.texts(rows, "LOCA_ID"),
            "specimen_id": specimen_id.map(
                lambda key: None if pd.isna(key) else str(int(key))
            ),
            "sample_reference": _sample_reference(build, group, rows),
            "specimen_reference": build.texts(rows, "SPEC_REF"),
            "depth": depth,
            "depth_basis": basis,
            "depth_top": specimen_depth.where(both),
            "depth_base": specimen_base.where(both),
            "_sample_depth": sample_depth,
            "_sample_basis": sample_basis,
            "_line": rows["_line"],
        },
        index=rows.index,
    )


def _sample_reference(build: Build, group: str, rows: pd.DataFrame) -> pd.Series:
    """``SAMP_ID``, else ``<type><ref> at <top>`` as the file wrote them."""
    unit = build.data.heading_info(group, "SAMP_TOP")["file_unit"] or ""

    def reference(row) -> str | None:
        if isinstance(row.get("SAMP_ID"), str) and row["SAMP_ID"]:
            return row["SAMP_ID"]
        kind = row.get("SAMP_TYPE") if isinstance(row.get("SAMP_TYPE"), str) else ""
        ref = row.get("SAMP_REF") if isinstance(row.get("SAMP_REF"), str) else ""
        top = build.data.text_at(group, row["_line"], "SAMP_TOP")
        if not (kind or ref) and top is None:
            return None
        at = f" at {top} {unit}".rstrip() if top is not None else ""
        return f"{kind}{ref}{at}"

    return pd.Series(
        [reference(row) for row in rows.to_dict("records")],
        index=rows.index,
        dtype=object,
    )


def atterberg(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the Atterberg dataset; see ``Project.atterberg``."""
    build = Build(
        path,
        noun=("Atterberg result", "Atterberg results"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("LLPL"):
        return build.finish(pd.DataFrame(), ATTERBERG_COLUMNS, group="LLPL", **common)
    rows = build.rows("LLPL")
    frame = specimens(build, "LLPL", rows)
    frame = frame.join(limits(build, rows))
    frame["water_content"] = _water_content(build, frame)
    labels = frame["loca_id"].astype(str) + " " + specimen_names(frame)
    frame = classify_plasticity(frame, labels)
    return build.finish(frame, ATTERBERG_COLUMNS, group="LLPL", **common)


def limits(build: Build, rows: pd.DataFrame) -> pd.DataFrame:
    """LL, PL, the PI the file gives, and ``non_plastic`` of ``LLPL`` rows (§6.2)."""
    non_plastic = pd.Series(False, index=rows.index)
    for heading in ("LLPL_LL", "LLPL_PL", "LLPL_PI"):
        non_plastic |= build.flagged("LLPL", rows, heading, "NP")
    return pd.DataFrame(
        {
            "liquid_limit": build.numbers(rows, "LLPL_LL"),
            "plastic_limit": build.numbers(rows, "LLPL_PL"),
            "plasticity_index": build.numbers(rows, "LLPL_PI"),
            "non_plastic": non_plastic,
        },
        index=rows.index,
    )


def specimen_names(frame: pd.DataFrame) -> pd.Series:
    """``<sample reference>/<SPEC_REF>``, as warnings name a specimen."""
    return (
        frame["sample_reference"].fillna("").astype(str)
        + "/"
        + frame["specimen_reference"].fillna("").astype(str)
    )


def classify_plasticity(frame: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    """Add PI (where blank), LI, Ic and the classes with ``plasticity()`` (§6.2).

    ``plasticity()`` stops on a plastic specimen with PL above LL, or an NP one
    with a PI, which is right for a table a user typed in. A dataset doesn't
    stop on bad data in the file (that's QC's job), so those rows keep LL and
    PL as the file gives them, with blank PI, LI, Ic and classes, and one
    warning names them. ``plasticity()``'s warning about a PI more than 1
    point from LL - PL isn't repeated, since QC A002 reports it. ``labels``
    name the rows in the warnings.
    """
    frame = frame.copy()
    non_plastic = frame["non_plastic"].astype(bool)
    inverted = ~non_plastic & (frame["plastic_limit"] > frame["liquid_limit"])
    contradicts = non_plastic & frame["plasticity_index"].notna()
    for rows, problem, rule in (
        (inverted, "a plastic limit above the liquid limit", "A001"),
        (contradicts, "an NP flag and a plasticity index", "A004"),
    ):
        if rows.any():
            named = ", ".join(dict.fromkeys(labels[rows]))
            warn(
                f"Atterberg results with {problem}: {named}. Their "
                "plasticity_index, liquidity_index, consistency_index and "
                f"plasticity classes are left blank. p.qc() lists them ({rule})."
            )
    usable = ~(inverted | contradicts)
    inputs = frame.loc[
        usable,
        [
            "liquid_limit",
            "plastic_limit",
            "plasticity_index",
            "non_plastic",
            "water_content",
        ],
    ].set_axis(labels[usable].to_numpy())
    for column in PLASTICITY_COLUMNS:
        frame[column] = (
            pd.Series(np.nan, index=frame.index, dtype=float)
            if column.endswith("_index")
            else pd.Series(None, index=frame.index, dtype=object)
        )
    if usable.any():
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message=r"Rows .* have a plasticity_index more than"
            )
            classified = plasticity(inputs)
        for column in PLASTICITY_COLUMNS:
            frame.loc[usable, column] = classified[column].to_numpy()
    return frame


def _water_content(build: Build, frame: pd.DataFrame) -> pd.Series:
    """``LNMC_MC`` of each row's specimen, where it has exactly one (§6.2)."""
    water = pd.Series(np.nan, index=frame.index, dtype=float)
    if not build.has("LNMC") or "specimen_id" not in build.data.table("LNMC"):
        return water
    lnmc = build.data.table("LNMC").dropna(subset=["specimen_id"])
    keys = lnmc["specimen_id"].astype(int).astype(str)
    counts = keys.value_counts()
    single = pd.Series(
        build.numbers(lnmc, "LNMC_MC").to_numpy(), index=keys.to_numpy()
    )[lambda s: s.index.isin(counts.index[counts == 1])]
    water = frame["specimen_id"].map(single).astype(float)
    several = frame["specimen_id"].isin(counts.index[counts > 1])
    if several.any():
        named = ", ".join(
            dict.fromkeys(
                f"{row.loca_id} {row.sample_reference}/{row.specimen_reference}"
                for row in frame[several].itertuples()
            )
        )
        warn(
            f"Specimens with more than one water content (LNMC) row: {named}. "
            "Their water_content, liquidity_index and consistency_index are left "
            "blank, since hangtu can't tell which applies. Check LNMC."
        )
    return water


def grain_size(
    path: str | PathLike[str],
    *,
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the grading-curve dataset; see ``Project.grain_size``."""
    build = Build(
        path,
        noun=("grading point", "grading points"),
        display_units=display_units,
        include_incomplete=include_incomplete,
    )
    if not build.has("GRAT"):
        return build.finish(pd.DataFrame(), GRAIN_SIZE_COLUMNS, group="GRAT", **common)
    rows = build.rows("GRAT")
    frame = specimens(build, "GRAT", rows)
    frame["particle_size"] = build.numbers(rows, "GRAT_SIZE")
    frame["percent_passing"] = build.numbers(rows, "GRAT_PERP")
    frame["qualifier"] = build.qualifier("GRAT", rows, "GRAT_PERP")
    return build.finish(frame, GRAIN_SIZE_COLUMNS, group="GRAT", **common)


def grain_size_summary(
    path: str | PathLike[str],
    *,
    fractions="astm_uscs",
    d_values=(10, 30, 60),
    display_units: str | None = None,
    include_incomplete: bool = False,
    **common,
) -> pd.DataFrame:
    """Build the grading summary; see ``Project.grain_size_summary``.

    ``gradation()`` on the finished ``grain_size()`` dataset (§6.5), so the
    filters, units and warnings are those of the curves.
    """
    curves = grain_size(
        path,
        display_units=display_units,
        include_incomplete=include_incomplete,
        **common,
    )
    geology = list(curves.columns[curves.columns.get_loc("qualifier") + 1 : -1])
    return summarize_curves(curves, SPECIMEN_COLUMNS, geology, fractions, d_values)


def summarize_curves(
    curves: pd.DataFrame,
    first: list[str],
    last: list[str],
    fractions="astm_uscs",
    d_values=(10, 30, 60),
) -> pd.DataFrame:
    """Return ``gradation()`` of a ``grain_size()`` frame, one row per specimen.

    The columns are ``first``, the D-values, Cu, Cc, the fractions and
    ``fraction_system``, then ``last``. A curve with a percent passing outside
    0 to 100, or a size of 0 or less, which ``gradation()`` rejects, is kept
    with blank values and one warning, since a dataset doesn't stop on the
    file's data (QC P002 reports it).
    """
    wanted = _check_d_values(d_values)
    system, system_fractions = fraction_system(fractions)
    contents = [content_column(fraction["name"]) for fraction in system_fractions]
    computed = [
        *(f"d{percent}" for percent in wanted),
        "uniformity_coefficient",
        "curvature_coefficient",
        *contents,
    ]
    passing, size = curves["percent_passing"], curves["particle_size"]
    bad = curves.loc[(passing < 0) | (passing > 100) | (size <= 0), "specimen_id"]
    if not bad.empty:
        named = curves.drop_duplicates("specimen_id").loc[
            lambda df: df["specimen_id"].isin(bad)
        ]
        warn(
            "Grading curves with a percent passing outside 0 to 100 or a "
            f"particle size of 0 or less: {', '.join(_curve_names(named))}. Their "
            "D-values and fractions are left blank. p.qc() lists them (P002)."
        )
    good = curves[~curves["specimen_id"].isin(bad)]
    summary = (
        curves.drop_duplicates("specimen_id")
        .reindex(columns=[*first, *computed, "fraction_system", *last])
        .reset_index(drop=True)
    )
    summary[computed] = summary[computed].astype(float)
    summary["fraction_system"] = system if len(summary) else None
    if not good.empty:
        found = gradation(good, fractions=fractions, d_values=wanted)
        found = found.set_index("specimen_id")
        for column in computed:
            summary[column] = summary["specimen_id"].map(found[column]).astype(float)
    summary.attrs = {
        **curves.attrs,
        "units": {
            **{c: u for c, u in curves.attrs["units"].items() if c in summary},
            **{f"d{percent}": "mm" for percent in wanted},
            **dict.fromkeys(contents, "%"),
        },
    }
    return summary


def _curve_names(frame: pd.DataFrame) -> list[str]:
    return list(frame["loca_id"].astype(str) + " " + specimen_names(frame))
