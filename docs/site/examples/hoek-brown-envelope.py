import hangtu as ht

# The lab's CSV, in ht.template("triaxial")'s columns: a UCS test is a row
# with a cell pressure of 0. Every stress column needs its unit, even blank.
stages = ht.read_csv(
    ht.examples.path("rock_triaxial.csv"),
    units={
        "depth": "ft",
        "cell_pressure": "MPa",
        "deviator_stress_at_failure": "MPa",
        "back_pressure": "MPa",
        "pore_pressure_at_failure": "MPa",
        "reported_intact_compressive_strength": "MPa",
    },
)
rock = ht.analysis.triaxial_failure_stresses(stages)

fig, ax, fit = ht.plot.hoek_brown_envelope(
    rock,
    group_by="geology_unit",
    failure_modes=["Shear"],
    judgments=ht.examples.path("judgments.yaml"),
)
fig.savefig("hoek-brown-envelope.png")
print(fit)
