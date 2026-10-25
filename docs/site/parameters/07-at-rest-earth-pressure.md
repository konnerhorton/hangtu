# At-rest earth pressure

| | |
|---|---|
| **Parameters** | K0 (coefficient of earth pressure at rest, σ′h0 / σ′v0), K0NC (normally consolidated); σ′h0, σh0 |
| **Material** | Soil (in situ stress in rock is a separate page) |
| **Models that use it** | All numerical models, for the initial stresses (the K0 procedure); Hardening Soil also uses K0NC for the cap |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0, u0); [drained shear strength](04-drained-shear-strength-soil.md) (φ′); [preconsolidation](06-preconsolidation-and-compressibility.md) (OCR) |
| **Feeds** | Elastic and Hardening Soil stiffness (the mean stress p′0); small-strain stiffness; earth pressure on walls that don't yield |

## What it is

K0 is the ratio of horizontal to vertical effective stress in level ground with no lateral strain. During virgin
loading it is roughly constant and close to 1 − sin φ′. On unloading (erosion, glacial retreat, excavation) part of
the horizontal stress stays locked in, so K0 rises with OCR and can exceed 1 in heavily overconsolidated clays, up
to the passive limit (Kulhawy & Mayne 1990, pp. 3-1 to 3-6). Reloading lowers it again, so most natural deposits
sit between the unloading and reloading paths (p. 3-6). Aging, cementation, desiccation and tectonic stress also
change σ′h0, and the correlations don't capture them (Loehr et al. 2016, p. 11-39). K0 is hard to measure: every
in situ device disturbs the ground as it goes in (Kulhawy & Mayne 1990, p. 3-25).

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Numerical models, initial stresses | σ′h0 = K0 σ′v0 in every element | High: sets the deviatoric stress and the distance to failure |
| Walls that don't yield (basement walls, braced or propped excavations at rest) | the lateral pressure K0 σ′v0 + u0 | High: linear in K0 |
| Stress-dependent stiffness (Hardening Soil, HS-small) | p′0 = σ′v0 (1 + 2 K0) / 3 sets the reference stress | Moderate |
| Limit equilibrium stability | weakly, through σh on a wedge | Low |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| K0 | – | – | dimensionless; a ratio of **effective** stresses |
| σh0, σ′h0 | kPa | psf, psi, ksf | 1 kPa = 20.885 psf = 0.1450 psi; 1 ksf = 47.88 kPa |

## Typical values

| Material | Range | Source |
|---|---|---|
| Normally consolidated soils, K0NC = 1 − sin φ′ | φ′ = 20°, 25°, 30°, 35°, 40°: 0.66, 0.58, 0.50, 0.43, 0.36 | computed from Jaky's simplified form (Kulhawy & Mayne 1990, Eq. 3-4, p. 3-3) |
| Overconsolidated soils, (1 − sin φ′) OCR^sin φ′, φ′ = 30° | OCR 2, 4, 10: 0.71, 1.00, 1.58 | computed from Mayne & Kulhawy (1982) (Kulhawy & Mayne 1990, Eq. 3-10, p. 3-6) |
| Physical bounds, φ′ = 40° | Ka 0.22 to Kp 4.6 | Kulhawy & Mayne (1990), p. 3-2 |
| Clays, measured K0, means of 8 site groups | 0.48 to 2.88, mean 1.28 | Ching & Schweckendiek (2021), Table 1.2, p. 11 |
| Sands, measured K0, means of 4 site groups | 0.64 to 2.20, mean 1.16 | Ching & Schweckendiek (2021), Table 1.3, p. 11 |

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Self-boring pressuremeter (lift-off) | – | ISO 22476-6 | `PMTG`: `PMTG_HO`, `PMTG_TYPE`; `PMTP`: `PMTP_HO`, `PMTP_U0` | σh0, the most direct measurement |
| Prebored (Ménard) pressuremeter | D4719 | ISO 22476-4 | `PMMG`: `PMMG_P1` | a rough σh0 (the borehole has unloaded) |
| Flat dilatometer | D6635 | ISO 22476-11 | `DMTT`: `DMTT_P0`; `DMTP`: `DMTP_KD`, `DMTP_K0`, `DMTP_K0M` | K_D, for a K0 correlation |
| CPTu (correlation input) | D5778 | ISO 22476-1 | `SCPT`: `SCPT_QT`, `SCPT_PWP2` | q_t, for a K0 correlation |
| SPT (correlation input) | D1586/D1586M | ISO 22476-3 | `ISPT`: `ISPT_NVAL` | field N, for the correlation below |
| K0-consolidated triaxial | D4767 or D7181, consolidated anisotropically | ISO 17892-9 | `TREG_TYPE` (CAUC, CAUE, CADC, CADE) | K0NC in the laboratory; K0 on unloading |
| Oedometer (for OCR) | D2435, D4186 | ISO 17892-5 | `CONG`, `CONS` ([preconsolidation](06-preconsolidation-and-compressibility.md)) | σ′p, so OCR |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Kulhawy et al. (1989), as given by Kulhawy & Mayne (1990) | field N, σ′v0 | clays; 0 < N pa/σ′v0 ≤ 60 | [`ht.analysis.correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989()`](../reference/correlations.md#hangtu.analysis.correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989) |
| Jaky, simplified: K0NC = 1 − sin φ′ (Kulhawy & Mayne 1990, Eq. 3-4, p. 3-3) | φ′ in triaxial compression | virgin loading, uncemented soils | W3 |
| Mayne & Kulhawy (1982), primary unloading: K0 = (1 − sin φ′) OCR^sin φ′ (Kulhawy & Mayne 1990, Eq. 3-10, p. 3-6; Loehr et al. 2016, Eq. 11.31, p. 11-39) | φ′, OCR | mechanically overconsolidated, uncemented clays, silts and sands | W3 |
| Mayne & Kulhawy (1982), unloading and reloading (Kulhawy & Mayne 1990, Eq. 3-9, p. 3-6) | φ′, OCR, OCR_max | soils reloaded after unloading | W3 |
| Passive limit: K0 ≤ Kp (Kulhawy & Mayne 1990, Eq. 3-1, p. 3-2) | φ′ in plane strain | a cap on any estimate | W3 |
| CPTu, K0 ≈ 0.1 (q_t − σv0) / σ′v0, Kulhawy et al. (1989) (Kulhawy & Mayne 1990, Eq. 3-32) | q_t, σv0, σ′v0 | clays | later |
| Dilatometer, K0 = (K_D / 1.5)^0.47 − 0.6, Marchetti (1980) (Kulhawy & Mayne 1990, Eq. 3-29, p. 3-25) | K_D | insensitive, uncemented clays; low in fissured overconsolidated clays | later |

The SPT correlation reads field N, as measured, because its data predate energy correction; σ′v0 comes from
`ht.analysis.vertical_stress()`. Its equation, range and sources are in its reference entry, and
[(N1)60 and correlations](../guides/correlations.md) shows the correlations on the example project.

## How the methods compare

Measured σh0 (self-boring pressuremeter) is the basis where there is one. Without it, K0 from φ′ and an oedometer
OCR (Mayne & Kulhawy 1982) carries the uncertainty of OCR as roughly OCR^0.5. The SPT
correlation is a check, and a biased one: on the TC304 clay database, measured K0 averaged about twice its estimate
(below). Assuming OCR = 1 where there is no oedometer data gives the lowest K0, and underestimates K0 in most
natural deposits (Kulhawy & Mayne 1990, p. 3-6). Choosing a design value is stage D (M18).

## Variability

- Measured K0, COV within a site: clays 2.4 to 22 %, mean 13.5 %; sands 25.8 to 36.9 %, mean 33.1 % (Ching &
  Schweckendiek 2021, Tables 1.2 and 1.3, p. 11).
- SPT, Kulhawy et al. (1989): n = 57, r² = 0.771, S.D. = 0.43, on 13 intact and 5 fissured clays (Kulhawy & Mayne
  1990, Eq. 3-31, p. 3-27, and Fig. 3-30, p. 3-28). On the TC304 clay database (n = 74), the mean of measured over
  estimated K0 is b = 2.16, with COV δ = 0.70 (Ching & Schweckendiek 2021, Table 5.2, p. 178).
- Mayne & Kulhawy (1982): b = 1.00, δ = 0.34 for clay (n = 1009, φ′ = 25° assumed); b = 1.05, δ = 0.50 for sand
  (n = 1207, φ′ = 30°) (Ching & Schweckendiek 2021, Tables 5.2 and 5.3, pp. 178–179).

## Pitfalls

- Use effective stresses: K0 = (σh0 − u0) / σ′v0. Pressuremeters and dilatometers give total σh0.
- Use φ′ from triaxial compression; a plane-strain or residual φ′ shifts K0NC.
- K0 from primary unloading is an upper bound for a soil that has since been reloaded (Kulhawy & Mayne 1990,
  p. 3-21).
- Cap K0 at Kp. A K0 above 1 in sand, or well above it in clay, needs a geological reason (erosion, glacial
  loading).
- Desiccated crusts give a high OCR and K0 near the surface, where σ′v0 is small.
- In cemented, aged or tectonically stressed ground the correlations don't apply; measure σh0 (Loehr et al. 2016,
  p. 11-39).
- AGS `DMTP_K0` is the contractor's correlation, named in `DMTP_K0M`; don't pool it with estimates from other
  methods.
- The SPT correlation reads field N, not N60, and is for clays. Pass the rows it applies to, or `uscs="proposed"`
  with a `uscs_symbol` column to give no estimate outside CL and CH.

## References

- Ching, J. and Schweckendiek, T. (eds.) (2021). *State-of-the-art review of inherent variability and uncertainty
  in geotechnical properties and models.* ISSMGE TC304. <https://doi.org/10.53243/R0001>
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Kulhawy, F.H., Jackson, C.S. and Mayne, P.W. (1989). *Foundation Engineering: Current Principles and Practices*,
  ASCE, 121–134.
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Mayne, P.W. and Kulhawy, F.H. (1982). K0–OCR relationships in soil. *Journal of the Geotechnical Engineering
  Division*, ASCE 108(GT6), 851–872. <https://doi.org/10.1061/AJGEB6.0001306>
