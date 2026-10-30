import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
spt = ht.analysis.spt(spt)

fig, axs, result = ht.plot.distribution_fit(
    spt, value="spt_n60", by="geology_unit", group="Terrace"
)
fig.savefig("distribution-fit.png")
