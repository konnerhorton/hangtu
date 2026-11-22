import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_readings_map(ht.examples.path("readings_map.csv"))
readings = p.oedometer_readings()

# B-5's fourth increment moves 0.003 in, so the first reading's scatter
# tilts the root time early line. Fit it from 0.25 min instead, and say why.
b5 = readings.loc[readings["sample_reference"] == "B-5-U2", "specimen_id"].iloc[0]
overrides = ht.set_units(
    pd.DataFrame(
        {
            "specimen_id": [b5],
            "test_stage": ["4"],
            "consolidation_method": ["root_time"],
            "curve_portion": ["early"],
            "elapsed_time_start": [0.25],
            "elapsed_time_end": [4.0],
            "override_reason": ["0.1 min reading off the early line"],
        }
    ),
    {"elapsed_time_start": "min", "elapsed_time_end": "min"},
)
fig, axs = ht.plot.consolidation_time_curves(
    readings,
    specimen="B-5-U2-C1",
    increments=["4"],
    overrides=overrides,
    display_units="US",
)
fig.savefig("consolidation-time-curves-override.png")
