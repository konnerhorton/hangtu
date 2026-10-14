"""CSV to plot: hangtu on your own data files.

Reads the example SPT, Atterberg and permeability files, which are laid out
like hangtu's CSV templates, and draws four plots on one tabloid sheet. To
start a file of your own, save an empty template and fill it in:

    ht.template("spt").to_csv("spt.csv", index=False)

Run this script from any folder. It writes csv_example.pdf there.
"""

import hangtu as ht

# 1. Read the files and declare their units. hangtu never guesses a unit, so
#    each column that has one is declared here. Columns in percent or counts
#    (spt_n, liquid_limit) need none.
lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
intervals = {**lengths, "depth_top": "ft", "depth_base": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
atterberg = ht.read_csv(ht.examples.path("atterberg.csv"), units=intervals)
permeability = ht.read_csv(
    ht.examples.path("permeability.csv"),
    units={**intervals, "hydraulic_conductivity": "cm/s"},
)

# 2. Colors for the geology units, used by every plot in this session. (A
#    project's geology map does this for AGS data.)
ht.settings.palette = {"Fill": "#9e9e9e", "Alluvium": "#5b8db8", "Terrace": "#e0b040"}

# 3. A tabloid sheet with four panels, two by two.
sheet = ht.Sheet("tabloid", layout=(2, 2), title="Riverside example site, from CSV")

# 4. SPT N60 with elevation (P02). N60 is worked out from each test's
#    energy_ratio; refusals are drawn at the cap and counted.
ht.plot.spt_profile(spt, n="spt_n60", ax=sheet[0, 0])

# 5. SPT N60 classes in the coarse soil (P03). The cohesionless table only
#    fits sand and gravel, so the clay is left out.
coarse = spt[spt["soil_class"] == "coarse"]
ht.plot.spt_histogram(coarse, n="spt_n60", ax=sheet[0, 1])

# 6. Hydraulic conductivity on a log axis (P01). Lab tests are points; field
#    tests are bars over the zone they tested.
ht.plot.profile(
    permeability,
    "hydraulic_conductivity",
    preset="hydraulic_conductivity",
    ax=sheet[1, 0],
)

# 7. Plasticity index in each geology unit (P07).
ht.plot.geology_unit_comparison(atterberg, "plasticity_index", ax=sheet[1, 1])

sheet.save("csv_example.pdf")
print("Wrote csv_example.pdf")
