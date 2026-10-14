"""Write the synthetic AGS4 test files in this folder (docs/data/ingest.md §11).

Run from the repository root after changing the data below:

    uv run python tests/data/ags/_make_files.py

The SI values are written by hand. The US twin divides each by an exact
conversion factor from its definition (0.3048 m per ft, 0.45359237 kg per lb,
standard gravity 9.80665 m/s²), not by pint, so the twin-file test checks
hangtu's conversions against independent arithmetic. Converted US values are
written to 10 significant figures (TYPE ``10SF``), enough for the 1e-9
relative tolerance of acceptance criterion 1.
"""

from pathlib import Path

from python_ags4.AGS4 import _format_SF

HERE = Path(__file__).parent

FOOT = 0.3048  # m
INCH = 25.4  # mm
POUND = 0.45359237  # kg
LBF = POUND * 9.80665  # N
CUBIC_FOOT = FOOT**3  # m³
SQUARE_FOOT = FOOT**2  # m²

# US unit and the SI value of one of them, in the heading's SI unit.
TSF = ("tsf", 2000 * LBF / SQUARE_FOOT / 1000)
US = {
    "m": ("ft", FOOT),
    "mm": ("in", INCH),
    "kPa": ("psf", LBF / SQUARE_FOOT / 1000),
    "Mg/m3": ("pcf", POUND / CUBIC_FOOT / 1000),  # density: lb/ft³
    "kN/m3": ("pcf", LBF / CUBIC_FOOT / 1000),  # unit weight: lbf/ft³
    "m/s": ("cm/s", 0.01),
}

UNIT_DESCRIPTIONS = {
    "m": "metre",
    "mm": "millimetre",
    "%": "percentage",
    "kPa": "kilopascal",
    "Mg/m3": "megagrams per cubic metre",
    "kN/m3": "kilonewtons per cubic metre",
    "m/s": "metres per second",
    "l/s": "litres per second",
    "bar": "bar",
    "Bar": "bar",
    "DegC": "degrees Celsius",
    "degC": "degrees Celsius",
    "ft": "foot",
    "in": "inch",
    "psf": "pounds force per square foot",
    "tsf": "short tons force per square foot",
    "pcf": "pounds per cubic foot",
    "cm/s": "centimetres per second",
    "yyyy-mm-dd": "year month day",
    "yyyy-mm-ddThh:mm:ss": "year month day hour minute second",
    "hh:mm:ss": "hours minutes seconds",
    "mm:ss": "minutes seconds",
    "MPa": "megapascal",
    "GPa": "gigapascal",
    "Ft": "foot (wrong case)",
    "feet": "foot (not an AGS spelling)",
}

TYPE_DESCRIPTIONS = {
    "ID": "Unique identifier",
    "PA": "Text listed in ABBR group",
    "X": "Text",
    "XN": "Text or numeric",
    "DT": "Date time",
    "T": "Elapsed time",
    "YN": "Yes or No",
    "DMS": "Degrees:Minutes:Seconds",
    "0DP": "Value with 0 decimal places",
    "1DP": "Value with 1 decimal place",
    "2DP": "Value with 2 decimal places",
    "3DP": "Value with 3 decimal places",
    "1SCI": "Scientific notation with 1 decimal place",
    "3SF": "Value with 3 significant figures",
    "10SF": "Value with 10 significant figures",
    "9SCI": "Scientific notation with 9 decimal places",
}

ABBR = [
    ("LOCA_TYPE", "CP", "Cable percussion (shell and auger)"),
    ("SAMP_TYPE", "U", "Undisturbed sample - open drive"),
    ("SAMP_TYPE", "D", "Small disturbed sample"),
    ("SAMP_TYPE", "B", "Bulk disturbed sample"),
    ("DICT_TYPE", "GROUP", "Flag to indicate definition is a GROUP"),
    ("DICT_TYPE", "HEADING", "Flag to indicate definition is a HEADING"),
]


def group(name, headings, rows, us=None):
    """A group: headings as (name, TYPE, unit), rows as lists of values.

    ``us`` names the headings converted in the US twin. A row value is a number
    (written in the heading's TYPE), a string (written as is), or None (blank).
    """
    return {"name": name, "headings": headings, "rows": rows, "us": set(us or ())}


# --- The data, in SI -----------------------------------------------------------

PROJ = group(
    "PROJ",
    [("PROJ_ID", "ID", ""), ("PROJ_NAME", "X", "")],
    [["HT-SYN-1", "hangtu synthetic site"]],
)


def tran(version):
    headings = [
        ("TRAN_ISNO", "X", ""),
        ("TRAN_DATE", "DT", "yyyy-mm-dd"),
        ("TRAN_PROD", "X", ""),
        ("TRAN_STAT", "X", ""),
        ("TRAN_DESC", "X", ""),
        ("TRAN_AGS", "X", ""),
        ("TRAN_RECV", "X", ""),
        ("TRAN_DLIM", "X", ""),
        ("TRAN_RCON", "X", ""),
    ]
    return group(
        "TRAN",
        headings,
        [
            [
                "1",
                "2026-10-14",
                "hangtu",
                "Draft",
                "Synthetic test data",
                version,
                "hangtu tests",
                "|",
                "+",
            ]
        ],
    )


def dict_group(us=False):
    """The DICT entry for XPPT, in the units and TYPEs of the file's XPPT group."""
    depth, res = (
        (("10SF", "ft"), ("10SF", "tsf")) if us else (("2DP", "m"), ("0DP", "kPa"))
    )
    headings = [
        ("DICT_TYPE", "PA", ""),
        ("DICT_GRP", "X", ""),
        ("DICT_HDNG", "X", ""),
        ("DICT_STAT", "X", ""),
        ("DICT_DTYP", "X", ""),
        ("DICT_DESC", "X", ""),
        ("DICT_UNIT", "X", ""),
        ("DICT_EXMP", "X", ""),
        ("DICT_PGRP", "X", ""),
        ("DICT_REM", "X", ""),
        ("FILE_FSET", "X", ""),
    ]
    rows = [
        [
            "GROUP",
            "XPPT",
            None,
            None,
            None,
            "Pocket penetrometer",
            None,
            None,
            "LOCA",
            None,
            None,
        ],
        [
            "HEADING",
            "XPPT",
            "LOCA_ID",
            "KEY",
            "ID",
            "Location identifier",
            None,
            "BH1",
            None,
            None,
            None,
        ],
        [
            "HEADING",
            "XPPT",
            "XPPT_DPTH",
            "KEY",
            *depth[:1],
            "Depth of reading",
            depth[1],
            "1.20",
            None,
            None,
            None,
        ],
        [
            "HEADING",
            "XPPT",
            "XPPT_RES",
            "OTHER",
            res[0],
            "Pocket penetrometer reading",
            res[1],
            "150",
            None,
            None,
            None,
        ],
    ]
    return group("DICT", headings, rows)


LOCA = group(
    "LOCA",
    [
        ("LOCA_ID", "ID", ""),
        ("LOCA_TYPE", "PA", ""),
        ("LOCA_NATE", "2DP", "m"),
        ("LOCA_NATN", "2DP", "m"),
        ("LOCA_GL", "2DP", "m"),
        ("LOCA_FDEP", "2DP", "m"),
        ("LOCA_STAR", "DT", "yyyy-mm-dd"),
        ("LOCA_LAT", "DMS", ""),
    ],
    [
        [
            "BH1",
            "CP",
            523101.25,
            4182240.50,
            12.40,
            10.00,
            "2026-09-01",
            "37:47:36.100",
        ],
        ["BH2", "CP", 523150.75, 4182290.00, 11.85, 8.50, "2026-09-02", "37:47:37.700"],
        ["BH3", "CP", 523210.00, 4182330.25, 13.10, 6.00, "2026-09-03", None],
    ],
    us=["LOCA_NATE", "LOCA_NATN", "LOCA_GL", "LOCA_FDEP"],
)

GEOL = group(
    "GEOL",
    [
        ("LOCA_ID", "ID", ""),
        ("GEOL_TOP", "2DP", "m"),
        ("GEOL_BASE", "2DP", "m"),
        ("GEOL_DESC", "X", ""),
        ("GEOL_FORM", "X", ""),
    ],
    [
        ["BH1", 0.00, 2.50, "Brown sandy CLAY with gravel", "Fill"],
        ["BH1", 2.50, 10.00, "Soft grey silty CLAY", "Alluvium"],
        ["BH2", 0.00, 8.50, "Soft grey silty CLAY", "Alluvium"],
        ["BH3", 0.00, 6.00, "Medium dense brown SAND", "Terrace"],
    ],
    us=["GEOL_TOP", "GEOL_BASE"],
)

SAMP = group(
    "SAMP",
    [
        ("LOCA_ID", "ID", ""),
        ("SAMP_TOP", "2DP", "m"),
        ("SAMP_REF", "X", ""),
        ("SAMP_TYPE", "PA", ""),
        ("SAMP_ID", "ID", ""),
        ("SAMP_BASE", "2DP", "m"),
        ("SAMP_BAR", "1DP", "bar"),
    ],
    [
        ["BH1", 1.50, "1", "U", "BH1-U1", 1.95, 1.0],
        ["BH1", 3.00, "2", "D", "BH1-D2", 3.45, None],
        ["BH2", 2.00, "1", "D", "BH2-D1", 2.45, None],
        ["BH2", 4.50, "2", "U", "BH2-U2", 4.95, 1.0],
        ["BH3", 1.00, "1", "B", "BH3-B1", 1.50, None],
    ],
    us=["SAMP_TOP", "SAMP_BASE"],
)

ISPT = group(
    "ISPT",
    [
        ("LOCA_ID", "ID", ""),
        ("ISPT_TOP", "2DP", "m"),
        ("ISPT_NPEN", "0DP", "mm"),
        ("ISPT_NVAL", "0DP", ""),
        ("ISPT_REP", "X", ""),
        ("ISPT_CAS", "2DP", "m"),
        ("ISPT_WAT", "XN", "m"),
        ("ISPT_ERAT", "0DP", "%"),
        ("ISPT_N60", "0DP", ""),
    ],
    [
        ["BH1", 3.00, 450, 12, "N=12", 2.50, "2.10", 80, 16],
        ["BH1", 6.00, 300, 50, "25/75 50/75", 5.50, "2.10", 80, None],
        ["BH2", 2.00, 450, 8, "N=8", 1.50, None, 80, 11],
        ["BH2", 5.00, 450, 30, "N=30", 4.50, "1.80", 80, 40],
        ["BH3", 1.50, 450, 4, "N=4", None, "Dry", None, None],
    ],
    us=["ISPT_TOP", "ISPT_NPEN", "ISPT_CAS", "ISPT_WAT"],
)

SPECIMEN = [
    ("LOCA_ID", "ID", ""),
    ("SAMP_TOP", "2DP", "m"),
    ("SAMP_REF", "X", ""),
    ("SAMP_TYPE", "PA", ""),
    ("SAMP_ID", "ID", ""),
    ("SPEC_REF", "X", ""),
    ("SPEC_DPTH", "2DP", "m"),
]
SPECIMEN_US = ["SAMP_TOP", "SPEC_DPTH"]
BH1_U1 = ["BH1", 1.50, "1", "U", "BH1-U1", "1", 1.60]
BH2_D1 = ["BH2", 2.00, "1", "D", "BH2-D1", "1", 2.00]
BH2_U2 = ["BH2", 4.50, "2", "U", "BH2-U2", "1", 4.60]
BH3_B1 = ["BH3", 1.00, "1", "B", "BH3-B1", "1", 1.00]

LLPL = group(
    "LLPL",
    [
        *SPECIMEN,
        ("LLPL_LL", "0DP", "%"),
        ("LLPL_PL", "XN", "%"),
        ("LLPL_PI", "0DP", ""),
    ],
    [[*BH1_U1, 48, "22", 26], [*BH2_D1, 31, "NP", None], [*BH2_U2, 55, "25", 30]],
    us=SPECIMEN_US,
)

LNMC = group(
    "LNMC",
    [*SPECIMEN, ("LNMC_MC", "X", "%"), ("LNMC_TEMP", "0DP", "DegC")],
    [[*BH1_U1, "32", 105], [*BH2_U2, "41", 105], [*BH3_B1, "12", 105]],
    us=SPECIMEN_US,
)

GRAG = group(
    "GRAG",
    [
        *SPECIMEN,
        ("GRAG_GRAV", "1DP", "%"),
        ("GRAG_SAND", "1DP", "%"),
        ("GRAG_FINE", "1DP", "%"),
        ("GRAG_PDEN", "XN", "Mg/m3"),
        ("GRAG_SUFF", "YN", ""),
    ],
    [[*BH3_B1, 12.0, 80.5, 7.5, "#2.65", "Y"], [*BH2_D1, 0.0, 35.0, 65.0, "2.70", "N"]],
    us=[*SPECIMEN_US, "GRAG_PDEN"],
)

GRAT = group(
    "GRAT",
    [*SPECIMEN, ("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "0DP", "%")],
    [
        [*BH3_B1, 20.0, 100],
        [*BH3_B1, 2.00, 88],
        [*BH3_B1, 0.425, 40],
        [*BH3_B1, 0.0630, 8],
    ],
    us=[*SPECIMEN_US, "GRAT_SIZE"],
)

PTST = group(
    "PTST",
    [
        *SPECIMEN,
        ("PTST_TESN", "X", ""),
        ("PTST_DIAM", "2DP", "mm"),
        ("PTST_BDEN", "2DP", "Mg/m3"),
        ("PTST_K", "1SCI", "m/s"),
        ("PTST_TSTR", "0DP", "kPa"),
    ],
    [
        [*BH1_U1, "1", 100.00, 1.85, 2.3e-9, 75],
        [*BH2_U2, "1", 100.00, 1.78, 5.0e-10, 100],
    ],
    us=[*SPECIMEN_US, "PTST_DIAM", "PTST_BDEN", "PTST_K", "PTST_TSTR"],
)

CPTP = group(
    "CPTP",
    [("LOCA_ID", "ID", ""), ("CPTP_DPTH", "2DP", "m"), ("CPTP_SUW1", "1DP", "kN/m3")],
    [["BH3", 1.00, 18.5], ["BH3", 2.00, 19.2]],
    us=["CPTP_DPTH", "CPTP_SUW1"],
)

FGHG_KEY = [
    ("LOCA_ID", "ID", ""),
    ("FGHG_TOP", "2DP", "m"),
    ("FGHG_BASE", "2DP", "m"),
    ("FGHG_TESN", "X", ""),
]
FGHG = group(
    "FGHG",
    [
        *FGHG_KEY,
        ("FGHG_TYPE", "X", ""),
        ("FGHG_IPRM", "1SCI", "m/s"),
        ("FGHG_ILUG", "XN", ""),
    ],
    [["BH3", 3.00, 4.00, "1", "Falling head", 4.2e-6, "<1"]],
    us=["FGHG_TOP", "FGHG_BASE", "FGHG_IPRM"],
)

FGHS = group(
    "FGHS",
    [
        *FGHG_KEY,
        ("FGHS_STG", "0DP", ""),
        ("FGHS_STTM", "DT", "yyyy-mm-ddThh:mm:ss"),
        ("FGHS_HEAD", "2DP", "m"),
        ("FGHS_FLOW", "1DP", "l/s"),
        ("FGHS_IPRM", "1SCI", "m/s"),
        ("FGHS_ILUG", "XN", ""),
    ],
    [
        ["BH3", 3.00, 4.00, "1", 1, "2026-09-03T10:15:00", 2.50, 0.2, 4.0e-6, "<1"],
        ["BH3", 3.00, 4.00, "1", 2, "2026-09-03T11:00:00", 5.00, 0.5, 4.4e-6, ">100"],
    ],
    us=["FGHG_TOP", "FGHG_BASE", "FGHS_HEAD", "FGHS_IPRM"],
)

XPPT = group(
    "XPPT",
    [("LOCA_ID", "ID", ""), ("XPPT_DPTH", "2DP", "m"), ("XPPT_RES", "0DP", "kPa")],
    [["BH1", 1.20, 145], ["BH2", 1.00, 70]],
    us=["XPPT_DPTH", "XPPT_RES"],
)
# Headings whose US unit isn't the default for their SI unit.
US_OVERRIDE = {"XPPT_RES": TSF}

# The 4.0.4 file: IPRG/IPRT in place of FGHG/FGHS (no mapping, ingest.md §6),
# RUCS with a heading 4.2 removed (RUCS_E), and the old unit spellings.
IPRG_KEY = [
    ("LOCA_ID", "ID", ""),
    ("IPRG_TOP", "2DP", "m"),
    ("IPRG_TESN", "X", ""),
    ("IPRG_BASE", "2DP", "m"),
    ("IPRG_STG", "0DP", ""),
]
IPRG = group(
    "IPRG",
    [
        *IPRG_KEY,
        ("IPRG_TYPE", "X", ""),
        ("IPRG_IPRM", "1SCI", "m/s"),
        ("IPRG_HEAD", "2DP", "m"),
    ],
    [
        ["BH3", 3.00, "1", 4.00, 1, "Falling head", 4.0e-6, 2.50],
        ["BH3", 3.00, "1", 4.00, 2, "Falling head", 4.4e-6, 5.00],
    ],
)
IPRT = group(
    "IPRT",
    [*IPRG_KEY, ("IPRT_TIME", "T", "hh:mm:ss"), ("IPRT_DPTH", "2DP", "m")],
    [
        ["BH3", 3.00, "1", 4.00, 1, "00:00:00", 0.50],
        ["BH3", 3.00, "1", 4.00, 1, "00:05:00", 0.85],
        ["BH3", 3.00, "1", 4.00, 1, "01:20:00", 1.40],
    ],
)
RUCS = group(
    "RUCS",
    [
        *SPECIMEN,
        ("RUCS_DURN", "T", "mm:ss"),
        ("RUCS_UCS", "3SF", "MPa"),
        ("RUCS_E", "3SF", "GPa"),
    ],
    [[*BH1_U1, "05:30", 1.20, 0.250]],
)


def without(g, *names):
    """The same group without the headings ``names``."""
    keep = [i for i, (h, _, _) in enumerate(g["headings"]) if h not in names]
    return {
        **g,
        "headings": [g["headings"][i] for i in keep],
        "rows": [[row[i] for i in keep] for row in g["rows"]],
    }


def old_spellings(g):
    """The same group with the 4.0.x unit spellings (degC, Bar)."""
    old = {"DegC": "degC", "bar": "Bar"}
    headings = [(h, t, old.get(u, u)) for h, t, u in g["headings"]]
    return {**g, "headings": headings}


# --- Writing --------------------------------------------------------------------


def text(value, ags_type):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if ags_type.endswith("DP"):
        return f"{value:.{int(ags_type[:-2])}f}"
    if ags_type.endswith("SCI"):
        return f"{value:.{int(ags_type[:-3])}E}"
    if ags_type.endswith("SF"):
        return _format_SF(value, ags_type)
    return str(value)


def to_us(g):
    """The group in US units: converted headings get the US unit and TYPE 10SF."""
    headings, convert = [], []
    for h, t, u in g["headings"]:
        if h in g["us"]:
            unit, factor = US_OVERRIDE.get(h) or US[u]
            us_type = "XN" if t == "XN" else "9SCI" if t.endswith("SCI") else "10SF"
            headings.append((h, us_type, unit))
            convert.append(factor)
        else:
            headings.append((h, t, u))
            convert.append(None)
    rows = []
    for row in g["rows"]:
        new = []
        for value, factor in zip(row, convert, strict=True):
            if factor is None or value is None:
                new.append(value)
            elif isinstance(value, str):  # XN: keep a leading flag character
                prefix = value[0] if value[0] in "<>#" else ""
                if not value[len(prefix) :].replace(".", "").isdigit():
                    new.append(value)  # a flag such as "Dry" has no number
                    continue
                number = float(value[len(prefix) :]) / factor
                new.append(prefix + _format_SF(number, "10SF"))
            else:
                new.append(value / factor)
        rows.append(new)
    return {**g, "headings": headings, "rows": rows}


def write_group(lines, g):
    names = [h for h, _, _ in g["headings"]]
    lines.append(["GROUP", g["name"]])
    lines.append(["HEADING", *names])
    lines.append(["UNIT", *(u for _, _, u in g["headings"])])
    lines.append(["TYPE", *(t for _, t, _ in g["headings"])])
    for row in g["rows"]:
        values = [text(v, t) for v, (_, t, _) in zip(row, g["headings"], strict=True)]
        lines.append(["DATA", *values])
    lines.append(None)


def write_file(path, version, groups):
    """Write PROJ, TRAN, UNIT, TYPE and ABBR, then ``groups``, as an AGS4 file."""
    used_units = {u for g in groups for _, _, u in g["headings"] if u} | {"yyyy-mm-dd"}
    used_types = {t for g in groups for _, t, _ in g["headings"]} | {
        "ID",
        "X",
        "DT",
        "PA",
    }
    unit = group(
        "UNIT",
        [("UNIT_UNIT", "X", ""), ("UNIT_DESC", "X", "")],
        [[u, UNIT_DESCRIPTIONS[u]] for u in sorted(used_units)],
    )
    types = group(
        "TYPE",
        [("TYPE_TYPE", "X", ""), ("TYPE_DESC", "X", "")],
        [[t, TYPE_DESCRIPTIONS[t]] for t in sorted(used_types)],
    )
    abbr = group(
        "ABBR",
        [("ABBR_HDNG", "X", ""), ("ABBR_CODE", "X", ""), ("ABBR_DESC", "X", "")],
        [list(a) for a in ABBR],
    )
    lines = []
    for g in [PROJ, tran(version), unit, types, abbr, *groups]:
        write_group(lines, g)
    out = "".join(
        "\r\n" if line is None else ",".join(f'"{v}"' for v in line) + "\r\n"
        for line in lines
    )
    path.write_text(out, encoding="utf-8", newline="")


def site_groups(us=False):
    return [
        dict_group(us),
        LOCA,
        GEOL,
        SAMP,
        ISPT,
        LLPL,
        LNMC,
        GRAG,
        GRAT,
        PTST,
        CPTP,
        FGHG,
        FGHS,
        XPPT,
    ]


def defects_groups():
    """One case per ingest finding (ingest.md §9), plus an orphan sample."""
    loca = {
        **LOCA,
        "headings": [
            ("LOCA_ID", "ID", ""),
            ("LOCA_TYPE", "PA", ""),
            ("LOCA_NATE", "2DP", "kPa"),  # U004: a stress unit in a length heading
            ("LOCA_NATN", "2DP", "m"),
            ("LOCA_GL", "2DP", "m"),
            ("LOCA_FDEP", "2DP", "Ft"),  # U001: unknown (case-sensitive) unit
            ("LOCA_STAR", "DT", "yyyy-mm-dd"),
            ("LOCA_LAT", "DMS", ""),
        ],
    }
    samp = {
        **SAMP,
        "headings": [
            *SAMP["headings"][:5],
            ("SAMP_BASE", "2DP", "feet"),  # U002: pint reads it, no alias
            SAMP["headings"][6],
        ],
    }
    ispt = {
        **ISPT,
        "headings": [
            *ISPT["headings"][:5],
            ("ISPT_CAS", "2DP", ""),  # U003: no unit where the dictionary has one
            *ISPT["headings"][6:],
        ],
    }
    lnmc = {**LNMC, "rows": [*LNMC["rows"], [*BH2_D1, "wet", 105]]}  # T001
    orphan = ["BH2", 7.00, "9", "D", "BH2-D9", "1", 7.00]  # no such SAMP row (V10)
    llpl = {**LLPL, "rows": [*LLPL["rows"], [*orphan, 40, "20", 20]]}
    # A user-defined group with no DICT entry (python-ags4 Rule 9).
    xund = group(
        "XUND", [("LOCA_ID", "ID", ""), ("XUND_VAL", "2DP", "m")], [["BH1", 1.00]]
    )
    return [loca, GEOL, samp, ispt, llpl, lnmc, xund]


def main(out=HERE):
    out = Path(out)
    write_file(out / "site_si.ags", "4.2", site_groups())
    write_file(out / "site_us.ags", "4.2", [to_us(g) for g in site_groups(us=True)])
    # Headings added in 4.1 aren't in the 4.0.4 file.
    v404 = [
        dict_group(),
        LOCA,
        GEOL,
        old_spellings(SAMP),
        without(ISPT, "ISPT_N60"),
        LLPL,
        old_spellings(LNMC),
        without(GRAG, "GRAG_PDEN", "GRAG_SUFF"),
        GRAT,
        PTST,
        RUCS,
        IPRG,
        IPRT,
        XPPT,
    ]
    write_file(out / "site_v404.ags", "4.0.4", v404)
    write_file(out / "defects.ags", "4.9", defects_groups())  # V000: unknown version


if __name__ == "__main__":
    main()
