import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# σ′v0 at the specimen's depth gives OCR and the sample quality. B-4's log has
# a gap from 9 to 10 ft (QC G002), so its specimen is left out here.
oed = ht.analysis.vertical_stress(
    p.oedometer(holes=["B-5"]), stratigraphy=p.stratigraphy()
)

fig, ax, fit = ht.plot.consolidation_curve(oed, display_units="US")
fig.savefig("consolidation-curve.png")
print(fit)
