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

fig, ax, fit = ht.plot.triaxial_shearing(
    readings, space="s_t", group_by="geology_unit", display_units="US"
)
fig.savefig("triaxial-shearing-paths.png")
print(fit)
