# Index properties

| | |
|---|---|
| **Parameters** | w (water content), LL (liquid limit), PL (plastic limit), PI (plasticity index), LI (liquidity index), Ic (consistency index), A (activity), FC (fines content) |
| **Material** | Soil (w also for rock) |
| **Models that use it** | None directly; inputs to the correlations behind Mohr–Coulomb, Hardening Soil and Soft Soil parameters |
| **Depends on** | – |
| **Feeds** | [Unit weight](01-unit-weight-and-vertical-stress.md) (the γ check), [specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (e0), [drained](04-drained-shear-strength-soil.md) and [undrained](05-undrained-shear-strength.md) strength, [compressibility](06-preconsolidation-and-compressibility.md), [small-strain stiffness](10-small-strain-stiffness.md), hydraulic conductivity |

## What it is

Index properties describe what a soil is, not how it behaves under a given load: its grading (fines content), the
water-holding capacity of its clay (the Atterberg limits) and its water content relative to those limits (LI).
They come from standardized remolded tests, so they carry no fabric or stress history, but soils with similar
limits tend to have similar strength, compressibility and permeability (Loehr et al. 2016, §4.8). LI near 1
indicates a soft, normally consolidated or sensitive clay; LI at or below 0 a heavily overconsolidated or expansive
one (Loehr et al. 2016, p. 4-13). The clay minerals control how much PI each percent of clay gives, which is the
activity (Loehr et al. 2016, §4.9).

$$
PI = LL - PL, \qquad
LI = \frac{w - PL}{PI}, \qquad
I_C = \frac{LL - w}{PI} = 1 - LI, \qquad
A = \frac{PI}{CF}
$$

where CF is the clay fraction, the percentage by dry mass finer than 0.002 mm (Kulhawy & Mayne 1990, p. 2-2;
Loehr et al. 2016, eqs. 4.12, 4.13 and 4.16, after Skempton 1953 for activity).

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Strength, stiffness and compressibility from correlations | φ′, su/σ′v, γ0.7, Cc and K0 correlations on PI, LL or w | Moderate: errors carry through correlations with a large transformation error |
| Soft Soil models | λ* and κ* from Cc, Cs and e0, which comes from w | Moderate |
| Slurry tunneling, spoil handling | fines and clay content load the separation plant | High, for cost and logistics |
| Groundwater inflow | fines content as a screen for k | Moderate, as a screen only |
| Settlement and volume loss | w and LI flag soft, sensitive ground | Moderate |
| Face stability | fines content decides drained or undrained behavior at the rate of advance | High, through the choice of analysis |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| w, LL, PL, PI | % by dry mass | % | none; AGS stores % (`LLPL_PI` has no unit in the dictionary) |
| LI, Ic, A | – | – | dimensionless |
| FC | % passing 0.063 mm (ISO, BS, AGS) | % passing 0.075 mm (No. 200) | not convertible exactly; read both from the grading curve |

## Typical values

| Material | Range | Source |
|---|---|---|
| Sands, w | 0–20 % | Loehr et al. (2016), p. 4-7 |
| Inorganic, insensitive silts and clays, w | 10–40 % | Loehr et al. (2016), p. 4-7 |
| Soft, sensitive or organic clays, w | 40–300 % or more | Loehr et al. (2016), p. 4-7 |
| Clays (103 site groups), LL site means | 19.3–158.6 %, mean 55.6 % | Ching & Schweckendiek (2021), Table 1.2 |
| Clays, PI site means | 6.2–60.8 %, mean 29.0 % | Ching & Schweckendiek (2021), Table 1.2 |
| Clays, LI site means | 0.09–2.47, mean 0.93 | Ching & Schweckendiek (2021), Table 1.2 |
| Activity | about 0.4 (kaolinite) to about 8 (sodium montmorillonite); most natural soils 0.4–2.5 | Loehr et al. (2016), p. 4-14 and Table 4-6 |
| "Highly plastic" | LL above 50 % | Kulhawy & Mayne (1990), p. 2-2 |

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Water content (oven) | D2216 | ISO 17892-1; BS 1377-2 | `LNMC`: `LNMC_MC` (%), `LNMC_TEMP` | w |
| Liquid and plastic limits | D4318 (cup, thread) | ISO 17892-12 (cone or cup); BS 1377-2 (cone) | `LLPL`: `LLPL_LL`, `LLPL_PL`, `LLPL_PI`, `LLPL_425`, `LLPL_TYPE` | LL, PL, PI |
| Particle size, sieve | D6913 | ISO 17892-4; BS 1377-2 | `GRAG`: `GRAG_FINE` (% finer than 0.063 mm); `GRAT`: `GRAT_SIZE`, `GRAT_PERP` | FC, grading |
| Particle size, hydrometer | D7928 | ISO 17892-4; BS 1377-2 | `GRAT` continued into the fines; `GRAG_CLAY` | clay fraction (finer than 0.002 mm) |
| Classification | D2487 (lab), D2488 (visual) | ISO 14688-1, -2; BS 5930 | `GEOL_DESC` (no heading for the group symbol) | USCS or BS group |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| PI, LI and Ic (definitions), plasticity class | w, LL, PL | plastic soils; NP kept as a flag | [`ht.analysis.plasticity()`](../reference/analysis.md#hangtu.analysis.plasticity) |
| D-values, Cu, Cc and fractions by system | the grading curve | any grading; never extrapolated | [`ht.analysis.gradation()`](../reference/analysis.md#hangtu.analysis.gradation) |
| USCS group symbol (ASTM D2487) | fractions, Cu, Cc, plasticity | soil finer than 75 mm | [`ht.analysis.uscs()`](../reference/analysis.md#hangtu.analysis.uscs) |
| AASHTO group and group index | fractions, LL, PI | soil finer than 75 mm | [`ht.analysis.aashto()`](../reference/analysis.md#hangtu.analysis.aashto) |
| Activity (Skempton 1953) | PI, clay finer than 0.002 mm | plastic soils with a hydrometer stage | [`ht.analysis.clay_activity()`](../reference/analysis.md#hangtu.analysis.clay_activity) |

`p.index_properties()` combines each sample's water content, limits and grading on one row and adds all of these,
activity included where the grading reaches 0.002 mm. With data typed in from a lab report, `clay_activity()` reads
the clay content with a `fraction_system` column saying `iso14688`, which confirms that the clay is the fraction
finer than 0.002 mm. A non-plastic specimen has no activity, not an activity of 0.

```python
--8<-- "clay-activity.py"
```

``` { .text .no-copy }
--8<-- "clay-activity.txt"
```

## How the methods compare

The index properties are measured, not estimated, so the methods don't compete: each is a definition or a
classification standard applied to the test results. What varies is the test: the cone and the cup give practically
the same LL below about 120 % (Loehr et al. 2016, p. 4-11), and the fines boundary is 0.063 mm in ISO and BS but
0.075 mm in ASTM.

## Variability

- Clays, inherent site COV, mean (range): LL 15.6 % (3.4–39), PL 13.5 % (2.9–38.1), PI 23.5 % (6.5–57), w 15.3 %
  (3.5–46), LI 24.5 % (5.8–88) (Ching & Schweckendiek 2021, Table 1.2).
- Derived quantities (PI, LI) vary more than the limits they are calculated from.

## Pitfalls

- The fines boundary is 0.063 mm in AGS (`GRAG_FINE`), ISO and BS, and 0.075 mm in ASTM and USCS. Don't mix them
  in one statistic. hangtu carries the system in `fraction_system`, and the classifications check it.
- The limits are run on the fraction finer than 0.425 mm (`LLPL_425`), and the clay fraction on the whole sample.
  Activity takes them as published, without correcting for the coarse fraction.
- LI needs the in situ water content (`LNMC`), not the water content of the limit test (`LLPL_WC`).
- Samples near the top of a sampler or poorly sealed give a biased w (Loehr et al. 2016, p. 4-7).
- NP is not PI = 0. hangtu keeps it as a flag (`non_plastic`), counts it on plots and leaves LI, Ic and activity
  blank for it.
- Check: PL below LL (QC A001), PI equal to LL − PL (A002), points above the U-line; LI below 0 or above 1.5
  should match the geology.

## References

- Ching, J. and Schweckendiek, T. (eds.) (2021). *State-of-the-art review of inherent variability and uncertainty in
  geotechnical properties and models.* ISSMGE TC304. <https://doi.org/10.53243/R0001>
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Skempton, A.W. (1953). The colloidal activity of clays. *Proc. 3rd Int. Conf. Soil Mech. Found. Eng.*, Zurich,
  Vol. 1, 57–61. Cited as given in Loehr et al. (2016).
