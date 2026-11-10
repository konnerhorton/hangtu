import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
# The judgments file holds the significance level compare() tests at.
p.set_judgments(ht.examples.path("judgments.yaml"))

# Every test's s_u side by side: UU, laboratory vane (LV), the hand
# penetrometer on the tubes (an s_u, as AGS defines LPEN_PPEN), and the field
# vane in the borehole (BOREHOLE, AGS's IVAN_TYPE). Each keeps its source and
# test type.
tests = p.undrained_strength(geology=["Alluvium"])

compared = ht.stats.compare_sources(
    tests, value="undrained_shear_strength", display_units="US"
)
print(compared)

# The comparison tests nothing. compare() is the check for two row sources:
# do the UU and field vane results differ by more than chance?
pair = tests[tests["test_type"].isin(["UU", "BOREHOLE"])]
print()
print(
    ht.stats.compare(
        pair,
        value="undrained_shear_strength",
        by="test_type",
        groups=("UU", "BOREHOLE"),
    )
)

fig, ax = compared.geology_unit_comparison()
fig.savefig("sources-compared-undrained.png")
