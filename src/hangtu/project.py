"""A project: one AGS file read into a SQLite database (docs/data/ingest.md §2)."""

import hashlib
from importlib.metadata import version
from os import PathLike
from pathlib import Path
from typing import Any

import pandas as pd

import hangtu.db as database
from hangtu import ags, qc
from hangtu._settings import Settings, settings
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
