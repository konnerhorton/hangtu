import warnings

import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_readings_map(ht.examples.path("readings_map.csv"))
readings = p.triaxial_readings()

# The example's labs read q, Δu and εv in groups of their own, at their own
# strains, so Δu and εv at each failure reading are interpolated, with a
# warning that names the stages. Neither E50, Rf nor ψ reads those values.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*interpolated in strain")
    stiffness = ht.analysis.triaxial_stiffness_from_readings(
        readings, failure_criterion="max_deviator_stress"
    )
    dilatancy = ht.analysis.triaxial_dilatancy_from_readings(
        readings, failure_criterion="max_deviator_stress"
    )

# hangtu's E50 beside the lab's, where the lab reported one, and ψ.
key = ["specimen_id", "test_stage"]
lab = p.triaxial()[[*key, "reported_secant_modulus_at_50_percent_peak"]]
psi = dilatancy[[*key, "dilatancy_angle", "dilatancy_angle_reason"]]
table = stiffness.merge(lab, on=key).merge(psi, on=key)
table["secant_modulus_at_50_percent_peak"] /= 1000  # psf to ksf, as the lab's
columns = [
    "sample_reference",
    "test_type",
    "cell_pressure",
    "axial_strain_at_50_percent_peak",
    "secant_modulus_at_50_percent_peak",
    "reported_secant_modulus_at_50_percent_peak",
    "failure_ratio",
    "dilatancy_angle",
]
consolidated = table[table["test_type"] != "UU"]
with pd.option_context("display.width", 200, "display.precision", 3):
    print(consolidated[columns].to_string(index=False))

# Why a drained stage has no Rf or ψ.
drained = consolidated[consolidated["test_type"].isin(["CD", "CDM"])]
for column in ["failure_ratio_reason", "dilatancy_angle_reason"]:
    for _, row in drained[drained[column].notna()].iterrows():
        stage = f"{row['sample_reference']} at {row['cell_pressure']:.0f} psf"
        print(f"{stage}: {row[column]}")
