import hangtu as ht

p = ht.Project.from_ags(
    ht.examples.path("site.ags"),
    db="site.sqlite",
    display_units="US",
    vertical_datum="NAVD88",
)
p.set_geology_map(ht.examples.path("strata.csv"))
print(p.qc())

fig, ax = ht.plot.spt_profile(p.spt(), n="spt_n60")
fig.savefig("ags-to-plot.png")
