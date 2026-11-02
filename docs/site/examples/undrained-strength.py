import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
su = p.undrained_strength(display_units="US")

print(
    su[
        [
            "loca_id",
            "depth",
            "test_type",
            "undrained_shear_strength",
            "undrained_shear_strength_basis",
            "strength_sensitivity",
        ]
    ]
)
fig, ax = ht.plot.profile(su, "undrained_shear_strength", color_by="test_type")
fig.savefig("undrained-strength.png")
