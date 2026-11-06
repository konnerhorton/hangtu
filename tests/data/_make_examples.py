"""Write the example data that ships with hangtu (docs/work/m9-release.md, spec §1).

Run from the repository root after changing the data below:

    uv run python tests/data/_make_examples.py

The site is synthetic: a river valley with fill over soft alluvial clay over
terrace sand, with sandstone cored below the sand in B-3, in US units as a
US consultant's file would have them. Values come from fixed rules plus a
seeded ``random.Random``, whose sequence Python keeps the same across
versions, so the files are reproduced exactly.
The seeded tests loop over ``samples()``, so a sample added there changes
every value after it: list a new test's samples apart, as
``TRIAXIAL_SAMPLES`` does, or give the new values their own sequence.

The fill and the upper alluvium tubes have hydrometer tests, so their
grading curves continue into the fines; the terrace sands are sieved only.

``judgments.yaml`` holds the site's unit weights and specific gravities by
geology unit and a water level for each hole, as an engineer would set them
(SPEC §4). The Gs values are the medians of the measured LPDN tests, and the
sandstone's fixed σci the mean of its UCS tests that failed in shear.

``rock_triaxial.csv`` holds B-3's sandstone UCS and triaxial tests in MPa
(M17 c), in the ``triaxial`` template's columns; they aren't in ``site.ags``.

For comparing a parameter's sources (M18 d), ``site.ags`` also has single-stage
CD triaxial tests on four Terrace tubes and small shear box tests on three
Terrace spoons, more UU, laboratory vane, hand penetrometer and borehole vane
tests in the Alluvium, and ``judgments.yaml`` a φ′cv for the Terrace and the
selection of the Terrace's φ′ and c′ and the Alluvium's s_u (M18 e). Each set
has its own seeded sequence and its rows follow every other row of their
groups, so nothing written before changed. ``triaxial.csv``, ``shear_box.csv``
and ``strength.csv`` are the project's datasets in their templates' columns.

Two QC findings are planted, so the QC example has something to report:
- G002, a gap in the geology log of B-4 from 9.0 to 10.0 ft;
- A002, a plasticity index in B-3 that doesn't match LL - PL (an arithmetic slip).
"""

import importlib.util
import math
import random
import tempfile
from pathlib import Path

import pandas as pd

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
    ("GEOL_LEG", "SST", "Sandstone"),
    ("GEOL_GEOL", "TRC", "Terrace deposits"),
    ("GEOL_GEOL", "SST", "Sandstone"),
    ("SAMP_TYPE", "U", "Undisturbed sample - open drive"),
    ("SAMP_TYPE", "D", "Small disturbed sample"),
    ("SAMP_TYPE", "B", "Bulk disturbed sample"),
    ("SAMP_TYPE", "C", "Core sample"),
    ("ISPT_TYPE", "S", "Split spoon"),
    ("PTST_TYPE", "FW", "Flexible wall permeameter"),
    ("PTST_COND", "UND", "Undisturbed"),
    ("FGHG_TYPE", "FH", "Falling head"),
    ("LDEN_TYPE", "LINEAR", "Linear measurement"),
    ("LDEN_COND", "UNDISTURBED", "Undisturbed"),
    ("LPDN_TYPE", "SMALL PYK", "Small pyknometer"),
    ("TREG_TYPE", "CU", "Consolidated undrained with pwp measurement (single stage)"),
    ("TREG_TYPE", "CDM", "Consolidated drained (multi-stage)"),
    ("TREG_TYPE", "CD", "Consolidated drained (single stage)"),
    ("TREG_COND", "UNDISTURBED", "Undisturbed"),
    ("TRIG_TYPE", "UU", "Unconsolidated quick undrained (single stage)"),
    ("TRIG_COND", "UNDISTURBED", "Undisturbed"),
    ("LVAN_TYPE", "LV", "Laboratory vane"),
    ("SHBG_TYPE", "SMALL SBOX", "Small Shearbox"),
    ("SHBG_COND", "UNDISTURBED", "Undisturbed"),
    ("SHBG_COND", "RECOMPACTED", "Recompacted"),
    ("IVAN_TYPE", "BOREHOLE", "Borehole vane"),
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
# Rock cored below the soil (M17 b): hole, final depth (ft) and unit. The soil
# base stays HOLES' final depth, where the SPTs end, so the seeded values of
# every other test keep their sequence.
ROCK = {"B-3": (71.5, "SST")}

DESCRIPTIONS = {
    "FILL": ("FILL", "Fill", "Brown sandy lean CLAY with gravel (FILL)"),
    "ALV": ("CL", "Alluvium", "Soft to medium stiff gray lean CLAY (CL)"),
    "TRC": ("SP", "Terrace", "Medium dense to very dense brown SAND with gravel (SP)"),
    "SST": (
        "SST",
        "Sandstone",
        "Moderately strong gray fine-grained SANDSTONE, slightly weathered,"
        " thinly bedded",
    ),
}
SIEVES = [75.0, 37.5, 19.0, 9.5, 4.75, 2.0, 0.85, 0.425, 0.25, 0.15, 0.075]  # mm
# Hydrometer particle sizes (mm), as a lab's readings at set times give them.
HYDROMETER = [0.046, 0.033, 0.021, 0.012, 0.0089, 0.0063, 0.0031, 0.0013]

STRATA = """\
code,geology_unit,soil_class,order,color
FILL,Fill,fill,1,#9e9e9e
ALV,Alluvium,fine,2,#5b8db8
TRC,Terrace,coarse,3,#e0b040
SST,Sandstone,rock,4,#8c6d5a
"""

# The site's judgments (SPEC §4), in the file's US units.
JUDGMENTS = """\
# judgments.yaml: the example site's unit weights, water levels, Gs, α, the
# sandstone's fixed σci, the Terrace's φ′cv and the selected φ′, c′ and s_u (SPEC §4).
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
    Sandstone:
      bulk_unit_weight: 150
      reason: >-
        fine-grained sandstone, typical; no saturated weight is given, so
        vertical_stress() uses this one below B-3's water level too
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
fixed_intact_compressive_strength:
  by: geology_unit
  units: {intact_compressive_strength: MPa}
  values:
    Sandstone:
      intact_compressive_strength: 61
      reason: "mean of the three UCS tests that failed in shear, 60.8 MPa"
critical_state_friction_angle:
  by: geology_unit
  units: {critical_state_friction_angle: deg}
  values:
    Terrace:
      critical_state_friction_angle: 32
      reason: >-
        assumed for subangular quartz sand with gravel; no ring shear or
        angle of repose test yet
selection:
  effective_friction_angle:
    values:
      Terrace:
        source: "Mohr-Coulomb fit (CDM, CD)"
        method: fitted
        reason: >-
          the triaxial fit over all 15 stages; the converted shear box agrees,
          and the SPT correlations run 6-9 degrees higher in this gravelly sand
      Alluvium:
        method: none
        reason: "soft clay: designed undrained, with s_u"
  effective_cohesion:
    values:
      Terrace:
        source: "Mohr-Coulomb fit (CDM, CD)"
        method: fitted
        reason: "with φ′ from the same fit, so the pair stays on one line"
      Alluvium:
        method: none
        reason: "soft clay: designed undrained, with s_u"
  undrained_shear_strength:
    values:
      Alluvium:
        source: "lab, UU"
        method: characteristic
        estimate: mean
        side: low
        distribution: lognormal
        reason: >-
          the embankment's slip surfaces run through the whole layer, so a
          cautious estimate of the mean; the UU tests span only 13 to 19 ft,
          too little for a trend with depth
"""


def unit_at(hole, depth):
    _, _, _, _, _, fill, alluvium = hole
    return "FILL" if depth < fill else "ALV" if depth < alluvium else "TRC"


# --- Holes and geology -------------------------------------------------------------


def loca():
    rows = [
        [name, "HSA", east, north, "SPCS", gl, final, f"2026-08-{10 + i:02d}"]
        for i, (name, east, north, gl, fdep, _, _) in enumerate(HOLES)
        for final in [ROCK.get(name, (fdep,))[0]]
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
        if name in ROCK:
            layers.append((fdep, *ROCK[name]))
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


#: Samples taken for triaxial tests only, apart from samples() so that the
#: seeded values of the other tests stay as they were.
TRIAXIAL_SAMPLES = [("B-5", 35.0, 37.0, "U", "4")]
#: Rock core taken for the joint shear box tests (M17 b), apart likewise.
CORE_SAMPLES = [("B-3", 64.0, 65.0, "C", "5")]


def samp():
    rows = [
        [name, top, ref, kind, f"{name}-{kind}{ref}", base]
        for name, top, base, kind, ref in [
            *samples(),
            *TRIAXIAL_SAMPLES,
            *CORE_SAMPLES,
            *TERRACE_TRIAXIAL_SAMPLES,
            *TERRACE_SHEAR_BOX_SAMPLES,
        ]
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


# Triaxial tests (M11 b): a CU set on B-2's lower Alluvium tube (lean clay,
# about 26° and a small c′) and a three-stage CDM test on a Terrace tube
# (sand, about 35° and c′ near 0). Stresses in psf, back pressure 8640 psf
# (60 psi). Beside each stage, σ′3 = cell - u_f and σ′1 = σ′3 + q_f (psf).
# Every B-value is at least 0.95 and TRET_CONP is cell - back on the single
# stages and the first stage, so the tests raise no QC finding.
TRIAXIAL_SPECIMEN_HEADINGS = [
    *SAMPLE_HEADINGS,
    ("SPEC_REF", "X", ""),
    ("SPEC_DPTH", "1DP", "ft"),
]
BACK_PRESSURE = 8640  # psf
CU_SAMPLE = ["B-2", 17.5, "2", "U", "B-2-U2"]
CDM_SAMPLE = ["B-5", 35.0, "4", "U", "B-5-U4"]


def treg():
    headings = [
        *TRIAXIAL_SPECIMEN_HEADINGS,
        ("TREG_TYPE", "PA", ""),
        ("TREG_COND", "PA", ""),
        ("TREG_COH", "0DP", "psf"),
        ("TREG_PHI", "1DP", "deg"),
        ("TREG_FCR", "X", ""),
        ("TREG_REM", "X", ""),
    ]
    criterion = "Maximum deviator stress"
    rows = [
        [*CU_SAMPLE, ref, depth, "CU", "UNDISTURBED", 110, 25.8, criterion, None]
        for ref, depth in [("3", 17.8), ("4", 18.2), ("5", 18.6)]
    ]
    rows.append(
        [*CDM_SAMPLE, "1", 35.5, "CDM", "UNDISTURBED", 0, 35.0, criterion, None]
    )
    reported = terrace_triaxial_reported()
    for sample, ref, depth, *_ in terrace_triaxial():
        lab = reported[sample[4]]
        rows.append([*sample, ref, depth, "CD", "UNDISTURBED", *lab, criterion, None])
    return group("TREG", headings, rows)


def tret():
    headings = [
        *TRIAXIAL_SPECIMEN_HEADINGS,
        ("TRET_TESN", "X", ""),
        ("TRET_IMC", "X", "%"),
        ("TRET_BDEN", "1DP", "pcf"),
        ("TRET_DDEN", "1DP", "pcf"),
        ("TRET_CONP", "0DP", "psf"),
        ("TRET_CELL", "0DP", "psf"),
        ("TRET_STRN", "1DP", "%"),
        ("TRET_DEVF", "0DP", "psf"),
        ("TRET_PWPF", "0DP", "psf"),
        ("TRET_STV", "2DP", "%"),
        ("TRET_BACK", "0DP", "psf"),
        ("TRET_BVAL", "2DP", ""),
        ("TRET_IVR", "3DP", ""),
    ]
    # Each specimen's water content, bulk and dry density and void ratio.
    initial = {
        "3": ("29", 118.5, 91.9, 0.834),
        "4": ("30", 117.9, 90.7, 0.858),
        "5": ("28", 119.2, 93.1, 0.811),
        "1": ("18", 127.0, 107.6, 0.549),
    }
    # Specimen, depth, stage, consolidation, cell, strain, q_f, u_f, ε_v, B.
    cu = [
        ("3", 17.8, "1", 1000, 9640, 12.0, 1250, 9040, None, 0.97),  # σ′3 600, σ′1 1850
        ("4", 18.2, "1", 2000, 10640, 10.5, 2290, 9390, None, 0.96),  # 1250, 3540
        ("5", 18.6, "1", 4000, 12640, 9.0, 4200, 10140, None, 0.98),  # 2500, 6700
    ]
    cdm = [
        ("1", 35.5, "1", 2000, 10640, 3.5, 5450, 8640, 0.40, 0.96),  # 2000, 7450
        ("1", 35.5, "2", 4000, 12640, 4.0, 10700, 8640, 0.90, 0.96),  # 4000, 14700
        ("1", 35.5, "3", 8000, 16640, 5.5, 21400, 8640, 1.60, 0.96),  # 8000, 29400
    ]
    rows = []
    for sample, stages in ((CU_SAMPLE, cu), (CDM_SAMPLE, cdm)):
        for ref, depth, tesn, *test, stv, bval in stages:
            water, bulk, dry, void_ratio = initial[ref]
            initial_state = [water, bulk, dry]
            stage = [*test, stv, BACK_PRESSURE, bval, void_ratio]
            rows.append([*sample, ref, depth, tesn, *initial_state, *stage])
    # The CD specimens (M18 d): drained, so u_f is the back pressure.
    for sample, ref, depth, minor, deviator, t in terrace_triaxial():
        cell = minor + BACK_PRESSURE
        rows.append(
            [
                *[*sample, ref, depth, "1", t["water"], t["bulk"], t["dry"]],
                *[minor, cell, t["strain"], deviator, BACK_PRESSURE],
                *[t["volumetric"], BACK_PRESSURE, t["b_value"], t["void_ratio"]],
            ]
        )
    return group("TRET", headings, rows)


# Undrained strength (M17 a): a UU set on B-1's lower Alluvium tube, laboratory
# vanes and hand penetrometer readings on upper Alluvium tubes, and borehole
# vanes down B-6's Alluvium, all in psf. Beside each, s_u: q_f / 2 for UU (the
# lab's TRIT_CU is the same), as reported for the rest; and S_t = s_u / s_u,r.
UU_SAMPLE = ["B-1", 17.5, "3", "U", "B-1-U3"]


def trig():
    headings = [
        *TRIAXIAL_SPECIMEN_HEADINGS,
        ("TRIG_TYPE", "PA", ""),
        ("TRIG_COND", "PA", ""),
    ]
    rows = [
        [*UU_SAMPLE, ref, depth, "UU", "UNDISTURBED"]
        for ref, depth in [("3", 17.8), ("4", 18.2), ("5", 18.6)]
    ]
    rows += [
        [*sample, ref, depth, "UU", "UNDISTURBED"]
        for sample, ref, depth, *_ in alluvium_undrained()["uu"]
    ]
    return group("TRIG", headings, rows)


def trit():
    headings = [
        *TRIAXIAL_SPECIMEN_HEADINGS,
        ("TRIT_TESN", "X", ""),
        ("TRIT_IMC", "X", "%"),
        ("TRIT_CELL", "0DP", "psf"),
        ("TRIT_DEVF", "0DP", "psf"),
        ("TRIT_STRN", "1DP", "%"),
        ("TRIT_CU", "0DP", "psf"),
    ]
    rows = [
        [*UU_SAMPLE, "3", 17.8, "1", "31", 1000, 1100, 11.0, 550],  # s_u 550
        [*UU_SAMPLE, "4", 18.2, "1", "30", 2000, 1160, 12.5, 580],  # 580
        [*UU_SAMPLE, "5", 18.6, "1", "32", 3000, 1080, 13.0, 540],  # 540
    ]
    rows += [
        [*sample, ref, depth, "1", water, cell, deviator, strain, su]
        for sample, ref, depth, cell, deviator, strain, water, su in (
            alluvium_undrained()["uu"]
        )
    ]
    return group("TRIT", headings, rows)


def lvan():
    headings = [
        *TRIAXIAL_SPECIMEN_HEADINGS,
        ("LVAN_VNPK", "0DP", "psf"),
        ("LVAN_VNRM", "0DP", "psf"),
        ("LVAN_TYPE", "PA", ""),
    ]
    rows = [
        ["B-3", 12.5, "2", "U", "B-3-U2", "2", 13.0, 520, 180, "LV"],  # S_t 2.89
        ["B-4", 12.5, "1", "U", "B-4-U1", "2", 13.0, 610, 230, "LV"],  # 2.65
    ]
    rows += [
        [*sample, "2", depth, peak, remolded, "LV"]
        for sample, depth, peak, remolded in alluvium_undrained()["vane"]
    ]
    return group("LVAN", headings, rows)


def lpen():
    headings = [*TRIAXIAL_SPECIMEN_HEADINGS, ("LPEN_PPEN", "0DP", "psf")]
    rows = [
        ["B-2", 12.5, "1", "U", "B-2-U1", "2", 13.0, 600],
        ["B-5", 12.5, "1", "U", "B-5-U1", "2", 13.0, 700],
    ]
    rows += [
        [*sample, "6", depth, reading]
        for sample, depth, reading in alluvium_undrained()["penetrometer"]
    ]
    return group("LPEN", headings, rows)


def ivan():
    headings = [
        ("LOCA_ID", "ID", ""),
        ("IVAN_DPTH", "1DP", "ft"),
        ("IVAN_TESN", "X", ""),
        ("IVAN_TYPE", "PA", ""),
        ("IVAN_IVAN", "0DP", "psf"),
        ("IVAN_IVAR", "0DP", "psf"),
    ]
    rows = [
        ["B-6", 10.0, "1", "BOREHOLE", 480, 160],  # S_t 3.00
        ["B-6", 15.0, "2", "BOREHOLE", 560, 200],  # 2.80
        ["B-6", 20.0, "3", "BOREHOLE", 640, 210],  # 3.05
    ]
    numbers = {}
    for hole, depth, peak, remolded in alluvium_undrained()["field"]:
        numbers[hole] = numbers.get(hole, 0) + 1
        rows.append([hole, depth, str(numbers[hole]), "BOREHOLE", peak, remolded])
    return group("IVAN", headings, rows)


# Shear box (M17 b, docs/work/m17b-shear-box-fit.md, "Example data"): small
# shear box tests on two Alluvium tubes (undisturbed) and a Terrace spoon
# (recompacted), and bedding plane joints in B-3's sandstone core, two
# specimens set in resin. Every stress is in psf and written to 10 significant
# figures, as the joints are MPa values converted (MPa × 1e6 / 47.880259 psf),
# so they come back to 1e-9. SHBG_TYPE is blank on the joints: AGS has no
# rock joint code (M17 a, decision 9). SHBT_NORM only: no SHBT_PVST/RVST.
# The hand fits, τ = c + σn tan φ by least squares (free; through the origin):
#   B-3-U3 peak c 145 psf, b 727/1400, φ 27.44°; residual c 5, φ 21.70°
#   B-6-U2 peak c 195 psf, b 671/1400, φ 25.61°; residual c 50, φ 20.16°
#   Alluvium (both) peak c 170 psf, b 699/1400, φ 26.53° (origin 29.07°);
#     residual c 27.5, b 0.3825, φ 20.93° (origin 21.39°)
#   B-3-D4 peak c 71.0 psf, b 3933/5900, φ 33.69° (origin 34.33°);
#     residual c 3.05, b 3539/5900, φ 30.96° (origin 30.99°)
#   B-3-C5 specimen 1 peak c 0.095 MPa, φ 38.71°; residual c 0.015, φ 30.42°
#   B-3-C5 specimen 2 peak c 0.105 MPa, φ 37.49°; residual c 0.035, φ 28.94°
#   Sandstone (both) peak c 0.1 MPa, b 549/700, φ 38.11° (origin 40.40°);
#     residual c 0.025, b 0.57, φ 29.68° (origin 30.40°)
# The lab's pairs are each test's own fit, rounded.
PSF = 0.45359237 * 9.80665 / 0.3048**2  # Pa, exact by definition
SOIL_STRESSES = [1000, 2000, 4000]  # σn, psf
JOINT_STRESSES = [0.5, 1.0, 2.0]  # σn, MPa
SHEAR_BOX_TESTS = [
    # Specimen, type, condition, encapsulation, lab's peak (c, φ) and
    # residual (c, φ), then the stages' σn, τ_peak and τ_residual.
    (
        ["B-3", 17.5, "3", "U", "B-3-U3", "S1", 18.0],
        ("SMALL SBOX", "UNDISTURBED", None, 145, 27.4, 5, 21.7),
        (SOIL_STRESSES, [700, 1130, 2240], [430, 760, 1610]),
    ),
    (
        ["B-6", 17.5, "2", "U", "B-6-U2", "S1", 18.0],
        ("SMALL SBOX", "UNDISTURBED", None, 195, 25.6, 50, 20.2),
        (SOIL_STRESSES, [610, 1250, 2080], [380, 840, 1500]),
    ),
    (
        ["B-3", 30.0, "4", "D", "B-3-D4", "S1", 30.5],
        ("SMALL SBOX", "RECOMPACTED", None, 71, 33.7, 3, 31.0),
        ([1000, 2000, 4000, 6000], [760, 1420, 2650, 4120], [610, 1180, 2430, 3590]),
    ),
]
JOINT_TESTS = [
    # The same, in MPa.
    (
        ["B-3", 64.0, "5", "C", "B-3-C5", "1", 64.2],
        (None, "UNDISTURBED", "Resin", 0.095, 38.7, 0.015, 30.4),
        (JOINT_STRESSES, [0.52, 0.86, 1.71], [0.33, 0.57, 1.20]),
    ),
    (
        ["B-3", 64.0, "5", "C", "B-3-C5", "2", 64.6],
        (None, "UNDISTURBED", "Resin", 0.105, 37.5, 0.035, 28.9),
        (JOINT_STRESSES, [0.45, 0.93, 1.62], [0.29, 0.62, 1.13]),
    ),
]


def in_psf(mpa):
    return [value * 1e6 / PSF for value in mpa]


def shear_box_tests():
    """Every test, its stresses in psf."""
    tests = list(SHEAR_BOX_TESTS)
    for specimen_row, (kind, cond, enca, pc, pphi, rc, rphi), stages in JOINT_TESTS:
        test = (kind, cond, enca, *in_psf([pc]), pphi, *in_psf([rc]), rphi)
        tests.append((specimen_row, test, tuple(in_psf(v) for v in stages)))
    return [*tests, *terrace_shear_box()]


def shbg():
    headings = [
        *SPECIMEN_HEADINGS,
        ("SHBG_TYPE", "PA", ""),
        ("SHBG_COND", "PA", ""),
        ("SHBG_PCOH", "10SF", "psf"),
        ("SHBG_PHI", "1DP", "deg"),
        ("SHBG_RCOH", "10SF", "psf"),
        ("SHBG_RPHI", "1DP", "deg"),
        ("SHBG_ENCA", "X", ""),  # after RPHI, in the dictionary's order (Rule 7)
    ]
    rows = [
        [*specimen_row, kind, cond, *lab, enca]
        for specimen_row, (kind, cond, enca, *lab), _ in shear_box_tests()
    ]
    return group("SHBG", headings, rows)


def shbt():
    headings = [
        *SPECIMEN_HEADINGS,
        ("SHBT_TESN", "X", ""),
        ("SHBT_NORM", "10SF", "psf"),
        ("SHBT_PEAK", "10SF", "psf"),
        ("SHBT_RES", "10SF", "psf"),
        ("SHBT_CRIT", "X", ""),
    ]
    rows = [
        [*specimen_row, str(stage), norm, peak, res, "Maximum shear stress"]
        for specimen_row, _, stages in shear_box_tests()
        for stage, (norm, peak, res) in enumerate(zip(*stages, strict=True), 1)
    ]
    return group("SHBT", headings, rows)


# --- Sources compared (M18 d) ---------------------------------------------------------

# docs/work/m18d-sources-compared.md, decision 20: enough Terrace φ′ tests and
# Alluvium s_u tests to compare their sources. Each set draws from its own
# random.Random, made afresh on each call, and its rows go after every other
# row of their groups, so no value written before changes. φ′ scatters with a
# CoV about 0.1 and s_u about 0.3, both skewed high, each with one outlier.

#: Terrace tubes for single-stage CD triaxial tests, three specimens each.
TERRACE_TRIAXIAL_SAMPLES = [
    ("B-1", 30.0, 32.0, "U", "5"),
    ("B-2", 40.0, 42.0, "U", "4"),
    ("B-4", 45.0, 47.0, "U", "4"),
    ("B-6", 35.0, 37.0, "U", "4"),
]
#: Terrace spoons for small shear box tests, recompacted.
TERRACE_SHEAR_BOX_SAMPLES = [
    ("B-2", 30.0, 31.5, "D", "5"),
    ("B-5", 45.0, 46.5, "D", "5"),
    ("B-6", 45.0, 46.5, "D", "5"),
]
CD_STRESSES = [1000, 2000, 4000]  # σ′3, psf
WATER_UNIT_WEIGHT = 62.428  # pcf
TERRACE_GS = 2.67  # judgments.yaml's Terrace specific gravity


def sample_row(sample):
    name, top, _, kind, ref = sample
    return [name, top, ref, kind, f"{name}-{kind}{ref}"]


def lab_fit(normal, shear):
    """The lab's least-squares line τ = c + σ tan φ: (c, φ in degrees).

    A negative c is reported as 0, with the line through the origin.
    """
    n = len(normal)
    mx, my = sum(normal) / n, sum(shear) / n
    sxx = sum((x - mx) ** 2 for x in normal)
    slope = sum((x - mx) * (y - my) for x, y in zip(normal, shear, strict=True)) / sxx
    if my - slope * mx < 0:
        pairs = zip(normal, shear, strict=True)
        slope = sum(x * y for x, y in pairs) / sum(x * x for x in normal)
        return 0.0, math.degrees(math.atan(slope))
    return my - slope * mx, math.degrees(math.atan(slope))


def terrace_triaxial():
    """Each CD specimen: (sample row, ref, depth, σ′3, q_f, test values), psf.

    Each sample has its own φ′, 25° plus a lognormal (median 10°, so about
    35° and skewed high), and each specimen scatters about it by 0.7°; c′ is
    an apparent 200 psf. B-4-U4's second specimen is 6° low, a loose layer: the
    outlier. σ′1 = σ′3 Kp + 2 c′ √Kp, so q_f = σ′1 - σ′3.
    """
    draw = random.Random(2029)
    found = []
    for sample in TERRACE_TRIAXIAL_SAMPLES:
        phi = 25 + draw.lognormvariate(math.log(10), 0.3)
        for i, minor in enumerate(CD_STRESSES):
            angle = (
                phi + draw.gauss(0, 0.7) - (6 if sample[0] == "B-4" and i == 1 else 0)
            )
            kp = (1 + math.sin(math.radians(angle))) / (
                1 - math.sin(math.radians(angle))
            )
            major = minor * kp + 2 * 200 * math.sqrt(kp)
            water = draw.uniform(14, 20)
            bulk = round(draw.uniform(124, 131), 1)
            dry = round(bulk / (1 + water / 100), 1)
            test = {
                "water": str(round(water)),
                "bulk": bulk,
                "dry": dry,
                "void_ratio": round(TERRACE_GS * WATER_UNIT_WEIGHT / dry - 1, 3),
                "strain": round(draw.uniform(3.0, 7.0), 1),
                "volumetric": round(draw.uniform(0.2, 1.2), 2),
                "b_value": round(draw.uniform(0.95, 0.99), 2),
            }
            depth = round(sample[1] + 0.3 + 0.4 * i, 1)
            found.append(
                (
                    sample_row(sample),
                    str(i + 1),
                    depth,
                    minor,
                    round(major - minor),
                    test,
                )
            )
    return found


def terrace_triaxial_reported():
    """{sample id: the lab's (c′, φ′)}: each sample's s′-t line, rounded."""
    by_sample = {}
    for sample, _, _, minor, deviator, _ in terrace_triaxial():
        by_sample.setdefault(sample[4], []).append((minor + deviator / 2, deviator / 2))
    reported = {}
    for name, points in by_sample.items():
        a, alpha = lab_fit(*zip(*points, strict=True))
        phi = math.asin(math.tan(math.radians(alpha)))
        reported[name] = (round(a / math.cos(phi)), round(math.degrees(phi), 1))
    return reported


def terrace_shear_box():
    """Each shear box test, as SHEAR_BOX_TESTS lists them.

    Peak φ 25° plus a lognormal (median 8°, about 33°), c 50 to 150 psf, each
    τ scattered by 25 psf; residual φ about 30.5° (σ 1°), near critical state
    whatever the peak, c 20 to 60 psf.
    """
    draw = random.Random(2030)
    tests = []
    for sample in TERRACE_SHEAR_BOX_SAMPLES:
        phi = 25 + draw.lognormvariate(math.log(8), 0.3)
        cohesion = draw.uniform(50, 150)
        residual_phi = draw.gauss(30.5, 1.0)
        residual_c = draw.uniform(20, 60)
        peaks, residuals = [], []
        for normal in SOIL_STRESSES:
            peak = cohesion + normal * math.tan(math.radians(phi))
            residual = residual_c + normal * math.tan(math.radians(residual_phi))
            peaks.append(round(peak + draw.gauss(0, 25)))
            residuals.append(round(residual + draw.gauss(0, 25)))
        pc, pphi = lab_fit(SOIL_STRESSES, peaks)
        rc, rphi = lab_fit(SOIL_STRESSES, residuals)
        lab = (round(pc), round(pphi, 1), round(rc), round(rphi, 1))
        row = [*sample_row(sample), "S1", sample[1] + 0.5]
        tests.append(
            (
                row,
                ("SMALL SBOX", "RECOMPACTED", None, *lab),
                (SOIL_STRESSES, peaks, residuals),
            )
        )
    return tests


#: Alluvium tubes for more UU tests: (sample, specimens' depths).
ALLUVIUM_UU = [
    (("B-4", 17.5, 19.5, "U", "2"), [17.8, 18.2, 18.6]),
    (("B-5", 17.5, 19.5, "U", "2"), [17.8, 18.2, 18.6]),
    (("B-6", 12.5, 14.5, "U", "1"), [12.8, 13.2]),
]
#: Alluvium tubes for more laboratory vanes (specimen 2) and hand penetrometer
#: readings (specimen 6).
ALLUVIUM_VANE = [
    ("B-1", 12.5, 14.5, "U", "2"),
    ("B-6", 12.5, 14.5, "U", "1"),
    ("B-4", 17.5, 19.5, "U", "2"),
    ("B-5", 17.5, 19.5, "U", "2"),
]
ALLUVIUM_PENETROMETER = [
    ("B-1", 12.5, 14.5, "U", "2"),
    ("B-3", 12.5, 14.5, "U", "2"),
    ("B-4", 17.5, 19.5, "U", "2"),
    ("B-6", 12.5, 14.5, "U", "1"),
]
#: More borehole vanes: (hole, depth).
ALLUVIUM_FIELD_VANE = [
    ("B-1", 10.0),
    ("B-1", 15.0),
    ("B-1", 20.0),
    ("B-2", 10.0),
    ("B-2", 15.0),
    ("B-2", 20.0),
    ("B-4", 12.0),
    ("B-4", 17.0),
]


def alluvium_undrained():
    """{test: values} in psf: s_u lognormal, median 560 psf, σ_ln 0.3.

    UU: (cell, q_f, strain, water); B-5-U2's third specimen is 2.2 times the
    rest, a sandy seam: the outlier. Vanes: (peak, remolded), sensitivity
    2.4 to 3.3. Hand penetrometer readings to 50 psf.
    """
    draw = random.Random(2031)

    def strength():
        return draw.lognormvariate(math.log(560), 0.3)

    uu = []
    for sample, depths in ALLUVIUM_UU:
        for i, depth in enumerate(depths):
            su = strength() * (2.2 if sample[0] == "B-5" and i == 2 else 1)
            su = round(su, -1)
            water = str(round(draw.uniform(27, 34)))
            strain = round(draw.uniform(8, 15), 1)
            uu.append(
                (
                    sample_row(sample),
                    str(i + 3),
                    depth,
                    1000 * (i + 1),
                    2 * su,
                    strain,
                    water,
                    su,
                )
            )
    vanes = []
    for sample in ALLUVIUM_VANE:
        peak = round(strength(), -1)
        vanes.append(
            (
                sample_row(sample),
                sample[1] + 0.5,
                peak,
                round(peak / draw.uniform(2.4, 3.3), -1),
            )
        )
    penetrometer = [
        (sample_row(sample), sample[1] + 0.5, 50 * round(strength() / 50))
        for sample in ALLUVIUM_PENETROMETER
    ]
    field = []
    for hole, depth in ALLUVIUM_FIELD_VANE:
        peak = round(strength(), -1)
        field.append((hole, depth, peak, round(peak / draw.uniform(2.4, 3.3), -1)))
    return {"uu": uu, "vane": vanes, "penetrometer": penetrometer, "field": field}


# --- Rock triaxial and UCS tests (M17 c) ----------------------------------------------

# B-3's sandstone cores, for hoek_brown_fit() (docs/work/m17c-hoek-brown-fit.md,
# "Example data"): made about σci = 60 MPa and mi = 15 (sandstone, 17 ± 4) with
# site-like scatter, a multistage specimen low at its later stages, and two
# failures that aren't shear. Stresses in MPa, depths in ft. They go only in
# rock_triaxial.csv, not in site.ags, which would store them in psf. The core
# samples after B-3-C5 are this CSV's own, so site.ags is unchanged.
#
# Hand fits, x = σ3, y = (σ1 - σ3)², the 13 Shear rows:
#   all stages: n 13, Σx 100, Σy 132377.83, Σxy 1508743.35, Σx² 1387.5;
#     b = 127517611/160750 = 793.266631, a = 262399233/64300 = 4080.85899,
#     σci = √a = 63.8816013, mi = b/σci = 12.4177637, R² 0.950690094;
#     σci fixed at 61: Σx(y - 3721) = 1136643.35, b = 819.202414,
#     mi = 13.4295478, R² 0.948857038.
#   single stage (10 rows): Σx 65, Σy 95644.63, Σxy 1002175.75, Σx² 862.5;
#     b = 6917921/8000 = 864.740125, a = 12619687/3200 = 3943.65219,
#     σci = 62.7985047, mi = 13.7700751, R² 0.966311262;
#     σci fixed at 61: mi = 14.4511428, R² 0.965568515.
#   UCS (Shear): 3, mean 365/6 = 60.8333 MPa, the judgments file's 61.
# The lab's own fit of the 13 Shear rows, rounded: σci 64 MPa, mi 12.4.
ROCK_TRIAXIAL = [
    # Sample, specimen, depth (ft), test type, stage, multistage, σ3, σ1 (MPa),
    # failure mode.
    ("C5", "3", 64.8, "UCS", 1, False, 0, 54.2, "Shear"),
    ("C6", "1", 66.0, "UCS", 1, False, 0, 66.8, "Shear"),
    ("C6", "2", 66.4, "Triaxial", 1, False, 2.5, 74.1, "Shear"),
    ("C6", "3", 66.8, "Triaxial", 1, False, 5, 98.7, "Shear"),
    ("C6", "4", 67.2, "Triaxial", 1, False, 10, 117.4, "Shear"),
    ("C7", "1", 68.0, "UCS", 1, False, 0, 61.5, "Shear"),
    ("C7", "2", 68.4, "Triaxial", 1, False, 2.5, 83.9, "Shear"),
    ("C7", "3", 68.8, "Triaxial", 1, False, 10, 129.0, "Shear"),
    ("C7", "4", 69.2, "Triaxial", 1, False, 10, 88.0, "Along bedding"),
    ("C8", "1", 70.0, "UCS", 1, False, 0, 38.6, "Axial splitting"),
    ("C8", "2", 70.4, "Triaxial", 1, False, 15, 151.2, "Shear"),
    ("C8", "3", 70.8, "Triaxial", 1, False, 20, 160.3, "Shear"),
    ("C8", "4", 71.2, "Triaxial multistage", 1, True, 5, 93.0, "Shear"),
    ("C8", "4", 71.2, "Triaxial multistage", 2, True, 10, 115.8, "Shear"),
    ("C8", "4", 71.2, "Triaxial multistage", 3, True, 20, 153.4, "Shear"),
]
ROCK_REPORTED = (64, 12.4)  # the lab's σci (MPa) and mi


def write_rock_triaxial(out):
    """Write ``rock_triaxial.csv`` in ``ht.template("triaxial")``'s columns."""
    rows = []
    for sample, ref, depth, kind, stage, multi, minor, major, mode in ROCK_TRIAXIAL:
        sample_id = f"B-3-{sample}"
        rows.append(
            {
                "loca_id": "B-3",
                "specimen_id": f"{sample_id}-{ref}",
                "sample_reference": sample_id,
                "specimen_reference": ref,
                "depth": depth,
                "test_type": kind,
                "test_stage": stage,
                "multistage_test": multi,
                "failure_criterion": "Peak axial stress",
                "failure_mode": mode,
                "cell_pressure": minor,
                "deviator_stress_at_failure": round(major - minor, 1),
                "reported_intact_compressive_strength": ROCK_REPORTED[0],
                "reported_intact_hoek_brown_constant": ROCK_REPORTED[1],
                "geology_unit": "Sandstone",
                "soil_class": "rock",
            }
        )
    pd.DataFrame(rows, columns=list(ht.template("triaxial").columns)).to_csv(
        out / "rock_triaxial.csv",
        index=False,
        float_format="%.6g",
        lineterminator="\n",
    )


# --- Writing --------------------------------------------------------------------------


def site_groups():
    llpl, lnmc = atterberg()
    grag, grat = grading()
    groups = [loca(), geol(), samp(), ispt(), llpl, lnmc, grag, grat, ptst(), fghg()]
    undrained = [trig(), trit(), lvan(), lpen(), ivan()]
    shear_box = [shbg(), shbt()]
    return [*groups, lden(lnmc), lpdn(), treg(), tret(), *undrained, *shear_box]


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
        # The tests compared in M18 (d), in their templates' columns. A
        # specimen is named by its sample and reference, as rock_triaxial.csv
        # names them, not by the database's number; a field test has none.
        for name, dataset in (
            ("triaxial", p.triaxial()),
            ("shear_box", p.shear_box()),
            ("strength", p.undrained_strength()),
        ):
            sample = dataset["sample_reference"]
            named = sample + "-" + dataset["specimen_reference"].astype(str)
            dataset = dataset.assign(specimen_id=named.where(sample.notna()))
            dataset[list(ht.template(name).columns)].to_csv(
                out / f"{name}.csv",
                index=False,
                float_format="%.6g",
                lineterminator="\n",
            )
        # The readings are treg()/tret()'s; the UU and CD stages have none.
        write_readings(out, p.triaxial(where={"test_type": ["CU", "CDM"]}))
    write_rock_triaxial(out)


# Readings during shearing (M11 c, docs/work/m11c-triaxial-shearing.md, spec
# decision 10): synthetic, not a test hangtu reads anything from. Each stage of
# treg()/tret() gets readings at fixed strains, the deviator stress on a
# hyperbola q = ε / (a + ε) scaled so its largest value is TRET_DEVF at
# TRET_STRN. The hyperbola only shapes the curves; it isn't a method hangtu
# offers. CU: Δu rises and flattens to TRET_PWPF - back pressure. CDM: Δu is
# 0 (drained), and ε_v contracts to a peak at 0.75 ε_f, then turns toward
# dilation, passing TRET_STV at failure. Each stage's failure reading is the
# lab's mark; the last stage of each test runs on past failure, with q falling.
READING_STRAINS = [0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15]
PAST_FAILURE = [(1.5, 0.98), (3.0, 0.96)]  # strain beyond ε_f, fraction of q_f


def readings_of(stage, last):
    """One stage's readings, as (ε_a, q, Δu, ε_v, failure) tuples."""
    strain_f = stage["axial_strain_at_failure"]
    q_f = stage["deviator_stress_at_failure"]
    excess_f = stage["pore_pressure_at_failure"] - stage["back_pressure"]
    drained = stage["test_type"] == "CDM"
    a = strain_f / 10

    def q(strain):
        return q_f * (strain / (a + strain)) / (strain_f / (a + strain_f))

    def excess(strain):
        if drained:
            return 0.0
        b = strain_f / 4
        return excess_f * (1 - math.exp(-strain / b)) / (1 - math.exp(-strain_f / b))

    def volumetric(strain):
        if not drained:
            return None
        c2 = 2 * stage["volumetric_strain_at_failure"] / strain_f**2
        return round(1.5 * strain_f * c2 * strain - c2 * strain**2, 2)

    rows = [
        (strain, round(q(strain)), round(excess(strain)), volumetric(strain), False)
        for strain in READING_STRAINS
        if strain < strain_f
    ]
    rows.append((strain_f, q_f, excess_f, volumetric(strain_f), True))
    if last:
        for extra, fraction in PAST_FAILURE:
            strain = strain_f + extra
            rows.append(
                (
                    strain,
                    round(q_f * fraction),
                    round(excess_f * (1 + extra / 100)),
                    volumetric(strain),
                    False,
                )
            )
    return rows


def write_readings(out, stages):
    """Write ``triaxial_readings.csv``: the example stages' readings, in psf."""
    columns = list(ht.template("triaxial_readings").columns)
    stage_columns = [c for c in columns if c in stages.columns]
    rows = []
    for position, (_, stage) in enumerate(stages.iterrows()):
        following = stages.iloc[position + 1 :]
        last = not (following["specimen_id"] == stage["specimen_id"]).any()
        for strain, q, excess, volumetric, failure in readings_of(stage, last):
            rows.append(
                {
                    **stage[stage_columns].to_dict(),
                    "axial_strain": strain,
                    "deviator_stress": q,
                    "excess_pore_pressure": excess,
                    "volumetric_strain": volumetric,
                    "reported_failure_reading": failure,
                }
            )
    pd.DataFrame(rows, columns=columns).to_csv(
        out / "triaxial_readings.csv",
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
