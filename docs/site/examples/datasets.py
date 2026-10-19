import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))

atterberg = p.atterberg(geology=["Alluvium"], depth=(0, 30))
print(atterberg[["loca_id", "depth", "elevation", "geology_unit", "liquid_limit"]])
