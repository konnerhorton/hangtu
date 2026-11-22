import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_readings_map(ht.examples.path("readings_map.csv"))
readings = p.oedometer_readings()

# Three loading increments of B-4's specimen, either side of its σ′p.
fig, axs = ht.plot.consolidation_time_curves(
    readings,
    specimen="B-4-U1-C1",
    increments=["3", "4", "5"],
    display_units="US",
)
fig.savefig("consolidation-time-curves.png")

# The numbers behind the panels, every increment with readings.
rows = ht.analysis.consolidation_coefficient_from_readings(readings, display_units="US")
columns = [
    "specimen_id",
    "test_stage",
    "time_to_90_percent_consolidation",
    "coefficient_of_consolidation_root_time",
    "reported_coefficient_of_consolidation_root_time",
    "time_to_50_percent_consolidation",
    "coefficient_of_consolidation_log_time",
    "reported_coefficient_of_consolidation_log_time",
]
named = rows["sample_reference"] + "-" + rows["specimen_reference"]
with pd.option_context("display.width", 200, "display.precision", 3):
    print(rows.assign(specimen_id=named)[columns].to_string(index=False))
print(rows.attrs["units"]["coefficient_of_consolidation_root_time"])
