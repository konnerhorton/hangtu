import hangtu as ht

lengths = {"ground_level": "ft", "depth": "ft", "elevation": "ft"}
spt = ht.read_csv(
    ht.examples.path("spt.csv"), units={**lengths, "spt_penetration": "in"}
)
spt = ht.analysis.spt(spt)

# Normal, lognormal, gamma and Weibull fitted to N60 in each unit, ranked by
# AICc. The Terrace refusals are fitted as censored, not at their N60.
terrace = spt[spt["geology_unit"] == "Terrace"]
result = ht.stats.fit(terrace, value="spt_n60")
print(result)

# The same numbers as a table, for a report.
columns = ["distribution", "rank", "median", "percentile_5", "delta_aicc"]
print()
print(result.to_frame()[columns].round(2).to_string(index=False))

# The fitted distribution itself, for any quantile.
lognormal = result.distribution("lognormal")
print()
print(f"10th percentile of the lognormal fit: {lognormal.ppf(0.10):.1f}")
