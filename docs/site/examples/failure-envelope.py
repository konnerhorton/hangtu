import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
stages = p.triaxial()

fig, ax, fit = ht.plot.failure_envelope(
    stages, group_by="geology_unit", display_units="US"
)
fig.savefig("failure-envelope.png")
print(fit)
