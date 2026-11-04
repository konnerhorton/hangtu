import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
stages = p.shear_box(geology=["Alluvium", "Terrace"])

fig, ax, fit = ht.plot.shear_box_envelope(
    stages, group_by="geology_unit", display_units="US"
)
fig.savefig("shear-box-envelope.png")
print(fit)
