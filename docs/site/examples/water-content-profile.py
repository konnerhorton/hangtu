import hangtu as ht

lengths = ["ground_level", "depth", "elevation", "depth_top", "depth_base"]
atterberg = ht.read_csv(
    ht.examples.path("atterberg.csv"), units=dict.fromkeys(lengths, "ft")
)

fig, ax = ht.plot.water_content_profile(atterberg)
fig.savefig("water-content-profile.png")
