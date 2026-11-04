import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
joints = p.shear_box(geology="Sandstone")

# The file stores psf; show the joints in MPa.
with ht.settings.override(display_overrides={"stress": "MPa"}):
    fig, ax, fit = ht.plot.shear_box_envelope(joints, display_units="SI")
fig.savefig("discontinuity-shear-strength.png")
print(fit)
