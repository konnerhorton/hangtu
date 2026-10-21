# 20 — In situ stress in rock

| | |
|---|---|
| **Parameters** | σH (major horizontal stress), σh (minor horizontal stress), σv, kH = σH/σv, kh = σh/σv, k = σh,av/σv, σH azimuth |
| **Material** | Rock |
| **Constitutive models that use it** | Initial stress state for all FE models (MC, HB, HS); closed-form convergence-confinement; Kirsch boundary stresses |
| **Depends on** | [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (σv), [14-intact-rock-deformability](14-intact-rock-deformability.md), [18-rock-mass-modulus](18-rock-mass-modulus.md) (Eh for Sheorey) |
| **Feeds** | [17-rock-mass-strength](17-rock-mass-strength.md), [19-post-peak-rock-mass](19-post-peak-rock-mass.md), [21-swelling-rock](21-swelling-rock.md) (stress relief triggers swell), [22-discontinuity-shear-strength](22-discontinuity-shear-strength.md) |

## 1. Phenomenon
The vertical stress is usually close to the overburden weight (σv ≈ γz); the horizontal stresses reflect tectonics,
erosion/glacial unloading, residual (locked-in) stress and the stiffness of each layer, and are hard to predict [1][2].
Measured k is high and scattered at shallow depth and tends towards ~0.5–1.3 at depth [2]. In bedded sedimentary
rock the stiffer layers (e.g. limestone, dolostone) carry higher horizontal stress than the softer ones (shale), so
stress can vary layer by layer at one site. σH ≠ σh in general; the vertical is not always a principal direction.
In the Paleozoic (Ordovician–Silurian) rocks of southern Ontario, horizontal stresses well above σv at shallow depth
are a known regional condition, shown by quarry-floor heave, canal-floor buckling, tunnel springline cracking and
long-term wall movement [5][6].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| σH, σh, σv | MPa (kPa) | psi; ksf | 1 MPa = 145.04 psi = 20.885 ksf; 1 kPa = 20.885 psf (computed) |
| Stress gradient | MPa/m (MN/m³) | psi/ft | 0.027 MN/m³ = 1.194 psi/ft (computed) |
| kH, kh, k | — | — | dimensionless |
| σH azimuth | ° from north | ° | — |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| World compilation, σv | σv ≈ 0.027 z (MPa, z in m) | [2] eq. 8, Fig. 1 [V] |
| World compilation, k = σh,av/σv | 100/z + 0.30 ≤ k ≤ 1500/z + 0.50; at z = 500 m k = 0.5–3.5; at 2000 m 0.35–1.25 | [2] eq. 9, Fig. 2 [V] |
| Southern Ontario Silurian / Ordovician rock | σH,max 6–14 MPa depending on depth and rock type | [5] abstract [V] |
| Southern Ontario, shallow (to ~200 m) | k ≈ 4–6 reported | Lo (1978) as cited by a UBC thesis [U] |
| Queenston shale (example FE input in literature) | kH = 4.00, kh = 2.44 | Al-Maamori & El Naggar (2018) Table 1, citing Al-Maamori et al. (2014) [V] via [8] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Overcoring, CSIRO hollow inclusion (HI) cell | — | ISRM SM 2003 Part 2 [3] | none in AGS 4.2 standard dictionary (project user-defined group needed) | Full 3D tensor from one overcore (needs E, ν of core, biaxial test of core) |
| Overcoring, USBM borehole deformation gauge | D4623-16 (withdrawn 2025, no replacement) | ISRM SM 2003 Part 2 [3] | none (user-defined) | 2D stress in plane normal to the borehole; 3 non-parallel holes for 3D |
| Overcoring, doorstopper (borehole-end strain cell) | — | ISRM SM 2003 Part 2 [3] | none (user-defined) | 2D stress normal to borehole axis at the hole bottom |
| Hydraulic fracturing (HF) / hydraulic tests on pre-existing fractures (HTPF) | D4645-08 (withdrawn 2017, no replacement) | ISRM SM 2003 Part 3 [4] | none (user-defined) | σh (shut-in), σH (HF, vertical hole, vertical fracture assumption); HTPF gives tensor from fracture normal stresses |
| Flat jack (surface of an opening) | D4729-19 | ISRM SM 1987 [U] | none | Stress tangential to the excavation wall |
| Borehole breakouts / drilling-induced tensile fractures (televiewer, caliper) | — | ISRM SM 2003 Part 1 strategy [3a] | none | σH azimuth (breakouts align with σh); magnitude only with strength model |

Notes: the AGS 4.2 standard dictionary has no stress-measurement group (checked); data arrive in project-defined
groups (e.g. an "ISOC"-type group), whose headings must be read from the file's DICT rows.

## 5. Derivations and correlations

### 5.1 Ratio to vertical stress
$$k_H = \sigma_H/\sigma_v,\quad k_h = \sigma_h/\sigma_v,\quad \sigma_v = \gamma z$$
- **Inputs:** measured σH, σh at test depth; σv from the unit-weight profile (sheet 01), not 0.027 z, when site γ is known.
- **Source:** [1] eq. 1–2 [V].

### 5.2 Sheorey (1994) — k from depth and horizontal modulus
$$k = 0.25 + 7E_h\left(0.001 + \frac{1}{z}\right)$$
- **Inputs:** Eh average deformation modulus of the upper crust in the horizontal direction (GPa), z depth (m).
- **Valid for:** first estimate; elastic-thermal crustal model. Does not explain very high horizontal stresses, σH ≠ σh,
  or σv above overburden [1]. Direction of Eh matters in layered sedimentary rock [1].
- **Example (computed):** z = 50 m: k = 1.72 (Eh 10 GPa), 7.60 (Eh 50 GPa).
- **Source:** [7] (original); [V] via Hoek, "In situ and induced stresses", eq. 3, p. 3, Fig. 2 [1].

### 5.3 Brown & Hoek (1978) — empirical bounds
$$\frac{100}{z} + 0.30 \le k \le \frac{1500}{z} + 0.50$$
- **Inputs:** z (m). k = average horizontal / vertical stress, σv = 0.027 z.
- **Valid for:** world compilation of measurements (mining and civil sites); a range, not a prediction.
- **Scatter:** the band itself; very wide at shallow depth (e.g. computed z = 25 m: 4.3–60.5).
- **Source:** [2] eq. 9 and Fig. 2, p. 214 [V].

### 5.4 Hydraulic fracturing (classical interpretation)
$$\sigma_h = P_s,\qquad \sigma_H = 3\sigma_h - P_r - P_0$$
- **Inputs:** Ps shut-in pressure, Pr fracture reopening pressure, P0 pore pressure.
- **Valid for:** vertical borehole parallel to a principal stress, linear elastic isotropic rock, vertical fracture.
  σH from Pr is the least reliable term (system compliance) [4].
- **Source:** [4] [U] (equation not seen in the SM text).

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE (MC, HB) initial stress | K0 / initial stress field; kH and kh by tunnel orientation relative to σH | High: sets the stress concentration and yield zone shape |
| Crown / invert stress, spalling | Kirsch (circular, elastic): crown/invert tangential stress = (3k − 1)σv, sidewalls (3 − k)σv, tensile for k > 3 [U, textbook]; high stress concentration at crown and invert fails weaker layers [6] | High: brittle spalling / buckling of thin beds in crown and invert [6] |
| Squeezing / convergence | Ratio σcm / p0 controls plastic zone and convergence | High (non-linear) |
| Lining loads | Loading from stress relief and time-dependent deformation after installation; ovalization under anisotropic stress | Moderate–high |
| Swelling (sheet 21) | Stress relief by excavation initiates swelling in argillaceous rock [5] | High in swelling shale |
| Shafts, open cuts | Floor heave, wall convergence in bedded rock | High at shallow depth |

**Typical variability:** no published COV located. The Brown & Hoek band (k = 0.5–3.5 at 500 m) shows the regional
uncertainty when no measurements exist [2]; site measurements narrow it, but overcoring results in bedded rock often
scatter by tens of percent between tests _[Judgment — for review]_. Sheorey and Brown & Hoek are first estimates;
transformation error is not stated in the sources.

## 7. Pitfalls and QA checks
- Check which σv was used in published ratios (γz with site γ vs 0.027 z); recompute kH, kh from sheet 01 at test depth.
- Shallow overcoring results are affected by topography, near-surface relief, weathering and the near-field of the
  access opening; flag depth and setting.
- Overcoring needs core E and ν (biaxial test); anisotropic rock with an isotropic solution biases magnitudes.
- Report σH azimuth and the tunnel alignment angle; use the stress component in the tunnel cross-section plane.
- Layer contrast: stress in limestone ≠ stress in shale at the same site; do not average across lithologies.
- HF assumes a principal direction along the hole; HTPF needed where that is not true.
- Do not read a "k" ratio as the soil K0 of sheet 07; they are different parameters.

## References
[1] Hoek, E. (n.d.). In situ and induced stresses. Chapter in Practical Rock Engineering (course notes); copy hosted as CED Engineering G05-004 "Rock Engineering – Underground Openings". https://www.cedengineering.com/userfiles/G05-004%20-%20Rock%20Engineering%20-%20Underground%20Openings%20-%20US.pdf — [V] eqs. 1–3, pp. 1–3, Figs. 1–2
[2] Brown, E.T. & Hoek, E. (1978). Trends in relationships between measured in-situ stresses and depth. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 15, 211–215. https://www.rocscience.com/assets/resources/learning/hoek/Trends-in-Relationship-between-Measured-In-Situ-Stresses-and-Depth-1978.pdf — [V] eqs. 8–10, p. 214
[3] Sjöberg, J., Christiansson, R. & Hudson, J.A. (2003). ISRM Suggested Methods for rock stress estimation—Part 2: overcoring methods. Int. J. Rock Mech. Min. Sci. 40(7–8), 999–1010. https://doi.org/10.1016/j.ijrmms.2003.07.012 — [V] citation; content [U]
[3a] Hudson, J.A., Cornet, F.H. & Christiansson, R. (2003). ISRM Suggested Methods for rock stress estimation—Part 1: Strategy for rock stress estimation. Int. J. Rock Mech. Min. Sci. 40(7–8), 991–998. https://doi.org/10.1016/j.ijrmms.2003.07.011 — [V] citation; content [U]
[4] Haimson, B.C. & Cornet, F.H. (2003). ISRM Suggested Methods for rock stress estimation—Part 3: hydraulic fracturing (HF) and/or hydraulic testing of pre-existing fractures (HTPF). Int. J. Rock Mech. Min. Sci. 40(7–8), 1011–1020. https://doi.org/10.1016/j.ijrmms.2003.08.002 — [V] citation; equations [U]
[5] Lo, K.Y. (1978). Regional distribution of in situ horizontal stresses in rocks of Southern Ontario. Can. Geotech. J. 15(3), 371–381. https://doi.org/10.1139/t78-034 — [V] abstract (6–14 MPa; case histories)
[6] Lo, K.Y. & Morton, J.D. (1976). Tunnels in bedded rock with high horizontal stresses. Can. Geotech. J. 13(3), 216–230. https://doi.org/10.1139/t76-025 — [V] abstract (crown/invert stress concentration, reversed movement pattern)
[7] Sheorey, P.R. (1994). A theory for in situ stresses in isotropic and transversely isotropic rock. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 31(1), 23–34. https://doi.org/10.1016/0148-9062(94)92312-4 — [V] via [1]
[8] Al-Maamori, H.M.S. & El Naggar, M.H. (2018). Performance of vertical shafts constructed in swelling shale using finite element method. GeoEdmonton 2018, CGS. https://members.cgs.ca/conferences/GeoEdmonton/papers/geo2018Paper252.pdf — [V] Table 1
