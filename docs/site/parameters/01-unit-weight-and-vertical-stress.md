# Unit weight and vertical stress

| | |
|---|---|
| **Parameters** | γ (bulk unit weight), γsat (saturated), γd (dry), γ′ (buoyant), σv0 (total vertical stress), u0 (in situ pore pressure), σ′v0 (effective vertical stress) |
| **Material** | Both: soil and intact rock |
| **Models that use it** | All: Mohr–Coulomb, Hardening Soil, generalized Hoek–Brown (self-weight, initial stress, stress-dependent stiffness) |
| **Depends on** | Water content; [specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (phase relations) |
| **Feeds** | Drained and undrained strength, preconsolidation and OCR, K0, small-strain stiffness, Hardening Soil stiffness, in situ stress in rock |

## What it is

Unit weight is the weight of a unit volume of ground: solids, water and air. Density is the mass equivalent,
γ = ρg. It is controlled by mineralogy (Gs), packing (e or n) and the degree of saturation, so within one geology
unit it varies much less than strength or stiffness does.

Integrated over depth, unit weight gives the total vertical stress σv0. Subtracting the pore pressure u0 gives
the effective vertical stress σ′v0, which controls the strength, stiffness and stress history of soil:

$$
\sigma_{v0} = \sum_i \gamma_i \,\Delta z_i, \qquad
u_0 = \gamma_w \max(0,\ z - z_w), \qquad
\sigma'_{v0} = \sigma_{v0} - u_0
$$

where γi is the unit weight of layer i over its thickness Δzi above depth z (γsat below the water table), zw is the
depth of the water table and γw the unit weight of water (Loehr et al. 2016, eqs. 11.26–11.29). Pore pressure is
hydrostatic only where there is no vertical flow: artesian or under-drained conditions come from piezometers, not
from a water-table depth (Loehr et al. 2016, §11.8.2).

Related definitions: γ = γd (1 + w) (Kulhawy & Mayne 1990, eq. 2-9; Loehr et al. 2016, eq. 4.9);
γsat = γw (Gs + e) / (1 + e); γ′ = γsat − γw.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Initial stress in a numerical model | σv0 from γ; σh0 = K0 σ′v0 + u0 | Moderate: linear in γ, but γ varies little. The water level matters more |
| Stress-dependent stiffness (Hardening Soil) | E = E_ref (σ′/p_ref)^m | Low to moderate, through σ′v0 |
| Face support of a closed-face tunnel | target ≈ K σ′v0 + u0 at the face | Moderate for γ; high for u0 |
| Loads on linings, walls and buried structures | load ∝ γ × cover | Moderate, linear |
| Uplift and flotation | weight of cover (γ) against buoyancy (γw) | High where cover is small |
| SPT and CPT correlations | (N1)60 and normalized cone resistance take σ′v0 | Moderate |

A σ′v0 that is too high is not conservative in a fixed direction: it lowers (N1)60, which is on the safe side for
strength, but it also lowers OCR, which is on the unsafe side for settlement.

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| γ, γsat, γd, γ′ | kN/m³ | pcf (lbf/ft³) | 1 kN/m³ = 6.3659 pcf; 1 pcf = 0.15709 kN/m³ |
| ρ (AGS `LDEN`, `IDEN`, `TRET`) | Mg/m³ (= g/cm³) | lb/ft³ | γ [kN/m³] = ρ [Mg/m³] × 9.80665 |
| ρ (AGS `RDEN`) | kg/m³ | lb/ft³ | γ [kN/m³] = ρ [kg/m³] × 9.80665 / 1000 |
| σv0, u0, σ′v0 | kPa | psf, ksf, psi | 1 kPa = 20.885 psf = 0.02089 ksf = 0.1450 psi |
| γw | 9.81 kN/m³ | 62.4 pcf | Fresh water at 20 °C 9.789 kN/m³; seawater (1025 kg/m³) 10.05 kN/m³ |

hangtu uses one γw, `ht.settings.water_unit_weight`, 9.81 kN/m³ by default, converted to 62.45 pcf in US units.
Set it to `"62.4 pcf"`, or to a seawater value, where that is what the design uses.

## Typical values

| Material | Range | Source |
|---|---|---|
| Soils, loosest to densest state, organic clay to well-graded gravel | γd 4.7–23.2 kN/m³; γsat 12.8–24.5 kN/m³ | Kulhawy & Mayne (1990), Table 2-8, after Hough (1969); ranges by soil type there |
| Intact rock, all types (56 site groups) | site means 18.0–28.1 kN/m³; mean 24.6 kN/m³ | Ching & Schweckendiek (2021), Table 1.4 |
| Limestone (n = 778) | 22–28.2 kN/m³; mean 26.2 kN/m³ | Ching & Schweckendiek (2021), Appendix, after Sabatakakis et al. (2008) |

The soil ranges span the loosest to the densest states; natural in situ values usually sit in the middle to upper
part of them.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Density of a soil specimen | D7263 | ISO 17892-2; BS 1377-2 | `LDEN`: `LDEN_BDEN`, `LDEN_DDEN` (Mg/m³), `LDEN_MC` | ρ, ρd, w |
| Initial state in strength and consolidation tests | D4767, D7181, D2435, D3080 | ISO 17892-5, -7, -8, -9, -10 | `TRET_BDEN`, `TRIT_BDEN`, `CONG_BDEN`, `SHBT_BDEN` and their dry densities and water contents | ρ, ρd, w (as checks) |
| Field density | D1556 (sand cone), D2937 (drive cylinder), D6938 (nuclear) | BS 1377-9 | `IDEN`: `IDEN_IDEN` (Mg/m³), `IDEN_MC` | in-place ρ, w |
| Rock density and porosity | | ISRM (1979) | `RDEN`: `RDEN_BDEN`, `RDEN_DDEN` (kg/m³), `RDEN_PORO`, `RDEN_MC` | ρ, ρd, n, w |
| CPT / CPTu | D5778 | ISO 22476-1 | `SCPT_BDEN`, `SCPT_CPO`, `SCPT_CPOD`; `CPTP_DUW1`, `CPTP_SUW1` | γ estimate, σv0, σ′v0, u0 |
| Flat dilatometer | D6635 | ISO 22476-11 | `DMTP_BUW`, `DMTP_TVS`, `DMTP_EVS`, `DMTP_U0` | γ estimate, σv0, u0 |
| Groundwater level and pore pressure | | ISO 18674-4 (piezometers) | `MOND` (`MOND_TYPE` WDEP, WHD, PRES), `WSTG_DPTH` | zw, measured u |
| Stratigraphy | | | `GEOL`: `GEOL_TOP`, `GEOL_BASE`, `GEOL_GEOL` | layer thicknesses Δzi |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Layered integration, hydrostatic pore pressure (Loehr et al. 2016) | each hole's log, unit weight by geology unit, water level by hole | level ground, geostatic stress, no vertical flow | [`ht.analysis.vertical_stress()`](../reference/analysis.md#hangtu.analysis.vertical_stress) |
| γd = γ / (1 + w) and γsat = γw (Gs + e) / (1 + e) (definitions) | γ and w of one specimen, Gs | any specimen | [`ht.analysis.phase_relations()`](../reference/analysis.md#hangtu.analysis.phase_relations) |
| γ from CPTu (Robertson & Cabal 2022, p. 39) | qt, fs, Gs | uncemented mineral soils; a check only | not planned |
| γ from DMT (Kulhawy & Mayne 1990, Fig. 2-12) | ID, ED | a check only | not planned |

Unit weights and water levels are judgments: hangtu takes them from the project's judgments file or the call,
never from a default, and records which values it used on the result ([Judgments and vertical
stress](../guides/judgments.md)).

## How the methods compare

Measured densities (`LDEN`, the initial state of strength tests, `RDEN`) are the basis; a unit's median, with its
spread, is the usual starting point for its design value. Values from CPT and DMT carry a transformation error that
isn't quantified, so they check the measured values and aren't pooled with them. A unit with no measurements takes
a value from the typical ranges above, stated as a judgment with its reason.

## Variability

- Soil within a unit: COV of γ about 1–5 % (Zhang et al. 2010, for silty clay, clay and silty sand, in Ching &
  Schweckendiek 2021, Table 3.3); 3.3 % at one clay site (Ching & Schweckendiek 2021, Appendix).
- Intact rock: site COV mean 5.2 %, range 0.4–21.5 % (Ching & Schweckendiek 2021, Table 1.4).
- The water level usually matters more to σ′v0 than the scatter in γ does.

## Pitfalls

- AGS `LDEN` gives density in Mg/m³, not unit weight. A kN/m³ heading such as `LDEN_UWT` is a project addition to
  the dictionary, not AGS 4.2; check its unit.
- `RDEN_BDEN` is in kg/m³ while `LDEN`, `TRET` and `CONG` densities are in Mg/m³: a factor of 1000. hangtu converts
  each by its declared unit on ingest.
- Densities from disturbed samples, or thick-walled samples of granular soil, are approximate (Loehr et al. 2016,
  p. 4-7).
- Rock specimens exclude joints and voids; the unit weight of a weathered or karstic rock mass can be lower.
- Check γ against γd (1 + w) and against γsat from Gs and e: S = w Gs / e should be about 1 below the water table.
  `phase_relations()` flags S above 100 % in `oversaturated`.
- Integrate σv0 continuously across layer boundaries, with γ above the water table and γsat below it. hangtu
  integrates through each hole's log, and stops with an error at a gap or an overlap in it (QC G002, G003).
- Hydrostatic u0 is an assumption: artesian or under-drained heads change σ′v0 at depth (Loehr et al. 2016,
  §11.8.2). hangtu's pore pressure is hydrostatic only, and says so on the result.
- A water level above ground (a flooded load case) adds the water's weight to σv0; hangtu warns when it does.
- Use one value of g (9.80665 m/s²) consistently between ρ → γ and γw.

## References

- Ching, J. and Schweckendiek, T. (eds.) (2021). *State-of-the-art review of inherent variability and uncertainty in
  geotechnical properties and models.* ISSMGE TC304. <https://doi.org/10.53243/R0001>
- ISO 18674-4:2020. *Geotechnical investigation and testing — Geotechnical monitoring by field instrumentation —
  Part 4: Measurement of pore water pressure: Piezometers.* <https://www.iso.org/standard/73819.html>
- ISRM (1979). Suggested methods for determining water content, porosity, density, absorption and related
  properties and swelling and slake-durability index properties. *Int. J. Rock Mech. Min. Sci. & Geomech. Abstr.*
  16(2), 141–156.
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Robertson, P.K. and Cabal, K.L. (2022). *Guide to Cone Penetration Testing for Geotechnical Engineering*, 7th ed.
  Gregg Drilling LLC.
