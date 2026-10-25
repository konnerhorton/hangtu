# Preconsolidation and compressibility

| | |
|---|---|
| **Parameters** | σ′p (preconsolidation or yield stress), OCR = σ′p / σ′v0 (overconsolidation ratio), Cc (compression index), Cs or Cr (swelling or recompression index) |
| **Material** | Soil, mainly fine-grained |
| **Models that use it** | Soft Soil and Modified Cam Clay (λ* = Cc / (2.3 (1 + e)), κ*), Hardening Soil (OCR or POP sets the initial cap), SHANSEP |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0); index properties (LL, PI); specific gravity and void ratio (e0) |
| **Feeds** | [Undrained shear strength](05-undrained-shear-strength.md) (SHANSEP), [at-rest earth pressure](07-at-rest-earth-pressure.md) (K0 from OCR), Hardening Soil stiffness (Eoed, POP) |

## What it is

In one-dimensional compression a soil is stiff, on the recompression slope Cr, up to the largest effective stress
it has carried, or to a yield stress raised by aging and cementation: σ′p. Beyond it, the soil compresses along the
much steeper virgin line, slope Cc in e–log σ′v; unloading follows the swelling slope Cs. OCR = σ′p / σ′v0
summarizes the stress history and controls K0, s_u and stiffness. σ′p is a yield point, not a sharp break: its
value depends on the method used to read it off the curve, on the loading rate (higher in constant rate of strain
tests), and above all on sample disturbance, which rounds the curve, lowers σ′p and raises Cr. Cc depends on
mineralogy, water content and structure.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Consolidation settlement | Δe = Cr log(σ′p / σ′v0) + Cc log(σ′vf / σ′p) when σ′vf > σ′p | High: whether the final stress passes σ′p decides whether the soil compresses on the virgin line |
| Numerical models (Soft Soil, Hardening Soil) | λ*, κ*; OCR or POP sets the cap, so the initial stiffness and yield | High in clay |
| Initial stresses | K0 rises with OCR ([at-rest earth pressure](07-at-rest-earth-pressure.md)) | Moderate to high |
| Undrained strength (SHANSEP) | s_u rises with OCR^m | High |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| σ′p, σ′v0 | kPa | psf, tsf | 1 kPa = 20.885 psf; 1 tsf = 95.76 kPa |
| OCR | – | – | dimensionless |
| Cc, Cs, Cr | – (per log cycle of stress) | – | the same in any units; the compression ratio CR = Cc / (1 + e0) |

## Typical values

| Material | Range | Source |
|---|---|---|
| Compressibility slight, moderate, high | Cc < 0.2, 0.2–0.4, > 0.4 | Kulhawy & Mayne (1990), Table 6-1, p. 6-4 |
| Normally consolidated clay, LL 30, 50 and 80 % | Cc ≈ 0.18, 0.36 and 0.63 | from Cc = 0.009 (LL − 10), Kulhawy & Mayne (1990), Eq. 6-5, p. 6-4, after Terzaghi & Peck (1967) |
| Clays, Cs / Cc | about 0.1 to 0.3 | from Λ = 1 − Cs/Cc ≈ 0.8 ± 0.1, Mayne et al. (2009), p. 2789 |
| Clays, σ′p / (q_t − σv0) | 0.2 to 0.5, average 0.33 | Robertson & Cabal (2022), p. 44 |

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Incremental-load oedometer | D2435/D2435M | ISO 17892-5; BS 1377-5 | `CONG`: `CONG_TYPE`, `CONG_COND`, `CONG_IVR`, `CONG_HIGT`; `CONS`: `CONS_INCN`, `CONS_INCF`, `CONS_INCE`, `CONS_INMV` | e against σ′v, for σ′p, Cc, Cs |
| Constant rate of strain; Rowe cell | D4186/D4186M | BS 1377-6 | `ESCG`: `ESCG_PCP`, `ESCG_YSR`, `ESCG_CC`, `ESCG_CS`, `ESCG_IVR`; `ESCT`: `ESCT_INCF`, `ESCT_VR0` | a continuous curve; the laboratory's σ′p, Cc, Cs |
| CPTu (correlation input) | D5778 | ISO 22476-1 | `SCPT`: `SCPT_QT` | q_net, for σ′p |
| SPT (correlation input) | D1586/D1586M | ISO 22476-3 | `ISPT`: `ISPT_NVAL` | field N, for the correlations below |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| σ′p, Mayne & Kemper (1988), as given by Kulhawy & Mayne (1990) | field N | clays; 0.5 ≤ N ≤ 200 | [`ht.analysis.correlations.preconsolidation_stress_mayne_kemper_1988()`](../reference/correlations.md#hangtu.analysis.correlations.preconsolidation_stress_mayne_kemper_1988) |
| OCR, Mayne & Kemper (1988), as given by Kulhawy & Mayne (1990) | field N, σ′v0 | clays; 1 ≤ N pa/σ′v0 ≤ 100 | [`ht.analysis.correlations.overconsolidation_ratio_mayne_kemper_1988()`](../reference/correlations.md#hangtu.analysis.correlations.overconsolidation_ratio_mayne_kemper_1988) |
| σ′p, Cc and Cs from an oedometer curve | e and σ′v of each increment | specimens of known quality, with points on both sides of σ′p | W3 |
| Cc from LL, Cc = 0.009 (LL − 10) (Kulhawy & Mayne 1990, Eq. 6-5, after Terzaghi & Peck 1967) | LL | normally consolidated clays | W3 |
| CPTu, σ′p ≈ 0.33 (q_t − σv0) (Mayne et al. 2009, Eq. 4.15, p. 2832) | q_t, σv0 | intact clays; low in fissured clays | later |

The two SPT correlations are separate regressions on different data, so an OCR from one isn't σ′p / σ′v0 from the
other: at the same test they differ (0.58 against 0.47). Both read field N, as measured, because their data predate
energy correction; the OCR correlation also reads σ′v0, from `ht.analysis.vertical_stress()`. The equations, ranges
and sources are in each function's reference entry, and [(N1)60 and correlations](../guides/correlations.md) shows
the correlations on the example project.

## How the methods compare

Oedometer tests on good-quality samples of the unit are the basis, and overrule an SPT estimate. SPT N is a poor
predictor in clay: use the SPT correlations to check an oedometer σ′p profile, or to sketch one where there is none,
not to set a design value. Fissured clays plot above the Mayne & Kemper trend (Kulhawy & Mayne 1990, Fig. 3-9).
Choosing a design value is stage D (M18).

## Variability

- σ′p from N, Mayne & Kemper: n = 126, r² = 0.699, S.D. = 4.37 pa, on 49 intact and 2 fissured clays (Kulhawy &
  Mayne 1990, Fig. 3-9, p. 3-10).
- OCR from N, Mayne & Kemper: n = 112, r² = 0.661, S.D. = 3.82, on 48 intact and 3 fissured clays (Kulhawy &
  Mayne 1990, Fig. 3-18, p. 3-18).
- An SPT estimate carries the scatter of N and of the correlation, on top of the soil's own variability.

## Pitfalls

- Grade each specimen before using its σ′p. By Δe/e0 = (e0 − e at σ′v0) / e0, for OCR 1 to 2, below 0.04 is very
  good to excellent and above 0.14 very poor; for OCR 2 to 4, below 0.03 and above 0.10 (Lunne et al. 1997, as
  given by Amundsen et al. 2016, Table 1). Poor samples give σ′p too low and Cr too high.
- Read σ′p and Cc from the loading branch, and Cs from a clear unload–reload loop; a reload slope isn't Cc.
- Check σ′v0 at the specimen depth (water level, unit weight): an OCR is often wrong through σ′v0, not σ′p.
- An OCR below 1 means disturbance, a wrong σ′v0 or an underconsolidated deposit: flag it, don't clip it.
- σ′p from a constant rate of strain test depends on the rate and is higher than from an incremental test; note
  which before combining them.
- The SPT correlations read field N, not N60. hangtu reads the column each was derived with, and a missing one is
  an error naming what adds it.
- The correlations are for clays. Pass the rows they apply to, or `uscs="proposed"` with a `uscs_symbol` column to
  give no estimate outside CL and CH.
- Check whether the laboratory reports Cc (e–log σ′v) or CR (ε–log σ′v).

## References

- Amundsen, H.A., Thakur, V. and Emdal, A. (2016). Sample disturbances in block samples on low plastic soft clays.
  *Proc. 17th Nordic Geotechnical Meeting (NGM 2016)*, Reykjavik.
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Lunne, T., Berre, T. and Strandvik, S. (1997). Sample disturbance effects in soft low plastic Norwegian clay.
  *Proc. Symposium on Recent Developments in Soil and Pavement Mechanics*, Rio de Janeiro, 81–102.
- Mayne, P.W., Coop, M.R., Springman, S.M., Huang, A.-B. and Zornberg, J.G. (2009). Geomaterial behavior and
  testing. *Proc. 17th ICSMGE*, Alexandria, 2777–2872. <https://doi.org/10.3233/978-1-60750-031-5-2777>
- Mayne, P.W. and Kemper, J.B. (1988). *Geotechnical Testing Journal* 11(2), 139–147.
- Robertson, P.K. and Cabal, K.L. (2022). *Guide to Cone Penetration Testing*, 7th ed. Gregg Drilling.
- Terzaghi, K. and Peck, R.B. (1967). *Soil Mechanics in Engineering Practice*, 2nd ed. Wiley.
