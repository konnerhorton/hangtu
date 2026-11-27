import hangtu as ht

shown = [
    "depth",
    "cell_pressure",
    "bulk_unit_weight",
    "reported_secant_modulus_at_50_percent_peak",
    "water_content",
    "geology_unit",
]

# Read the file without units, and check each column's default unit.
lab = ht.read_csv(ht.examples.path("triaxial.csv"))
table = ht.columns(lab).set_index("name")
print(table.loc[shown, ["quantity", "us_unit", "si_unit"]].to_string())

# The lab sheet is in these US units throughout, so declare the system.
lab = ht.set_units(lab, system="US")
declared = ht.units_of(lab)
print()
for column in shown:
    print(f"{column}: {declared.get(column, '(none needed)')}")
