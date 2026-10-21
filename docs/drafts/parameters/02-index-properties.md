# 02 — Index properties

| | |
|---|---|
| **Parameters** | w (natural water content), LL / wL (liquid limit), PL / wP (plastic limit), PI (plasticity index), LI (liquidity index), IC (consistency index), A (activity), FC (fines content) |
| **Material** | Soil (w also for rock) |
| **Constitutive models that use it** | None directly; inputs to correlations for MC, HS, SSC parameters |
| **Depends on** | – |
| **Feeds** | [01](01-unit-weight-and-vertical-stress.md) (γ check), [03](03-specific-gravity-and-void-ratio.md) (e0), [04](04-drained-shear-strength-soil.md), [05](05-undrained-shear-strength.md), [06](06-preconsolidation-and-compressibility.md), [10](10-small-strain-stiffness.md) (γ0.7 from PI), [12](12-hydraulic-conductivity.md) |

## 1. Phenomenon
Index properties describe what a soil is, not how it behaves under a given load: grading (fines content),
the water-holding capacity of the clay fraction (Atterberg limits) and the in situ water content relative to
those limits (LI). They are standardized remolded tests, so they carry no fabric or stress-history information
directly, but soils with similar limits tend to have similar strength, compressibility and permeability
[2] §4.8 p. 4-9 [V]. LI near 1 indicates soft, normally consolidated or sensitive clay; LI ≤ 0 indicates
heavily overconsolidated or expansive clay [2] p. 4-13 [V]. Clay mineralogy controls PI per unit clay
fraction (activity) [2] §4.9 [V].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| w, LL, PL, PI | % (by dry mass) | % | dimensionless; AGS stores % (LLPL_PI has no unit in the dictionary) |
| LI, IC, A | – | – | dimensionless |
| FC | % passing 0.063 mm (ISO / BS / AGS) or 0.075 mm (ASTM No. 200) | % passing No. 200 | not convertible exactly; read both from the PSD curve |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Sands, w | 0–20 % | [2] p. 4-7 [V] |
| Inorganic, insensitive silts and clays, w | 10–40 % | [2] p. 4-7 [V] |
| Soft, sensitive or organic clays, w | 40–300 % or more | [2] p. 4-7 [V] |
| Clays (103 site groups), LL site means | 19.3–158.6 %, mean 55.6 % | [3] Table 1.2 p. 11 [V] |
| Clays, PL site means | 13.9–112.7 %, mean 29.1 % | [3] Table 1.2 [V] |
| Clays, PI site means | 6.2–60.8 %, mean 29.0 % | [3] Table 1.2 [V] |
| Clays, w site means | 13.1–120.2 %, mean 43.5 % | [3] Table 1.2 [V] |
| Clays, LI site means | 0.09–2.47, mean 0.93 | [3] Table 1.2 [V] |
| Activity A | kaolinite ≈ 0.4 to Na-montmorillonite ≈ 8; most natural soils 0.4–2.5 | [2] p. 4-14, Table 4-6 [V] |
| "Highly plastic" | LL > 50 % | [1] p. 2-2 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Water content (oven) | D2216 (D4643 microwave) | ISO 17892-1; BS 1377-2 | LNMC: LNMC_MC (%), LNMC_TEMP, LNMC_ISNT, LNMC_COMM | w |
| Water content of rock | D2216 | ISRM SM (1979) | RWCO: RWCO_MC, RWCO_TEMP | w (rock) |
| Liquid and plastic limits | D4318 (Casagrande cup, thread) | ISO 17892-12 (fall cone or cup); BS 1377-2 (80 g / 30° cone) | LLPL: LLPL_LL, LLPL_PL, LLPL_PI, LLPL_425, LLPL_PREP, LLPL_TYPE, LLPL_CONE, LLPL_POIN, LLPL_WC | LL, PL, PI |
| Shrinkage limit / linear shrinkage | D4943 | BS 1377-2 | LSLT: LSLT_SLIM, LSLT_SHRA; LLIN: LLIN_LS | SL, LS |
| Particle size (sieve) | D6913/D6913M (D1140 wash for fines) | ISO 17892-4; BS 1377-2 | GRAG: GRAG_FINE (% < 63 µm), GRAG_GRAV, GRAG_SAND, GRAG_SILT, GRAG_CLAY, GRAG_VCRE, GRAG_UC, GRAG_CC; GRAT: GRAT_SIZE, GRAT_PERP, GRAT_TYPE | FC, gradation |
| Particle size (hydrometer) | D7928 | ISO 17892-4; BS 1377-2 | GRAT (GRAT_TYPE = HY / PP); GRAG_CLAY | clay fraction (< 2 µm) |
| Classification | D2487 (lab), D2488 (visual) | ISO 14688-1, -2; BS 5930 | GEOL_DESC (description; no group-symbol heading) | USCS / BS group |
| CPT-correlated fines | D5778 | ISO 22476-1 | CPTP: CPTP_FC1 (%), CPTP_IC1 | FC estimate |

## 5. Derivations and correlations

### 5.1 Plasticity, liquidity and consistency indices
$$PI = LL - PL,\qquad LI = \frac{w - PL}{LL - PL},\qquad I_C = \frac{LL - w}{PI} = 1 - LI$$
- **Inputs:** w, LL, PL (%), w measured on the same sample as the limits where possible.
- **Valid for:** plastic soils (PI > 0); LI is meaningless for non-plastic soils (NP).
- **Source:** [1] p. 2-2 [V]; [2] eqs. 4.12–4.13 p. 4-13 [V] (IC: [2] eq. 4.15 p. 4-13, form not legible in the text layer; given here as the identity 1 − LI).

### 5.2 Casagrande plasticity chart (QA check)
$$\text{A-line: } PI = 0.73\,(LL - 20),\qquad \text{U-line: } PI = 0.9\,(LL - 8)$$
- **Use:** classify fines (CL/ML/CH/MH); a point above the U-line should be questioned and re-tested.
- **Source:** [1] Table 2-6 p. 2-9 (reproducing ASTM D2487) and p. 2-8 text [V].

### 5.3 Activity — Skempton (1953)
$$A = \frac{PI}{CF},\quad CF = \%\ \text{by dry mass} < 0.002\ \text{mm}$$
- **Source:** [2] eq. 4.16 p. 4-14, Table 4-6 [V] (Skempton 1953 original [U]).

### 5.4 Fines content from CPT — Mayne et al. (2009)
$$FC\,(\%) = 1.75\,I_{c}^{3.25} - 3.7\quad (1.26 < I_{c} < 3.50);\ 0 \text{ below},\ 100 \text{ above}$$
- **Inputs:** Ic (Jefferies–Been form, I_c-JB).
- **Scatter:** not given; [2] notes large scatter in CPT–FC correlations generally.
- **Source:** [2] Table 4-17 p. 4-35 [V].

### 5.5 Fines content from the PSD curve
Interpolate GRAT_PERP at 0.063 mm (ISO / AGS GRAG_FINE) or 0.075 mm (ASTM) on log(size); report which.
_[Judgment — for PE review]_

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE (MC / HS) | indirect: PI-based φ′, Su/σ′v0, γ0.7 (Vardanega & Bolton), Cc, K0 correlations | Moderate: errors propagate through correlations with large transformation error |
| Soft Soil / SSC models | λ*, κ* from Cc, Cs and e0 (w-based) | Moderate |
| EPB TBM clogging / conditioning | clogging risk charts use IC and PI (Thewes type) [U] | High for drive performance |
| Slurry TBM separation, spoil | FC and clay fraction drive separation plant load | High (cost / logistics) |
| Groundwater inflow | FC as a proxy for k (sheet 12) | Moderate (screening only) |
| Settlement / volume loss | w and LI flag soft, sensitive ground and long-term consolidation | Moderate |
| Face stability | FC decides drained vs undrained behavior at TBM advance rates | High (choice of analysis type) |

**Typical variability (inherent, site-specific, clays):** COV mean (range) LL 15.6 % (3.4–39), PL 13.5 %
(2.9–38.1), PI 23.5 % (6.5–57), w 15.3 % (3.5–46), LI 24.5 % (5.8–88) [3] Table 1.2 p. 11 [V]. Zhang et al.
(2010): w 2–18 %, LL 1–18 %, PI 9–38 %, LI 11–47 % [3] Table 3.3 p. 121 [V]. Fines content COV: no generic
source seen [U]. Derived quantities (PI, LI) have larger COV than the limits themselves.

## 7. Pitfalls and QA checks
- **Fines size:** AGS GRAG_FINE and ISO / BS use 63 µm; ASTM / USCS use 75 µm (No. 200). Do not mix them in one statistic.
- **Fall cone vs Casagrande LL:** practically identical below LL ≈ 120 [2] p. 4-11 [V]; record LLPL_TYPE / LLPL_CONE.
- **LLPL_425:** limits are run on the < 425 µm fraction; for gravelly soils correct the whole-soil index if needed.
- w measured on the limit sample (LLPL_WC) vs natural w (LNMC): LI needs the in situ w.
- Drying temperature (LNMC_TEMP): 105–110 °C drives off gypsum and organic water; a lower temperature (about 60 °C) is used for such soils [U].
- Samples near the top of a sampler or poorly sealed give biased w [2] p. 4-7 [V].
- NP (non-plastic) is not PI = 0 numerically; keep as a flag, exclude from PI statistics.
- QA: PL < LL; points above the U-line; LI < 0 or > 1.5 should match the geology (OC crust, sensitive clay).

## References
[1] Kulhawy, F.H. and Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800. https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] PI, LI definitions p. 2-2; Table 2-6 p. 2-9 (A- and U-lines).
[2] Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). Geotechnical Site Characterization. GEC No. 5, FHWA NHI-16-072. https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] §4.6 p. 4-7; §4.8 pp. 4-9–4-13; §4.9 p. 4-14, Table 4-6; Table 4-17 p. 4-35.
[3] Ching, J. and Schweckendiek, T. (eds.) (2021). State-of-the-art review of inherent variability and uncertainty in geotechnical properties and models. ISSMGE TC304. https://doi.org/10.53243/R0001 — [V] Table 1.2 p. 11; Table 3.3 p. 121.
[4] Skempton, A.W. (1953). The colloidal activity of clays. Proc. 3rd ICSMFE, Zurich, Vol. 1, 57–61 — [U].
[5] Mayne, P.W., Coop, M.R., Springman, S.M., Huang, A.-B. and Zornberg, J.G. (2009). Geomaterial behavior and testing. Proc. 17th ICSMGE, Alexandria, Vol. 4, 2777–2872 — [U] (FC–Ic equation seen only via [2]).
[6] Hollmann, F.S. and Thewes, M. (2013). Assessment method for clay clogging and disintegration of fines in mechanised tunnelling. Tunnelling and Underground Space Technology 37, 96–106. https://doi.org/10.1016/j.tust.2013.03.010 — [U].
