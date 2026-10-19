"""A project: one AGS file read into a SQLite database (docs/data/ingest.md §2)."""

import hashlib
from importlib.metadata import version
from os import PathLike
from pathlib import Path
from typing import Any

import pandas as pd

import hangtu.db as database
from hangtu import ags, datasets, qc
from hangtu._settings import Settings, settings
from hangtu.datasets import _geology_map
from hangtu.errors import HangtuError, warn

_KEY_COLUMNS = ("_row", "_line", "location_id", "sample_id", "specimen_id")


class Project:
    """An AGS4 file in a project database, ready to query.

    Build one with ``Project.from_ags`` and open it again later with
    ``Project.open``; the database doesn't need the AGS file after that.

    Examples
    --------
    >>> p = ht.Project.from_ags("site.ags", db="site.sqlite", display_units="US")
    >>> p.groups
    ['PROJ', 'TRAN', ..., 'LOCA', 'GEOL', 'ISPT']
    >>> spt = p.table("ISPT")              # typed, SI, df.attrs["units"] set
    >>> raw = p.table("ISPT", raw=True)    # the file's text
    >>> p.sql('select * from ISPT where ISPT_NVAL > 50')
    >>> p = ht.Project.open("site.sqlite")
    """

    def __init__(self, path: str | PathLike[str]) -> None:
        self._path = Path(path)

    @classmethod
    def from_ags(
        cls,
        path: str | PathLike[str],
        db: str | PathLike[str] | None = None,
        *,
        overwrite: bool = False,
        **project_settings: Any,
    ) -> "Project":
        """Read the AGS4 file at ``path`` into a new project database.

        Parameters
        ----------
        path
            The AGS4 file (versions 4.0.3 to 4.2).
        db
            Where to write the database. By default it goes next to the AGS
            file, with the suffix ``.sqlite``.
        overwrite
            Rebuild ``db`` if it already exists. Otherwise that is an error, so
            a project isn't replaced by accident.
        **project_settings
            Project settings such as ``display_units="US"`` or
            ``vertical_datum="NAVD88"``; any not given come from ``ht.settings``.

        Notes
        -----
        Ingest stops only when the file can't be read as AGS4 at all. Every
        other problem (validation, units, unrecognized text) is stored as a
        finding: ``p.sql("select * from finding")``.
        """
        path = Path(path)
        target = path.with_suffix(".sqlite") if db is None else Path(db)
        if target.exists() and not overwrite:
            raise HangtuError(
                f"{str(target)!r} already exists. Open it with "
                f"ht.Project.open({str(target)!r}), or rebuild it from the AGS file "
                f"with ht.Project.from_ags({str(path)!r}, db={str(target)!r}, "
                "overwrite=True)."
            )
        chosen = {
            **settings._values,
            **{k: Settings._validate(k, v) for k, v in project_settings.items()},
        }
        result = ags.ingest(path)  # raises before anything is written
        database.write(target, result, chosen, version("hangtu"))
        return cls(target)

    @classmethod
    def open(cls, path: str | PathLike[str]) -> "Project":
        """Open a project database built by ``Project.from_ags``.

        Warns when the AGS file is still where it was read from but has
        changed since, since the database is then out of date.
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(
                f"No project database at {str(path)!r}. Build one with "
                'ht.Project.from_ags("site.ags", db=...).'
            )
        if "meta_source" not in _tables(path):
            raise HangtuError(
                f"{str(path)!r} isn't a hangtu project database. Build one with "
                'ht.Project.from_ags("site.ags", db=...).'
            )
        project = cls(path)
        project._check_schema()
        project._check_source()
        return project

    # --- What's in it ----------------------------------------------------------

    @property
    def path(self) -> Path:
        """The database file."""
        return self._path

    @property
    def settings(self) -> "ProjectSettings":
        """The project's settings, stored in the database.

        Change one by assigning to it: ``p.settings.display_units = "SI"``.
        """
        return ProjectSettings(self._path)

    @property
    def groups(self) -> list[str]:
        """The AGS groups in the file, in file order."""
        rows = database.read_sql(
            self._path,
            'SELECT "group" FROM meta_heading GROUP BY "group" ORDER BY MIN(rowid)',
        )
        return list(rows["group"])

    def table(self, group: str, raw: bool = False) -> pd.DataFrame:
        """Return one AGS group as a DataFrame.

        Parameters
        ----------
        group
            The group name, e.g. ``"ISPT"``.
        raw
            False (the default) gives the canonical table: typed, in SI, with
            surrogate keys and ``df.attrs["units"]`` set. True gives the text
            exactly as in the file, with each row's ``_line``.
        """
        groups = self.groups
        if group not in groups:
            raise HangtuError(
                f"This project has no group {group!r}. Groups: {', '.join(groups)}."
            )
        if raw:
            return database.read_table(self._path, f"raw_{group}")
        df = database.read_table(self._path, group)
        for column in _KEY_COLUMNS:
            if column in df:
                df[column] = df[column].astype("Int64")
        headings = database.read_sql(
            self._path,
            'SELECT heading, unit, file_type FROM meta_heading WHERE "group" = ? '
            "ORDER BY rowid",
            (group,),
        )
        yes_no = headings.loc[headings["file_type"] == "YN", "heading"]
        for column in yes_no:
            df[column] = df[column].astype("Int64")
        with_units = headings.dropna(subset="unit")
        df.attrs["units"] = dict(
            zip(with_units["heading"], with_units["unit"], strict=True)
        )
        return df

    def sql(self, query: str, params: tuple | dict = ()) -> pd.DataFrame:
        """Run a read-only SQL query on the database and return the result.

        Table names are AGS group names (``ISPT``), ``raw_<GROUP>`` for the
        file's text, and ``finding``, ``value_flag``, ``specimen`` and
        ``meta_*``. Quote ``"group"``, which is an SQL keyword.
        """
        try:
            return database.read_sql(self._path, query, params)
        except pd.errors.DatabaseError as error:
            reason = str(error.__cause__ or error)
            read_only = (
                " p.sql() is read-only: it reads tables but can't change them."
                if "readonly" in reason
                else ""
            )
            raise HangtuError(f"The query failed: {reason}.{read_only}") from None

    def qc(
        self,
        rules: "str | PathLike[str] | dict | None" = None,
        min_fields: "str | PathLike[str] | dict | None" = None,
    ) -> "qc.Report":
        """Check the data for integrity problems and return a report (qc.md).

        Runs every QC level 1 rule over the canonical tables and adds the
        findings stored at ingest. Nothing is written to the database, so
        running it twice gives the same report.

        Parameters
        ----------
        rules
            Overrides of the default rule settings (``qc/rules.yaml``): a path
            to a YAML file or a dict holding only what changes. Each rule takes
            ``enabled``, ``severity`` and ``thresholds``; a threshold with a
            unit is written with it (``"0.05 ft"``).
        min_fields
            Overrides of the minimally useful fields per group
            (``qc/min_fields.yaml``), ``required`` and ``recommended`` lists.

        Examples
        --------
        >>> report = p.qc()
        >>> report = p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}},
        ...                      "A004": {"enabled": False}})
        >>> report.findings
        >>> report.to_csv("qc_report.csv")   # and qc_report_rules.csv
        """
        return qc.run(self._path, rules, min_fields)

    def diff(
        self,
        group: str,
        heading: str | list[str] | None = None,
        changed_only: bool = False,
    ) -> pd.DataFrame:
        """Compare the file's text with the stored value, cell by cell (qc.md §7).

        Parameters
        ----------
        group
            The AGS group, e.g. ``"ISPT"``.
        heading
            One heading or a list; by default every heading of the group.
        changed_only
            Keep only the cells ingest changed: ``flagged``, ``not_converted``,
            ``converted`` and ``reformatted``.

        Returns
        -------
        DataFrame
            One row per cell, in file order: ``_line``, ``loca_id``,
            ``heading``, ``text`` and ``file_unit`` as in the file; ``value``
            and ``unit`` as stored (SI); ``display_value`` and
            ``display_unit`` in the project's display units; ``flag`` and
            ``bound``; and ``change``, which says what ingest did: ``blank``,
            ``flagged``, ``not_converted``, ``converted``, ``reformatted`` or
            ``unchanged``.

        Examples
        --------
        >>> p.diff("ISPT", heading="ISPT_TOP")
        >>> p.diff("ISPT", changed_only=True)
        """
        return qc.diff(self._path, group, heading, changed_only)

    # --- Datasets (datasets.md) -------------------------------------------------

    @property
    def locations(self) -> pd.DataFrame:
        """One row per hole: ID, type, ground level, final depth, coordinates.

        In the project's display units, with ``df.attrs["units"]`` set
        (datasets.md §3).
        """
        return datasets.locations(self._path)

    def spt(
        self,
        *,
        hammer_efficiency: float | None = None,
        cap: int | None = None,
        holes: "str | list[str] | None" = None,
        geology: "str | list[str] | None" = None,
        depth: "tuple | None" = None,
        elevation: "tuple | None" = None,
        where: dict | None = None,
        contains: "str | list[str] | None" = None,
        geology_fields: "str | list[str] | None" = None,
        include_incomplete: bool = False,
        display_units: str | None = None,
    ) -> pd.DataFrame:
        """Return the SPT results, one row per test, ready for P02 and P03.

        Each test is placed at the middle of its test drive (SPEC §8.2):
        ``depth_basis`` says ``mid_drive`` when the file gives the increment
        penetrations, ``mid_drive_nominal`` when hangtu assumed the nominal
        150 mm seating drive. Refusal, N60 and capped N come from
        ``ht.analysis.spt()``; ``spt_n60`` keeps an N60 the file gives, and
        ``energy_source`` says where each N60 came from. See
        ``docs/data/datasets.md`` §6.1.

        Parameters
        ----------
        hammer_efficiency, cap
            Passed to ``ht.analysis.spt()``: the energy ratio (%) for tests
            without ``ISPT_ERAT``, and the N refusals are capped at.
        holes, geology
            Keep these holes (``LOCA_ID``) or geology units.
        depth, elevation
            Keep ``low <= value <= high``, given in the dataset's units
            (``(0, 30)``) or as quantity strings (``("0 ft", "30 ft")``).
            Either end may be None.
        where
            Keep rows matching ``{column: value or list of values}``.
        contains
            Keep rows whose geology description contains this text (any
            case), or any of a list.
        geology_fields
            GEOL headings to add as columns, e.g. ``["GEOL_FORM"]``.
        include_incomplete
            Keep records with a blank required field (QC C001). By default
            they're left out, with a warning that counts them.
        display_units
            ``"US"`` or ``"SI"``; by default the project's.

        Examples
        --------
        >>> spt = p.spt(geology=["Alluvium"], depth=(0, 30))
        >>> fig, ax = ht.plot.spt_profile(spt)
        """
        return datasets.spt(
            self._path,
            hammer_efficiency=hammer_efficiency,
            cap=cap,
            holes=holes,
            geology=geology,
            depth=depth,
            elevation=elevation,
            where=where,
            contains=contains,
            geology_fields=geology_fields,
            include_incomplete=include_incomplete,
            display_units=display_units,
        )

    def atterberg(
        self,
        *,
        holes: "str | list[str] | None" = None,
        geology: "str | list[str] | None" = None,
        depth: "tuple | None" = None,
        elevation: "tuple | None" = None,
        where: dict | None = None,
        contains: "str | list[str] | None" = None,
        geology_fields: "str | list[str] | None" = None,
        include_incomplete: bool = False,
        display_units: str | None = None,
    ) -> pd.DataFrame:
        """Return the Atterberg limits, one row per LLPL record, ready for P01 and P07.

        Each result has its specimen's water content (``LNMC``), and the
        liquidity index, consistency index and plasticity classes (USCS and
        BS 5930) from ``ht.analysis.plasticity()``. A non-plastic specimen has
        ``non_plastic = True`` and a blank plastic limit and plasticity index,
        so plots count it as NP, never as a blank. A blank ``LLPL_PI`` is
        filled with LL - PL. A plastic limit above the liquid limit is kept as
        the file gives it, with the computed columns blank and a warning.
        Depth is the specimen's, else its sample's midpoint, else its top
        (``depth_basis``). See ``docs/data/datasets.md`` §6.2.

        Parameters
        ----------
        holes, geology
            Keep these holes (``LOCA_ID``) or geology units.
        depth, elevation
            Keep ``low <= value <= high``, given in the dataset's units
            (``(0, 30)``) or as quantity strings (``("0 ft", "30 ft")``).
            Either end may be None.
        where
            Keep rows matching ``{column: value or list of values}``.
        contains
            Keep rows whose geology description contains this text (any
            case), or any of a list.
        geology_fields
            GEOL headings to add as columns, e.g. ``["GEOL_FORM"]``.
        include_incomplete
            Keep records with a blank required field (QC C001). By default
            they're left out, with a warning that counts them.
        display_units
            ``"US"`` or ``"SI"``; by default the project's.

        Examples
        --------
        >>> atterberg = p.atterberg(geology=["Alluvium"])
        >>> fig, ax = ht.plot.geology_unit_comparison(atterberg, "plasticity_index")
        """
        return datasets.atterberg(
            self._path,
            holes=holes,
            geology=geology,
            depth=depth,
            elevation=elevation,
            where=where,
            contains=contains,
            geology_fields=geology_fields,
            include_incomplete=include_incomplete,
            display_units=display_units,
        )

    def grain_size(
        self,
        *,
        holes: "str | list[str] | None" = None,
        geology: "str | list[str] | None" = None,
        depth: "tuple | None" = None,
        elevation: "tuple | None" = None,
        where: dict | None = None,
        contains: "str | list[str] | None" = None,
        geology_fields: "str | list[str] | None" = None,
        include_incomplete: bool = False,
        display_units: str | None = None,
    ) -> pd.DataFrame:
        """Return the grading curves, one row per GRAT point, in file order.

        ``particle_size`` is in mm in US and SI output alike, as US practice
        keeps it. Each point carries its specimen (``specimen_id``) and depth,
        so a curve is the rows of one specimen. See ``docs/data/datasets.md``
        §6.3.

        Parameters
        ----------
        holes, geology
            Keep these holes (``LOCA_ID``) or geology units.
        depth, elevation
            Keep ``low <= value <= high``, given in the dataset's units
            (``(0, 30)``) or as quantity strings (``("0 ft", "30 ft")``).
            Either end may be None.
        where
            Keep rows matching ``{column: value or list of values}``.
        contains
            Keep rows whose geology description contains this text (any
            case), or any of a list.
        geology_fields
            GEOL headings to add as columns, e.g. ``["GEOL_FORM"]``.
        include_incomplete
            Keep records with a blank required field (QC C001). By default
            they're left out, with a warning that counts them.
        display_units
            ``"US"`` or ``"SI"``; by default the project's.

        Examples
        --------
        >>> curves = p.grain_size(holes=["BH3"])
        >>> curves.groupby("specimen_id")["percent_passing"].min()
        """
        return datasets.grain_size(
            self._path,
            holes=holes,
            geology=geology,
            depth=depth,
            elevation=elevation,
            where=where,
            contains=contains,
            geology_fields=geology_fields,
            include_incomplete=include_incomplete,
            display_units=display_units,
        )

    def permeability(
        self,
        *,
        holes: "str | list[str] | None" = None,
        geology: "str | list[str] | None" = None,
        depth: "tuple | None" = None,
        elevation: "tuple | None" = None,
        where: dict | None = None,
        contains: "str | list[str] | None" = None,
        geology_fields: "str | list[str] | None" = None,
        include_incomplete: bool = False,
        display_units: str | None = None,
    ) -> pd.DataFrame:
        """Return hydraulic conductivity from lab and field tests, for P01 and P07.

        One row per result: ``PTST_K`` (``source = "lab"``, at the specimen's
        depth), ``FGHG_IPRM`` and, in 4.0.x files, each ``IPRG_IPRM`` stage
        (``source = "field"``, at the middle of the test zone, with
        ``depth_top`` and ``depth_base``). ``<``/``>`` results keep their
        bound as the value and the sign in ``qualifier``. See
        ``docs/data/datasets.md`` §6.4.

        Parameters
        ----------
        holes, geology
            Keep these holes (``LOCA_ID``) or geology units.
        depth, elevation
            Keep ``low <= value <= high``, given in the dataset's units
            (``(0, 30)``) or as quantity strings (``("0 ft", "30 ft")``).
            Either end may be None.
        where
            Keep rows matching ``{column: value or list of values}``.
        contains
            Keep rows whose geology description contains this text (any
            case), or any of a list.
        geology_fields
            GEOL headings to add as columns, e.g. ``["GEOL_FORM"]``.
        include_incomplete
            Keep records with a blank required field (QC C001). By default
            they're left out, with a warning that counts them.
        display_units
            ``"US"`` or ``"SI"``; by default the project's.

        Examples
        --------
        >>> k = p.permeability()
        >>> fig, ax = ht.plot.profile(k, "hydraulic_conductivity", marker_by="source")
        """
        return datasets.permeability(
            self._path,
            holes=holes,
            geology=geology,
            depth=depth,
            elevation=elevation,
            where=where,
            contains=contains,
            geology_fields=geology_fields,
            include_incomplete=include_incomplete,
            display_units=display_units,
        )

    # --- Geology map (datasets.md §5.2) -----------------------------------------

    def set_geology_map(
        self, source: "str | PathLike[str] | pd.DataFrame | None"
    ) -> None:
        """Map the geology codes in the file to the units you report on.

        The map is checked and stored with the project, replacing any earlier
        one, until the database is rebuilt. The codes are values of the
        ``p.settings.geology_key`` heading (``GEOL_GEOL`` by default), matched
        exactly and case-sensitively.

        Parameters
        ----------
        source
            A CSV file or a DataFrame with the columns ``code`` and
            ``geology_unit`` (required) and ``soil_class``, ``order`` and
            ``color`` (optional). None removes the map.

        Examples
        --------
        >>> p.set_geology_map("strata.csv")
        >>> p.geology_map
        >>> p.set_geology_map(None)
        """
        rows = None if source is None else _geology_map.read(source)
        database.write_geology_map(self._path, rows)

    @property
    def geology_map(self) -> pd.DataFrame | None:
        """The stored geology map, or None if there isn't one."""
        rows = database.read_geology_map(self._path)
        return None if rows.empty else rows

    def __repr__(self) -> str:
        """Summarize the file, its groups and the findings by severity."""
        source = database.read_source(self._path)
        findings = database.read_sql(
            self._path, "SELECT severity, COUNT(*) AS n FROM finding GROUP BY severity"
        )
        counts = dict(zip(findings["severity"], findings["n"], strict=True))
        summary = ", ".join(
            f"{counts[s]} {s}{'s' if counts[s] != 1 and s != 'info' else ''}"
            for s in ("error", "warning", "info")
            if s in counts
        )
        return (
            f"Project({str(self._path)!r})\n"
            f"  file:     {Path(source['path']).name} (AGS {source['ags_version']}), "
            f"ingested {source['ingested_at']}\n"
            f"  groups:   {', '.join(self.groups)}\n"
            f"  findings: {summary or 'none'}"
        )

    # --- Checks on open --------------------------------------------------------

    def _check_schema(self) -> None:
        source = database.read_source(self._path)
        if source["schema_version"] != database.SCHEMA_VERSION:
            raise HangtuError(
                f"{str(self._path)!r} was built by hangtu {source['hangtu_version']}, "
                "and this version of hangtu can't read it. Rebuild it from the AGS "
                f"file with ht.Project.from_ags({source['path']!r}, "
                f"db={str(self._path)!r}, overwrite=True)."
            )

    def _check_source(self) -> None:
        source = database.read_source(self._path)
        file = Path(source["path"])
        if not file.is_file():
            return  # the database is self-contained; a moved file is fine
        if hashlib.sha256(file.read_bytes()).hexdigest() != source["sha256"]:
            warn(
                f"{file.name} has changed since {self._path.name} was built from it, "
                "so the database is out of date. Rebuild it with "
                f"ht.Project.from_ags({str(file)!r}, db={str(self._path)!r}, "
                "overwrite=True)."
            )


class ProjectSettings:
    """A project's settings, stored in its database.

    The same settings as ``ht.settings``, checked the same way. Assigning one
    saves it straight away.
    """

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        object.__setattr__(self, "_path", path)

    def __getattr__(self, name: str) -> Any:
        """Read a stored setting."""
        stored = database.read_settings(self._path)
        if name not in stored:
            Settings._validate(name, None)  # raises for an unknown name
            raise AttributeError(name)
        return Settings._validate(name, stored[name])

    def __setattr__(self, name: str, value: Any) -> None:
        """Check a setting and save it in the database."""
        checked = Settings._validate(name, value)
        database.write_settings(self._path, {name: checked})

    def __repr__(self) -> str:
        """List the stored settings."""
        stored = database.read_settings(self._path)
        lines = [f"    {name}={value!r}," for name, value in stored.items()]
        return "ProjectSettings(\n" + "\n".join(lines) + "\n)"


def _tables(path: Path) -> list[str]:
    try:
        return database.tables(path)
    except pd.errors.DatabaseError:
        return []
