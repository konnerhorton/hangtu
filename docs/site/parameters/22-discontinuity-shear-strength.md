# Discontinuity shear strength

| | |
|---|---|
| **Parameters** | φj, cj (peak friction angle and cohesion intercept of a joint or bedding plane), φr (residual friction angle), φb (basic friction angle), i (roughness angle), JRC and JCS (joint roughness coefficient and joint wall compressive strength) |
| **Material** | Rock: joints, bedding planes and other discontinuities |
| **Models that use it** | Mohr–Coulomb slip on a joint, Barton–Bandis, ubiquitous-joint models, joint and interface elements, limit equilibrium of wedges and blocks |
| **Depends on** | intact rock strength (JCS is at most σci); [unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (the normal stress on the plane) |
| **Feeds** | rock mass strength, where a structure controls it; GSI and joint condition, qualitatively |

## What it is

The shear strength of a discontinuity is friction on its mineral surfaces plus a roughness component. A planar,
unweathered surface has the basic friction angle φb, close to the residual φr. On a rough surface, asperities force
the joint to dilate at low normal stress and are sheared off at higher stress, so the envelope is curved. The
cohesion of a straight line fitted to rough-joint results is then mostly apparent: an intercept from roughness, not
bonding (Hoek 2023, ch. 4, p. 2):

$$
\tau_p = c_j + \sigma_n \tan\phi_j, \qquad \tau_r = \sigma_n \tan\phi_r
$$

(Hoek 2023, ch. 4, eqs. 1–2, p. 2). Peak strength drops to a residual value after a few millimeters of shear. It is
lowered by weathering of the walls (a lower JCS), by clay coatings or infill (bedding planes in shale) and by water
pressure on the plane, which reduces the effective normal stress (p. 10). Roughness and wall strength both fall
with joint length, so laboratory peak values on 50 to 100 mm specimens overstate the strength at field scale (p. 6).

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Wedge and block stability (limit equilibrium) | sliding resistance σn tan φj + cj over the plane | High; cj dominates small wedges at low normal stress, so it is usually set to 0 unless the plane is bonded |
| Bedding-plane slip in flat-bedded rock over an opening | slip and separation along bedding drive sag and loosening of the roof | High for wide spans in thinly bedded rock |
| Ubiquitous-joint numerical models | joint yield on the bedding orientation throughout the zone | High: controls the shape of the yield zone |
| Joint and interface elements | normal and shear stiffness with φj, cj or Barton–Bandis | Moderate to high |
| Isotropic Hoek–Brown rock mass | not used directly (joint condition enters through GSI) | Low |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| τ, σn, cj, JCS | kPa, MPa | psf, psi, ksi | 1 kPa = 20.885 psf = 0.1450 psi; 1 MPa = 145.04 psi |
| φj, φr, φb, i | degrees (°) | degrees (°) | – |
| JRC | – | – | dimensionless, on a scale of 0 to 20 |
| Shear displacement | mm | in | 1 in = 25.4 mm |

## Typical values

| Material | Range | Source |
|---|---|---|
| Clay shale, stratification surfaces | residual c 0, φr 19–25° | Hoek (2023), ch. 4, Table 1, p. 11, after Barton (1974) |
| Greywacke, 1–2 mm clay in bedding | residual c 0, φr 21° | as above |
| Limestone, clay filling under 1 mm | peak c 0.05–0.2 MPa, φ 17–21° | as above |
| Limestone, 6 mm clay layer | residual φr 13° | as above |
| Bentonitic shale | peak c 0–0.27 MPa, φ 8.5–29°; residual φr 8.5° | as above |
| Rough discontinuities, a probabilistic example | φ mean 35°, standard deviation 5°; c mean about 98 kPa | Hoek (2023), ch. 9, p. 8 |

Infilled and clay-coated planes are weaker than the rock either side; the values place a material roughly and
aren't design values.

## Tests

| Test | ASTM | ISO / ISRM | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Direct shear of a rock discontinuity, constant normal load | D5607-16, withdrawn in 2025 with no replacement | ISRM suggested method (Muralha et al. 2014) | `SHBG`: `SHBG_TYPE`, `SHBG_ENCA`, `SHBG_PCOH`, `SHBG_PHI`, `SHBG_RCOH`, `SHBG_RPHI`; `SHBT`: `SHBT_NORM`, `SHBT_PVST`, `SHBT_RVST`, `SHBT_PEAK`, `SHBT_RES`, `SHBT_PDIS`, `SHBT_PDIN`, `SHBT_DIA1`, `SHBT_DIA2`, `SHBT_REVS` | peak and residual τ at each σn; dilation |
| Tilt test; Schmidt hammer on the joint walls | – | ISRM suggested methods | – | estimates of φb, JCS, JRC |

`SHBG_TYPE`'s codes are shear box and ring shear, with none for a rock joint, and no heading records the
orientation of the sheared plane against bedding: check the specimen description, `SHBG_REM` and the test sheets.
[`p.shear_box()`](../reference/project.md#hangtu.Project.shear_box) gives one row per stage, soil and rock joint
tests alike, and doesn't label which a test is (`docs/data/datasets.md` §6.12).

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Linear fit of peak and residual results (Hoek 2023, ch. 4, eqs. 1–2) | τ and σn per stage | any discontinuity, over the tested σn range | M17 (b) |
| Fit through the origin (cj = 0) | as above | open or clay-coated planes; report it beside the free fit | M17 (b) |
| Patton (1966), τ = σn tan(φb + i), as given by Hoek (2023, ch. 4, eq. 3) | φb, i | low σn, where sliding rides over the asperities | wave 4 |
| Barton (1973), Barton & Choubey (1977), as given by Hoek (2023, ch. 4, eqs. 4–6) | JRC, JCS, φr | natural joints in variably weathered rock; not as σn → 0 | wave 4 |
| Scale corrections, Barton & Bandis (1982), as given by Hoek (2023, ch. 4, eqs. 7–8) | JRC, JCS, block size | rough joints, from laboratory to field scale | wave 4 |

## How the methods compare

Test results on the discontinuity of interest are the basis. Report the free fit and the fit through the origin
together: a large intercept from few stages is usually roughness, not cohesion. Over a wide range of normal stress
the envelope of a rough joint is curved, so a straight line holds only near its stresses; Hoek (2023, ch. 4, p. 10)
takes the tangent to the curved envelope at the design normal stress for programs that need c and φ. Correct a rough
joint for scale before design use; a planar, clay-coated bedding plane changes little with scale. Choosing a design
value is selection (M18).

## Variability

- Hoek's probabilistic example (2023, ch. 9, pp. 8, 10) uses a COV of about 14 % for φ and 20 % for c, and notes
  that c and φ from shear tests are negatively correlated.
- The scale correction and the uncertainty in the plane's orientation are often larger than the scatter of the tests.

## Pitfalls

- Confirm that the sheared plane is the joint or bedding of interest; a shear through intact rock gives c and φ far
  too high.
- Report peak and residual separately, and check the displacement at the residual: it needs several millimeters,
  or reversals (`SHBT_REVS`).
- Report the free and the through-origin fit; a large intercept from few stages is usually apparent cohesion.
- Match the normal stress of the tests to the field's: at low normal stress, near the crown of a shallow opening,
  the curvature matters.
- Use the effective normal stress where water pressure acts on the plane (Hoek 2023, ch. 4, p. 10).
- Check the sign of the dilation (`SHBT_PDIN`) against the roughness; contraction suggests crushing of an infill.
- Encapsulation and alignment errors can add an artificial angle (Hoek 2023, ch. 4, p. 2).
- `SHBT_NORM`, `SHBT_PVST` and `SHBT_RVST` can differ where the lab corrects for the contact area; `p.shear_box()`
  keeps all three, and the fit says which it used.

## References

- Hoek, E. (2023). *Practical Rock Engineering*, ch. 4, "Shear strength of discontinuities". Rocscience.
  <https://static.rocscience.cloud/assets/resources/learning/hoek/4.-Shear-strength-of-discontinuities_2023-06-30-120608_pbkx.pdf>
- Hoek, E. (2023). *Practical Rock Engineering*, ch. 9, "Factor of safety and probability of failure". Rocscience.
  <https://static.rocscience.cloud/assets/resources/learning/hoek/9.-Factor-of-safety-and-probability-of-failure_2023-06-30-120706_oohd.pdf>
- ASTM D5607-16 (withdrawn 2025). *Standard Test Method for Performing Laboratory Direct Shear Strength Tests of
  Rock Specimens Under Constant Normal Force.* <https://store.astm.org/d5607-16.html>
- Muralha, J., Grasselli, G., Tatone, B., Blümel, M., Chryssanthakis, P. and Jiang, Y. (2014). ISRM suggested method
  for laboratory determination of the shear strength of rock joints: revised version. *Rock Mechanics and Rock
  Engineering* 47(1), 291–302. <https://doi.org/10.1007/s00603-013-0519-z>

Barton (1973, 1974), Barton & Choubey (1977), Barton & Bandis (1982) and Patton (1966) are cited as Hoek (2023)
gives them; their originals haven't been checked here.
