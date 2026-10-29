# Undrained shear strength

| | |
|---|---|
| **Parameters** | s_u (undrained shear strength), s_u,r (remolded), S_t = s_u / s_u,r (sensitivity) |
| **Material** | Soil: fine-grained, or any soil that can't drain at the rate of loading |
| **Models that use it** | Mohr–Coulomb or Tresca in total stress (φu = 0), NGI-ADP, Hardening Soil and HS-small in undrained mode, SHANSEP |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σv0, σ′v0); index properties (PI); [drained shear strength](04-drained-shear-strength-soil.md) (φ′, for the critical-state ratio); [preconsolidation](06-preconsolidation-and-compressibility.md) (OCR, σ′p) |
| **Feeds** | Elastic stiffness (E/s_u), Hardening Soil stiffness (undrained calibration) |

## What it is

s_u is the shear stress at failure when the soil can't drain. It isn't a soil constant: it is where the
effective-stress path from the in situ state (e0, σ′v0, OCR) meets the critical state. So it depends on stress
history, on the mode of shear (compression gives more than simple shear, and simple shear more than extension), on
the strain rate and on sample disturbance, which usually lowers it. Fissures lower the operational s_u of stiff
overconsolidated clays. Each test (UU triaxial, vane, CPT, pocket penetrometer) measures its own s_u, so values are
referred to one mode before they are combined.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Bearing capacity of foundations on clay, short term | q_ult = N_c s_u + q | High: linear in s_u |
| Slope and embankment stability, end of construction | resisting shear along the slip surface | High: linear in s_u |
| Excavation base heave and support | the stability number γH / s_u | High in soft clay |
| Face stability of a tunnel in clay | the stability ratio (σv − σT) / s_u | High |
| Numerical models in total stress | the yield stress; the extent of plastic zones | High near failure; moderate where the response is mostly elastic |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| s_u, q_u (= 2 s_u) | kPa | psf, ksf, tsf, psi | 1 kPa = 20.885 psf = 0.1450 psi; 1 tsf = 95.76 kPa; 1 kg/cm² = 98.07 kPa |
| s_u/σ′v0, S, m | – | – | dimensionless |

## Typical values

| Material | Range | Source |
|---|---|---|
| Clay by field N: 0–2, 2–4, 4–8, 8–15, 15–30, > 30 blows/ft | s_u < 12.5, 12.5–25, 25–50, 50–100, 100–200, > 200 kPa | Kulhawy & Mayne (1990), Table 4-10, p. 4-54, after Terzaghi & Peck (1967) |
| Normally consolidated clay, field vane | s_u/σ′v0 = 0.11 + 0.0037 PI, about 0.15 to 0.33 for PI 10 to 60 | Kulhawy & Mayne (1990), Eq. 4-18, p. 4-28, after Skempton |
| Normally consolidated clay, direct simple shear | s_u/σ′v0 ≈ 0.22 | Mayne et al. (2009), Eq. 1.4, p. 2789 |
| Mobilized in field failures | s_u/σ′p ≈ 0.22 | Mayne et al. (2009), Eq. 1.5, p. 2789, after Mesri (1975) |

The N classes place a clay roughly; SPT N is a poor predictor of s_u (below), so they aren't a design value.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| UU triaxial | D2850 | ISO 17892-8; BS 1377-7 | `TRIG`: `TRIG_TYPE`, `TRIG_COND`; `TRIT`: `TRIT_CELL`, `TRIT_DEVF`, `TRIT_CU`, `TRIT_STRN` | s_u = q_f / 2, compression, total stress |
| Unconfined compression | D2166/D2166M | ISO 17892-7; BS 1377-7 | `LUCT`: `LUCT_UCS`, `LUCT_STRA` | s_u = q_u / 2 |
| CU triaxial | D4767 | ISO 17892-9; BS 1377-8 | `TREG_TYPE` (CIUC, CAUC, CAUE); `TRET`: `TRET_CU`, `TRET_DEVF`, `TRET_CONP` | s_u at the consolidation stress (SHANSEP input) |
| Direct simple shear | D6528 | – | no AGS 4.2 group (user-defined) | s_u in simple shear |
| Field vane | D2573/D2573M | ISO 22476-9; BS 1377-9 | `IVAN`: `IVAN_IVAN` (peak), `IVAN_IVAR` (remolded) | s_u (vane), S_t |
| Laboratory vane | D4648/D4648M | BS 1377-7 | `LVAN`: `LVAN_VNPK`, `LVAN_VNRM` | s_u, s_u,r |
| Pocket penetrometer | no ASTM method | – | `LPEN`: `LPEN_PPEN`; `IPEN`: `IPEN_IPEN` | index s_u, or q_u: check the instrument |
| CPTu (correlation input) | D5778 | ISO 22476-1 | `SCPT`: `SCPT_QT`; `SCPP`: `SCPP_CSU` | q_net for s_u = q_net / N_kt |
| SPT (correlation input) | D1586/D1586M | ISO 22476-3 | `ISPT`: `ISPT_NVAL`, `ISPT_ERAT`, `ISPT_N60` | N and N60 for the correlations below |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Stroud (1974), as given by Loehr et al. (2016) | N60, PI | clays with PI ≥ 15; a band for 15 ≤ PI < 30 | [`ht.analysis.correlations.undrained_shear_strength_stroud_1974()`](../reference/correlations.md#hangtu.analysis.correlations.undrained_shear_strength_stroud_1974) |
| Terzaghi & Peck (1967), as given by Kulhawy & Mayne (1990) | field N | clays; a band by class | [`ht.analysis.correlations.undrained_shear_strength_terzaghi_peck_1967()`](../reference/correlations.md#hangtu.analysis.correlations.undrained_shear_strength_terzaghi_peck_1967) |
| UU triaxial and unconfined compression, s_u = q_f / 2 | deviator stress at failure | saturated, intact specimens | W2 |
| Field vane, with Bjerrum's correction μ(PI) (Kulhawy & Mayne 1990, Fig. 4-48, p. 4-52) | vane s_u, PI | clays; μ applies to the field vane only | W2 |
| SHANSEP, s_u/σ′v0 = S OCR^m (Ladd & Foott 1974; Ladd 1991) | σ′v0, OCR, CU or DSS tests | sedimentary clays of low to moderate sensitivity; not fissured, cemented or structured clays | W3 |
| CPTu, s_u = (q_t − σv0) / N_kt | q_t, σv0, a site N_kt | clays | later |

Stroud's correlation reads PI, which is rarely tested at the SPT depth. `ht.analysis.add_judgment()` puts a PI per
geology unit on the rows from the project's judgments file, and `ht.stats.describe()` summarizes the measured
PI by unit to choose it. Both SPT methods give a band where their source gives one, in
`undrained_shear_strength_lower` and `undrained_shear_strength_upper`, and leave the value blank there;
`ht.plot.profile()` draws a band as a bar. The equations, ranges and sources are in each function's reference
entry, and [(N1)60 and correlations](../guides/correlations.md) shows them on the example project.

## How the methods compare

Laboratory and vane results on the unit's own soil are the basis, and overrule an SPT estimate. Loehr et al.
(2016, p. 7-38) give Stroud's values as "somewhat lower bound values", and say "SPT N-values are generally a poor
predictor of undrained shear strength". Terzaghi & Peck's classes were "developed primarily using unconfined
compression tests" (Kulhawy & Mayne 1990, p. 4-53). Use either to check measured s_u, not in its place.

Before combining tests, refer each s_u to one mode and rate. Kulhawy & Mayne (1990) give, for 20° < φ′tc < 40°,
the ratio to isotropically consolidated triaxial compression (CIUC) as 1.13 − 0.0094 φ′tc for K0-consolidated
compression, 0.77 − 0.0064 φ′tc for direct simple shear and 0.56 − 0.0046 φ′tc for K0-consolidated extension
(Table 4-9, p. 4-50), and the rate effect as s_u / s_u(1 %/h) = 1.0 + 0.1 log ε̇ (%/h) (Eq. 4-54, p. 4-48).
Choosing a design value is stage D (M18).

## Variability

- Neither SPT source states a scatter; the band of each class is all the source gives.
- An SPT estimate carries the scatter of N and of the correlation, on top of the soil's own variability.

## Pitfalls

- State the mode (triaxial compression, simple shear, extension, vane, CPT) of every s_u, and convert before
  averaging across modes.
- Check the N each correlation takes: Terzaghi & Peck read field N, Stroud N60. hangtu reads the one column each
  was derived with, and a missing one is an error naming what adds it.
- Stroud gives f1 at two plasticities only (4.5 at PI ≳ 30, 5.5 at PI ≅ 15). hangtu doesn't interpolate between
  them: it gives the band, and no estimate below PI 15.
- The correlations are for clays. Pass the rows they apply to, or `uscs="proposed"` with a `uscs_symbol` column
  to give no estimate outside CL and CH.
- UU tests on fissured, silty or sandy clays scatter and are often low; a UU test on a partly saturated specimen
  doesn't give s_u.
- Check for disturbance (low strain at failure, the sample-quality ratio Δe/e0 on
  [preconsolidation](06-preconsolidation-and-compressibility.md)).
- A pocket penetrometer may read q_u or s_u, a factor of 2 apart: check the instrument.
- SHANSEP needs a reliable σ′p profile, and carries its uncertainty.

## References

- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Ladd, C.C. (1991). Stability evaluation during staged construction (22nd Terzaghi Lecture). *Journal of
  Geotechnical Engineering* 117(4), 540–615. <https://doi.org/10.1061/(ASCE)0733-9410(1991)117:4(540)>
- Ladd, C.C. and Foott, R. (1974). New design procedure for stability of soft clays. *Journal of the Geotechnical
  Engineering Division*, ASCE 100(GT7), 763–786. <https://doi.org/10.1061/AJGEB6.0000066>
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Mayne, P.W., Coop, M.R., Springman, S.M., Huang, A.-B. and Zornberg, J.G. (2009). Geomaterial behavior and
  testing. *Proc. 17th ICSMGE*, Alexandria, 2777–2872. <https://doi.org/10.3233/978-1-60750-031-5-2777>
- Stroud, M.A. (1974). The standard penetration test in insensitive clays and soft rocks. *Proc. European
  Symposium on Penetration Testing (ESOPT-II)*, Stockholm, Vol. 2, 367–375.
- Terzaghi, K. and Peck, R.B. (1967). *Soil Mechanics in Engineering Practice*, 2nd ed. Wiley.
