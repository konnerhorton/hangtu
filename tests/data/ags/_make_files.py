"""Write the synthetic AGS4 test files in this folder (ingest.md §11, qc.md §8).

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
    "%/log cycle": "percent strain per log cycle of stress",
    "kN/mm": "kilonewtons per millimetre",
    "um": "micrometre",
    "mm:ss": "minutes seconds",
    "MPa": "megapascal",
    "deg": "degree",
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
    "2SF": "Value with 2 significant figures",
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
    ("LDEN_TYPE", "LINEAR", "Linear measurement"),
    ("LDEN_TYPE", "IMMERSION", "Immersion/displacement measurement"),
    ("LDEN_COND", "UNDISTURBED", "Undisturbed"),
    ("LDEN_COND", "RECOMPACTED", "Recompacted"),
    ("LPDN_TYPE", "SMALL PYK", "Small pyknometer"),
    ("IDEN_TYPE", "SAND", "Sand Replacement/Cone"),
    ("IDEN_TYPE", "NUCLEAR", "Nuclear"),
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
        ("LOCA_DATM", "X", ""),  # LOCA_GL's datum: no LOCA_LOCZ (ingest.md §7)
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
            "NAVD88",
            "37:47:36.100",
        ],
        [
            "BH2",
            "CP",
            523150.75,
            4182290.00,
            11.85,
            8.50,
            "2026-09-02",
            "NAVD88",
            "37:47:37.700",
        ],
        ["BH3", "CP", 523210.00, 4182330.25, 13.10, 6.00, "2026-09-03", "NAVD88", None],
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
        ("GEOL_GEOL", "X", ""),
        ("GEOL_FORM", "X", ""),
    ],
    [
        ["BH1", 0.00, 2.50, "Brown sandy CLAY with gravel", "FILL", "Fill"],
        ["BH1", 2.50, 10.00, "Soft grey silty CLAY", "ALV", "Alluvium"],
        ["BH2", 0.00, 8.50, "Soft grey silty CLAY", "ALV", "Alluvium"],
        ["BH3", 0.00, 6.00, "Medium dense brown SAND", "TRC", "Terrace"],
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

# Blows and penetrations (mm) of increments 1 to 6 for a refusal 125 mm into
# the test drive: 25 seating blows, then 50 test blows.
REFUSAL = [10, 15, 25, 25, None, None, 75, 75, 75, 50, None, None]

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
        *((f"ISPT_INC{i}", "0DP", "") for i in range(1, 7)),
        *((f"ISPT_PEN{i}", "0DP", "mm") for i in range(1, 7)),
        ("ISPT_N60", "0DP", ""),
    ],
    # BH1 has increments (mid_drive, datasets.md §6.1): a complete drive, and a
    # refusal 125 mm into the test drive. BH2 and BH3 have none (nominal).
    [
        ["BH1", 3.00, 450, 12, "N=12", 2.50, "2.10", 80, 1, 2, 3, 3, 3, 3]
        + [75] * 6
        + [16],
        ["BH1", 6.00, 275, 50, "25/150 50/125", 5.50, "2.10", 80, *REFUSAL, None],
        ["BH2", 2.00, 450, 8, "N=8", 1.50, None, 80] + [None] * 12 + [11],
        ["BH2", 5.00, 450, 30, "N=30", 4.50, "1.80", 80] + [None] * 12 + [40],
        ["BH3", 1.50, 450, 4, "N=4", None, "Dry", None] + [None] * 13,
    ],
    us=["ISPT_TOP", "ISPT_NPEN", "ISPT_CAS", "ISPT_WAT"]
    + [f"ISPT_PEN{i}" for i in range(1, 7)],
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
    # BH3-B1 is NP, so its sand, with about 9 % fines, can be classified
    # (datasets.md §13 #14: no warning on the good files).
    [
        [*BH1_U1, 48, "22", 26],
        [*BH2_D1, 31, "NP", None],
        [*BH2_U2, 55, "25", 30],
        [*BH3_B1, 21, "NP", None],
    ],
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

# Density (M14, docs/work/m14a-density-data.md). BH1-U1's values are AC 1's
# golden values (1.95 / 1.25 = 1.56); BH2-U2 is recompacted (2.02 / 1.18 =
# 1.71). Each sample has one particle density specimen, so p.density() picks
# none; BH2-U2's is assumed (#). BH2's field test has a stabilizer.
LDEN_HEADINGS = [
    *SPECIMEN,
    ("LDEN_TYPE", "PA", ""),
    ("LDEN_COND", "PA", ""),
    ("LDEN_MC", "X", "%"),
    ("LDEN_BDEN", "2DP", "Mg/m3"),
    ("LDEN_DDEN", "2DP", "Mg/m3"),
]
LDEN = group(
    "LDEN",
    LDEN_HEADINGS,
    [
        [*BH1_U1, "LINEAR", "UNDISTURBED", "25", 1.95, 1.56],
        [*BH2_U2, "IMMERSION", "RECOMPACTED", "18", 2.02, 1.71],
    ],
    us=[*SPECIMEN_US, "LDEN_BDEN", "LDEN_DDEN"],
)

LPDN_HEADINGS = [*SPECIMEN, ("LPDN_PDEN", "XN", "Mg/m3"), ("LPDN_TYPE", "PA", "")]
LPDN = group(
    "LPDN",
    LPDN_HEADINGS,
    [
        ["BH1", 1.50, "1", "U", "BH1-U1", "2", 1.65, "2.68", "SMALL PYK"],
        ["BH2", 4.50, "2", "U", "BH2-U2", "2", 4.65, "#2.65", "SMALL PYK"],
    ],
    us=[*SPECIMEN_US, "LPDN_PDEN"],
)

IDEN = group(
    "IDEN",
    [
        ("LOCA_ID", "ID", ""),
        ("IDEN_DPTH", "2DP", "m"),
        ("IDEN_TESN", "X", ""),
        ("IDEN_TYPE", "PA", ""),
        ("IDEN_IDEN", "2DP", "Mg/m3"),
        ("IDEN_MC", "X", "%"),
        ("IDEN_STAB", "2SF", "%"),
    ],
    [
        ["BH1", 0.50, "1", "SAND", 1.85, "15", None],
        ["BH2", 0.40, "1", "NUCLEAR", 1.92, "12", 3.0],
    ],
    us=["IDEN_DPTH", "IDEN_IDEN"],
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


def write_file(path, version, groups, undefined_units=()):
    """Write PROJ, TRAN, then ``groups``, then UNIT, TYPE and ABBR, as an AGS4 file.

    UNIT, TYPE and ABBR come last, so a group, unit or code added to a file
    doesn't move the lines of the data before it, which the tests name. Units
    in ``undefined_units`` are left out of the UNIT group (AGS Rule 15).
    """
    used_units = {u for g in groups for _, _, u in g["headings"] if u} | {"yyyy-mm-dd"}
    used_units -= set(undefined_units)
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
    for g in [PROJ, tran(version), *groups, unit, types, abbr]:
        write_group(lines, g)
    out = "".join(
        "\r\n" if line is None else ",".join(_quoted(v) for v in line) + "\r\n"
        for line in lines
    )
    path.write_text(out, encoding="utf-8", newline="")


def _quoted(value):
    """Quote a value, doubling any quote inside it (AGS Rule 5)."""
    return '"' + str(value).replace('"', '""') + '"'


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
        LDEN,
        LPDN,
        IDEN,
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
            ("LOCA_DATM", "X", ""),
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
    # A user-defined group with no DICT entry (python-ags4 Rule 9), with the
    # units hangtu doesn't convert (ingest.md §7, step 5).
    xund = group(
        "XUND",
        [
            ("LOCA_ID", "ID", ""),
            ("XUND_VAL", "2DP", "m"),
            ("XUND_SWEL", "2DP", "%/log cycle"),  # U005: defined in the UNIT group
            ("XUND_BLOW", "0DP", "blows/ft"),  # U001: not in the UNIT group
            ("XUND_STIF", "1DP", "kN/mm"),  # no quantity kind: kept as kN/mm
            ("XUND_SIZE", "0DP", "um"),  # converted to m
        ],
        [["BH1", 1.00, 1.25, 12, 35.5, 75]],
    )
    return [loca, GEOL, samp, ispt, llpl, lnmc, xund]


def qc_defects_groups():
    """One case per computed QC rule (qc.md §8), on five holes.

    BH1 to BH4 sit on a 50 m grid; BH4's ground level is 8 m above the median of
    the other three (L005). BH5 has no coordinates, ground level, final depth or
    geology (L001, L002, L003, G001). Some cases necessarily raise a second
    rule; tests/qc/test_qc_acceptance.py lists them.
    """
    loca = group(
        "LOCA",
        [
            ("LOCA_ID", "ID", ""),
            ("LOCA_NATE", "2DP", "m"),
            ("LOCA_NATN", "2DP", "m"),
            ("LOCA_GL", "2DP", "m"),
            ("LOCA_FDEP", "2DP", "m"),
            ("LOCA_DATM", "X", ""),
        ],  # no LOCA_TYPE (C002)
        [
            ["BH1", 1000.00, 1000.00, 10.00, 10.00, "NAVD88"],
            ["BH2", 1050.00, 1000.00, 10.50, 8.00, "NAVD88"],
            ["BH3", 1000.00, 1050.00, 9.50, 6.00, "NAVD88"],
            ["BH4", 1050.00, 1050.00, 18.00, 6.00, "NGVD29"],  # L005; L007
            ["BH5", None, None, None, None, None],  # L001, L002, L003
        ],
    )
    horn = group(
        "HORN",
        [
            ("LOCA_ID", "ID", ""),
            ("HORN_TOP", "2DP", "m"),
            ("HORN_BASE", "2DP", "m"),
            ("HORN_ORNT", "0DP", "deg"),
            ("HORN_INCL", "0DP", "deg"),
        ],
        [["BH2", 0.00, 3.00, 0, 80]],  # L004
    )
    geol = group(
        "GEOL",
        [
            ("LOCA_ID", "ID", ""),
            ("GEOL_TOP", "2DP", "m"),
            ("GEOL_BASE", "2DP", "m"),
            ("GEOL_DESC", "X", ""),
        ],
        [
            ["BH1", 0.00, 2.50, "Brown sandy CLAY (fill)"],
            ["BH1", 3.00, 10.00, "Soft gray silty CLAY"],  # G002: 2.50 to 3.00 missing
            ["BH2", 0.00, 3.00, "Brown sandy CLAY (fill)"],
            ["BH2", 3.00, 7.50, "Soft gray silty CLAY"],  # G002: stops 0.50 m short
            ["BH3", 0.00, 2.00, "Brown sandy CLAY (fill)"],
            ["BH3", 2.00, 4.00, "Medium dense SAND"],
            ["BH3", 3.50, 6.00, "Dense GRAVEL"],  # G003: overlaps 3.50 to 4.00
            ["BH4", 0.00, 2.50, None],  # C001: GEOL_DESC blank
            ["BH4", 2.50, 6.00, "Stiff brown CLAY"],
        ],
    )
    samp = group(
        "SAMP",
        [
            ("LOCA_ID", "ID", ""),
            ("SAMP_TOP", "2DP", "m"),
            ("SAMP_REF", "X", ""),
            ("SAMP_TYPE", "PA", ""),
            ("SAMP_ID", "ID", ""),
            ("SAMP_BASE", "2DP", "m"),
        ],
        [
            ["BH1", 1.00, "1", "U", "BH1-U1", 1.45],
            ["BH1", 5.00, "2", "D", "BH1-D2", 4.50],  # D001
            ["BH2", 1.00, "1", "U", "BH2-U1", 1.45],
            ["BH2", 4.00, "2", "D", "BH2-D2", 4.45],
            ["BH3", 1.00, "1", "B", "BH3-B1", 1.50],
            ["BH4", 2.30, "1", "U", "BH4-U1", 2.80],  # D005: across 2.50
            ["BH4", 4.00, "2", "U", "BH4-U2", 4.45],
        ],
    )
    ispt = group(
        "ISPT",
        [
            ("LOCA_ID", "ID", ""),
            ("ISPT_TOP", "2DP", "m"),
            ("ISPT_NVAL", "0DP", ""),
            ("ISPT_REP", "X", ""),
            ("ISPT_ERAT", "0DP", "%"),
            ("ISPT_INC3", "0DP", ""),
            ("ISPT_INC4", "0DP", ""),
            ("ISPT_INC5", "0DP", ""),
            ("ISPT_INC6", "0DP", ""),
            ("ISPT_N60", "0DP", ""),
        ],
        [
            ["BH1", -0.50, 10, "N=10", 60, None, None, None, None, None],  # D002
            ["BH1", 1.50, 15, "hard", 60, None, None, None, None, None],  # S001
            ["BH1", 2.75, 12, "N=12", 60, None, None, None, None, None],  # D004
            ["BH1", 6.00, 150, "N=150", 60, None, None, None, None, None],  # S002
            ["BH2", 2.00, 20, "N=20", 60, 4, 5, 5, 5, None],  # S004
            ["BH2", 5.00, 20, "N=20", 75, None, None, None, None, 30],  # S005
            ["BH3", 1.50, 8, "N=8", 60, None, None, None, None, None],
            ["BH3", 7.00, 30, "N=30", 60, None, None, None, None, None],  # D003
            ["BH4", 1.50, 10, "N=10", None, None, None, None, None, None],  # S003
            ["BH4", 4.50, 14, "N=14", None, None, None, None, None, None],  # S003
            ["BH5", 1.00, 6, "N=6", 60, None, None, None, None, None],  # G001
            ["BH2", 3.50, 50, "50/76 ft", 60, None, None, None, None, None],  # S001
            # A complete test, not a refusal, so S002 checks it.
            ["BH2", 6.00, 126, "41,81,57,75/113 N=126", 60, *[None] * 5],  # S002
            # Accepted reports, raising nothing; the refusals have N blank (no C001).
            ["BH3", 0.50, 12, "5,6,6 N=12", 60, None, None, None, None, None],
            ["BH3", 5.00, 35, "6,8/8,9,9,9 N=35", 60, None, None, None, None, None],
            ["BH1", 4.00, None, '50/3"', 60, None, None, None, None, None],
            ["BH1", 8.00, None, "22-30-50/3in", 60, None, None, None, None, None],
        ],
    )
    bh1_u1 = ["BH1", 1.00, "1", "U", "BH1-U1", "1", 1.10]
    bh2_u1 = ["BH2", 1.00, "1", "U", "BH2-U1", "1", 1.10]
    bh2_d2 = ["BH2", 4.00, "2", "D", "BH2-D2", "1", 4.10]
    bh3_b1 = ["BH3", 1.00, "1", "B", "BH3-B1", "1", 1.55]  # D008: 0.05 below base
    bh4_u1 = ["BH4", 2.30, "1", "U", "BH4-U1", "1", 2.40]
    bh4_u2 = ["BH4", 4.00, "2", "U", "BH4-U2", "1", 4.75]  # D007: 0.30 below base
    llpl = group(
        "LLPL",
        [
            *SPECIMEN,
            ("LLPL_LL", "0DP", "%"),
            ("LLPL_PL", "XN", "%"),
            ("LLPL_PI", "0DP", ""),
        ],
        [
            [*bh1_u1, 30, "35", None],  # A001
            [*bh2_u1, 50, "20", 25],  # A002: 50 - 20 = 30, not 25
            [*bh2_d2, 8, "5", 3],  # A003
            [*bh3_b1, 25, "NP", None],  # A004
            [*bh4_u2, 40, "20", 20],
        ],
    )
    grag = group(
        "GRAG",
        [
            *SPECIMEN,
            ("GRAG_GRAV", "1DP", "%"),
            ("GRAG_SAND", "1DP", "%"),
            ("GRAG_FINE", "1DP", "%"),
        ],
        [
            [*bh1_u1, 0.0, 30.0, 70.0],
            [*bh2_d2, 5.0, 40.0, 55.0],
            [*bh3_b1, 10.0, 60.0, 24.0],  # P003: sums to 94
            [*bh4_u1, 0.0, 45.0, 55.0],
        ],
    )
    grat = group(
        "GRAT",
        [*SPECIMEN, ("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "0DP", "%")],
        [
            [*bh1_u1, 20.0, 104],  # P002
            [*bh1_u1, 2.00, 90],
            [*bh1_u1, 0.425, 75],
            [*bh1_u1, 0.0630, 70],
            [*bh2_d2, 20.0, 100],
            [*bh2_d2, 2.00, 80],
            [*bh2_d2, 0.425, 85],  # P001: rises
            [*bh2_d2, 0.0630, 55],
            [*bh4_u1, 2.00, 100],  # P004: three points
            [*bh4_u1, 0.425, 80],
            [*bh4_u1, 0.0630, 55],
        ],
    )
    ptst = group(
        "PTST",
        [*SPECIMEN, ("PTST_TESN", "X", ""), ("PTST_K", "1SCI", "m/s")],
        [[*bh2_u1, "1", 0.0]],  # K001: zero
    )
    fghg = group(
        "FGHG",
        [*FGHG_KEY, ("FGHG_IPRM", "1SCI", "m/s")],
        [["BH4", 3.00, 4.00, "1", 5.0]],  # K001: above 1 m/s
    )
    # Density rules (qc.md §4.11). BH4-U1 is the AGS dictionary's own example,
    # 1.66 / 1.57 = 1.057 against 1.06: no B001.
    lden = group(
        "LDEN",
        LDEN_HEADINGS,
        [
            [*bh1_u1, "LINEAR", "UNDISTURBED", "20", 2.00, 1.80],  # B001: 1.667
            [*bh2_u1, "LINEAR", "UNDISTURBED", None, 1.80, 1.90],  # B002
            [*bh2_d2, "LINEAR", "UNDISTURBED", "15", 19.5, 16.96],  # B003: kN/m3
            [*bh4_u1, "LINEAR", "UNDISTURBED", "57", 1.66, 1.06],
        ],
    )
    lpdn = group(
        "LPDN",
        LPDN_HEADINGS,
        [
            ["BH1", 1.00, "1", "U", "BH1-U1", "2", 1.20, "26.5", "SMALL PYK"],  # B003
            ["BH2", 1.00, "1", "U", "BH2-U1", "2", 1.20, "#2.65", "SMALL PYK"],  # B004
        ],
    )
    return [loca, horn, geol, samp, ispt, llpl, grag, grat, ptst, fghg, lden, lpdn]


def joins_groups():
    """Edge cases for the depth and geology joins (datasets.md §12), in SI.

    J1's log has an overlap (TRC from 4.50 overlaps ALV to 5.00), a gap (8.00 to
    9.00) and a code missing from strata.csv (BED). J2 has no ground level, J3
    no geology. Expected depths are hand-calculated in tests/datasets.
    """
    loca = group(
        "LOCA",
        [
            ("LOCA_ID", "ID", ""),
            ("LOCA_TYPE", "PA", ""),
            ("LOCA_GL", "2DP", "m"),
            ("LOCA_FDEP", "2DP", "m"),
        ],
        [
            ["J1", "CP", 10.00, 10.00],
            ["J2", "CP", None, 5.00],  # no ground level: blank elevation
            ["J3", "CP", 12.00, 4.00],  # no geology
        ],
    )
    geol = group(
        "GEOL",
        [
            ("LOCA_ID", "ID", ""),
            ("GEOL_TOP", "2DP", "m"),
            ("GEOL_BASE", "2DP", "m"),
            ("GEOL_DESC", "X", ""),
            ("GEOL_GEOL", "X", ""),
        ],
        [
            ["J1", 0.00, 2.00, "Brown sandy CLAY with gravel", "FILL"],
            ["J1", 2.00, 5.00, "Soft grey silty CLAY", "ALV"],
            ["J1", 4.50, 8.00, "Medium dense brown SAND", "TRC"],  # overlap
            ["J1", 9.00, 10.00, "Weak grey MUDSTONE", "BED"],  # after a gap; unmapped
            ["J2", 0.00, 5.00, "Soft grey silty CLAY", "ALV"],
        ],
    )
    ispt = group(
        "ISPT",
        [
            ("LOCA_ID", "ID", ""),
            ("ISPT_TOP", "2DP", "m"),
            ("ISPT_NPEN", "0DP", "mm"),
            ("ISPT_NVAL", "0DP", ""),
            ("ISPT_REP", "X", ""),
            *((f"ISPT_INC{i}", "0DP", "") for i in range(1, 7)),
            *((f"ISPT_PEN{i}", "0DP", "mm") for i in range(1, 7)),
        ],
        [
            # Complete drive, mid-drive exactly on the 2.00 m boundary: ALV.
            ["J1", 1.70, 450, 12, "N=12", 2, 2, 3, 3, 3, 3] + [75] * 6,
            # Refusal in the seating drive: 3.00 + 0.050 = 3.05 m.
            ["J1", 3.00, 50, 25, "25/50", 25, *[None] * 5, 50, *[None] * 5],
            # No increments, NPEN 450: 4.80 m, in the overlap: TRC.
            ["J1", 4.50, 450, 18, "N=18"] + [None] * 12,
            # Incomplete (ISPT_NVAL blank, C001): left out by default.
            ["J1", 6.00, 450, None, None] + [None] * 12,
            # No increments, NPEN 100 (seating only): 8.10 + 0.100 = 8.20 m, in the gap.
            ["J1", 8.10, 100, 50, "50/100"] + [None] * 12,
            # 9.70 + 0.300 = 10.00 m, the base of the deepest layer: BED.
            ["J1", 9.70, 450, 40, "N=40"] + [None] * 12,
            # NPEN 200: 1.00 + 0.150 + 0.050 / 2 = 1.175 m; no ground level.
            ["J2", 1.00, 200, 50, "50/200"] + [None] * 12,
            # No increments and no NPEN: 1.00 + 0.300 = 1.30 m; no geology.
            ["J3", 1.00, None, 10, "N=10"] + [None] * 12,
            # Refusal with ISPT_NVAL blank (not C001): kept, at the cap. NPEN 376:
            # 7.00 + 0.150 + 0.226 / 2 = 7.263 m: TRC.
            ["J1", 7.00, 376, None, '22-30-50/3"'] + [None] * 12,
        ],
    )
    samp = group(
        "SAMP",
        [
            ("LOCA_ID", "ID", ""),
            ("SAMP_TOP", "2DP", "m"),
            ("SAMP_REF", "X", ""),
            ("SAMP_TYPE", "PA", ""),
            ("SAMP_ID", "ID", ""),
            ("SAMP_BASE", "2DP", "m"),
        ],
        [
            ["J1", 1.00, "1", "U", "J1-U1", 1.50],
            ["J1", 3.00, "2", "D", "J1-D2", None],  # no base
            ["J1", 6.00, "3", "U", "J1-U3", 6.50],
            ["J1", 7.00, "4", "B", "J1-B4", 7.50],
            ["J2", 2.00, "1", "U", "J2-U1", 2.50],
        ],
    )
    j1_u1 = ["J1", 1.00, "1", "U", "J1-U1"]
    j1_d2 = ["J1", 3.00, "2", "D", "J1-D2"]
    j1_u3 = ["J1", 6.00, "3", "U", "J1-U3"]
    j1_b4 = ["J1", 7.00, "4", "B", "J1-B4"]
    j2_u1 = ["J2", 2.00, "1", "U", "J2-U1"]
    # Combining a sample's tests (datasets.md §6.6, §13 #16):
    # - J1-U1: one water content specimen (3, at 1.15) and two Atterberg
    #   specimens, 1 at 1.10 (0.05 away) and 2 with no depth (at the sample's
    #   1.25, 0.10 away): specimen 1 is used.
    # - J1-U3: two Atterberg specimens 0.05 from the sample's 6.25, B listed
    #   first and so with the lower specimen key: A is used, by SPEC_REF.
    # - J1-B4: only a grading, with about 9 % fines and so no USCS symbol.
    # - J2-U1: specimen 2 has a water content and limits, and specimen 1 limits
    #   at the same depth: specimen 2 is used, though 1 is the lower SPEC_REF.
    llpl = group(
        "LLPL",
        [*SPECIMEN, ("LLPL_LL", "0DP", "%"), ("LLPL_PL", "XN", "%")],
        [
            [*j1_u1, "1", 1.10, 45, "20"],  # spec_depth 1.10
            [*j1_u1, "2", None, 50, "22"],  # sample_mid (1.00 + 1.50) / 2 = 1.25
            [*j1_d2, "1", None, 38, "18"],  # sample_top 3.00
            [*j1_u3, "B", 6.30, 42, "21"],
            [*j1_u3, "A", 6.20, 36, "19"],
            [*j2_u1, "1", 2.20, 33, "17"],
            [*j2_u1, "2", 2.20, 40, "20"],
        ],
    )
    lnmc = group(
        "LNMC",
        [*SPECIMEN, ("LNMC_MC", "0DP", "%")],
        [[*j1_u1, "3", 1.15, 28], [*j2_u1, "2", 2.20, 30]],
    )
    grag = group(  # GRAT's parent (AGS Rule 10c)
        "GRAG",
        [*SPECIMEN, ("GRAG_FINE", "1DP", "%")],
        [[*j1_b4, "1", 7.20, 9.0]],
    )
    grat = group(
        "GRAT",
        [*SPECIMEN, ("GRAT_SIZE", "3SF", "mm"), ("GRAT_PERP", "0DP", "%")],
        [
            [*j1_b4, "1", 7.20, 20.0, 100],
            [*j1_b4, "1", 7.20, 2.00, 90],
            [*j1_b4, "1", 7.20, 0.425, 45],
            [*j1_b4, "1", 7.20, 0.0630, 8],
        ],
    )
    # Particle density by sample (datasets.md §6.8):
    # - J1-U1: density specimen 4 at 1.20; particle density specimens 5 at 1.10
    #   (0.10 away) and 6 at 1.25 (0.05 away, assumed): 6 is used, flag kept.
    # - J1-U3: density specimen C at 6.25; E at 6.30 and D at 6.20, both 0.05
    #   away, E listed first and so with the lower specimen key: D is used.
    # - J2-U1: a density and no particle density: blank.
    # - J1-D2: no bulk density, so incomplete (C001).
    lden = group(
        "LDEN",
        LDEN_HEADINGS,
        [
            [*j1_u1, "4", 1.20, "LINEAR", "UNDISTURBED", "30", 1.90, 1.46],
            [*j1_u3, "C", 6.25, "LINEAR", "UNDISTURBED", "20", 2.00, 1.67],
            [*j2_u1, "3", 2.25, "LINEAR", "UNDISTURBED", "28", 1.88, 1.47],
            [*j1_d2, "2", 3.10, "LINEAR", "UNDISTURBED", "22", None, 1.60],
        ],
    )
    lpdn = group(
        "LPDN",
        LPDN_HEADINGS,
        [
            [*j1_u1, "5", 1.10, "2.70", "SMALL PYK"],
            [*j1_u1, "6", 1.25, "#2.65", "SMALL PYK"],
            [*j1_u3, "E", 6.30, "2.74", "SMALL PYK"],
            [*j1_u3, "D", 6.20, "2.71", "SMALL PYK"],
        ],
    )
    return [loca, geol, samp, ispt, llpl, lnmc, grag, grat, lden, lpdn]


#: Geology map for the test files (datasets.md §5.2). BED is left out on purpose.
STRATA = """code,geology_unit,soil_class,order,color
FILL,Fill,fill,1,#a0a0a0
ALV,Alluvium,fine,2,tan
TRC,Terrace,coarse,3,#d9b26f
"""


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
        LDEN,
        LPDN,
        IDEN,
    ]
    write_file(out / "site_v404.ags", "4.0.4", v404)
    # V000: unknown version
    write_file(
        out / "defects.ags", "4.9", defects_groups(), undefined_units={"blows/ft"}
    )
    write_file(out / "qc_defects.ags", "4.2", qc_defects_groups())
    write_file(out / "joins.ags", "4.2", joins_groups())
    (out / "strata.csv").write_text(STRATA, encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
