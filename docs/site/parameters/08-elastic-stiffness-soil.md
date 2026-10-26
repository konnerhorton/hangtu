# Elastic stiffness of soil

| | |
|---|---|
| **Parameters** | E (Young's modulus: drained E′ or undrained Eu), ν (Poisson's ratio), G (shear modulus) |
| **Material** | Soil |
| **Models that use it** | Linear elastic and Mohr–Coulomb (E, ν); Hardening Soil uses its own moduli instead |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0); [preconsolidation](06-preconsolidation-and-compressibility.md) (OCR); [small-strain stiffness](10-small-strain-stiffness.md) (G0) |
| **Feeds** | Settlement of foundations and embankments; displacements in numerical models; [at-rest earth pressure](07-at-rest-earth-pressure.md) (the ν–K0 check) |

## What it is

Soil isn't linear elastic. Its secant stiffness falls by one to two orders of magnitude from very small strains
(G0, from shear wave velocity) to failure, and rises with mean effective stress. A single E is a secant value that
holds at one strain level, stress level and stress path: field tests sit at different points on that curve, and
modulus values "consistent with working strains induced in the field must be established" (Loehr et al. 2016,
§8.9, p. 8-25). Drained (E′, ν′) and undrained (Eu, νu → 0.5) constants describe the same soil skeleton: G is the
same in both, and undrained behavior comes from the pore water stopping volume change. In isotropic elasticity,

$$
G = \frac{E}{2(1+\nu)}, \qquad E_u = \frac{3E'}{2(1+\nu')} \quad (\nu_u = 0.5)
$$

so Eu/E′ is 1.25, 1.20 and 1.15 for ν′ = 0.2, 0.25 and 0.3 (computed).

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Settlement of shallow foundations (elastic) | s ∝ q B (1 − ν²) / E | High: inversely proportional to E |
| Numerical models, Mohr–Coulomb | one E scales every elastic displacement | High for displacements; a stiff layer below controls heave |
| Retaining structures and linings (beam on springs) | subgrade reaction from E | Moderate |
| Limit equilibrium stability | not used | Low: strength governs |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| E, G | kPa, MPa | psf, ksf, tsf, psi, ksi | 1 MPa = 20.885 ksf = 145.04 psi = 10.443 tsf; 1 tsf = 2 ksf = 95.76 kPa; 1 ksi = 6.895 MPa |
| ν | – | – | dimensionless |

**Unit trap.** FHWA NHI-06-088 gives E from SPT as 4, 7, 10 and 12 × (N1)60 in **tsf** (Samtani & Nowatzki 2006,
Table 5-16, p. 5-85). Read as ksf, the same factors halve E. hangtu keeps the constants in tsf and converts them,
and displays E in MPa or ksf.

## Typical values

| Material | E | ν | Source |
|---|---|---|---|
| Clay, soft sensitive / medium stiff to stiff / very stiff | 25–150 / 150–500 / 500–1000 tsf (2.4–14 / 14–48 / 48–96 MPa) | 0.4–0.5 (undrained) | Samtani & Nowatzki (2006), Table 5-16, p. 5-85 |
| Silt | 20–200 tsf (1.9–19 MPa) | 0.3–0.35 | same |
| Sand, loose / medium dense / dense | 100–300 / 300–500 / 500–800 tsf (9.6–29 / 29–48 / 48–77 MPa) | 0.20–0.36 loose, 0.30–0.40 dense | same |
| Gravel, loose / medium dense / dense | 300–800 / 800–1000 / 1000–2000 tsf (29–77 / 77–96 / 96–192 MPa) | 0.20–0.35 loose, 0.30–0.40 dense | same |
| Coarse-grained soils, drained loading | – | about 0.1–0.2 | Loehr et al. (2016), p. 8-26 |

The same ranges in ksi are in Loehr et al. (2016), Table 8-10, p. 8-26. MPa values are computed.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Triaxial CU / CD | D4767; D7181 | ISO 17892-9 | `TRET`: `TRET_E50` | E50, the secant modulus at half the peak deviator stress |
| Triaxial UU / unconfined | D2850; D2166 | ISO 17892-8, -7 | `TRIT`, `LUCT` | Eu, low where samples are disturbed |
| Oedometer | D2435 | ISO 17892-5 | `CONS`: `CONS_INMV` | constrained modulus, 1/mv |
| Pressuremeter | D4719 | ISO 22476-4, -6 | `PMTP`, `PMTL` | G from first loading and from unload–reload loops |
| Flat dilatometer | D6635 | ISO 22476-11 | `DMTP`: `DMTP_ED` | dilatometer modulus E_D |
| SPT (correlation input) | D1586/D1586M | ISO 22476-3 | `ISPT`: `ISPT_NVAL` | N, for the correlations below |
| Seismic (Vs) | D4428; D7400 | – | `ISTA`: `ISTA_WVL` | G0, see [small-strain stiffness](10-small-strain-stiffness.md) |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| AASHTO (2004), E = C (N1)60 tsf, C by soil row (Samtani & Nowatzki 2006, Table 5-16) | (N1)60 | silts, sands and gravels, by the source's rows | [`ht.analysis.correlations.drained_youngs_modulus_aashto_2004()`](../reference/correlations.md#hangtu.analysis.correlations.drained_youngs_modulus_aashto_2004) |
| Kulhawy & Mayne (1990), E/pa = C N60, C by soil row (EPRI Eqs. 5-26a–c) | N60 | sands with fines, clean NC and clean OC sands | [`ht.analysis.correlations.drained_youngs_modulus_kulhawy_mayne_1990()`](../reference/correlations.md#hangtu.analysis.correlations.drained_youngs_modulus_kulhawy_mayne_1990) |
| E50 and Eu from triaxial tests | stress–strain curves | tested specimens | W2 |
| Constrained modulus from the oedometer | mv | tested specimens | W3 |
| Equivalent modulus from Vs with a modulus reduction ratio (Loehr et al. 2016, Eqs. 8.17–8.18 and Fig. 8-15, pp. 8-25 to 8-27) | Vs, ρ, ν, E/Emax | intact clays and uncemented sands under foundations | W5 |

Both SPT correlations take their coefficient from the source's soil row, which `soil=` names: one row for every
test, or a row per geology unit. hangtu never infers it, and `uscs=` only checks it. The equations, rows, ranges
and sources are in the reference entries, and [(N1)60 and correlations](../guides/correlations.md) shows them on
the example project.

## How the methods compare

Measured stiffness at the right strain level is the basis where there is one: pressuremeter or dilatometer tests,
or Vs with a reduction for strain. Both SPT correlations give a drained, working-strain secant modulus "as a first
order estimator" (Kulhawy & Mayne 1990, p. 5-17); NHI-06-088 gives its table "for preliminary design" (p. 5-83).
They are not interchangeable with E0 from Vs, which is far stiffer, nor with an undrained Eu. Choosing a design
value is stage D (M18).

## Variability

- Neither SPT correlation gives a statistic. "All attempts to date which correlate a modulus with N show
  considerable scatter" (Kulhawy & Mayne 1990, p. 5-17), and the relationships "should only be considered as
  approximate estimates" (Loehr et al. 2016, p. 8-25).
- The two SPT correlations differ for the same sand: for (N1)60 = N60 = 20 in a clean sand, AASHTO gives 13.4 MPa
  and Kulhawy & Mayne 20 MPa (NC) or 30 MPa (OC) (computed).

## Pitfalls

- Check the unit of any E-from-N table: tsf against ksf is a factor of 2.
- Match the strain level: E0 from Vs is much larger than a working-strain E. With E/E0 = 1 − (q/q_ult)^0.3 for
  intact clays and uncemented sands (Loehr et al. 2016, Fig. 8-15, p. 8-27), E/E0 is 0.38 at q/q_ult = 0.2 and
  0.19 at 0.5 (computed).
- Unloading problems (excavations, tunnels) need an unload–reload modulus, not E50 or a loading E.
- Eu from disturbed UU or unconfined samples underestimates stiffness.
- Don't mix drained E′ and undrained Eu; convert with the relation above.
- E grows with depth and stress, so one E for a thick layer hides the trend.
- The AASHTO correlation reads (N1)60 and Kulhawy & Mayne N60: hangtu raises if the column isn't there, and never
  corrects one into the other.

## References

- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Samtani, N.C. and Nowatzki, E.A. (2006). *Soils and Foundations Reference Manual*, Vol. I. FHWA NHI-06-088.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi06088.pdf>
- AASHTO (2004). *LRFD Bridge Design Specifications*, with 2006 Interims. American Association of State Highway
  and Transportation Officials. (Cited through Samtani & Nowatzki 2006.)
