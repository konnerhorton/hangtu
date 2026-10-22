import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))

fig, ax = ht.plot.grain_size(p.grain_size())
fig.savefig("grain-size.png")
