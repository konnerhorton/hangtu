import pandas as pd

import hangtu as ht

# Plasticity index and clay content (finer than 0.002 mm, from the hydrometer
# stage) as typed in from a lab report. fraction_system says the clay content
# is the ISO 14688 clay, finer than 0.002 mm.
lab = pd.DataFrame(
    {
        "sample_reference": ["B1-U2", "B2-U2", "B3-U2"],
        "plasticity_index": [31, 26, 17],
        "clay_content": [27.4, 30.4, 27.9],
        "fraction_system": "iso14688",
    }
)

lab = ht.analysis.clay_activity(lab)
print(lab.round(2).to_string(index=False))
