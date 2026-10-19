import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
coarse = spt[spt["soil_class"] == "coarse"]  # the cohesionless table fits these

fig, ax = ht.plot.spt_histogram(coarse, n="spt_n60", table="cohesionless")
fig.savefig("spt-histogram.png")
