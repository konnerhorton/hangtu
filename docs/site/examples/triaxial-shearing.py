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

# Each stage's failure reading is the one the lab marked.
fig, ax, _ = ht.plot.triaxial_shearing(
    readings[readings["test_type"] == "CU"],
    second_axis="excess_pore_pressure",
    display_units="US",
)
fig.savefig("triaxial-shearing.png")
