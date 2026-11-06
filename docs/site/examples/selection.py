import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
# The judgments file holds the selection: per parameter and geology unit, the
# source and the method that give the value, each with its reason.
p.set_judgments(ht.examples.path("judgments.yaml"))

# The Terrace's φ′ sources, as on the drained shear strength page.
holes = ["B-1", "B-2", "B-3", "B-5", "B-6"]
spt = ht.analysis.vertical_stress(p.spt(holes=holes), stratigraphy=p.stratigraphy())
spt = ht.analysis.spt_n1_60(spt, method="liao_whitman_1986")
sand = spt[(spt["geology_unit"] == "Terrace") & (spt["spt_n60"] <= 40)]
correlations = pd.concat(
    [
        ht.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996(sand),
        ht.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990(sand),
    ],
    ignore_index=True,
)
triaxial = ht.analysis.mohr_coulomb_fit(
    p.triaxial(geology=["Terrace"]), group_by="geology_unit"
)
shear_box = ht.analysis.shear_box_fit(
    p.shear_box(geology=["Terrace"]), group_by="geology_unit"
)
converted = ht.analysis.friction_angle_from_shear_box(shear_box, soil="cohesionless")

# φ′ and c′, each fitted from the one triaxial fit: the pair stays on one line.
friction = ht.stats.select(
    correlations, triaxial, converted, value="effective_friction_angle"
)
print(friction)
cohesion = ht.stats.select(triaxial, value="effective_cohesion")
print()
print(cohesion)

# The Alluvium's s_u: the characteristic mean of the UU tests, drawn against depth.
tests = p.undrained_strength(
    geology=["Alluvium"], hand_penetrometer_scale="unconfined_compressive_strength"
)
strength = ht.stats.select(tests, value="undrained_shear_strength", display_units="US")
print()
print(strength)

fig, ax = strength.profile(geology_unit="Alluvium")
fig.savefig("selection.png")
