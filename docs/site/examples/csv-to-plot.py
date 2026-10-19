import hangtu as ht

ht.template("spt").to_csv("my_spt.csv", index=False)  # an empty file to fill in

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"),  # or your own file
    units={**lengths, "spt_penetration": "in"},
)
fig, ax = ht.plot.spt_histogram(spt[spt["soil_class"] == "coarse"], n="spt_n60")
fig.savefig("csv-to-plot.png")
