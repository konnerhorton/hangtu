import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
sheet = ht.Sheet("letter", layout=(1, 2), title="SPT, example site")
ht.plot.spt_profile(spt, n="spt_n60", ax=sheet[0])
ht.plot.spt_histogram(spt[spt["soil_class"] == "coarse"], n="spt_n60", ax=sheet[1])
sheet.save("sheet.png", dpi=100)
