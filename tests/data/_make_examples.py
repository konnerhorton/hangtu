"""Write the example data that ships with hangtu (docs/work/m9-release.md, spec §1).

Run from the repository root after changing the data below:

    uv run python tests/data/_make_examples.py

The site is synthetic: a river valley with fill over soft alluvial clay over
terrace sand, in US units as a US consultant's file would have them. Values
come from fixed rules plus a seeded ``random.Random``, whose sequence Python
keeps the same across versions, so the files are reproduced exactly.

The fill and the upper alluvium tubes have hydrometer tests, so their
grading curves continue into the fines; the terrace sands are sieved only.

``judgments.yaml`` holds the site's unit weights and specific gravities by
geology unit and a water level for each hole, as an engineer would set them
(SPEC §4). The Gs values are the medians of the measured LPDN tests.

Two QC findings are planted, so the QC example has something to report:
- G002, a gap in the geology log of B-4 from 9.0 to 10.0 ft;
- A002, a plasticity index in B-3 that doesn't match LL - PL (an arithmetic slip).
"""

import importlib.util
import math
import random
import tempfile
from pathlib import Path

import hangtu as ht

HERE = Path(__file__).parent
OUT = HERE.parents[1] / "src" / "hangtu" / "examples" / "data"

_spec = importlib.util.spec_from_file_location(
    "_make_files", HERE / "ags" / "_make_files.py"
)
_files = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_files)
group, write_group = _files.group, _files.write_group

rng = random.Random(2026)
# Hydrometer values have their own sequence, so adding them left every other
# value in the files unchanged.
hydrometer_rng = random.Random(2027)
# So do the densities (M14).
density_rng = random.Random(2028)

ABBR = [
    ("LOCA_TYPE", "HSA", "Hollow stem auger"),
    ("LOCA_GREF", "SPCS", "NAD83 State Plane, US survey feet"),
    ("GEOL_LEG", "FILL", "Fill"),
    ("GEOL_LEG", "CL", "Lean clay"),
    ("GEOL_LEG", "SP", "Poorly graded sand"),
    ("GEOL_GEOL", "FILL", "Fill"),
    ("GEOL_GEOL", "ALV", "Alluvium"),
    ("GEOL_GEOL", "TRC", "Terrace deposits"),
    ("SAMP_TYPE", "U", "Undisturbed sample - open drive"),
    ("SAMP_TYPE", "D", "Small disturbed sample"),
    ("SAMP_TYPE", "B", "Bulk disturbed sample"),
    ("ISPT_TYPE", "S", "Split spoon"),
    ("PTST_TYPE", "FW", "Flexible wall permeameter"),
    ("PTST_COND", "UND", "Undisturbed"),
    ("FGHG_TYPE", "FH", "Falling head"),
    ("LDEN_TYPE", "LINEAR", "Linear measurement"),
    ("LDEN_COND", "UNDISTURBED", "Undisturbed"),
    ("LPDN_TYPE", "SMALL PYK", "Small pyknometer"),
]

# Hole, easting, northing (ft), ground level, final depth, fill base and
# alluvium base (ft). The terrace runs from the alluvium base to the final depth.
HOLES = [
    ("B-1", 6201250.0, 2101480.0, 36.5, 51.5, 4.5, 22.0),
    ("B-2", 6201410.0, 2101525.0, 35.8, 51.5, 6.5, 24.5),
    ("B-3", 6201580.0, 2101460.0, 34.2, 61.5, 5.0, 27.0),
    ("B-4", 6201330.0, 2101690.0, 37.1, 51.5, 5.0, 19.5),
    ("B-5", 6201520.0, 2101720.0, 35.0, 56.5, 4.5, 25.0),
    ("B-6", 6201700.0, 2101640.0, 33.6, 61.5, 5.0, 29.0),
]
GAP = ("B-4", 9.0, 10.0)  # planted G002, between two SPTs

DESCRIPTIONS = {
    "FILL": ("FILL", "Fill", "Brown sandy lean CLAY with gravel (FILL)"),
    "ALV": ("CL", "Alluvium", "Soft to medium stiff gray lean CLAY (CL)"),
    "TRC": ("SP", "Terrace", "Medium dense to very dense brown SAND with gravel (SP)"),
}
SIEVES = [75.0, 37.5, 19.0, 9.5, 4.75, 2.0, 0.85, 0.425, 0.25, 0.15, 0.075]  # mm
# Hydrometer particle sizes (mm), as a lab's readings at set times give them.
HYDROMETER = [0.046, 0.033, 0.021, 0.012, 0.0089, 0.0063, 0.0031, 0.0013]

STRATA = """\
code,geology_unit,soil_class,order,color
FILL,Fill,fill,1,#9e9e9e
ALV,Alluvium,fine,2,#5b8db8
TRC,Terrace,coarse,3,#e0b040
"""

# The site's judgments (SPEC §4), in the file's US units.
JUDGMENTS = """\
# judgments.yaml: the example site's unit weights, water levels, Gs and α (SPEC §4).
unit_weight:
  by: geology_unit
  units: {bulk_unit_weight: pcf, saturated_unit_weight: pcf}
  values:
    Fill: {bulk_unit_weight: 120, reason: "compacted sandy lean clay fill, typical"}
    Alluvium:
      bulk_unit_weight: 110
      saturated_unit_weight: 112
      reason: "soft lean clay, typical"
    Terrace:
      bulk_unit_weight: 125
      saturated_unit_weight: 130
      reason: "medium dense to very dense sand with gravel, typical"
water_level:
  units: {depth: ft}
  by_hole:
    B-1: {depth: 8.0, reason: "encountered while drilling, 2026-08-10"}
    B-2: {depth: 9.5, reason: "encountered while drilling, 2026-08-11"}
    B-3: {depth: 7.0, reason: "encountered while drilling, 2026-08-12"}
    B-4: {depth: 8.5, reason: "encountered while drilling, 2026-08-13"}
    B-5: {depth: 10.0, reason: "encountered while drilling, 2026-08-14"}
    B-6: {depth: 6.5, reason: "encountered while drilling, 2026-08-15"}
specific_gravity:
  by: geology_unit
  values:
    Alluvium: {specific_gravity: 2.70, reason: "median of 6 LPDN, measured (168.9 pcf)"}
    Terrace: {specific_gravity: 2.67, reason: "median of 6 LPDN, measured (166.4 pcf)"}
significance_level:
  project: {significance_level: 0.05, reason: "the usual convention"}
"""


def unit_at(hole, depth):
    _, _, _, _, _, fill, alluvium = hole
    return "FILL" if depth < fill else "ALV" if depth < alluvium else "TRC"


# --- Holes and geology -------------------------------------------------------------


def loca():
    rows = [
        [name, "HSA", east, north, "SPCS", gl, fdep, f"2026-08-{10 + i:02d}"]
        for i, (name, east, north, gl, fdep, _, _) in enumerate(HOLES)
    ]
    headings = [
        ("LOCA_ID", "ID", ""),
        ("LOCA_TYPE", "PA", ""),
        ("LOCA_NATE", "1DP", "ft"),
        ("LOCA_NATN", "1DP", "ft"),
        ("LOCA_GREF", "PA", ""),
        ("LOCA_GL", "1DP", "ft"),
        ("LOCA_FDEP", "1DP", "ft"),
        ("LOCA_STAR", "DT", "yyyy-mm-dd"),
    ]
    return group("LOCA", headings, rows)


def geol():
    rows = []
    for hole in HOLES:
        name, _, _, _, fdep, fill, alluvium = hole
        layers = [(0.0, fill, "FILL"), (fill, alluvium, "ALV"), (alluvium, fdep, "TRC")]
        for top, base, code in layers:
            pieces = [(top, base)]
            if name == GAP[0] and top < GAP[1] < base:
                pieces = [(top, GAP[1]), (GAP[2], base)]
            legend, _, description = DESCRIPTIONS[code]
            rows += [[name, a, b, description, legend, code] for a, b in pieces]
    headings = [
        ("LOCA_ID", "ID", ""),
        ("GEOL_TOP", "1DP", "ft"),
        ("GEOL_BASE", "1DP", "ft"),
        ("GEOL_DESC", "X", ""),
        ("GEOL_LEG", "PA", ""),
        ("GEOL_GEOL", "PA", ""),
    ]
    return group("GEOL", headings, rows)


# --- SPT ------------------------------------------------------------------------------


def spt_n(hole, top):
    """A typical N for the unit at mid-drive: 50 or more is a refusal."""
    middle = top + 1.0
    code = unit_at(hole, middle)
    if code == "FILL":
        return rng.randint(6, 14)
    if code == "ALV":
        return max(1, round(2 + middle / 10 + rng.uniform(-2, 2)))
    return round(18 + 1.3 * (middle - hole[6]) + rng.uniform(-5, 5))


def drive(n):
    """Blows and penetrations (in) of six 3 in increments, and the report.

    A complete test splits N over increments 3 to 6. A refusal stops at 50
    blows partway through the test drive, after 3 + 2 = 5 in.
    """
    seat = [max(1, round(min(n, 50) / 4 * rng.uniform(0.6, 0.9))) for _ in range(2)]
    if n < 50:
        base, extra = divmod(n, 4)
        test = [base + (i >= 4 - extra) for i in range(4)]
        return seat + test, [3] * 6, n, 18, f"N={n}"
    test = [22, 28]
    return (
        seat + test + [None] * 2,
        [3, 3, 3, 2, None, None],
        50,
        11,
        (f"{sum(seat)}/6 50/5"),
    )


def ispt():
    rows = []
    for hole in HOLES:
        name, *_, fdep, _, _ = hole
        # US practice: every 2.5 ft to 10 ft, then every 5 ft.
        for top in [2.5, 5.0, 7.5] + [10.0 + 5 * i for i in range(20)]:
            if top + 1.5 > fdep:
                break
            blows, pens, n, npen, report = drive(spt_n(hole, top))
            water = "12.0" if top >= 12.0 else "Dry"
            fields = [name, top, npen, n, report, top, water, "S", "AH-2041", 80]
            rows.append([*fields, *blows, *pens])
    headings = [
        ("LOCA_ID", "ID", ""),
        ("ISPT_TOP", "1DP", "ft"),
        ("ISPT_NPEN", "0DP", "in"),
        ("ISPT_NVAL", "0DP", ""),
        ("ISPT_REP", "X", ""),
        ("ISPT_CAS", "1DP", "ft"),
        ("ISPT_WAT", "XN", "ft"),
        ("ISPT_TYPE", "PA", ""),
        ("ISPT_HAM", "X", ""),
        ("ISPT_ERAT", "0DP", "%"),
        *((f"ISPT_INC{i}", "0DP", "") for i in range(1, 7)),
        *((f"ISPT_PEN{i}", "0DP", "in") for i in range(1, 7)),
    ]
    return group("ISPT", headings, rows)


# --- Samples and lab tests ---------------------------------------------------------

SAMPLE_HEADINGS = [
    ("LOCA_ID", "ID", ""),
    ("SAMP_TOP", "1DP", "ft"),
    ("SAMP_REF", "X", ""),
    ("SAMP_TYPE", "PA", ""),
    ("SAMP_ID", "ID", ""),
]
SPECIMEN_HEADINGS = [
    *SAMPLE_HEADINGS,
    ("SPEC_REF", "X", ""),
    ("SPEC_DPTH", "1DP", "ft"),
]


def samples():
    """(hole, top, base, type, reference): bulk fill, tubes, terrace spoons."""
    found = []
    for hole in HOLES:
        name, *_, alluvium = hole
        if name in ("B-1", "B-3"):
            found.append((name, 1.0, 2.0, "B"))
        found += [(name, 12.5, 14.5, "U"), (name, 17.5, 19.5, "U")]
        terrace = 5.0 * math.ceil(alluvium / 5.0)
        found.append((name, terrace, terrace + 1.5, "D"))
    numbered, counts = [], {}
    for name, top, base, kind in found:
        counts[name] = counts.get(name, 0) + 1
        numbered.append((name, top, base, kind, str(counts[name])))
    return numbered


def samp():
    rows = [
        [name, top, ref, kind, f"{name}-{kind}{ref}", base]
        for name, top, base, kind, ref in samples()
    ]
    return group("SAMP", [*SAMPLE_HEADINGS, ("SAMP_BASE", "1DP", "ft")], rows)


def specimen(sample):
    name, top, _, kind, ref = sample
    return [name, top, ref, kind, f"{name}-{kind}{ref}", "1", top + 0.5]


def atterberg():
    """LLPL and LNMC rows for each tube and fill bulk sample."""
    llpl, lnmc = [], []
    for sample in samples():
        name, top, _, kind, _ = sample
        if kind == "D":
            continue
        if kind == "B":
            liquid, plastic, passing = rng.randint(28, 36), rng.randint(17, 21), 78
        else:
            liquid, plastic, passing = rng.randint(35, 62), rng.randint(19, 27), 100
        index = liquid - plastic
        if (name, top) == ("B-3", 17.5):
            index -= 3  # planted A002: the PI was worked out wrong
        water = plastic + (0.6 if kind == "U" else -0.1) * index + rng.uniform(-3, 3)
        llpl.append([*specimen(sample), liquid, plastic, index, passing, "As received"])
        lnmc.append([*specimen(sample), f"{water:.0f}"])
    llpl_group = group(
        "LLPL",
        [
            *SPECIMEN_HEADINGS,
            ("LLPL_LL", "0DP", "%"),
            ("LLPL_PL", "0DP", "%"),
            ("LLPL_PI", "0DP", ""),
            ("LLPL_425", "0DP", "%"),
            ("LLPL_PREP", "X", ""),
        ],
        llpl,
    )
    lnmc_group = group("LNMC", [*SPECIMEN_HEADINGS, ("LNMC_MC", "X", "%")], lnmc)
    return llpl_group, lnmc_group


def curve(d50, slope, fines):
    """Percent passing each sieve: a smooth S-curve, never rising as size falls."""
    passing, last = [], 100
    for size in SIEVES:
        value = fines + (100 - fines) / (1 + (d50 / size) ** slope)
        last = min(last, round(value))
        passing.append(last)
    passing[0] = 100
    return passing


def fines_curve(fines, d50, slope):
    """Percent passing each hydrometer size, continuing down from the #200 sieve.

    An S-curve through the fines, scaled to meet ``fines`` at 0.075 mm and
    never rising as size falls.
    """

    def share(size):
        return 1 / (1 + (d50 / size) ** slope)

    passing, last = [], fines
    for size in HYDROMETER:
        last = min(last, round(fines * share(size) / share(0.075)))
        passing.append(last)
    return passing


def grading():
    """GRAG and GRAT rows for each terrace spoon, fill bulk and upper alluvium tube.

    The fill and alluvium have hydrometer points below the #200 sieve.
    """
    grag, grat = [], []
    for sample in samples():
        _, top, _, kind, _ = sample
        hydrometer = None
        if kind == "D":
            passing = curve(
                rng.uniform(0.5, 1.4), rng.uniform(1.6, 2.4), rng.randint(3, 9)
            )
        elif kind == "B":
            passing = curve(
                rng.uniform(1.5, 3.0), rng.uniform(0.9, 1.2), rng.randint(18, 26)
            )
            hydrometer = (
                hydrometer_rng.uniform(0.012, 0.025),
                hydrometer_rng.uniform(0.8, 1.0),
            )
        elif kind == "U" and top == 12.5:
            passing = curve(
                hydrometer_rng.uniform(0.12, 0.2),
                hydrometer_rng.uniform(1.8, 2.4),
                hydrometer_rng.randint(84, 95),
            )
            hydrometer = (
                hydrometer_rng.uniform(0.004, 0.009),
                hydrometer_rng.uniform(0.7, 0.9),
            )
        else:
            continue
        gravel = passing[SIEVES.index(4.75)]
        fines = passing[SIEVES.index(0.075)]
        grag.append([*specimen(sample), 100 - gravel, gravel - fines, fines])
        sizes = list(SIEVES)
        if hydrometer is not None:
            passing = passing + fines_curve(fines, *hydrometer)
            sizes += HYDROMETER
        grat += [
            [*specimen(sample), size, percent]
            for size, percent in zip(sizes, passing, strict=True)
        ]
    grag_group = group(
        "GRAG",
        [
            *SPECIMEN_HEADINGS,
            ("GRAG_GRAV", "0DP", "%"),
            ("GRAG_SAND", "0DP", "%"),
            ("GRAG_FINE", "0DP", "%"),
        ],
        grag,
    )
    headings = [
        *SPECIMEN_HEADINGS,
        ("GRAT_SIZE", "3SF", "mm"),
        ("GRAT_PERP", "0DP", "%"),
    ]
    return grag_group, group("GRAT", headings, grat)


def ptst():
    rows = [
        [
            *specimen(sample),
            "1",
            "UND",
            10 ** rng.uniform(-8.0, -6.3),
            round(rng.uniform(900, 2400), -1),
            "FW",
        ]
        for sample in samples()
        if sample[3] == "U" and sample[1] == 12.5
    ]
    headings = [
        *SPECIMEN_HEADINGS,
        ("PTST_TESN", "X", ""),
        ("PTST_COND", "PA", ""),
        ("PTST_K", "1SCI", "cm/s"),
        ("PTST_TSTR", "0DP", "psf"),
        ("PTST_TYPE", "PA", ""),
    ]
    return group("PTST", headings, rows)


#: Pound mass per cubic foot in Mg/m3 (exact): a lab's density in pcf.
PCF = 0.45359237 / 0.3048**3 / 1000


def particle_densities():
    """(sample, Gs) for the first tube and the terrace spoon of each hole."""
    found = []
    for sample in samples():
        _, top, _, kind, _ = sample
        if kind == "U" and top == 12.5:
            found.append((sample, round(density_rng.uniform(2.68, 2.74), 2)))
        elif kind == "D":
            found.append((sample, round(density_rng.uniform(2.64, 2.68), 2)))
    return found


def lpdn():
    rows = []
    for (name, top, _, kind, ref), gs in particle_densities():
        key = [name, top, ref, kind, f"{name}-{kind}{ref}", "2", top + 0.8]
        rows.append([*key, f"{gs:.2f}", "SMALL PYK"])
    headings = [
        *SPECIMEN_HEADINGS,
        ("LPDN_PDEN", "XN", "Mg/m3"),
        ("LPDN_TYPE", "PA", ""),
    ]
    return group("LPDN", headings, rows)


def lden(lnmc):
    """Each tube's density, on its water content specimen, in pcf.

    A nearly saturated clay: e = w Gs / S, rho_d = Gs rho_w / (1 + e) and
    rho = rho_d (1 + w), with Gs 2.70 and S 0.95 to 1.00, so the three values
    on a row agree (QC B001).
    """
    water = {(row[0], row[1]): float(row[-1]) / 100 for row in lnmc["rows"]}
    rows = []
    for sample in samples():
        name, top, _, kind, _ = sample
        if kind != "U":
            continue
        w = water[name, top]
        void_ratio = w * 2.70 / density_rng.uniform(0.95, 1.00)
        dry = 2.70 / (1 + void_ratio)
        test = ["LINEAR", "UNDISTURBED", f"{100 * w:.0f}", dry * (1 + w) / PCF]
        rows.append([*specimen(sample), *test, dry / PCF])
    headings = [
        *SPECIMEN_HEADINGS,
        ("LDEN_TYPE", "PA", ""),
        ("LDEN_COND", "PA", ""),
        ("LDEN_MC", "X", "%"),
        ("LDEN_BDEN", "1DP", "pcf"),
        ("LDEN_DDEN", "1DP", "pcf"),
    ]
    return group("LDEN", headings, rows)


def fghg():
    rows = [
        [name, 35.0, 40.0, "1", "FH", 10 ** rng.uniform(-3.5, -2.0)]
        for name in ("B-2", "B-3", "B-5", "B-6")
    ]
    headings = [
        ("LOCA_ID", "ID", ""),
        ("FGHG_TOP", "1DP", "ft"),
        ("FGHG_BASE", "1DP", "ft"),
        ("FGHG_TESN", "X", ""),
        ("FGHG_TYPE", "PA", ""),
        ("FGHG_IPRM", "1SCI", "cm/s"),
    ]
    return group("FGHG", headings, rows)


# --- Writing --------------------------------------------------------------------------


def site_groups():
    llpl, lnmc = atterberg()
    grag, grat = grading()
    groups = [loca(), geol(), samp(), ispt(), llpl, lnmc, grag, grat, ptst(), fghg()]
    return [*groups, lden(lnmc), lpdn()]


def write_site(path):
    """Write PROJ, TRAN, UNIT, TYPE and ABBR, then the site's groups."""
    groups = site_groups()
    proj = group(
        "PROJ",
        [("PROJ_ID", "ID", ""), ("PROJ_NAME", "X", "")],
        [["HT-EX-1", "Riverside example site (synthetic)"]],
    )
    tran = _files.tran("4.2")
    tran["rows"][0][4] = "Synthetic example data for hangtu"
    tran["rows"][0][6] = "hangtu users"
    every = [proj, tran, *groups]
    used_units = {u for g in every for _, _, u in g["headings"] if u}
    used_types = {t for g in every for _, t, _ in g["headings"]}
    unit = group(
        "UNIT",
        [("UNIT_UNIT", "X", ""), ("UNIT_DESC", "X", "")],
        [[u, _files.UNIT_DESCRIPTIONS[u]] for u in sorted(used_units)],
    )
    types = group(
        "TYPE",
        [("TYPE_TYPE", "X", ""), ("TYPE_DESC", "X", "")],
        [[t, _files.TYPE_DESCRIPTIONS[t]] for t in sorted(used_types | {"X"})],
    )
    abbr = group(
        "ABBR",
        [("ABBR_HDNG", "X", ""), ("ABBR_CODE", "X", ""), ("ABBR_DESC", "X", "")],
        [list(a) for a in ABBR],
    )
    lines = []
    for g in [proj, tran, unit, types, abbr, *groups]:
        write_group(lines, g)
    out = "".join(
        "\r\n" if line is None else ",".join(f'"{v}"' for v in line) + "\r\n"
        for line in lines
    )
    path.write_text(out, encoding="utf-8", newline="")


def write_csvs(out):
    """Write each dataset's template columns, as a CSV user would type them.

    Depths and levels are in ft and hydraulic conductivity in cm/s, the
    display units of the US datasets. A reader declares them with
    ``ht.read_csv(..., units={...})``. ``spt_n60`` is left blank, as in most
    users' files: the plots work it out from ``energy_ratio``.
    """
    with tempfile.TemporaryDirectory() as folder:
        p = ht.Project.from_ags(
            out / "site.ags", db=Path(folder) / "site.sqlite", display_units="US"
        )
        p.set_geology_map(out / "strata.csv")
        for name in ("spt", "atterberg", "permeability"):
            dataset = getattr(p, name)()
            frame = dataset[list(ht.template(name).columns)]
            if name == "spt":
                frame = frame.assign(spt_n60=float("nan"))
            frame.to_csv(
                out / f"{name}.csv",
                index=False,
                float_format="%.6g",
                lineterminator="\n",
            )


def main(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng.seed(2026)
    hydrometer_rng.seed(2027)
    density_rng.seed(2028)
    write_site(out / "site.ags")
    (out / "strata.csv").write_text(STRATA, encoding="utf-8", newline="")
    (out / "judgments.yaml").write_text(JUDGMENTS, encoding="utf-8", newline="")
    write_csvs(out)


if __name__ == "__main__":
    main()
