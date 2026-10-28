import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# Each row is one specimen: its bulk unit weight and water content, and the
# particle density of its sample where one was tested. The other rows take
# Gs from the judgments file, by geology unit.
rows = ht.analysis.phase_relations(p.density())

columns = [
    "loca_id",
    "depth",
    "specific_gravity",
    "specific_gravity_source",
    "void_ratio",
    "degree_of_saturation",
]
print(rows[columns].head(6).round(2).to_string(index=False))

fig, ax = ht.plot.profile(rows, "void_ratio", preset="void_ratio", vs="depth")
fig.savefig("phase-relations.png")
