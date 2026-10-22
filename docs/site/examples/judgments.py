import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# B-4's log has a gap from 9 to 10 ft (QC G002), so it is left out here.
holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())

columns = ["loca_id", "depth", "geology_unit", "effective_vertical_stress"]
print(spt[columns].head(6).round(1).to_string(index=False))
print(spt.attrs["judgments"]["water_level"]["values"]["B-1"])

fig, ax = ht.plot.profile(spt, "effective_vertical_stress", vs="depth")
fig.savefig("judgments.png")
