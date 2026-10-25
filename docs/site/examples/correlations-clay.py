import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# B-4's log has a gap from 9 to 10 ft (QC G002), so it is left out here.
holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())

# Stroud reads PI. Few tests are at an SPT depth, so PI is a judgment by unit:
# look at the Atterberg tests, then choose.
print(ht.analysis.summary_by(p.atterberg(), "plasticity_index").to_string(index=False))
clay = spt[spt["geology_unit"] == "Alluvium"]
clay = ht.analysis.add_judgment(clay, "plasticity_index", value={"Alluvium": 23.5})

estimates = pd.concat(
    [
        ht.analysis.correlations.undrained_shear_strength_stroud_1974(clay),
        ht.analysis.correlations.undrained_shear_strength_terzaghi_peck_1967(clay),
    ],
    ignore_index=True,
)

columns = ["depth", "spt_n", "spt_n60", "undrained_shear_strength_lower"]
columns += ["undrained_shear_strength_upper", "correlation_name"]
rows = estimates[estimates["loca_id"] == "B-3"]
print()
print(rows[columns].round(1).to_string(index=False))
print("s_u in", estimates.attrs["units"]["undrained_shear_strength_lower"])

# One hole, so each depth has one band per correlation, drawn side by side.
fig, ax = ht.plot.profile(
    rows,
    "undrained_shear_strength",
    vs="depth",
    color_by="correlation_name",
)
fig.savefig("correlations-clay.png")
