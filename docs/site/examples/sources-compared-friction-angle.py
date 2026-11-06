import pandas as pd

import hangtu as ht

p = ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite")
p.set_geology_map(ht.examples.path("strata.csv"))
p.set_judgments(ht.examples.path("judgments.yaml"))

# The SPT correlations, on the medium dense upper Terrace sand, as on the
# correlations guide. B-4's log has a gap (QC G002), so it is left out.
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

# The triaxial fit, and the shear box fit converted to a triaxial φ′. φ′cv
# comes from the judgments file, keyed by geology unit.
triaxial = ht.analysis.mohr_coulomb_fit(
    p.triaxial(geology=["Terrace"]), group_by="geology_unit"
)
shear_box = ht.analysis.shear_box_fit(
    p.shear_box(geology=["Terrace"]), group_by="geology_unit"
)
converted = ht.analysis.friction_angle_from_shear_box(shear_box, soil="cohesionless")
print(converted)

compared = ht.stats.compare_sources(
    correlations, triaxial, converted, value="effective_friction_angle"
)
print()
print(compared)
print()
print(compared.positions().round(1).to_string(index=False))

fig, ax = compared.profile(
    geology_unit="Terrace", preset="effective_friction_angle", display_units="US"
)
fig.savefig("sources-compared-friction-angle.png")
