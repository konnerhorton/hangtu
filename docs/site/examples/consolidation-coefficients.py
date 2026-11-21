import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# σ′v0 at the specimen's depth marks the increments that span it. B-4's log
# has a gap from 9 to 10 ft (QC G002), so its specimen is left out here.
oed = ht.analysis.vertical_stress(
    p.oedometer(holes=["B-5"]), stratigraphy=p.stratigraphy()
)

fig, axs = ht.plot.consolidation_coefficients(oed, display_units="US")
fig.savefig("consolidation-coefficients.png")

increments = ht.analysis.oedometer_increments(oed, display_units="US")
columns = [
    "applied_vertical_stress_at_increment_start",
    "applied_vertical_stress",
    "load_branch",
    "coefficient_of_volume_compressibility",
    "reported_coefficient_of_volume_compressibility",
    "constrained_modulus",
    "hydraulic_conductivity_root_time",
    "spans_effective_vertical_stress",
]
with pd.option_context("display.width", 200, "display.precision", 4):
    print(increments[columns].to_string(index=False))
print(increments.attrs["units"]["constrained_modulus"])
