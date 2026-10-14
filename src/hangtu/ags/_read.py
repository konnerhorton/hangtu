"""Read an AGS4 file into text tables and python-ags4 findings (docs/data/ingest.md §3).

python-ags4 parses and validates the file. Everything it prints or logs is
captured here and turned into findings, so ingest prints nothing.
"""

import contextlib
import hashlib
import io
import logging
import re
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path

import pandas as pd
from python_ags4 import AGS4

from hangtu.ags._findings import Finding
from hangtu.errors import AgsFileError

VERSIONS = ("4.0.3", "4.0.4", "4.1", "4.1.1", "4.2")
REFERENCE_VERSION = "4.2"

_BOM = b"\xef\xbb\xbf"

# Log messages that say nothing a finding doesn't already say.
_QUIET_LOG = {
    "DICT group not found in input file.",  # normal when there are no user groups
}
# python-ags4's note on an unknown TRAN_AGS names the dictionary it would have
# used; ingest uses 4.2 instead and says so in V000.
_UNKNOWN_VERSION_NOTE = "is not a recognized AGS4 version"


@dataclass
class AgsText:
    """An AGS file as text: what python-ags4 read, before any typing.

    ``tables`` holds the DATA rows of each group, every value a string, with
    the file line in ``_line``. ``units`` and ``types`` are the group's UNIT
    and TYPE rows, by heading (empty strings where the row is missing).
    """

    path: Path
    sha256: str
    size: int
    version: str
    version_source: str
    tables: dict[str, pd.DataFrame]
    headings: dict[str, list[str]]
    units: dict[str, dict[str, str]]
    types: dict[str, dict[str, str]]
    group_lines: dict[str, int]
    heading_lines: dict[str, int]
    findings: list[Finding] = field(default_factory=list)


def read(path: str | PathLike[str]) -> AgsText:
    """Read and validate the AGS4 file at ``path``.

    Raises ``AgsFileError`` only when the file can't be read as AGS4 at all
    (SPEC §6.2); every other problem is a finding.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"No AGS file at {str(path)!r}. Check the path; it is relative to "
            f"{str(Path.cwd())!r} unless it starts from a drive or /."
        )
    data = path.read_bytes()
    text = _decode(data, path)
    _check_is_ags4(text, path)

    log = _Capture()
    with log:
        try:
            tables, _, line_numbers = AGS4.AGS4_to_dataframe(
                io.StringIO(text, newline=""), get_line_numbers=True
            )
        except AGS4.AGS4Error as error:
            raise AgsFileError(
                f"Can't read {path.name}: {error} Fix that line and ingest again."
            ) from None
    if not tables:
        raise AgsFileError(_not_ags4(path))

    version, version_source, findings = _version(tables)
    with log:
        results = AGS4.check_file(
            io.StringIO(text, newline=""), standard_AGS4_dictionary=version
        )
    findings += _validation_findings(results)
    findings += log.findings()

    result = AgsText(
        path=path.resolve(),
        sha256=hashlib.sha256(data).hexdigest(),
        size=len(data),
        version=version,
        version_source=version_source,
        tables={},
        headings={},
        units={},
        types={},
        group_lines={},
        heading_lines={},
        findings=findings,
    )
    for group, table in tables.items():
        _add_group(result, group, table, line_numbers.get(group, {}))
    return result


def _decode(data: bytes, path: Path) -> str:
    if data.startswith(_BOM):
        data = data[len(_BOM) :]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        line = data.count(b"\n", 0, error.start) + 1
        raise AgsFileError(
            f"{path.name} isn't UTF-8 text: line {line} has a character hangtu "
            "can't read (often a degree sign or accent saved in an older "
            "Windows encoding). Save the file as UTF-8 and ingest again."
        ) from None


def _check_is_ags4(text: str, path: Path) -> None:
    for line in text.splitlines():
        if line.startswith('"**'):
            raise AgsFileError(
                f"{path.name} looks like an AGS3 file (its group lines start "
                'with "**"). hangtu reads AGS4 only (versions 4.0.3 to 4.2); '
                "convert the file to AGS4 first."
            )
        if line.startswith('"GROUP"'):
            return
    raise AgsFileError(_not_ags4(path))


def _not_ags4(path: Path) -> str:
    return (
        f"{path.name} isn't an AGS4 file: it has no GROUP line. An AGS4 file "
        'starts with a line such as "GROUP","PROJ", followed by HEADING, UNIT, '
        "TYPE and DATA lines."
    )


def _version(tables: dict[str, pd.DataFrame]) -> tuple[str, str, list[Finding]]:
    """Return the version to read the file as, where it came from, and V000."""
    tran = tables.get("TRAN")
    stated = line = None
    if tran is not None and "TRAN_AGS" in tran:
        rows = tran.loc[tran["HEADING"] == "DATA"]
        if len(rows):
            stated = rows["TRAN_AGS"].iloc[0].strip() or None
            line = int(rows["line_number"].iloc[0])
    if stated in VERSIONS:
        return stated, "TRAN_AGS", []
    said = f'TRAN_AGS is "{stated}"' if stated else "TRAN_AGS is missing"
    finding = Finding(
        rule="V000",
        severity="warning",
        group="TRAN",
        heading="TRAN_AGS",
        line=line,
        message=(
            f"{said}, which isn't an AGS4 version hangtu knows "
            f"({', '.join(VERSIONS)}), so the file was read as AGS {REFERENCE_VERSION}."
        ),
    )
    return REFERENCE_VERSION, "assumed", [finding]


_RULE = re.compile(r"(?:AGS Format Rule|Related to Rule) (\w+)")


def _validation_findings(results: dict[str, list[dict]]) -> list[Finding]:
    """Turn ``check_file`` results into V findings (plan decision 2)."""
    findings = []
    for name, entries in results.items():
        if name in ("Metadata", "Summary of data"):
            continue
        rule, severity = _rule_of(name)
        for entry in entries:
            message = entry["desc"]
            if _UNKNOWN_VERSION_NOTE in message:
                continue
            line = entry.get("line")
            findings.append(
                Finding(
                    rule=rule,
                    severity=severity,
                    message=message,
                    group=entry.get("group") or None,
                    line=line if isinstance(line, int) else None,
                )
            )
    return findings


def _rule_of(name: str) -> tuple[str, str]:
    match = _RULE.search(name)
    if name.startswith("AGS Format Rule"):
        return (f"V{match[1]}" if match else "V"), "error"
    if name.startswith("FYI"):
        return (f"V{match[1]}" if match else "VFYI"), "info"
    if name.startswith("Warning"):
        return (f"V{match[1]}" if match else "VWARNING"), "warning"
    if name == "General":
        return "VGENERAL", "warning"
    return "VPROCESS", "error"  # "Validator Process Error" and anything new


def _add_group(result: AgsText, group: str, table: pd.DataFrame, lines: dict) -> None:
    headings = [column for column in table.columns if column not in _NOT_HEADINGS]
    rows = table["HEADING"]

    def row_of(kind: str) -> dict[str, str]:
        found = table.loc[rows == kind, headings]
        return dict(found.iloc[0]) if len(found) else dict.fromkeys(headings, "")

    data = table.loc[rows == "DATA", headings].reset_index(drop=True)
    data.insert(0, "_line", table.loc[rows == "DATA", "line_number"].to_numpy())
    result.tables[group] = data
    result.headings[group] = headings
    result.units[group] = row_of("UNIT")
    result.types[group] = row_of("TYPE")
    result.group_lines[group] = lines.get("GROUP")
    result.heading_lines[group] = lines.get("HEADING")


_NOT_HEADINGS = ("HEADING", "line_number")


class _Capture:
    """Capture python-ags4's printing and logging while it runs (plan decision 3).

    Use it as a context manager around each call; ``findings()`` then returns
    what was logged, as V findings.
    """

    def __init__(self) -> None:
        self._records: list[logging.LogRecord] = []
        self._stack: contextlib.ExitStack | None = None

    def __enter__(self) -> "_Capture":
        logger = logging.getLogger("python_ags4")
        handler = _ListHandler(self._records)
        saved = logger.propagate
        stack = contextlib.ExitStack()
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        logger.addHandler(handler)
        logger.propagate = False

        def restore() -> None:
            logger.removeHandler(handler)
            logger.propagate = saved

        stack.callback(restore)
        self._stack = stack
        return self

    def __exit__(self, *exc: object) -> None:
        assert self._stack is not None
        self._stack.close()

    def findings(self) -> list[Finding]:
        found, seen = [], set()
        for record in self._records:
            message = record.getMessage()
            # check_file parses the file again, so each message comes twice.
            if record.levelno < logging.WARNING or message in _QUIET_LOG | seen:
                continue
            seen.add(message)
            severity = "error" if record.levelno >= logging.ERROR else "warning"
            found.append(Finding(rule="VLOG", severity=severity, message=message))
        return found


class _ListHandler(logging.Handler):
    def __init__(self, records: list[logging.LogRecord]) -> None:
        super().__init__(level=logging.DEBUG)
        self._records = records

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(record)
