import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
print(ht.units_of(spt))

fig, ax = ht.plot.spt_profile(spt, n="spt_n60", display_units="SI")
fig.savefig("units.png")
