# Drained shear strength of soil

| | |
|---|---|
| **Parameters** | φ′ (effective friction angle: peak φ′p, critical-state φ′cv, residual φ′r), c′ (effective cohesion intercept) |
| **Material** | Soil |
| **Models that use it** | Mohr–Coulomb, Hardening Soil and HS-small (failure line), Modified Cam Clay (through M = 6 sin φ′cv / (3 − sin φ′cv)) |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0 for the SPT correlations); index properties (PI, fines); relative density |
| **Feeds** | Undrained shear strength (critical-state ratios), at-rest earth pressure, dilatancy, Hardening Soil stiffness |

## What it is

Drained strength is the frictional resistance on the effective-stress failure envelope:

$$
\tau_f = c' + \sigma'_n \tan\phi'
$$

The peak angle φ′p is the critical-state angle φ′cv plus a dilatancy component that grows with density and falls
with confining stress (Bolton 1986). φ′cv is a material constant, set by mineralogy and grading. The residual angle
φ′r of a plastic clay after large displacement, when platy particles have aligned, can be much lower. The intercept
c′ of a straight-line fit is mostly the curvature of the envelope, plus any true bonding (cementation, structure):
it depends on the stress range of the fit, and for uncemented normally consolidated soils it is often taken as
zero. Strength also depends on the loading mode: triaxial compression gives a lower φ′ than plane strain, and
extension and direct shear differ again.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Bearing capacity of shallow foundations | the bearing capacity factors grow steeply with tan φ′ | High: a few degrees change the capacity by large factors |
| Slope stability | resisting shear along the slip surface | High, roughly linear in tan φ′; c′ matters most for shallow slips |
| Earth pressure on walls | Ka and Kp from φ′ | Moderate for active, high for passive |
| Face support of a tunnel, limit equilibrium | resisting shear on the wedge and silo | High in sands and silts |
| Numerical models (Mohr–Coulomb, Hardening Soil) | the yield or failure surface; the extent of plastic zones | High near failure; moderate where the response is mostly elastic |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| φ′ | degrees (°) | degrees (°) | 1 rad = 57.2958° |
| c′ | kPa | psf, psi | 1 kPa = 20.885 psf = 0.1450 psi |

## Typical values

| Material | Range | Source |
|---|---|---|
| Sand by SPT N: very loose (0–4), loose (4–10), medium (10–30), dense (30–50), very dense (> 50) | φ′ (triaxial compression) < 28°, 28–30°, 30–36°, 36–41°, > 41° | Kulhawy & Mayne (1990), Table 4-3, after Peck, Hanson & Thornburn (1974) |
| Normally consolidated clay, PI 10, 20, 40 and 80 % | φ′cv about 36°, 31°, 27° and 23° | from sin φ′cv ≈ 0.8 − 0.094 ln PI, Kulhawy & Mayne (1990), Fig. 4-20, p. 4-21 |

The SPT classes place a sand roughly; they aren't a design value.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Drained triaxial (CD) | D7181 | ISO 17892-9; BS 1377-8 | `TREG`: `TREG_TYPE`, `TREG_PHI`, `TREG_COH`, `TREG_FCR`; `TRET`: `TRET_CELL`, `TRET_DEVF`, `TRET_PWPF`, `TRET_STRN` | σ′1f, σ′3f per specimen, for an s′–t fit |
| Undrained triaxial with pore pressure (CU) | D4767 | ISO 17892-9; BS 1377-8 | as above (`TREG_TYPE` CU, CIUC, CAUC) | effective stresses at failure; also s_u |
| Direct shear (shear box) | D3080/D3080M | ISO 17892-10; BS 1377-7 | `SHBG`: `SHBG_PHI`, `SHBG_PCOH`, `SHBG_RPHI`, `SHBG_RCOH`; `SHBT`: `SHBT_NORM`, `SHBT_PEAK`, `SHBT_RES` | τ–σ′n pairs, peak and residual |
| Ring shear (residual) | D6467; D7608 (fully softened) | BS 1377-7 | `SHBG_TYPE` ring shear; `SHBG_RPHI`, `SHBT_RES` | φ′r |
| SPT (correlation input) | D1586/D1586M; energy D4633 | ISO 22476-3 | `ISPT`: `ISPT_NVAL`, `ISPT_ERAT`, `ISPT_N60` | N, N60, (N1)60 for the correlations below |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Hatanaka & Uchida (1996), at 60 % energy (Loehr et al. 2016) | (N1)60 | relatively clean fine to medium sands; 4.55 ≤ (N1)60 ≤ 39 | [`ht.analysis.correlations.hatanaka_uchida_1996()`](../reference/correlations.md#hangtu.analysis.correlations.hatanaka_uchida_1996) |
| Kulhawy & Mayne (1990), after Schmertmann (1975) | N60, σ′v0 | relatively clean sands; σ′v0 ≤ 300 kPa, N60 ≤ 60 | [`ht.analysis.correlations.kulhawy_mayne_1990()`](../reference/correlations.md#hangtu.analysis.correlations.kulhawy_mayne_1990) |
| Wolff (1989), a fit to Peck, Hanson & Thornburn (1974) | (N1)60 | sands | not built: its equation isn't yet verified against the source |
| s′–t fit of triaxial results | σ′1f, σ′3f of each specimen in a unit | saturated specimens, one failure criterion | W2 |
| Direct shear envelope (Kulhawy & Mayne 1990, Eq. 4-10, Table 4-5, p. 4-25) | τ and σ′n of each stage | drained shear on a forced plane | W2 |
| φ′cv from PI (Kulhawy & Mayne 1990, Fig. 4-20) | PI | normally consolidated clays | later |
| Peak from φ′cv and dilatancy (Bolton 1986; Kulhawy & Mayne 1990, Eqs. 4-5 to 4-7) | φ′cv, relative density, p′ | sands | later |

The SPT correlations need (N1)60 or N60 and σ′v0, from `ht.analysis.spt_n1_60()` and
`ht.analysis.vertical_stress()`. Each reads the one N it was derived with, and gives no estimate, with a count,
outside its range or for a refusal. The equations, ranges and sources are in each function's reference entry, and
[(N1)60 and correlations](../guides/correlations.md) shows them on the example project.

## How the methods compare

Triaxial and direct shear results on the unit's own soil are the basis, and overrule an SPT estimate. The SPT
correlations are for sands only and give the peak angle in triaxial compression. For the same test they differ by
a few degrees: at N60 = 20 and σ′v0 = 50 kPa, Hatanaka & Uchida gives 40.9° (with Liao & Whitman's C_N) and Kulhawy
& Mayne 43.9°; at N60 = 10 and 100 kPa, 32.4° and 33.8°. Comparing them on one profile, colored by
`correlation_name`, shows where they agree. Choosing a design value from them is stage D (M18).

A direct shear φ′ is not a triaxial φ′: convert before combining them (Kulhawy & Mayne 1990, Eq. 4-10).

## Variability

- Sand, laboratory φ′ at 16 sites with at least 10 tests each: COV 4.2–12.5 % (Ching & Schweckendiek 2021,
  Table 1.A2, pp. 54–55).
- Hatanaka & Uchida (1996): most of their data within ±3° of the correlation. Kulhawy & Mayne state no scatter.
- An SPT estimate carries the scatter of N and of the correlation, on top of the soil's own variability.

## Pitfalls

- Check the N each correlation takes: field N, N60 or (N1)60. hangtu reads the one column each was derived with,
  and a missing one is an error naming what adds it.
- Hatanaka & Uchida's paper gives its equation for N1 at 78 % energy; with (N1)60 it overstates φ′ by up to about
  3°. hangtu uses the 60 % form (Loehr et al. 2016, Eq. 7.23).
- SPT in gravel or cobbles overstates φ′; neither correlation is for gravelly soils. hangtu doesn't read the soil
  type: pass the rows a correlation applies to.
- Kulhawy & Mayne is somewhat conservative at depths less than about 6 ft (1.8 m) (Loehr et al. 2016, p. 7-55).
- Fit s′–t per unit, not per test, and report the stress range of the fit: c′ doesn't extrapolate to σ′ = 0.
- Check saturation (B value) and the drainage rate; an undrained test without pore pressure can't give φ′.
- Don't mix failure criteria (maximum q, maximum σ′1/σ′3) or peak and residual points in one fit; fit multistage
  tests with and without the later stages.
- Use φ′cv, not the peak, for large strains and progressive failure.

## References

- Bolton, M.D. (1986). The strength and dilatancy of sands. *Géotechnique* 36(1), 65–78.
  <https://doi.org/10.1680/geot.1986.36.1.65>
- Ching, J. and Schweckendiek, T. (eds.) (2021). *State-of-the-art review of inherent variability and uncertainty in
  geotechnical properties and models.* ISSMGE TC304. <https://doi.org/10.53243/R0001>
- Hatanaka, M. and Uchida, A. (1996). Empirical correlation between penetration resistance and internal friction
  angle of sandy soils. *Soils and Foundations* 36(4), 1–9. <https://doi.org/10.3208/sandf.36.4_1>
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Peck, R.B., Hanson, W.E. and Thornburn, T.H. (1974). *Foundation Engineering*, 2nd ed. Wiley.
- Schmertmann, J.H. (1975). Measurement of in situ shear strength. *Proc. ASCE Specialty Conference on In Situ
  Measurement of Soil Properties*, Raleigh.
- Wolff, T.F. (1989). Pile capacity prediction using parameter functions. *Predicted and Observed Axial Behavior of
  Piles*, ASCE GSP 23, 96–106.
