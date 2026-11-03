import pandas as pd

import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
spt = ht.analysis.spt(spt)

# EC7's characteristic value of N60 per unit: the mean at 95 % confidence
# (Type A), V_X computed from the data (Case 2), on the low side. Every
# judgment is an argument; none has a default.
characteristic = ht.stats.representative(
    spt,
    value="spt_n60",
    by="geology_unit",
    method="characteristic",
    estimate="mean",
    side="low",
    distribution="normal",
)
print(characteristic)

# Another view of the same rows: the 10th percentile of a lognormal fit.
percentile = ht.stats.representative(
    spt,
    value="spt_n60",
    by="geology_unit",
    method="percentile",
    percentile=10,
    side="low",
    distribution="lognormal",
)
columns = ["geology_unit", "value", "count", "geometric_mean"]
print()
print(percentile.to_frame()[columns].round(1).to_string(index=False))

# N60 rises with depth in the Alluvium: a line with depth, the mean at 95 %
# confidence along it.
alluvium = spt[spt["geology_unit"] == "Alluvium"]
trend = ht.stats.representative(
    alluvium,
    value="spt_n60",
    by="geology_unit",
    method="characteristic",
    estimate="mean",
    side="low",
    distribution="normal",
    trend="depth",
)
print()
print(trend)

# Both as design lines on the profile: the trend for the Alluvium, the
# constant values for the Fill and the Terrace.
constant = characteristic.design_lines()
lines = pd.concat(
    [constant[~constant["label"].str.startswith("Alluvium")], trend.design_lines()],
    ignore_index=True,
)
lines.attrs = constant.attrs
fig, ax = ht.plot.profile(spt, "spt_n60", vs="depth", design_lines=lines)
fig.savefig("representative-values.png")
