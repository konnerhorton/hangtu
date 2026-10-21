# 03 — Specific gravity and void ratio

| | |
|---|---|
| **Parameters** | Gs (specific gravity of solids; ρs particle density), e0 (initial / in situ void ratio), n (porosity), S (degree of saturation, as a check) |
| **Material** | Both (Gs, e0 soil; Gs, n rock) |
| **Constitutive models that use it** | HS / SS / SSC (einit; λ*, κ* from Cc, Cs), MC (einit for permeability change), Cam-clay family |
| **Depends on** | [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (γ), [02-index-properties](02-index-properties.md) (w) |
| **Feeds** | [01](01-unit-weight-and-vertical-stress.md) (γsat check), [06](06-preconsolidation-and-compressibility.md) (e–log σ′, λ*, κ*), [10](10-small-strain-stiffness.md) (G0 void-ratio functions), [11](11-hardening-soil-stiffness.md), [12](12-hydraulic-conductivity.md) (k–e) |

## 1. Phenomenon
Gs is the density of the solid mineral grains relative to water; it depends only on mineralogy and lies in a
narrow band for most soils, so it is often assumed rather than measured [1] p. 4-8 [V]. Void ratio e (volume
of voids / volume of solids) and porosity n (voids / total volume) describe packing: they fall with
consolidation, overconsolidation and cementation and rise with dilation and swelling. e0 is the in situ value
before testing or loading; it is normally back-calculated from γ, w and Gs because sampling and specimen
preparation disturb the measured value. In rock, n (connected porosity) controls density, strength, stiffness
and durability.

**Phase relations** (identities from the definitions; ρw ≈ 1.000 Mg/m³):

| Quantity | Expression |
|---|---|
| Specific gravity | Gs = ρs / ρw = ms / (Vs ρw) ([1] eq. 4.10 p. 4-8 [V]) |
| Porosity ↔ void ratio | n = e / (1 + e); e = n / (1 − n) |
| Dry unit weight | γd = Gs γw / (1 + e) → e = Gs γw / γd − 1 |
| Bulk unit weight | γ = Gs γw (1 + w) / (1 + e) |
| **Initial void ratio** | **e0 = Gs γw (1 + w) / γ − 1** |
| Saturation | S e = w Gs → S = w Gs / e (≈ 1 below the water table) |
| Saturated unit weight | γsat = γw (Gs + e) / (1 + e) |
| Rock porosity (from densities) | n = 1 − ρd / ρs |
| Relative density (granular) | Dr = (emax − e) / (emax − emin) ([2] eq. 2-1 p. 2-3 [V]) |

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Gs | – | – | dimensionless |
| ρs (AGS *_PDEN) | Mg/m³ (RDEN_PDEN: kg/m³) | lbm/ft³ | Gs = ρs [Mg/m³] / ρw; 1 Mg/m³ = 62.428 lbm/ft³ |
| e0 | – | – | dimensionless |
| n | % or decimal | % | n [%] = 100 e / (1 + e) |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Most soils, Gs | 2.7 ± 0.1 | [1] p. 4-8 [V] |
| Kaolinite / Omaha Lake Clay / Boston Blue Clay / Platte River Sand / Iowa Loess, Gs | 2.61 / 2.65 / 2.71 / 2.65 / 2.70 | [1] Table 4-5 [V] |
| Silica-based soils, Gs | about 2.65 | [3] p. 39 [V] |
| Exceptions (Gs outside the band) | organic soils and peat (lower); ores, tailings, high-carbonate soil or rock | [1] p. 4-8 [V] |
| Soils, emax / emin (well-graded gravel–sand–silt–clay to organic clay) | emin ≈ 0.13–0.70, emax ≈ 0.70–4.40; values by soil type in [2] Table 2-8 | [2] Table 2-8 p. 2-18 [V] |
| Sands (6 site groups), e site means | 0.47–0.63 | [4] Table 1.3 p. 11 [V] |
| Intact rock (31 site groups), n site means | 0.2–36.2 %, mean 6.9 % | [4] Table 1.4 p. 12 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Particle density, pycnometer (soil < 4.75 mm) | D854 | ISO 17892-3; BS 1377-2 | LPDN: LPDN_PDEN (Mg/m³, # prefix if assumed), LPDN_TYPE, LPDN_PVOL | ρs → Gs |
| Particle density, gas pycnometer | D5550 | ISO 17892-3 | LPDN_PDEN, LPDN_GAS | ρs → Gs |
| ρs reported with other tests | – | – | CONG_PDEN, GRAG_PDEN, SHBT_PDEN, CTRG_PDEN, RESG_PDEN, ESCG_PDEN, PTST_PDEN (Mg/m³, # if assumed) | ρs used by the lab |
| Initial void ratio of test specimens | (D2435, D4767, D7181, D3080) | ISO 17892-5, -8, -9, -10 | CONG_IVR, TRET_IVR, SHBT_IVR, CTRG_IVR, RESG_IVR, ESCG_IVR; CONS_IVR (per increment) | measured e0 (check) |
| Bulk density + water content | D7263, D2216 | ISO 17892-2, -1 | LDEN_BDEN, LDEN_DDEN, LDEN_MC; LNMC_MC | γ, γd, w → e0 |
| Max / min index density (granular) | D4253, D4254 | BS 1377-4 | RELD: RELD_DMAX, RELD_DMIN (Mg/m³) | emin, emax → Dr |
| Rock porosity and density | – | ISRM SM (1979) [5] | RDEN: RDEN_PORO (%), RDEN_PDEN, RDEN_DDEN, RDEN_BDEN (kg/m³), RDEN_SMC | n, ρs, ρd |

## 5. Derivations and correlations

### 5.1 Initial void ratio from γ, w and Gs
$$e_0 = \frac{G_s\,\gamma_w\,(1+w)}{\gamma} - 1$$
- **Inputs:** Gs (–), γw = 9.81 kN/m³, w (decimal), γ (kN/m³), all on the **same specimen**.
- **Valid for:** any soil; exact identity given the inputs.
- **Error propagation (computed, Gs = 2.70, w = 25 %, γ = 20 kN/m³):** ∂e/∂Gs ≈ 0.61 (ΔGs = ±0.05 → Δe ≈ ±0.03);
  ∂e/∂w = 1.32 (per unit w); ∂e/∂γ = −0.083 per kN/m³ (γ rounded to 1 kN/m³ → Δe up to ±0.04). γ resolution
  usually dominates. _[Judgment — for review]_
- **Source:** phase relations; [1] eqs. 4.9–4.10 [V]; [2] eq. 2-9 [V] (algebra combined here).

### 5.2 Saturation check
$$S = \frac{w\,G_s}{e_0}$$
- **Use:** S well above 1 below the water table points to a wrong Gs, an under-measured γ or w from a
  different specimen; S well below 1 to gas, sample swelling or disturbance. Tolerance about ±5 %. _[Judgment — for review]_

### 5.3 Gs from mineralogy (when no test)
Quartz ≈ 2.65, calcite ≈ 2.71, dolomite ≈ 2.85–2.87, kaolinite ≈ 2.6–2.65, organics ≪ 2 [U] (standard mineral
values, e.g. Mitchell & Soga 2005 [6]). Weighted by mass fraction for mixed soils. _[Judgment — for review]_

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE, Soft Soil / SSC | λ* = Cc / [2.3 (1 + e0)], κ* ≈ 2 Cs / [2.3 (1 + e0)] (PLAXIS Material Models manual) [U] | Low–moderate: (1 + e0) varies less than Cc, Cs |
| Tunnel FE, HS / MC | einit for permeability change with strain and the dilatancy cut-off (emax) | Low (only if those options are used) [U] |
| Consolidation / long-term settlement | e0 in Δe → strain: ε = Δe / (1 + e0) | Moderate |
| Small-strain stiffness | void-ratio functions F(e) in G0 correlations | Moderate |
| Groundwater inflow | k–e relations, n for storage / drainable porosity | Low–moderate |
| Unit weight (Gs) | γsat from Gs, e | Low: Gs band ±0.1 |
| Rock (n) | n correlates with σci, Ei, slake durability | Moderate (as a screening index) |

**Typical variability:** e site COV: sands 7–19.9 % (mean 11.1 %) [4] Table 1.3 p. 11 [V]; silty clay 5–15 %,
silty sand 6–19 % (Zhang et al. 2010, via [4] Table 3.3 p. 121 [V]). Rock n site COV 1.5–115 % (mean 50 %) [4]
Table 1.4 p. 12 [V]. Gs COV within a deposit is small (a few %) [U]; no generic table seen. e0 back-calculated
from γ, w, Gs inherits mainly the γ measurement error (5.1).

## 7. Pitfalls and QA checks
- AGS *_PDEN values carry a **# prefix when assumed** (e.g. "#2.65"): parse it, flag it, never pool assumed with measured values.
- AGS gives particle **density** (Mg/m³ or, in RDEN, kg/m³), not Gs; divide by ρw (≈ 1.000 Mg/m³).
- RDEN_PDEN is "apparent" particle density (closed pores included) — gives a lower n than total porosity.
- w and γ must come from the **same specimen** for e0; mixing a unit-mean γ with a sample w adds scatter.
- Lab-measured e0 (CONG_IVR etc.) is after trimming and seating: usually close to, not equal to, in situ e0; compare, do not pool.
- Check e0 against S = w Gs / e (5.2) and against γsat = γw (Gs + e) / (1 + e).
- Coarse fraction > 4.75 mm needs a separate Gs (absorption method) and a weighted average.
- Dr from emax / emin is meaningful only for < 15 % fines [2] p. 2-4 [V].

## References
[1] Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). Geotechnical Site Characterization. GEC No. 5, FHWA NHI-16-072. https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] §4.7 eqs. 4.9–4.10, p. 4-8, Table 4-5.
[2] Kulhawy, F.H. and Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800. https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] eq. 2-1 p. 2-3; p. 2-4 (15 % fines limit); eq. 2-9 p. 2-17; Table 2-8 p. 2-18.
[3] Robertson, P.K. and Cabal, K.L. (2022). Guide to Cone Penetration Testing, 7th ed. Gregg Drilling LLC — [V] p. 39 (Gs ≈ 2.65 for silica-based soils).
[4] Ching, J. and Schweckendiek, T. (eds.) (2021). State-of-the-art review of inherent variability and uncertainty in geotechnical properties and models. ISSMGE TC304. https://doi.org/10.53243/R0001 — [V] Tables 1.3, 1.4 pp. 11–12; Table 3.3 p. 121.
[5] ISRM (1979). Suggested methods for determining water content, porosity, density, absorption and related properties and swelling and slake-durability index properties. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 16(2), 141–156 — [U].
[6] Mitchell, J.K. and Soga, K. (2005). Fundamentals of Soil Behavior, 3rd ed. Wiley — [U] (mineral Gs values not checked).
