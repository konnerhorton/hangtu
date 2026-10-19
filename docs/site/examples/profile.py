import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "depth_top": "ft", "depth_base": "ft"}
permeability = ht.read_csv(
    ht.examples.path("permeability.csv"),
    units={**lengths, "elevation": "ft", "hydraulic_conductivity": "cm/s"},
)
fig, ax = ht.plot.profile(
    permeability, "hydraulic_conductivity", preset="hydraulic_conductivity"
)
fig.savefig("profile.png")
