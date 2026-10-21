# 22 — Discontinuity shear strength

| | |
|---|---|
| **Parameters** | φj, cj (peak friction angle and cohesion intercept of a joint or bedding plane), φr (residual), φb (basic), i (Patton roughness angle), JRC, JCS (Barton-Bandis) |
| **Material** | Rock (discontinuities) |
| **Constitutive models that use it** | MC joint (Coulomb slip), Barton-Bandis, ubiquitous joint, interface/joint elements, limit equilibrium wedge/block |
| **Depends on** | [13-intact-rock-strength](13-intact-rock-strength.md) (JCS ≤ σci), [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (σn) |
| **Feeds** | [17-rock-mass-strength](17-rock-mass-strength.md) (anisotropic / structurally controlled cases), [16-gsi-and-disturbance](16-gsi-and-disturbance.md) (joint condition, qualitative) |

## 1. Phenomenon
Shear strength of a discontinuity is friction on the mineral surfaces (φb ≈ φr for planar, unweathered surfaces)
plus a roughness component: asperities force dilation at low normal stress (Patton's i) and are sheared off at
higher stress, so the true envelope is curved and the "cohesion" of a straight-line fit to rough-joint data is
mostly apparent — a mathematical intercept from roughness, not bonding [1, p. 2]. Peak strength drops to a residual
value after a few millimetres of shear, and is reduced by weathering of the walls (lower JCS), by clay coatings or
infill (bedding planes in shale) and by pore pressure (use σ′n = σn − u) [1, p. 10]. Roughness and wall strength
both decrease with joint length, so laboratory peak values on 50–100 mm specimens overstate field-scale strength
(Barton & Bandis 1982) [1, p. 6].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| τ, σn, cj, JCS | kPa, MPa | psi, ksi | 1 kPa = 0.14504 psi; 1 MPa = 145.04 psi |
| φj, φr, φb, i | degrees | degrees | – |
| JRC | – | – | dimensionless (0–20 profile scale) |
| Shear displacement | mm | in | 1 in = 25.4 mm |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Rough rock discontinuities (probabilistic example) | φ mean 35°, SD 5° (truncated 15–70°); c mean 10 t/m² (≈ 98 kPa), SD 2 | [2] p. 8 table, p. 10 [V] |
| Clay shale, stratification surfaces | residual c′ 0, φr 19–25° | [1] Table 1, p. 11 (Barton 1974) [V] |
| Greywacke, 1–2 mm clay in bedding | residual c′ 0, φr 21° | [1] Table 1 [V] |
| Limestone with < 1 mm clay filling | peak c′ 0.05–0.2 MPa, φ 17–21° | [1] Table 1 [V] |
| Limestone, 6 mm clay layer | residual φr 13° | [1] Table 1 [V] |
| Bentonitic shale (triaxial / direct shear) | peak c′ 0–0.27 MPa, φ 8.5–29°; residual φr 8.5° | [1] Table 1 [V] |
| Basic friction angle φb, sawn surfaces of common sedimentary rocks | about 25–35° | Barton & Choubey (1977) table [3] [U] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Laboratory direct shear of rock discontinuity, constant normal load | D5607-16 (**withdrawn 2025, no replacement**) [4] | ISRM SM 1974 (in [5]); ISRM revised SM, Muralha et al. (2014) [6]; soil method BS EN ISO 17892-10:2018 sometimes quoted | SHBG: SHBG_TYPE, SHBG_COND, SHBG_PCOH, SHBG_PHI, SHBG_RCOH, SHBG_RPHI, SHBG_ENCA (encapsulation), SHBG_REM, SHBG_METH. SHBT (per stage): SHBT_TESN, SHBT_NORM, SHBT_PEAK, SHBT_RES, SHBT_PVST, SHBT_RVST, SHBT_PDIS, SHBT_RDIS, SHBT_PDIN, SHBT_RDIN, SHBT_DIA1/DIA2 ("rock joints"), SHBT_HGT, SHBT_CRIT, SHBT_REVS, SHBT_REM | Peak and residual τ at each σn; dilation |
| Tilt test, Schmidt rebound on joint walls | – | ISRM 1978 discontinuity description [5] | – | φb, JCS, JRC estimates |

AGS notes: SHBT stresses are in kPa. SHBG_TYPE codes (SMALL/LARGE SBOX, SMALL/LARGE RSHEAR) have no rock-joint
value, so rock tests may leave it blank. **No AGS heading records the orientation of the sheared plane relative to
bedding** — check SPEC_DESC, SHBG_REM and test sheets (FILE_FSET).

## 5. Derivations and correlations

### 5.1 Mohr-Coulomb peak and residual — linear fit
$$\tau_p = c_j + \sigma_n\tan\phi_j,\qquad \tau_r = \sigma_n\tan\phi_r$$
- **Fit:** least squares of τ on σn over the stages (SHBT_PEAK vs SHBT_PVST or SHBT_NORM)
- **Source:** [1] eqs. 1–2, p. 2 [V]

### 5.2 Fit through the origin (cj = 0)
$$\tan\phi_j = \frac{\sum \sigma_n\tau}{\sum \sigma_n^2}\qquad\text{(least squares, derived)};\qquad \phi_{sec,k} = \arctan(\tau_k/\sigma_{n,k})$$
- **Use:** conservative for open or clay-coated bedding; report both fits. Computed example (Barton envelope
  φr = 25°, JRC = 10, JCS = 50 MPa; σn = 0.1–2 MPa): linear fit c = 88 kPa, φ = 37.8°; through origin φ = 39.9°;
  secant φ falls from 52° at 0.1 MPa to 39° at 2 MPa — the intercept is apparent cohesion from roughness.

### 5.3 Patton saw-tooth — Patton (1966)
$$\tau = \sigma_n\tan(\phi_b + i)$$
- **Valid for:** low σn where sliding rides over asperities; at higher σn teeth shear off
- **Source:** [1] eq. 3, p. 5 [V]; [7] [U]

### 5.4 Barton–Choubey peak strength — Barton (1973); Barton & Choubey (1977)
$$\tau = \sigma_n\tan\left[\phi_r + JRC\,\log_{10}\!\left(\frac{JCS}{\sigma_n}\right)\right],\qquad \phi_r = (\phi_b - 20^\circ) + 20^\circ\,(r/R)$$
- **Inputs:** JRC (profile comparison), JCS (MPa; = σci for unweathered walls; Schmidt hammer), σn (MPa);
  r = Schmidt rebound on wet weathered joint wall, R = on dry unweathered sawn surface
- **Valid for:** 130 natural joint samples in variably weathered rock [1] p. 5; not valid as σn → 0 [1] p. 12
- **Source:** [1] eqs. 4–6, p. 5 [V]; [3] [U]

### 5.5 Scale corrections — Barton & Bandis (1982)
$$JRC_n = JRC_0\left(\frac{L_n}{L_0}\right)^{-0.02\,JRC_0},\qquad JCS_n = JCS_0\left(\frac{L_n}{L_0}\right)^{-0.03\,JRC_0}$$
- **Inputs:** L0 = 100 mm laboratory scale; Ln = in situ block size
- **Computed:** Ln/L0 = 10 → JRC 10 → 6.3, JCS × 0.50; JRC 5 → 4.0, JCS × 0.71
- **Source:** [1] eqs. 7–8, p. 6 [V]; [8] [U]

### 5.6 Instantaneous c and φ — Hoek
- Tangent to the curved (Barton-Bandis or fitted) envelope at the design σn gives ci and φi for MC-based
  programs; valid only near that σn [1] p. 10, Fig. 8 p. 12 [V].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Wedge / block stability (key-block, limit equilibrium) | Sliding resistance ∝ σn tanφj + cj·A; FS ∝ tanφj when cj = 0 | High; cj highly influential on small wedges (low σn) — use cj = 0 unless bonded |
| Bedding-plane slip in flat-bedded shale crowns | Slip and separation along bedding (φj, cj, joint tensile strength) drive crown sag and loosening, raise lining load | High for wide spans with thin beds _[Judgment — for review]_ |
| Ubiquitous-joint FE (anisotropic rock mass) | Joint yield on the bedding orientation everywhere in the zone (φj, cj, σt,j) | High: controls yield zone shape and crown displacement |
| Joint/interface elements (UDEC/RS2) | Kn, Ks with φj, cj or Barton-Bandis | Moderate–high |
| HB isotropic rock mass | Not used (joint condition only via GSI) | Low |

**Typical variability:** Hoek's probabilistic example uses φ COV ≈ 14 % (35° ± 5°) and c COV 20 %, and notes c and
φ from shear tests are negatively correlated [2] pp. 8, 10 [V]. Scale correction (5.5) and orientation
uncertainty usually exceed test scatter _[Judgment — for review]_.

## 7. Pitfalls and QA checks
- Confirm the sheared plane is the bedding/joint of interest (photos, SPEC_DESC); intact-rock shears give c, φ far too high.
- Report peak and residual separately; check SHBT_PDIS/RDIS (residual needs several mm, or reversals SHBT_REVS).
- Report linear and through-origin fits; a large intercept with few stages is usually apparent cohesion.
- σn range of the test must match the field σn (shallow crowns: low σn → curvature matters).
- Use effective normal stress where water pressure acts on the plane [1, p. 10].
- Apply scale reduction (5.5) to rough joints before design use; planar clay-coated bedding has little scale effect.
- Check dilation sign (SHBT_PDIN) is consistent with roughness; negative dilation suggests infill crushing.
- Encapsulation (SHBG_ENCA) and alignment errors can add an artificial angle [1, p. 2].

## References
[1] Hoek, E. (2023). Practical Rock Engineering, ch. 4 "Shear strength of discontinuities". Rocscience. https://static.rocscience.cloud/assets/resources/learning/hoek/4.-Shear-strength-of-discontinuities_2023-06-30-120608_pbkx.pdf — [V] eqs. 1–8 (pp. 2, 5, 6), p. 10, Table 1 p. 11 (after Barton 1974), Fig. 8 p. 12
[2] Hoek, E. (2023). Practical Rock Engineering, ch. 9 "Factor of safety and probability of failure". Rocscience. https://static.rocscience.cloud/assets/resources/learning/hoek/9.-Factor-of-safety-and-probability-of-failure_2023-06-30-120706_oohd.pdf — [V] random-variable table p. 8, commentary p. 10
[3] Barton, N. & Choubey, V. (1977). The shear strength of rock joints in theory and practice. Rock Mechanics 10(1–2), 1–54. https://doi.org/10.1007/BF01261801 — [U] (equations [V] via [1])
[4] ASTM D5607-16 (withdrawn 2025). Standard test method for performing laboratory direct shear strength tests of rock specimens under constant normal force. https://store.astm.org/d5607-16.html — [V] status
[5] Ulusay, R. & Hudson, J.A. (eds) (2007). The complete ISRM suggested methods for rock characterization, testing and monitoring: 1974–2006. ISRM, Ankara. — [U]
[6] Muralha, J., Grasselli, G., Tatone, B., Blümel, M., Chryssanthakis, P. & Jiang, Y. (2014). ISRM suggested method for laboratory determination of the shear strength of rock joints: revised version. Rock Mech. Rock Eng. 47(1), 291–302. https://doi.org/10.1007/s00603-013-0519-z — [U] (bibliography [V] via Crossref)
[7] Patton, F.D. (1966). Multiple modes of shear failure in rock. Proc. 1st ISRM Congress, Lisbon, 1, 509–513. — [U]
[8] Barton, N. & Bandis, S. (1982). Effects of block size on the shear behaviour of jointed rock. Proc. 23rd US Symp. Rock Mech., Berkeley, 739–760. — [U] (equations [V] via [1])
[9] Barton, N. & Bandis, S. (1990). Review of predictive capabilities of JRC-JCS model in engineering practice. Proc. Int. Symp. Rock Joints, Loen, 603–610. — [U]
