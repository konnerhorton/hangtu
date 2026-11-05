import hangtu as ht

# Rock UCS and triaxial results in ht.template("triaxial")'s columns, in MPa.
# Every stress column needs its unit, blank ones included.
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

# Name the shear failures as the lab wrote them; σci for the fixed fit comes
# from the example's judgments file.
fit = ht.analysis.hoek_brown_fit(
    rock,
    group_by="geology_unit",
    failure_modes=["Shear"],
    judgments=ht.examples.path("judgments.yaml"),
)
print(fit)
