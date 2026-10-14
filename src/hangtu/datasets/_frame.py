"""What every dataset shares (datasets.md §2, §4, §5, §7, §8).

A ``Build`` reads one project for one dataset call: it gives the builders the
canonical rows (leaving out incomplete records), their values and flags in SI,
and then ``finish()`` joins ground level, elevation and geology, converts to the
display units, applies the filters and issues the warnings.
"""

from collections.abc import Iterable, Sequence
from numbers import Real
from os import PathLike
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import hangtu.db as database
from hangtu import units
from hangtu._settings import _display_units, settings
from hangtu.datasets import _geology_map, _joins
from hangtu.errors import HangtuError, warn
from hangtu.qc._data import Data
from hangtu.qc._fields import blank_required
from hangtu.qc._settings import load as load_qc_settings
from hangtu.registry import column_info

#: GEOL headings that geology_fields= can add, and their columns (§5.3).
GEOLOGY_FIELDS = {
    "GEOL_GEOL": "geology_code",
    "GEOL_GEO2": "geology_code_secondary",
    "GEOL_LEG": "legend_code",
    "GEOL_FORM": "geology_formation",
    "GEOL_BGS": "bgs_lexicon_code",
}
#: Columns every dataset ends with, before any geology_fields= and source_line.
GEOLOGY_COLUMNS = ["geology_unit", "soil_class", "geology_description"]

Pair = Sequence[float | str | None] | None


class Build:
    """One project, read for one dataset call."""

    def __init__(
        self,
        path: str | PathLike[str],
        *,
        noun: tuple[str, str],
        display_units: str | None = None,
        include_incomplete: bool = False,
    ) -> None:
        self.data = Data(path, min_fields=load_qc_settings().min_fields)
        self.path = Path(path)
        self.noun = noun  # (singular, plural): ("SPT result", "SPT results")
        stored = self.data.project_settings
        self.system = _display_units(display_units or stored["display_units"])
        self.overrides = stored.get("display_overrides", {})
        self.geology_key = stored.get("geology_key", "GEOL_GEOL")
        self.datum = stored.get("vertical_datum")
        self.include_incomplete = include_incomplete
        self.file = Path(database.read_source(path)["path"]).name
        self._left_out: list[tuple[str, int, int, dict[str, list[int]]]] = []
        self._flags = database.read_flags(path)

    # --- Rows and values -------------------------------------------------------

    def has(self, group: str) -> bool:
        return group in self.data.groups

    def rows(self, group: str) -> pd.DataFrame:
        """Return the canonical rows of ``group``, without incomplete ones (§7)."""
        table = self.data.table(group)
        required = self.data.min_fields.get(group, {}).get("required", ())
        if self.include_incomplete or not required or table.empty:
            return table
        blank = blank_required(self.data, group, tuple(required))
        incomplete = blank.any(axis=1)
        if incomplete.any():
            lines: dict[str, list[int]] = {}
            for i in table.index[incomplete]:
                for heading in blank.columns[blank.loc[i]]:
                    lines.setdefault(heading, []).append(int(table.at[i, "_line"]))
            self._left_out.append((group, int(incomplete.sum()), len(table), lines))
        return table[~incomplete]

    @staticmethod
    def numbers(table: pd.DataFrame, heading: str) -> pd.Series:
        """Return a heading's SI values; NaN where blank or absent."""
        if heading not in table:
            return pd.Series(np.nan, index=table.index, dtype=float)
        return pd.to_numeric(table[heading], errors="coerce").astype(float)

    @staticmethod
    def texts(table: pd.DataFrame, heading: str) -> pd.Series:
        """Return a heading's text; None where blank or absent."""
        if heading not in table:
            return pd.Series(None, index=table.index, dtype=object)
        values = table[heading].astype(object)
        return values.where(values.notna() & (values != ""), None)

    def flagged(self, group: str, table: pd.DataFrame, heading: str, flag: str):
        """Return True where the cell has the value flag ``flag`` (ingest.md §8)."""
        flags = self._flags
        rows = flags.loc[
            (flags["group"] == group)
            & (flags["heading"] == heading)
            & (flags["flag"] == flag),
            "_row",
        ]
        return table["_row"].isin(set(rows)).set_axis(table.index)

    def qualifier(self, group: str, table: pd.DataFrame, heading: str) -> pd.Series:
        """``<`` / ``>`` from an ``LT`` / ``GT`` flag, else ``""`` (§4)."""
        less = self.flagged(group, table, heading, "LT")
        more = self.flagged(group, table, heading, "GT")
        return pd.Series(
            np.select([less, more], ["<", ">"], default=""),
            index=table.index,
            dtype=object,
        )

    def samples(self) -> pd.DataFrame:
        """``SAMP_TOP`` and ``SAMP_BASE`` (m) by ``sample_id``."""
        if not self.has("SAMP"):
            return pd.DataFrame(columns=["SAMP_TOP", "SAMP_BASE"], dtype=float)
        samp = self.data.table("SAMP").dropna(subset=["sample_id"])
        return pd.DataFrame(
            {
                "SAMP_TOP": self.numbers(samp, "SAMP_TOP").to_numpy(),
                "SAMP_BASE": self.numbers(samp, "SAMP_BASE").to_numpy(),
            },
            index=samp["sample_id"].astype(int),
        )

    # --- Finishing -------------------------------------------------------------

    def finish(
        self,
        frame: pd.DataFrame,
        columns: list[str],
        *,
        group: str | None = None,
        holes: Iterable[str] | str | None = None,
        geology: Iterable[str] | str | None = None,
        depth: Pair = None,
        elevation: Pair = None,
        where: dict[str, Any] | None = None,
        contains: Iterable[str] | str | None = None,
        geology_fields: Iterable[str] | str | None = None,
    ) -> pd.DataFrame:
        """Join, convert, filter and warn; return the dataset (§2, §4, §5).

        ``frame`` is in SI with ``location_id``, ``loca_id``, ``depth`` and
        ``_line``, plus the dataset's own columns. ``group`` names the source
        group when the dataset's group isn't in the file, for the warning.
        """
        fields = _geology_fields(geology_fields)
        order = [*columns, *GEOLOGY_COLUMNS, *fields.values(), "source_line"]
        if group is not None and not self.has(group):
            warn(
                f"No {group} group in {self.file}, so there are no {self.noun[1]}. "
                "The dataset is empty."
            )
            return self._empty(order)
        frame = frame.copy()
        frame["source_line"] = frame.pop("_line").astype("Int64")
        self._ground_level(frame)
        frame["elevation"] = _joins.elevation(frame["ground_level"], frame["depth"])
        palette = self._geology(frame, fields)
        frame = frame.reindex(columns=order)
        frame = self._to_display(frame)
        frame = self._filter(
            frame, holes, geology, depth, elevation, where, contains
        ).reset_index(drop=True)
        self._warn_left_out()
        frame.attrs["units"] = self._units(frame)
        if palette:
            frame.attrs["palette"] = palette
        if self.datum:
            frame.attrs["vertical_datum"] = self.datum
        return frame

    def _ground_level(self, frame: pd.DataFrame) -> None:
        if self.has("LOCA"):
            loca = self.data.table("LOCA").dropna(subset=["location_id"])
            ground = pd.Series(
                self.numbers(loca, "LOCA_GL").to_numpy(),
                index=loca["location_id"].astype(int),
            )
            frame["ground_level"] = frame["location_id"].map(ground).astype(float)
        else:
            frame["ground_level"] = np.nan

    def _geology(self, frame: pd.DataFrame, fields: dict[str, str]) -> dict:
        """Add the geology columns; return the map's palette (§5)."""
        for column in [*GEOLOGY_COLUMNS, *fields.values()]:
            frame[column] = None
        if not self.has("GEOL"):
            return {}
        geol = self.data.table("GEOL")
        layers = pd.DataFrame(
            {
                "location_id": geol["location_id"],
                "top": self.numbers(geol, "GEOL_TOP"),
                "base": self.numbers(geol, "GEOL_BASE"),
            }
        )
        layer, overlapping = _joins.place_in_geology(frame, layers)
        found = layer.notna()
        at = layer[found].astype(int)

        def from_layer(series: pd.Series) -> pd.Series:
            out = pd.Series(None, index=frame.index, dtype=object)
            out[found] = series.reindex(at.to_numpy()).to_numpy()
            return out.where(out.notna(), None)

        frame["geology_description"] = from_layer(self.texts(geol, "GEOL_DESC"))
        for heading, column in fields.items():
            frame[column] = from_layer(self.texts(geol, heading))
        self._warn_overlaps(frame, overlapping)

        if not self.data.has("GEOL", self.geology_key):
            present = [h for h in GEOLOGY_FIELDS if self.data.has("GEOL", h)]
            hint = (
                f" The file has {', '.join(present)}; use one with "
                f'p.settings.geology_key = "{present[0]}".'
                if present
                else f" The file has none of {', '.join(GEOLOGY_FIELDS)}."
            )
            warn(
                f"GEOL has no {self.geology_key} heading, so geology_unit is "
                f"blank.{hint}"
            )
            return {}
        codes = from_layer(self.texts(geol, self.geology_key))
        mapping = database.read_geology_map(self.path)
        if mapping.empty:
            frame["geology_unit"] = codes
            return {}
        units_of_code = dict(zip(mapping["code"], mapping["geology_unit"], strict=True))
        unit = codes.map(lambda code: units_of_code.get(code, code), na_action="ignore")
        unmapped = codes[codes.notna() & ~codes.isin(units_of_code)]
        if not unmapped.empty:
            counts = unmapped.value_counts(sort=False)
            listed = ", ".join(
                f"{code!r} ({n} row{'s' if n != 1 else ''})"
                for code, n in counts.items()
            )
            warn(
                f"{self.geology_key} codes not in the geology map: {listed}. "
                "They're kept as their own geology units. Add them to the map "
                "with p.set_geology_map()."
            )
        known = _geology_map.unit_order(mapping)
        extra = [code for code in dict.fromkeys(unmapped) if code not in known]
        frame["geology_unit"] = pd.Categorical(
            unit.where(unit.notna(), None), categories=[*known, *extra], ordered=True
        )
        soil = _geology_map.unit_values(mapping, "soil_class")
        frame["soil_class"] = unit.map(soil).where(lambda s: s.notna(), None)
        return _geology_map.unit_values(mapping, "color")

    def _count(self, n: int) -> str:
        return f"{n} {self.noun[0] if n == 1 else self.noun[1]}"

    def _warn_overlaps(self, frame: pd.DataFrame, overlapping: pd.Series) -> None:
        if not overlapping.any():
            return
        holes = list(dict.fromkeys(frame.loc[overlapping, "loca_id"]))
        count = int(overlapping.sum())
        where = " and ".join(holes) if len(holes) < 3 else ", ".join(holes)
        warn(
            f"{self._count(count)} in {where} {'is' if count == 1 else 'are'} in "
            "overlapping GEOL layers; each was put in the layer with the deepest "
            "top. p.qc() lists the overlaps (G003)."
        )

    def _to_display(self, frame: pd.DataFrame) -> pd.DataFrame:
        with settings.override(display_overrides=self.overrides):
            for column in frame.columns:
                kind = _kind(column)
                if kind is None or units.quantity_kind(kind)["canonical"] is None:
                    continue
                canonical = units.ureg.Unit(units.quantity_kind(kind)["canonical"])
                target, _ = units._display_target(kind, self.system)
                frame[column] = units.convert(
                    frame[column].astype(float), canonical, kind, target
                )
        return frame

    def _units(self, frame: pd.DataFrame) -> dict[str, str]:
        found = {}
        with settings.override(display_overrides=self.overrides):
            for column in frame.columns:
                kind = _kind(column)
                if kind is None:
                    continue
                if units.quantity_kind(kind)["canonical"] is None:
                    if kind == "percent":
                        found[column] = "%"
                    continue
                _, text = units._display_target(kind, self.system)
                found[column] = _plain(text)
        return found

    def _filter(self, frame, holes, geology, depth, elevation, where, contains):
        keep = pd.Series(True, index=frame.index)
        if holes is not None:
            wanted = _as_list(holes)
            known = self._hole_ids()
            unknown = [h for h in wanted if h not in known]
            if unknown:
                raise HangtuError(
                    f"holes= names holes this project doesn't have: "
                    f"{', '.join(map(repr, unknown))}. Holes: {', '.join(known)}."
                )
            keep &= frame["loca_id"].isin(wanted)
        if geology is not None:
            wanted = _as_list(geology)
            units_column = frame["geology_unit"]
            categories = (
                list(units_column.cat.categories)
                if isinstance(units_column.dtype, pd.CategoricalDtype)
                else []
            )
            known = list(dict.fromkeys([*categories, *units_column.dropna()]))
            unknown = [u for u in wanted if u not in known]
            if unknown:
                raise HangtuError(
                    f"geology= names geology units that aren't in the data: "
                    f"{', '.join(map(repr, unknown))}. Units: "
                    f"{', '.join(map(str, known)) or 'none'}."
                )
            keep &= frame["geology_unit"].isin(wanted)
        if depth is not None:
            keep &= self._between(frame["depth"], depth, "depth")
        if elevation is not None:
            values = frame["elevation"]
            missing = int((keep & values.isna()).sum())
            if missing:
                warn(
                    f"Left out {self._count(missing)} with no elevation (no LOCA_GL) "
                    "from the elevation= filter."
                )
            keep &= self._between(values, elevation, "elevation")
        if where is not None:
            if not isinstance(where, dict):
                raise HangtuError(
                    "where= must be a dict of {column: value or list of values}, "
                    f'not {where!r}. Example: where={{"loca_id": ["BH1", "BH2"]}}'
                )
            unknown = [c for c in where if c not in frame.columns]
            if unknown:
                raise HangtuError(
                    f"where= names columns this dataset doesn't have: "
                    f"{', '.join(map(repr, unknown))}. Columns: "
                    f"{', '.join(frame.columns)}."
                )
            for column, value in where.items():
                keep &= frame[column].isin(_as_list(value))
        if contains is not None:
            text = frame["geology_description"].fillna("").str.lower()
            found = pd.Series(False, index=frame.index)
            for word in _as_list(contains):
                found |= text.str.contains(str(word).lower(), regex=False)
            keep &= found
        return frame[keep]

    def _between(self, values: pd.Series, pair: Pair, name: str) -> pd.Series:
        example = f'{name}=(0, 30) or {name}=("0 ft", "30 ft")'
        if isinstance(pair, str) or not isinstance(pair, Sequence) or len(pair) != 2:
            raise HangtuError(
                f"{name}= must be a pair (low, high), not {pair!r}. Example: {example}"
            )
        low, high = (self._length(end, name, example) for end in pair)
        if low is not None and high is not None and low > high:
            low, high = high, low
        keep = values.notna()
        if low is not None:
            keep &= values >= low - 1e-9
        if high is not None:
            keep &= values <= high + 1e-9
        return keep

    def _length(self, end, name: str, example: str) -> float | None:
        if end is None:
            return None
        if isinstance(end, Real) and not isinstance(end, bool):
            return float(end)
        if isinstance(end, str):
            try:
                value, unit = units.parse_quantity(end, "length")
            except HangtuError as error:
                raise HangtuError(f"{name}=: {error} Example: {example}") from None
            with settings.override(display_overrides=self.overrides):
                converted, _ = units.to_display([value], unit, "length", self.system)
            return float(converted[0])
        raise HangtuError(
            f"{name}= ends must be numbers in the dataset's units, quantity strings "
            f"or None, not {end!r}. Example: {example}"
        )

    def _hole_ids(self) -> list[str]:
        if not self.has("LOCA"):
            return []
        return [str(h) for h in self.data.table("LOCA")["LOCA_ID"].dropna()]

    def _warn_left_out(self) -> None:
        for group, count, total, lines in self._left_out:
            detail = "; ".join(
                f"{heading} on line{'s' if len(at) > 1 else ''} "
                f"{', '.join(map(str, at))}"
                for heading, at in lines.items()
            )
            warn(
                f"Left out {count} of {total} {group} records with a blank required "
                f"field ({detail}). p.qc() lists them; include them with "
                "include_incomplete=True."
            )

    def _empty(self, order: list[str]) -> pd.DataFrame:
        frame = pd.DataFrame(
            {column: pd.Series(dtype=_dtype(column)) for column in order}
        )
        frame.attrs["units"] = self._units(frame)
        return frame


def _geology_fields(fields: Iterable[str] | str | None) -> dict[str, str]:
    if fields is None:
        return {}
    wanted = _as_list(fields)
    unknown = [f for f in wanted if f not in GEOLOGY_FIELDS]
    if unknown:
        raise HangtuError(
            f"geology_fields= takes GEOL headings, and {', '.join(map(repr, unknown))} "
            f"isn't one it can add. Headings: {', '.join(GEOLOGY_FIELDS)}."
        )
    return {heading: GEOLOGY_FIELDS[heading] for heading in wanted}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, str) or not isinstance(value, Iterable):
        return [value]
    return list(value)


def _kind(column: str) -> str | None:
    info = column_info(column)
    if info is None or info["type"] != "number":
        return None
    return info["quantity"]


def _dtype(column: str) -> str:
    info = column_info(column)
    if info is None:
        return "object"
    return {"number": "float", "bool": "boolean"}.get(info["type"], "object")


def _plain(text: str) -> str:
    """Write a label's unit text so the unit parser reads it (``kN/m³``: ``kN/m3``)."""
    return text.replace("³", "3").replace("²", "2").replace("°", "deg")


def locations(path: str | PathLike[str], display_units: str | None = None):
    """One row per hole (datasets.md §3)."""
    build = Build(path, noun=("hole", "holes"), display_units=display_units)
    columns = [
        "loca_id",
        "location_type",
        "ground_level",
        "final_depth",
        "easting",
        "northing",
        "latitude",
        "longitude",
        "remarks",
        "source_line",
    ]
    if not build.has("LOCA"):
        return build._empty(columns)
    loca = build.data.table("LOCA")
    frame = pd.DataFrame(
        {
            "loca_id": build.texts(loca, "LOCA_ID"),
            "location_type": build.texts(loca, "LOCA_TYPE"),
            "ground_level": build.numbers(loca, "LOCA_GL"),
            "final_depth": build.numbers(loca, "LOCA_FDEP"),
            "easting": build.numbers(loca, "LOCA_NATE"),
            "northing": build.numbers(loca, "LOCA_NATN"),
            "latitude": build.numbers(loca, "LOCA_LAT"),
            "longitude": build.numbers(loca, "LOCA_LON"),
            "remarks": build.texts(loca, "LOCA_REM"),
            "source_line": loca["_line"].astype("Int64"),
        }
    ).reset_index(drop=True)
    frame = build._to_display(frame)
    frame.attrs["units"] = build._units(frame)
    return frame
