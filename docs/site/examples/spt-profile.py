import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)

fig, ax = ht.plot.spt_profile(spt, n="spt_n60")
fig.savefig("spt-profile.png")
