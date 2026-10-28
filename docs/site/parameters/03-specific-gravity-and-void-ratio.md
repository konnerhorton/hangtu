# Specific gravity and void ratio

| | |
|---|---|
| **Parameters** | Gs (specific gravity of the solids; ρs, particle density), e0 (in situ void ratio), n (porosity), S (degree of saturation, as a check) |
| **Material** | Both: Gs and e0 for soil; Gs and n for rock |
| **Models that use it** | Soft Soil (λ* and κ* from Cc, Cs and e0), Hardening Soil (the initial void ratio), the Cam-clay family |
| **Depends on** | [Unit weight](01-unit-weight-and-vertical-stress.md) (γ); index properties (w) |
| **Feeds** | Unit weight (the γsat check), preconsolidation and compressibility (e–log σ′), small-strain stiffness (void-ratio functions), hydraulic conductivity (k–e) |

## What it is

Gs is the density of the solid grains relative to water. It depends only on the minerals, and lies in a narrow
band for most soils, so it is often assumed rather than measured (Loehr et al. 2016, p. 4-8). The void ratio e
(volume of voids / volume of solids) and the porosity n (voids / total volume) describe how the grains are
packed: they fall with consolidation and cementation and rise with dilation and swelling. The in situ void ratio
e0 is normally back-calculated from γ, w and Gs, because sampling and trimming disturb a measured one.

The phase relations are identities from these definitions. With w as a decimal and ρw ≈ 1.000 Mg/m³:

| Quantity | Expression |
|---|---|
| Specific gravity | Gs = ρs / ρw (Loehr et al. 2016, eq. 4.10) |
| Porosity and void ratio | n = e / (1 + e); e = n / (1 − n) |
| Dry unit weight | γd = γ / (1 + w) (Kulhawy & Mayne 1990, eq. 2-9; Loehr et al. 2016, eq. 4.9) |
| **Initial void ratio** | **e0 = Gs γw (1 + w) / γ − 1** |
| Degree of saturation | S = w Gs / e |
| Saturated unit weight | γsat = γw (Gs + e) / (1 + e) |
| Rock porosity, from densities | n = 1 − ρd / ρs |

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Consolidation settlement | ε = Δe / (1 + e0) | Moderate |
| Soft Soil models | the modified compression indices λ* and κ* depend on 1 + e0 | Low to moderate: 1 + e0 varies less than Cc and Cs |
| Small-strain stiffness | void-ratio functions F(e) in G0 correlations | Moderate |
| Groundwater inflow | k–e relations; n for storage | Low to moderate |
| Unit weight | γsat from Gs and e | Low: Gs varies by about ±0.1 |
| Rock | n correlates with strength, stiffness and durability | Moderate, as a screening index |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| Gs, e0 | – | – | dimensionless |
| ρs (AGS `LPDN_PDEN`) | Mg/m³ (`RDEN_PDEN`: kg/m³) | lb/ft³ | Gs = ρs / ρw; 1 Mg/m³ = 62.428 lb/ft³ |
| n, S | % | % | n = 100 e / (1 + e) |

hangtu takes ρw = γw / g, with γw = `ht.settings.water_unit_weight` and g = 9.80665 m/s², so the same water is in
Gs and in e0. For a specimen with a measured ρs, e0 = ρs (1 + w) / ρ − 1 then holds exactly, whatever γw is set to.

## Typical values

| Material | Range | Source |
|---|---|---|
| Most soils, Gs | 2.7 ± 0.1 | Loehr et al. (2016), p. 4-8 |
| Kaolinite; Boston Blue Clay; Platte River Sand, Gs | 2.61; 2.71; 2.65 | Loehr et al. (2016), Table 4-5 |
| Silica-based soils, Gs | about 2.65 | Robertson & Cabal (2022), p. 39 |
| Outside the band | organic soils and peat lower; ores, tailings and high-carbonate soil or rock higher | Loehr et al. (2016), p. 4-8 |
| Sands (6 site groups), e site means | 0.47–0.63 | Ching & Schweckendiek (2021), Table 1.3 |
| Intact rock (31 site groups), n site means | 0.2–36.2 %, mean 6.9 % | Ching & Schweckendiek (2021), Table 1.4 |

Minimum and maximum void ratios by soil type are in Kulhawy & Mayne (1990), Table 2-8.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Particle density, pycnometer (soil finer than 4.75 mm) | D854 | ISO 17892-3; BS 1377-2 | `LPDN`: `LPDN_PDEN` (Mg/m³, `#` if assumed), `LPDN_TYPE` | ρs → Gs |
| Particle density, gas pycnometer | D5550 | ISO 17892-3 | `LPDN_PDEN`, `LPDN_GAS` | ρs → Gs |
| ρs reported with other tests | | | `CONG_PDEN`, `GRAG_PDEN`, `SHBT_PDEN` and others (Mg/m³, `#` if assumed) | the ρs the lab used |
| Initial void ratio of test specimens | D2435, D4767, D7181, D3080 | ISO 17892-5, -8, -9, -10 | `CONG_IVR`, `TRET_IVR`, `SHBT_IVR` and others | a measured e0, as a check |
| Bulk density and water content | D7263, D2216 | ISO 17892-2, -1 | `LDEN`: `LDEN_BDEN`, `LDEN_DDEN`, `LDEN_MC` | γ, γd, w → e0 |
| Rock porosity and density | | ISRM (1979) | `RDEN`: `RDEN_PORO` (%), `RDEN_PDEN`, `RDEN_DDEN` (kg/m³) | n, ρs, ρd |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Phase relations (definitions; Loehr et al. 2016, eqs. 4.9–4.10; Kulhawy & Mayne 1990, eq. 2-9) | γ and w of one specimen; ρs of its sample, or the Gs judgment | any soil | [`ht.analysis.phase_relations()`](../reference/analysis.md#hangtu.analysis.phase_relations) |
| Initial void ratio of strength and oedometer specimens | the lab's measured e0 | tested specimens | W2, W3 |
| Rock porosity from densities | ρd, ρs | intact rock | W4 |

`p.density()` gives each specimen's γ and w, with the particle density of its sample where one was tested, and
`phase_relations()` adds e, n, S, γd and γsat. Where a sample has no particle density, Gs is a judgment, keyed by
geology unit in the project's judgments file:

```yaml
specific_gravity:
  by: geology_unit
  values:
    Alluvium: {specific_gravity: 2.70, reason: "median of 6 LPDN, measured (168.9 pcf)"}
```

Gs has no units, so the entry has no `units:` line. A file's assumed `#` value is the value the lab used, and the
judgment never replaces it. Each row says where its Gs came from in `specific_gravity_source`: `measured`,
`assumed` or `judgment`.

```python
--8<-- "phase-relations.py"
```

``` { .text .no-copy }
--8<-- "phase-relations.txt"
```

![Void ratio against depth, colored by geology unit](../img/generated/phase-relations.png){ width="440" }

## How the methods compare

A pycnometer ρs on the same sample is the basis for Gs. Where there is none, the median of a unit's measured values
is the usual judgment; the band is narrow, and the sensitivity of e0 to Gs is low. e0 from γ, w and Gs is preferred
to a lab specimen's measured e0, which is taken after trimming and seating. The two are compared, not pooled.

## Variability

- Void ratio, site COV: sands 7–19.9 %, mean 11.1 % (Ching & Schweckendiek 2021, Table 1.3); silty clay 5–15 %,
  silty sand 6–19 % (Zhang et al. 2010, in Ching & Schweckendiek 2021, Table 3.3).
- Rock porosity, site COV: 1.5–115 %, mean 50 % (Ching & Schweckendiek 2021, Table 1.4).
- e0 back-calculated from γ, w and Gs inherits mainly the error in γ.

## Pitfalls

- AGS gives particle density, not Gs: divide by ρw. hangtu does so with the same water as e0.
- A `#` before a particle density marks it as assumed. Assumed values are never pooled with measured ones: hangtu
  keeps the flag (`particle_density_assumed`), lists them in QC B004, and names them `assumed` in
  `specific_gravity_source`, with a warning.
- `RDEN_PDEN` is an apparent particle density (closed pores included), so it gives a lower porosity than the total.
- γ and w must come from the same specimen for e0. `p.density()` pairs each density with its own specimen's water
  content, never another's.
- S well above 100 % points to a wrong Gs, an under-measured γ or a w from another specimen. hangtu flags it in
  `oversaturated`, with a warning, and never corrects it.
- A recompacted specimen's e is the specimen's, not the ground's: `sample_condition` says which.
- The coarse fraction above 4.75 mm needs its own Gs and a weighted mean; a pycnometer value is for the finer part.

## References

- Ching, J. and Schweckendiek, T. (eds.) (2021). *State-of-the-art review of inherent variability and uncertainty in
  geotechnical properties and models.* ISSMGE TC304. <https://doi.org/10.53243/R0001>
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
