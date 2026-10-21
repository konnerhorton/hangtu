# 07 — At-rest earth pressure (soil)

| | |
|---|---|
| **Parameters** | K0 (coefficient of earth pressure at rest = σ′h0 / σ′v0), K0NC (normally consolidated), K0 for OC soil; σ′h0, σh0 |
| **Material** | Soil (rock in situ stress: [20](20-in-situ-stress-rock.md)) |
| **Constitutive models that use it** | All FE models (MC, HS, HSsmall, SSC) for the initial stress state (K0 procedure); HS also uses K0NC for the cap |
| **Depends on** | [01](01-unit-weight-and-vertical-stress.md) (σ′v0, u0), [04](04-drained-shear-strength-soil.md) (φ′), [06](06-preconsolidation-and-compressibility.md) (OCR) |
| **Feeds** | [08](08-elastic-stiffness-soil.md) / [11](11-hardening-soil-stiffness.md) (mean stress p′0 for stiffness), [10](10-small-strain-stiffness.md), face-pressure and lining-load calculations |

## 1. Phenomenon
K0 is the ratio of horizontal to vertical effective stress in level ground with no lateral strain. During
virgin (normally consolidated) loading it is roughly constant and close to 1 − sin φ′; on unloading (erosion,
ice retreat, excavation) the horizontal stress is partly "locked in", so K0 rises with OCR and can exceed 1 in
heavily overconsolidated clays, bounded by passive failure [1] pp. 3-1–3-6 [V]. Reloading lowers it again, so
most natural deposits sit between the unload and reload paths [1] p. 3-6 [V]. Ageing, cementation, desiccation
and tectonic stress also change σ′h0, and correlations do not capture them [2] p. 11-39 [V]. K0 is hard to
measure: every in situ device disturbs the ground on insertion [1] p. 3-25 [V].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| K0 | – | – | dimensionless; uses **effective** stresses |
| σh0, σ′h0 (AGS PMTP_HO, DMTP_THS, DMTP_EHS) | kPa | psf / psi / ksf | 1 kPa = 20.885 psf = 0.1450 psi; 1 ksf = 47.880 kPa; 1 tsf = 95.761 kPa |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| NC soils, K0NC = 1 − sin φ′ (computed) | φ′ = 20° → 0.66; 25° → 0.58; 30° → 0.50; 35° → 0.43; 40° → 0.36 | 5.1 [V] |
| OC soils, (1 − sin φ′) OCR^sin φ′ (computed, φ′ = 30°) | OCR 2 → 0.71; 4 → 1.00; 10 → 1.58 | 5.2 [V] |
| Physical bounds (Rankine), φ′ = 40° | Ka 0.22 to Kp 4.6 | [1] p. 3-2 [V] (0.2–4.6) |
| Clays (8 site groups), measured K0 site means | 0.48–2.88, mean 1.28 | [3] Table 1.2 p. 11 [V] |
| Sands (4 site groups), measured K0 site means | 0.64–2.20, mean 1.16 | [3] Table 1.3 p. 11 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Self-boring pressuremeter (lift-off) | – | ISO 22476-6 | PMTG: PMTG_HO, PMTG_TYPE, PMTG_WAT; PMTP: PMTP_HO, PMTP_HOM, PMTP_U0 (kPa) | σh0 (most direct measurement) |
| Prebored (Ménard) pressuremeter | D4719 | ISO 22476-4 | PMMG: PMMG_P1 (start of linear section; no σh0 heading), PMMG_PRWL | rough σh0 from P1 (borehole unloading; low quality) |
| Flat dilatometer | D6635 | ISO 22476-11 | DMTT_P0; DMTP: DMTP_KD, DMTP_K0, DMTP_K0M, DMTP_OCR, DMTP_THS, DMTP_EHS, DMTP_EVS | KD → K0 (correlation) |
| CPTu | D5778 | ISO 22476-1 | SCPT_QT, SCPT_PWP2 (MPa), SCPT_CPO, SCPT_CPOD (kPa); CPTP_K01 | K0 (correlation) |
| SPT | D1586/D1586M | ISO 22476-3 | ISPT_NVAL, ISPT_ERAT, ISPT_N60 | K0 (correlation) |
| K0-consolidated triaxial | – (D4767 / D7181 with anisotropic consolidation) | ISO 17892-9 | TREG_TYPE (CAUC, CAUE, CADC, CADE) | lab K0NC; K0 on unloading |
| Oedometer (for OCR) | D2435, D4186 | ISO 17892-5 | CONG / CONS (see sheet 06) | σ′p → OCR |

## 5. Derivations and correlations

### 5.1 Normally consolidated — Jaky (1944), simplified
$$K_{0NC} = 1 - \sin\phi'$$
- **Inputs:** φ′ (triaxial compression, φ′tc).
- **Valid for:** virgin loading, OCR = 1; uncemented sands, silts, clays.
- **Scatter:** lab data, 124 soils: K0NC = 0.97 (1 − sin φ′tc), r² = 0.707, SD = 0.06; most data within ±0.1.
- **Source:** [1] eq. 3-4 p. 3-3, Fig. 3-3 p. 3-4 (Mayne & Kulhawy 1982 p. 862) [V]; [2] Fig. 11-19 [V]. Jaky's original (longer) expression [5] [U].

### 5.2 Overconsolidated, primary unloading — Mayne & Kulhawy (1982)
$$K_0 = (1 - \sin\phi')\,OCR^{\sin\phi'}$$
- **Inputs:** φ′ (deg, φ′tc), OCR = σ′p / σ′v0 (–).
- **Valid for:** mechanically overconsolidated, uncemented clays, silts and sands; 171 lab-tested soils.
  Treat as an upper bound if the soil has been reloaded; NC assumption (OCR = 1) underestimates K0 in most deposits [1] p. 3-6 [V].
- **Scatter / transformation:** b = 1.00, δ (COV) = 0.34 for clay (φ′ = 25° assumed, n = 1009); b = 1.05, δ = 0.50 for sand (φ′ = 30°, n = 1207) [3] Tables 5.2–5.3 pp. 178–179 [V].
- **Source:** [4] (paywalled; abstract seen); [1] eq. 3-10 p. 3-6 [V]; [2] eq. 11.31 p. 11-39 [V]; [6] p. 47 [V].

### 5.3 Unload–reload — Mayne & Kulhawy (1982)
$$K_0 = (1 - \sin\phi')\left[\frac{OCR}{OCR_{max}^{\,(1-\sin\phi')}} + \frac{3}{4}\left(1 - \frac{OCR}{OCR_{max}}\right)\right]$$
- **Inputs:** current OCR, maximum past OCRmax; reload coefficient mr = 0.75 (1 − sin φ′) ([1] eq. 3-8, n = 35 soils, SD 0.06).
- **Source:** [1] eq. 3-9 p. 3-6 [V] (text layer partly garbled; form checked against eqs. 3-3, 3-6, 3-8).

### 5.4 Simplified, φ′ = 30°
$$K_0 \approx 0.5\,OCR^{0.5}$$
- **Valid for:** low-plasticity, mechanically OC fine-grained soils; guide only.
- **Source:** [1] eq. 3-27 p. 3-23 [V]; [6] p. 47 [V].

### 5.5 Passive cap
$$K_0 \le K_p = \frac{1+\sin\phi'_{ps}}{1-\sin\phi'_{ps}},\qquad \phi'_{ps}\approx 1.1\,\phi'_{tc}$$
- With φ′ps = φ′tc, 5.2 reaches Kp at OCR = [Kp / (1 − sin φ′)]^(1/sin φ′): ≈ 31 (25°), 36 (30°), 43 (35°) (computed).
- **Source:** [1] eq. 3-1 p. 3-2, p. 3-6 [V].

### 5.6 SPT check (clays) — Kulhawy et al. (1989)
$$K_0 \approx 0.073\,N_{60}\,/\,(\sigma'_{v0}/p_a)$$
- **Scatter / transformation:** b = 2.16, δ = 0.70 (n = 74) — strongly biased on the TC304 database.
- **Source:** [3] Table 5.2 p. 178 [V]; [1] eq. 3-31 p. 3-27 / Fig. 3-33 p. 3-30 legend [V]. No direct SPT correlation existed for sands in 1990 [1] p. 3-30 [V].

### 5.7 CPTu check (clays) — Kulhawy et al. (1989)
$$K_0 \approx 0.1\,(q_t - \sigma_{v0})\,/\,\sigma'_{v0}$$
- **Scatter / transformation:** b = 1.18, δ = 0.74 (n = 74).
- **Source:** [3] Table 5.2 p. 178 [V]; [1] eq. 3-32 / Fig. 3-33 legend p. 3-30 [V]. "No reliable method to determine K0 from CPT" [6] p. 47 [V].

### 5.8 CPT check (sands) — Mayne (2007)
$$K_0 \approx 0.192\,(q_t/p_a)^{0.22}\,(\sigma'_{v0}/p_a)^{-0.31}\,OCR^{0.27}$$
- **Valid for:** uncemented quartz sands (calibration chamber basis).
- **Source:** [7] [U] — equation not seen in a source during this review.

### 5.9 DMT check — Marchetti (1980)
$$K_0 = (K_D/1.5)^{0.47} - 0.6$$
- **Valid for:** insensitive, uncemented clays (Italian data); underestimates in fissured OC clays.
- **Source:** [1] eq. 3-29 p. 3-25 [V]; Marchetti (1980) [U].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE initial stress (K0 procedure) | σ′h0 = K0 σ′v0 in every element | High: sets deviatoric stress and distance to failure |
| Lining forces | ovalization bending moment ∝ (1 − K0) in elastic continuum solutions [U]; hoop force ∝ mean stress | High for bending; moderate for thrust |
| Surface settlement trough (FE) | high K0 gives troughs too wide and shallow in isotropic FE models [U] | Moderate–high (shape) |
| Face support pressure (EPB / slurry) | target ≈ K σ′v0 + u0, K between Ka and K0 _[Judgment — for PE review]_ | High where K0 is used as the target |
| Face stability (limit equilibrium) | weakly, via σh on the wedge | Low |
| HS / HSsmall stiffness | p′0 = σ′v0 (1 + 2 K0)/3 sets the reference stress | Moderate (m ≈ 0.5–1) |
| Groundwater inflow | none | – |

**Typical variability:** measured K0, site COV: clays 2.4–22 % (mean 13.5 %); sands 25.8–36.9 % (mean 33.1 %)
[3] Tables 1.2–1.3 p. 11 [V]. Transformation uncertainty dominates: δ = 0.34–0.50 for Mayne & Kulhawy and
0.70–0.74 for the SPT / CPT forms [3] Tables 5.2–5.3 [V]; "all soil models for K0 have 0.3 < δ < 0.9" [3] p. 172 [V].
Uncertainty in OCR propagates as OCR^sin φ′ (about OCR^0.5).

## 7. Pitfalls and QA checks
- Use **effective** stresses: K0 = (σh0 − u0) / σ′v0; DMT and PMT give total σh0.
- Use φ′ from triaxial compression (φ′tc); a plane-strain or residual φ′ shifts K0NC.
- OCR = 1 where no oedometer data gives the **lowest** K0; it underestimates K0 in most natural deposits [1] p. 3-6 [V].
- Primary-unloading K0 is an **upper bound** for soils that have since been reloaded [1] p. 3-21 [V].
- Cap at Kp; a K0 > 1 in sands or > 2–3 in clays needs geological support (erosion, glacial loading).
- Desiccated crusts give high OCR and K0 near surface; OCR from σ′p / σ′v0 blows up at shallow depth.
- Cemented, aged or tectonically stressed ground: correlations do not apply; measure (SBPM) [2] p. 11-39 [V].
- AGS DMTP_K0 is a vendor correlation (method in DMTP_K0M), "fine soils only" in the dictionary; do not pool with 5.2.
- Do not mix K0 (effective) with total-stress ratios from FE output or GBR tables.

## References
[1] Kulhawy, F.H. and Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800, Electric Power Research Institute, Palo Alto. https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] Section 3: eq. 3-1 p. 3-2; eqs. 3-4, 3-8 to 3-11 pp. 3-3–3-6; Fig. 3-3; eq. 3-27 p. 3-23; eq. 3-29 p. 3-25; Fig. 3-33 p. 3-30; pp. 3-21, 3-30.
[2] Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). Geotechnical Site Characterization. GEC No. 5, FHWA NHI-16-072. https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] §11.8.5, eq. 11.31 p. 11-39.
[3] Ching, J. and Schweckendiek, T. (eds.) (2021). State-of-the-art review of inherent variability and uncertainty in geotechnical properties and models. ISSMGE TC304. https://doi.org/10.53243/R0001 — [V] Tables 1.2–1.3 p. 11; Tables 5.2–5.3 pp. 178–179; p. 172.
[4] Mayne, P.W. and Kulhawy, F.H. (1982). K0–OCR relationships in soil. J. Geotech. Eng. Div. ASCE 108(GT6), 851–872. https://doi.org/10.1061/AJGEB6.0001306 — [V] bibliographic data and abstract only (equation via [1], [2]).
[5] Jaky, J. (1944). The coefficient of earth pressure at rest. J. Soc. Hungarian Architects and Engineers, Budapest, Oct. 1944, 355–358 — [U] (reference as listed in [1]).
[6] Robertson, P.K. and Cabal, K.L. (2022). Guide to Cone Penetration Testing, 7th ed. Gregg Drilling LLC. https://insitutek.com/wp-content/uploads/2024/08/CPT-Guide-to-Cone-Penetration-Testing-7th-Edition-Robertson-Cabal.pdf — [V] p. 47.
[7] Mayne, P.W. (2007). Cone Penetration Testing. NCHRP Synthesis 368, Transportation Research Board, Washington DC — [U].
[8] Marchetti, S. (1980). In situ tests by flat dilatometer. J. Geotech. Eng. Div. ASCE 106(GT3), 299–321 — [U].
