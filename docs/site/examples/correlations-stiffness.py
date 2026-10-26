import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# B-4's log has a gap from 9 to 10 ft (QC G002), so it is left out here.
holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())
spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")
# A refusal gives no estimate, so pass the tests that reached full penetration.
tested = spt[~spt["spt_refusal"]]

# E is for the sand. The source's soil row is your reading of the log, given
# by geology unit; the logs call the Terrace "SAND with gravel (SP)", so the
# USCS check reads that symbol, which you supply.
sand = tested[tested["geology_unit"] == "Terrace"].assign(uscs_symbol="SP")
modulus = pd.concat(
    [
        ht.analysis.correlations.drained_youngs_modulus_aashto_2004(
            sand, soil={"Terrace": "coarse_sands"}, uscs="proposed"
        ),
        ht.analysis.correlations.drained_youngs_modulus_kulhawy_mayne_1990(
            sand, soil={"Terrace": "clean_normally_consolidated_sands"}, uscs="proposed"
        ),
    ],
    ignore_index=True,
)

# Vs is for all soils, so both run on the whole profile. Ohta & Goto's data
# start at N60 = 2.23, and the two softest tests are below it.
firm = tested[tested["spt_n60"] >= 2.23]
velocity = pd.concat(
    [
        ht.analysis.correlations.shear_wave_velocity_imai_tonouchi_1982(firm),
        ht.analysis.correlations.shear_wave_velocity_ohta_goto_1978(firm),
    ],
    ignore_index=True,
)

columns = ["depth", "spt_n60", "spt_n1_60", "drained_youngs_modulus"]
rows = modulus[modulus["loca_id"] == "B-5"]
print(rows[[*columns, "correlation_soil"]].round(1).to_string(index=False))
print("E in", modulus.attrs["units"]["drained_youngs_modulus"])
print("Vs in", velocity.attrs["units"]["shear_wave_velocity"])

sheet = ht.Sheet("tabloid", layout=(1, 2), title="Stiffness from SPT, example site")
ht.plot.profile(
    modulus, "drained_youngs_modulus", vs="depth", color_by="correlation_name",
    ax=sheet[0],
)  # fmt: skip
ht.plot.profile(
    velocity, "shear_wave_velocity", vs="depth", color_by="correlation_name",
    ax=sheet[1],
)  # fmt: skip
sheet.save("correlations-stiffness.png", dpi=100)
