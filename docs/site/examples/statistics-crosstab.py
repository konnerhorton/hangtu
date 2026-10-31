import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))

# The legend code logged for each layer (GEOL_LEG), beside the class each
# specimen's liquid limit and plasticity index give on the plasticity chart.
limits = p.atterberg(geology_fields=["GEOL_LEG"])
logged = ht.stats.crosstab(limits, "legend_code", "plasticity_class_uscs", agree="same")
print(logged)

# Fill is logged by its origin, not its class: count any fine-grained class
# as agreeing with it, and CL-ML as agreeing with CL.
mapping = {"CL": ["CL", "CL-ML"], "FILL": ["CL", "CL-ML", "ML", "CH", "MH"]}
by_mapping = ht.stats.crosstab(
    limits, "legend_code", "plasticity_class_uscs", agree=mapping
)
print()
print(by_mapping.notes[0])

# The disagreeing rows, in full, for checking against the logs.
print()
print(limits.loc[by_mapping.mismatches.index, ["loca_id", "depth", "liquid_limit"]])
