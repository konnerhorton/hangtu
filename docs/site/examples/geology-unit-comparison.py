import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
atterberg = ht.read_csv(
    ht.examples.path("atterberg.csv"),
    units={**lengths, "depth_top": "ft", "depth_base": "ft"},
)
fig, ax = ht.plot.geology_unit_comparison(atterberg, "plasticity_index")
fig.savefig("geology-unit-comparison.png")
