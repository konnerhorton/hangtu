import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# B-4's log has a gap from 9 to 10 ft (QC G002), so it is left out here.
holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())
spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")

# The φ′ correlations are for sands: pass the rows they apply to. Here, the
# medium dense upper part of the Terrace sand.
sand = spt[(spt["geology_unit"] == "Terrace") & (spt["spt_n60"] <= 40)]
estimates = pd.concat(
    [
        ht.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996(sand),
        ht.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990(sand),
    ],
    ignore_index=True,
)

columns = ["loca_id", "depth", "spt_n60", "spt_n1_60", "effective_friction_angle"]
rows = estimates[estimates["loca_id"] == "B-5"]
print(rows[[*columns, "correlation_name"]].round(1).to_string(index=False))

fig, ax = ht.plot.profile(
    estimates,
    "effective_friction_angle",
    vs="depth",
    color_by="correlation_name",
    preset="effective_friction_angle",
)
fig.savefig("correlations.png")
