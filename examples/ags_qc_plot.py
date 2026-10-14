"""AGS to QC to plot: from a data file to checked figures.

Reads the example AGS4 file into a project database, checks it, and draws
the same four plots as csv_to_plot.py from hangtu's ready-made datasets.

Run this script from any folder. It writes site.sqlite, qc_report.csv (with
the rules it used in qc_report_rules.csv) and ags_example.pdf there.
"""

import hangtu as ht

# 1. Read the AGS file into a project database. Values are converted to the
#    display units on the way out, here US. The vertical datum goes on the
#    elevation labels.
p = ht.Project.from_ags(
    ht.examples.path("site.ags"),
    db="site.sqlite",
    overwrite=True,
    display_units="US",
    vertical_datum="NAVD88",
)

# 2. Map the file's geology codes (GEOL_GEOL) to the units you report on,
#    with their order and colors.
p.set_geology_map(ht.examples.path("strata.csv"))

# 3. Check the data. The summary counts findings by rule; the CSV report has
#    each one with its hole, depth and line in the file.
report = p.qc()
print(report)
report.to_csv("qc_report.csv")

# 4. The datasets: one row per test, with depth, elevation and geology unit
#    joined on, ready for the plots.
spt = p.spt()
permeability = p.permeability()
atterberg = p.atterberg()

# 5. The same four plots as from CSV, on a tabloid sheet.
sheet = ht.Sheet("tabloid", layout=(2, 2), title="Riverside example site, from AGS")
ht.plot.spt_profile(spt, n="spt_n60", ax=sheet[0, 0])
ht.plot.spt_histogram(p.spt(geology=["Terrace"]), n="spt_n60", ax=sheet[0, 1])
ht.plot.profile(
    permeability,
    "hydraulic_conductivity",
    preset="hydraulic_conductivity",
    ax=sheet[1, 0],
)
ht.plot.geology_unit_comparison(atterberg, "plasticity_index", ax=sheet[1, 1])

sheet.save("ags_example.pdf")
print("Wrote qc_report.csv, qc_report_rules.csv and ags_example.pdf")
