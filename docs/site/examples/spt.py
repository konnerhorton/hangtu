import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
spt = ht.analysis.spt(spt)  # refusal, N60 and capped N

coarse = spt[spt["soil_class"] == "coarse"]
print(ht.analysis.spt_class(coarse, n="spt_n60").value_counts(sort=False))
