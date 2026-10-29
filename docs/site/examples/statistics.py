import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))

# N60 by geology unit. Refusals are summarized at their N60 and counted.
spt = ht.analysis.spt(p.spt())
print(ht.stats.describe(spt, value="spt_n60", by="geology_unit"))

# Lab and field permeability tests are different sources: describe() won't
# pool them unless asked.
permeability = p.permeability()
try:
    ht.stats.describe(permeability, value="hydraulic_conductivity", log=True)
except ht.HangtuError as error:
    print()
    print(error)

# k spans orders of magnitude, so summarize it on a log scale, by unit.
result = ht.stats.describe(
    permeability, value="hydraulic_conductivity", by="geology_unit", log=True
)
print()
print(result)

# The same numbers as a table, for a report.
columns = ["geology_unit", "count", "geometric_mean", "median", "maximum"]
print()
print(result.to_frame()[columns].to_string(index=False))
