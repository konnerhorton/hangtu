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

``oedometer.csv`` is the project's oedometer tests in their template's columns
(M19 a), with their own seeded sequence like the M18 (d) sets.

Two QC findings are planted, so the QC example has something to report:
- G002, a gap in the geology log of B-4 from 9.0 to 10.0 ft;
- A002, a plasticity index in B-3 that doesn't match LL - PL (an arithmetic slip).
"""

import importlib.util
import itertools
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
    ("CONG_TYPE", "OEDOMETER", "Oedometer"),
    ("CONG_TYPE", "SWELLPRESS", "Measurement of swelling pressure"),
    ("CONG_COND", "UNDISTURBED", "Undisturbed"),
    ("DICT_TYPE", "GROUP", "Flag to indicate definition is a GROUP"),
    ("DICT_TYPE", "HEADING", "Flag to indicate definition is a HEADING"),
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


def tret_rows():
    """TRET without the lab's E50, which ``triaxial_stages()`` reads."""
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


#: The samples whose stages carry the lab's E50 (M23 a); the rest leave it blank.
E50_SAMPLES = {"B-2-U2", "B-1-U5", "B-2-U4"}


def strain_at_half_peak(curve, deviator):
    """The strain where the q curve first reaches ``deviator`` / 2, linearly
    interpolated between readings (%)."""
    half = deviator / 2
    for (s1, q1), (s2, q2) in itertools.pairwise(curve):
        if q2 >= half > q1:
            return s1 + (half - q1) / (q2 - q1) * (s2 - s1)
    raise ValueError("the curve never reaches half its peak")


def tret():
    """TRET with the lab's E50 and the consolidation stresses (M23 a).

    ε50 is read from each stage's own q curve in the file (``triaxial_curves()``
    with the draw ``curve_groups()`` uses, whose q curves come first), and E50 =
    (q_f / 2) / ε50 from the unrounded ε50; both are then rounded as written.
    They are generated, not hand-calculated, so they agree with the curves. The
    stages are isotropic, so TRET_CVP = TRET_CRP = TRET_CONP.
    """
    g = tret_rows()
    stages, _ = triaxial_stages()
    q_rows, _, _ = triaxial_curves(stages, random.Random(2031))
    rows = []
    for row, stage, (_, _, curve) in zip(g["rows"], stages, q_rows, strict=True):
        lab = [None] * 4
        if stage["SAMP_ID"] in E50_SAMPLES:
            strain = strain_at_half_peak(curve, stage["deviator"])
            modulus = stage["deviator"] / 2 / (strain / 100) / 1000  # ksf
            conp = stage["TRET_CONP"]
            lab = [conp, conp, strain, modulus]
        rows.append([*row, *lab])
    headings = [
        *g["headings"],
        ("TRET_CVP", "0DP", "psf"),
        ("TRET_CRP", "0DP", "psf"),
        ("TRET_EP50", "2DP", "%"),
        ("TRET_E50", "1DP", "ksf"),
    ]
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


# --- Oedometer (M19 a) ---------------------------------------------------------------

# Oedometer tests (docs/work/m19a-oedometer-data.md, spec decision 10): two
# incremental-load tests on Alluvium tubes and a swelling pressure test with no
# increments. The values are invented. B-4-U1 is lightly overconsolidated
# (σ′p about 1.5 × σ′v0), B-5-U2 stiffer, each with one unload-reload loop.
# The curve is bilinear in log σ′ (C_r to σ′p, C_c beyond; C_s on unloading
# and reloading) with scatter on each void ratio. The void ratios chain (each
# increment starts at the previous one's end), CONG_IVR is CONG_PDEN /
# CONG_DDEN - 1 from the values as written, and the lab's m_v is
# Δe / (1 + e_start) / Δσ′ from the void ratios as written, so QC finds
# nothing. Stresses in psf, m_v in ft²/kip, c_v in ft²/yr.
OEDOMETER_STRESSES = [250, 500, 1000, 2000, 4000, 8000, 2000, 500, 2000, 8000]
OEDOMETER_STRESSES += [16000, 4000]
OEDOMETER_TESTS = [
    # Specimen, then w (%), Gs, S and σ′p (psf).
    (["B-4", 12.5, "1", "U", "B-4-U1", "C1", 13.0], (39.0, 2.72, 0.98, 1500)),
    (["B-5", 17.5, "2", "U", "B-5-U2", "C1", 18.0], (31.0, 2.71, 0.99, 4200)),
]
#: Each test's C_r, C_c, C_s and c_v (ft²/yr).
OEDOMETER_SLOPES = [(0.045, 0.38, 0.06, 28.0), (0.030, 0.26, 0.04, 45.0)]
SWELLING_TEST = (["B-1", 12.5, "2", "U", "B-1-U2", "SW1", 13.0], (36.0, 2.72, 0.97))
SWELLING_PRESSURE = 420  # psf


def oedometer_specimen(w, gs, saturation):
    """The written w, ρs (Mg/m³), ρ and ρd (pcf), S (%) and e0 of a specimen.

    e = w Gs / S, ρd = Gs ρw / (1 + e) and ρ = ρd (1 + w); e0 is then
    ρs / ρd - 1 from ρd as written, so it agrees with QC E005.
    """
    e = w / 100 * gs / saturation
    dry = round(gs * WATER_UNIT_WEIGHT / (1 + e), 1)
    bulk = round(dry * (1 + w / 100), 1)
    e0 = round(gs * WATER_UNIT_WEIGHT / dry - 1, 3)
    return f"{w:.1f}", f"{gs:.2f}", bulk, dry, round(100 * saturation), e0


def oedometer_curve(e0, preconsolidation, slopes, draw):
    """Each increment's (σ′, e start, e end, m_v, c_v root, c_v log), as written.

    Loading follows C_r up to σ′p and C_c beyond it; unloading and reloading
    follow C_s from the largest stress so far, and a reloading curve past it
    rejoins the virgin line. Each end void ratio scatters by 0.002.
    """
    cr, cc, cs, cv = slopes
    seated = e0 - draw.uniform(0.001, 0.004)
    virgin = seated - cr * math.log10(preconsolidation / OEDOMETER_STRESSES[0])

    def on_virgin(stress):
        if stress <= preconsolidation:
            return seated - cr * math.log10(stress / OEDOMETER_STRESSES[0])
        return virgin - cc * math.log10(stress / preconsolidation)

    rows, start, previous, largest, e_at_largest = [], e0, None, 0.0, e0
    for stress in OEDOMETER_STRESSES:
        if stress > largest:
            ideal = on_virgin(stress)
        else:
            ideal = e_at_largest + cs * math.log10(largest / stress)
        end = round(ideal + draw.gauss(0, 0.002), 3)
        if previous is not None and stress > previous:
            end = min(end, round(start - 0.002, 3))  # compresses under a load
        elif previous is not None and stress < previous:
            end = max(end, round(start + 0.002, 3))  # swells as it unloads
        mv = cv_root = cv_log = None
        if previous is not None and stress > largest:
            ksf = (stress - previous) / 1000
            mv = (start - end) / (1 + start) / ksf
            root = cv * draw.lognormvariate(0, 0.25) * (1 if stress <= 2000 else 0.6)
            cv_root, cv_log = root, root * draw.uniform(0.7, 0.9)
        rows.append((stress, start, end, mv, cv_root, cv_log))
        if stress > largest:
            largest, e_at_largest = stress, end
        start, previous = end, stress
    return rows


def oedometer_tests():
    """Each specimen's CONG values and its increments; the swelling test has none."""
    draw = random.Random(2032)
    tests = []
    for (specimen_row, state), slopes in zip(
        OEDOMETER_TESTS, OEDOMETER_SLOPES, strict=True
    ):
        w, gs, saturation, preconsolidation = state
        values = oedometer_specimen(w, gs, saturation)
        curve = oedometer_curve(values[-1], preconsolidation, slopes, draw)
        final = f"{w - draw.uniform(6, 9):.1f}"
        tests.append((specimen_row, "OEDOMETER", values, final, None, curve))
    specimen_row, (w, gs, saturation) = SWELLING_TEST
    values = oedometer_specimen(w, gs, saturation)
    tests.append((specimen_row, "SWELLPRESS", values, None, SWELLING_PRESSURE, []))
    return tests


def cong():
    headings = [
        *SPECIMEN_HEADINGS,
        ("CONG_TYPE", "PA", ""),
        ("CONG_COND", "PA", ""),
        ("CONG_SDIA", "2DP", "in"),
        ("CONG_HIGT", "2DP", "in"),
        ("CONG_MCI", "X", "%"),
        ("CONG_MCF", "X", "%"),
        ("CONG_BDEN", "1DP", "pcf"),
        ("CONG_DDEN", "1DP", "pcf"),
        ("CONG_PDEN", "XN", "Mg/m3"),
        ("CONG_SATR", "0DP", "%"),
        ("CONG_SPRS", "2SF", "psf"),
        ("CONG_IVR", "3DP", ""),
        ("CONG_CORR", "YN", ""),
    ]
    rows = []
    for specimen_row, kind, values, final, swelling, _ in oedometer_tests():
        w, gs, bulk, dry, saturation, e0 = values
        rows.append(
            [
                *specimen_row,
                kind,
                "UNDISTURBED",
                2.50,
                0.75,
                w,
                final,
                bulk,
                dry,
                gs,
                saturation,
                swelling,
                e0,
                "Y",
            ]
        )
    return group("CONG", headings, rows)


def cons():
    headings = [
        *SPECIMEN_HEADINGS,
        ("CONS_INCN", "X", ""),
        ("CONS_IVR", "3DP", ""),
        ("CONS_INCF", "0DP", "psf"),
        ("CONS_INCE", "3DP", ""),
        ("CONS_INMV", "2SF", "ft2/kip"),
        ("CONS_CVRT", "2SF", "ft2/yr"),
        ("CONS_CVLG", "2SF", "ft2/yr"),
    ]
    rows = [
        [*specimen_row, str(i), start, stress, end, mv, cv_root, cv_log]
        for specimen_row, *_, curve in oedometer_tests()
        for i, (stress, start, end, mv, cv_root, cv_log) in enumerate(curve, 1)
    ]
    return group("CONS", headings, rows)


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


# --- Readings curves (M16) -----------------------------------------------------------

# Readings during shearing in user-defined groups (M16, datasets.md §6.15 to
# §6.17), shaped like a real file's: q, Δu and ε_v each in a group of their own
# (XTDS, XTPW, XTVS under TREG; XUDS for the UU stages under TRIG), read at
# their own strains, and τ and vertical displacement against horizontal
# displacement in XSBS under SHBG. The values are invented and have their own
# seeded sequence. Each q curve rises on a hyperbola q = ε / (a + ε) to the
# stage's TRET_DEVF at TRET_STRN, with scatter below it; Δu rises and flattens
# to TRET_PWPF - TRET_BACK; ε_v contracts to a peak at 0.75 ε_f and turns
# toward dilation, through TRET_STV. Each Δu and ε_v curve has a reading at the
# failure strain equal to the stage's value. The last stage of each test runs
# past failure, and the last stage of the multistage test ends with the unload
# before the specimen comes out (strain falling). Each shear box curve rises to
# SHBT_PEAK and falls to SHBT_RES at its last reading. The hyperbola and the
# exponentials only shape the curves; they aren't methods hangtu offers.
CURVE_STRAIN = ("STRN", "2DP", "%", "Axial strain", False)
CURVE_DEVIATOR = ("DEVF", "0DP", "psf", "Deviator stress", False)
CURVE_EXCESS = ("PWPE", "0DP", "psf", "Excess pore pressure", False)
CURVE_VOLUMETRIC = ("VOLS", "2DP", "%", "Volumetric strain", False)
CURVE_SHEAR_BOX = [
    ("HDIS", "3DP", "in", "Horizontal displacement", False),
    ("SHST", "0DP", "psf", "Shear stress", False),
    ("VDIS", "3DP", "in", "Vertical displacement", False),
]
CURVE_SETTLEMENT = [
    ("TIME", "2DP", "min", "Elapsed time since the load was applied", False),
    ("DISP", "5DP", "in", "Vertical displacement", False),
]
#: Strains (%) of the q readings below failure, and the q readings past it on a
#: test's last stage: (strain beyond ε_f, fraction of q_f).
READING_STRAINS = [0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15]
PAST_FAILURE = [(1.5, 0.98), (3.0, 0.96)]
#: Strains (%) of the Δu and ε_v readings, offset from READING_STRAINS.
OTHER_STRAINS = [0, 0.4, 0.8, 1.3, 1.8, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 9, 11, 13.5]
PAST_FAILURE_OTHER = [1.0, 2.5]  # strain beyond ε_f of the Δu and ε_v readings
UNLOAD = [(0.05, 0.6), (0.10, 0.25), (0.15, 0.02)]  # strain back, fraction of q
DISPLACEMENTS = [0, 0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.1, 0.15, 0.2, 0.25]
DISPLACEMENTS += [0.3, 0.35, 0.4]  # in


def records(g):
    """A group's rows as dicts by heading."""
    names = [h for h, _, _ in g["headings"]]
    return [dict(zip(names, row, strict=True)) for row in g["rows"]]


def specimen_key(row):
    return tuple(row[h] for h, _, _ in TRIAXIAL_SPECIMEN_HEADINGS)


def triaxial_curves(stages, draw):
    """Each stage's q, Δu and ε_v readings: three lists of (key, stage, rows)."""
    q_rows, excess_rows, volumetric_rows = [], [], []
    keys = [specimen_key(s) for s in stages]
    for i, stage in enumerate(stages):
        key, tesn = keys[i], stage["tesn"]
        last = key not in keys[i + 1 :]
        multistage = keys.count(key) > 1
        strain_f, q_f = stage["strain"], stage["deviator"]
        a = strain_f / 10

        def q(strain, strain_f=strain_f, q_f=q_f, a=a):
            return q_f * (strain / (a + strain)) / (strain_f / (a + strain_f))

        q_curve = [
            [s, round(min(q(s) * (1 + draw.gauss(0, 0.015)), 0.99 * q_f))]
            for s in READING_STRAINS
            if s < strain_f
        ]
        q_curve.append([strain_f, q_f])
        if last:
            for extra, fraction in PAST_FAILURE:
                value = q_f * fraction * (1 + draw.gauss(0, 0.005))
                q_curve.append([strain_f + extra, round(min(value, 0.995 * q_f))])
        if last and multistage:
            end_strain, end_q = q_curve[-1]
            for back, fraction in UNLOAD:
                q_curve.append([round(end_strain - back, 2), round(end_q * fraction)])
        q_rows.append((key, tesn, q_curve))
        others = [s for s in OTHER_STRAINS if s < strain_f] + [strain_f]
        if last:
            others += [strain_f + extra for extra in PAST_FAILURE_OTHER]
        if stage["type"] == "CU":
            excess_f = stage["excess"]
            b = strain_f / 4

            def excess(strain, excess_f=excess_f, b=b, strain_f=strain_f):
                rise = 1 - math.exp(-strain / b)
                return excess_f * rise / (1 - math.exp(-strain_f / b))

            curve = [
                [
                    s,
                    excess_f
                    if s == strain_f
                    else round(excess(s) * (1 + draw.gauss(0, 0.02))),
                ]
                for s in others
            ]
            excess_rows.append((key, tesn, curve))
        elif stage["type"] in ("CD", "CDM"):
            c2 = 2 * stage["volumetric"] / strain_f**2

            def volumetric(strain, c2=c2, strain_f=strain_f):
                return 1.5 * strain_f * c2 * strain - c2 * strain**2

            curve = [
                [
                    s,
                    stage["volumetric"]
                    if s == strain_f
                    else round(volumetric(s) + draw.gauss(0, 0.02) * (s > 0), 2),
                ]
                for s in others
            ]
            if last and multistage:
                end_strain, end_value = curve[-1]
                curve.append([round(end_strain - 0.10, 2), round(end_value - 0.03, 2)])
            volumetric_rows.append((key, tesn, curve))
    return q_rows, excess_rows, volumetric_rows


def triaxial_stages():
    """TRET's stages and TRIT's, each a dict of the values the curves need."""
    types = {specimen_key(r): r["TREG_TYPE"] for r in records(treg())}
    tret_stages = [
        {
            **r,
            "tesn": r["TRET_TESN"],
            "type": types[specimen_key(r)],
            "strain": r["TRET_STRN"],
            "deviator": r["TRET_DEVF"],
            "excess": r["TRET_PWPF"] - r["TRET_BACK"],
            "volumetric": r["TRET_STV"],
        }
        for r in records(tret_rows())
    ]
    trit_stages = [
        {
            **r,
            "tesn": r["TRIT_TESN"],
            "type": "UU",
            "strain": r["TRIT_STRN"],
            "deviator": r["TRIT_DEVF"],
        }
        for r in records(trit())
    ]
    return tret_stages, trit_stages


def shear_box_curves(draw):
    """Each SHBT stage's (key, stage, [[δh, τ, δv], ...]), in in and psf.

    Recompacted specimens and rock joints dilate after a little contraction;
    undisturbed clay contracts throughout.
    """
    conditions = {
        specimen_key(r): (r["SHBG_COND"], r["SHBG_ENCA"]) for r in records(shbg())
    }
    found = []
    for stage in records(shbt()):
        key = specimen_key(stage)
        condition, encapsulation = conditions[key]
        dilates = condition == "RECOMPACTED" or encapsulation is not None
        peak, residual = stage["SHBT_PEAK"], stage["SHBT_RES"]
        at_peak = round(draw.uniform(0.06, 0.12), 3)
        a = at_peak / 5
        points = sorted({*DISPLACEMENTS, at_peak})
        curve = []
        for d in points:
            if d == at_peak:
                tau = peak
            elif d == points[-1]:
                tau = residual
            elif d < at_peak:
                rise = (d / (a + d)) / (at_peak / (a + at_peak))
                tau = min(peak * rise * (1 + draw.gauss(0, 0.02)), 0.99 * peak)
            else:
                fall = math.exp(-(d - at_peak) / 0.08)
                tau = residual + (peak - residual) * fall
                tau = min(tau * (1 + draw.gauss(0, 0.01)), 0.99 * peak)
            if dilates:
                vertical = (
                    -0.002 * min(d, 0.03) / 0.03 + 0.012 * max(0, d - 0.03) / 0.37
                )
            else:
                vertical = -0.010 * (1 - math.exp(-d / 0.08))
            if d > 0:
                vertical += draw.gauss(0, 0.0003)
            curve.append([d, round(tau), round(vertical, 3)])
        found.append((key, stage["SHBT_TESN"], curve))
    return found


# Settlement-time readings (M19 c2): each oedometer test's loading increments
# that have a lab c_v (2 to 6 and 11), under CONG at the standard's reading
# times, as a dial gauge reads them: generated from Terzaghi's series as the
# test files' XCOT is (an immediate compression, rho U(T), a secondary
# compression per log cycle after t1, the time at T = 1), each increment's
# total movement its height change from the void ratios as written, then
# scatter of up to 0.002 mm and the reading written to 0.00001 in. The
# generating c_v is near the lab's root time value, except B-5-U2's increment
# 3, an early recompression increment at 20 m²/yr: too fast for these times,
# so log time finds fewer than three 1:4 pairs before the inflexion and root
# time fewer than three readings in the first half of the movement (the c2
# spec's AC 3 at c_v 20), and the lab's c_v can't be checked from them.
OEDOMETER_READING_TIMES = [0, 0.1, 0.25, 0.5, 1, 2, 4, 8, 15, 30, 60, 120, 240]
OEDOMETER_READING_TIMES += [480, 1440]
OEDOMETER_READING_INCREMENTS = (2, 3, 4, 5, 6, 11)
#: The fast increment, (specimen, increment), and its generating c_v (m²/yr).
FAST_INCREMENT = (("B-5-U2", 3), 20.0)
SQUARE_FEET_PER_SQUARE_METRE = 10.7639104
MM_PER_INCH = 25.4


def settlement_readings(cv, start, end, e0, height, draw):
    """Displacements (in, from the specimen's start) at the reading times.

    ``cv`` in m²/yr, ``height`` H0 in mm, ``start``, ``end`` and ``e0`` the
    increment's and the specimen's void ratios.
    """
    h1 = height * (1 + start) / (1 + e0)
    h2 = height * (1 + end) / (1 + e0)
    total = h1 - h2
    immediate = total * draw.uniform(0.05, 0.15)
    secondary = total * draw.uniform(0.02, 0.05)  # per log cycle of time
    drainage = (h1 + h2) / 4  # half the average height: double drainage
    rate = cv * 1.0e6 / 525960  # mm²/min
    t1 = drainage**2 / rate
    last = OEDOMETER_READING_TIMES[-1]
    rho = total - immediate - secondary * math.log10(1 + last / t1)
    values = []
    for t in OEDOMETER_READING_TIMES:
        y = 0.0
        if t > 0:
            y = immediate + rho * _files.terzaghi_degree(rate * t / drainage**2)
            y += secondary * math.log10(1 + t / t1) + draw.uniform(-0.002, 0.002)
        values.append(round((height - h1 + y) / MM_PER_INCH, 5))
    return values


def settlement_curves():
    """Each loading increment's (key, increment, [[t, δv], ...]), in min and in."""
    draw = random.Random(2033)
    found = []
    for specimen_row, kind, values, _, _, curve in oedometer_tests():
        if kind != "OEDOMETER":
            continue
        e0 = values[-1]
        height = 0.75 * MM_PER_INCH  # CONG_HIGT
        for incn in OEDOMETER_READING_INCREMENTS:
            _, start, end, _, cv_root, _ = curve[incn - 1]
            cv = cv_root / SQUARE_FEET_PER_SQUARE_METRE * draw.uniform(0.8, 1.0)
            if (specimen_row[4], incn) == FAST_INCREMENT[0]:
                cv = FAST_INCREMENT[1]
            readings = settlement_readings(cv, start, end, e0, height, draw)
            found.append(
                (
                    specimen_row,
                    str(incn),
                    [
                        list(r)
                        for r in zip(OEDOMETER_READING_TIMES, readings, strict=True)
                    ],
                )
            )
    return found


def curve_groups():
    """The curve groups and their DICT group, after every other group."""
    draw = random.Random(2031)
    tret_stages, trit_stages = triaxial_stages()
    q_rows, excess_rows, volumetric_rows = triaxial_curves(tret_stages, draw)
    uu_rows, _, _ = triaxial_curves(trit_stages, draw)
    key = TRIAXIAL_SPECIMEN_HEADINGS
    curves = [
        _files.curve_group("XTDS", [CURVE_STRAIN, CURVE_DEVIATOR], q_rows, key, []),
        _files.curve_group("XTPW", [CURVE_STRAIN, CURVE_EXCESS], excess_rows, key, []),
        _files.curve_group(
            "XTVS", [CURVE_STRAIN, CURVE_VOLUMETRIC], volumetric_rows, key, []
        ),
        _files.curve_group("XUDS", [CURVE_STRAIN, CURVE_DEVIATOR], uu_rows, key, []),
        _files.curve_group("XSBS", CURVE_SHEAR_BOX, shear_box_curves(draw), key, []),
        _files.curve_group(
            "XCOT", CURVE_SETTLEMENT, settlement_curves(), SPECIMEN_HEADINGS, []
        ),
    ]
    return [*curves, _files.dict_group(curves=curves, xppt=False)]


READINGS_MAP = """\
group,dataset,heading,column
XTDS,triaxial_readings,XTDS_TESN,test_stage
XTDS,triaxial_readings,XTDS_STRN,axial_strain
XTDS,triaxial_readings,XTDS_DEVF,deviator_stress
XTPW,triaxial_readings,XTPW_TESN,test_stage
XTPW,triaxial_readings,XTPW_STRN,axial_strain
XTPW,triaxial_readings,XTPW_PWPE,excess_pore_pressure
XTVS,triaxial_readings,XTVS_TESN,test_stage
XTVS,triaxial_readings,XTVS_STRN,axial_strain
XTVS,triaxial_readings,XTVS_VOLS,volumetric_strain
XUDS,triaxial_readings,XUDS_TESN,test_stage
XUDS,triaxial_readings,XUDS_STRN,axial_strain
XUDS,triaxial_readings,XUDS_DEVF,deviator_stress
XSBS,shear_box_readings,XSBS_TESN,test_stage
XSBS,shear_box_readings,XSBS_HDIS,horizontal_displacement
XSBS,shear_box_readings,XSBS_SHST,shear_stress
XSBS,shear_box_readings,XSBS_VDIS,vertical_displacement
XCOT,oedometer_readings,XCOT_TESN,test_stage
XCOT,oedometer_readings,XCOT_TIME,elapsed_time
XCOT,oedometer_readings,XCOT_DISP,vertical_displacement
"""


# --- Writing --------------------------------------------------------------------------


def site_groups():
    llpl, lnmc = atterberg()
    grag, grat = grading()
    groups = [loca(), geol(), samp(), ispt(), llpl, lnmc, grag, grat, ptst(), fghg()]
    undrained = [trig(), trit(), lvan(), lpen(), ivan()]
    shear_box = [shbg(), shbt()]
    oedometer = [cong(), cons()]
    return [
        *groups,
        lden(lnmc),
        lpdn(),
        treg(),
        tret(),
        *undrained,
        *shear_box,
        *oedometer,
        *curve_groups(),  # last, so nothing written before moves
    ]


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
            ("oedometer", p.oedometer()),
        ):
            sample = dataset["sample_reference"]
            named = sample + "-" + dataset["specimen_reference"].astype(str)
            dataset = dataset.assign(specimen_id=named.where(sample.notna()))
            if name == "strength":
                # The template has no undrained_shear_strength_basis, so an s_u
                # the dataset worked out (q_f / 2) would read as a second input
                # beside q_f. Only an s_u as reported is an input.
                derived = dataset["undrained_shear_strength_basis"] != "as_reported"
                su = dataset["undrained_shear_strength"].mask(derived)
                dataset = dataset.assign(undrained_shear_strength=su)
            dataset[list(ht.template(name).columns)].to_csv(
                out / f"{name}.csv",
                index=False,
                float_format="%.6g",
                lineterminator="\n",
            )
        # The readings curves (M16), read through the example's readings map.
        p.set_readings_map(out / "readings_map.csv")
        write_readings(out, p)
    write_rock_triaxial(out)


def write_readings(out, p):
    """Write ``triaxial_readings.csv``, ``shear_box_readings.csv`` and
    ``oedometer_readings.csv`` from the project's readings datasets, in psf, in
    and min, in their templates' columns.

    A specimen is named by its sample and reference, as the other CSVs name
    them. The triaxial file keeps the lab's mark, as a lab's CSV would: each
    stage's q reading at its failure strain, so the readings run without a
    failure criterion.
    """
    stages = p.triaxial()
    failure = {
        (specimen, stage): strain
        for specimen, stage, strain in zip(
            stages["specimen_id"],
            stages["test_stage"],
            stages["axial_strain_at_failure"],
            strict=True,
        )
    }
    for name in ("triaxial_readings", "shear_box_readings", "oedometer_readings"):
        dataset = getattr(p, name)()
        if name == "triaxial_readings":
            at_failure = [
                failure[(specimen, stage)] == strain and q == q
                for specimen, stage, strain, q in zip(
                    dataset["specimen_id"],
                    dataset["test_stage"],
                    dataset["axial_strain"],
                    dataset["deviator_stress"],
                    strict=True,
                )
            ]
            dataset = dataset.assign(reported_failure_reading=at_failure)
        named = dataset["sample_reference"] + "-" + dataset["specimen_reference"]
        dataset = dataset.assign(specimen_id=named)
        dataset[list(ht.template(name).columns)].to_csv(
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
    (out / "readings_map.csv").write_text(READINGS_MAP, encoding="utf-8", newline="")
    write_csvs(out)


if __name__ == "__main__":
    main()
