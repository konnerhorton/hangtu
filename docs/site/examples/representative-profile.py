import numpy as np
import pandas as pd

import hangtu as ht

# Undrained shear strength from lab tests in three clay units, made up with
# the scatter a site gives: lognormal about each unit's mean or trend (CoV
# about 0.3, skewed high), at uneven depths in clusters, from three holes.
rng = np.random.default_rng(18)


def unit(name, depths, center):
    spread = np.sqrt(np.log(1 + 0.3**2))
    scatter = rng.lognormal(-(spread**2) / 2, spread, len(depths))
    return pd.DataFrame(
        {
            "loca_id": rng.choice(["BH1", "BH2", "BH3"], len(depths)),
            "depth": depths,
            "geology_unit": name,
            "undrained_shear_strength": center(depths) * scatter,
        }
    )


upper = np.concatenate([rng.uniform(1.5, 4, 6), rng.uniform(5.5, 7, 4)])
upper = np.sort(np.concatenate([upper, rng.uniform(9, 11.5, 5)]))
lower = np.sort(np.concatenate([rng.uniform(13, 16, 5), rng.uniform(18, 24, 6)]))
strength = pd.concat(
    [
        unit("Crust", np.array([0.6, 1.1]), lambda z: 60.0),
        unit("Upper clay", upper, lambda z: 12 + 4.0 * z),
        unit("Lower clay", lower, lambda z: 40 + 3.0 * z),
    ],
    ignore_index=True,
)
# One vane test past the device's limit, one below its resolution.
strength["qualifier"] = ""
flagged = ["undrained_shear_strength", "qualifier"]
rows = strength.groupby("geology_unit").groups
strength.loc[rows["Lower clay"][4], flagged] = [150.0, ">"]
strength.loc[rows["Upper clay"][1], flagged] = [15.0, "<"]
strength["ground_level"] = 100.0
strength = ht.set_units(
    strength, {"depth": "m", "ground_level": "m", "undrained_shear_strength": "kPa"}
)

# EC7's characteristic value per unit, constant: the mean at 95 % confidence
# (Type A), V_X from the data (Case 2), on the low side.
fig, ax, result = ht.plot.representative_profile(
    strength,
    value="undrained_shear_strength",
    by="geology_unit",
    method="characteristic",
    estimate="mean",
    side="low",
    distribution="normal",
    display_units="US",
)
fig.savefig("representative-profile.png")
