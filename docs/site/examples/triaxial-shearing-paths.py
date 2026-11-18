import hangtu as ht

stresses = [
    "effective_consolidation_stress",
    "back_pressure",
    "cell_pressure",
    "deviator_stress",
    "excess_pore_pressure",
]
readings = ht.read_csv(
    ht.examples.path("triaxial_readings.csv"),
    units=dict.fromkeys(stresses, "psf"),
    dtype={"specimen_id": str, "test_stage": str},
)

# The CU and CDM stages: the UU stages have no effective stress path.
fig, ax, fit = ht.plot.triaxial_shearing(
    readings[readings["test_type"].isin(["CU", "CDM"])],
    space="s_t",
    group_by="geology_unit",
    display_units="US",
)
fig.savefig("triaxial-shearing-paths.png")
print(fit)
