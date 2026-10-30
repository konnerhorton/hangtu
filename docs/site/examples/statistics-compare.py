import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
# The judgments file holds the significance level, as every judgment.
p.set_judgments(ht.examples.path("judgments.yaml"))

spt = ht.analysis.spt(p.spt())
alluvium = spt[spt["geology_unit"] == "Alluvium"].copy()

# One parameter set for the Alluvium, or two? Its holes split into the south
# of the site (B-1 to B-3) and the north (B-4 to B-6).
south = alluvium["loca_id"].isin(["B-1", "B-2", "B-3"])
alluvium["area"] = south.map({True: "South", False: "North"})
print(ht.stats.compare(alluvium, value="spt_n60", by="area", groups=("South", "North")))

# Does it change from west to east? Three bands of two holes each, in that
# order: overall, and every pair.
bands = {"B-1": "West", "B-4": "West", "B-2": "Middle", "B-5": "Middle"}
band = alluvium["loca_id"].map(bands).fillna("East")
alluvium["band"] = pd.Categorical(band, categories=["West", "Middle", "East"])
print()
print(ht.stats.compare_groups(alluvium, value="spt_n60", by="band"))
