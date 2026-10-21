# 05 — Undrained shear strength

| | |
|---|---|
| **Parameters** | su (undrained shear strength; also cu), su,r (remolded), St = su/su,r (sensitivity) |
| **Material** | Soil (fine-grained; low-permeability under the loading rate) |
| **Constitutive models that use it** | MC / Tresca (φu = 0 total-stress), NGI-ADP, HS / HS-small in "undrained B" mode, SHANSEP-MC |
| **Depends on** | [01 Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σv0, σ′v0), [02 Index properties](02-index-properties.md) (PI), [04 Drained shear strength](04-drained-shear-strength-soil.md) (φ′ for CSSM ratio), [06 Preconsolidation and compressibility](06-preconsolidation-and-compressibility.md) (OCR, σ′p, Cs/Cc) |
| **Feeds** | [08 Elastic stiffness of soil](08-elastic-stiffness-soil.md) (E/su), [11 Hardening Soil stiffness](11-hardening-soil-stiffness.md) (undrained calibration) |

## 1. Phenomenon
su is the shear stress at failure when no drainage occurs, so it is not a soil constant but the result of the
effective-stress path the soil follows from its in-situ state (e0, σ′v0, OCR) to the critical state. It therefore
depends on stress history (OCR), mode of shear and stress rotation (compression > simple shear > extension:
anisotropy), strain rate (≈ 10 % per log cycle) and sample disturbance (which usually lowers it). Fissures and
sample size reduce operational su in stiff OC clays. Every test (UU, vane, pocket penetrometer, CPT) measures a
different "su", so values must be referenced to a mode (e.g., triaxial compression, DSS) before combining.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| su, qu (= 2 su) | kPa | psf, ksf, tsf, psi | 1 kPa = 20.8854 psf = 0.020885 ksf = 0.14504 psi; 1 tsf = 95.761 kPa; 1 kg/cm² = 98.066 kPa |
| su/σ′v0, S, m, Nkt, f1/pa | – | – | dimensionless |
| f1 (Stroud) | kPa per blow | psf per blow | as su |

## 3. Typical values

| Material (consistency) | su range | Source |
|---|---|---|
| Very soft / soft / medium (firm) / stiff / very stiff / hard | < 12.5 / 12.5–25 / 25–50 / 50–100 / 100–200 / > 200 kPa (< 261 / 261–522 / 522–1044 / 1044–2089 / 2089–4177 / > 4177 psf) | Terzaghi & Peck (1967) qu classes halved [V] via [9] |
| NC clay, su(VST)/σ′v0 | 0.11 + 0.0037 PI (≈ 0.15–0.33 for PI 10–60) | [1] Eq. 4-18, p. 4-28 (Skempton) [V] |
| NC clay, DSS su/σ′v0 (S) | ≈ 0.22 | [2] Eq. 1.4 [V] |
| Mobilized (field back-analysis) su/σ′p | ≈ 0.22 | [2] Eq. 1.5 (Mesri 1975) [V]; [1] Eq. 4-22 |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| UU triaxial | D2850 | ISO 17892-8; BS 1377-7 | TRIG: TRIG_TYPE (UU, UUM), TRIG_COND; TRIT: TRIT_CELL, TRIT_DEVF, TRIT_CU, TRIT_STRN, TRIT_RATE, TRIT_MODE | su = q_f/2 (TC mode, total stress) |
| Unconfined compression | D2166/D2166M | ISO 17892-7; BS 1377-7 | LUCT: LUCT_UCS, LUCT_STRA, LUCT_RATE | su = qu/2 |
| CU triaxial | D4767 | ISO 17892-9; BS 1377-8 | TREG_TYPE (CIUC, CAUC, CAUE…); TRET: TRET_CU, TRET_DEVF, TRET_CONP | su at the consolidation stress (SHANSEP input) |
| Direct simple shear | D6528 | – | no standard AGS 4.2 group (user-defined) | su,DSS |
| Field vane | D2573/D2573M | ISO 22476-9; BS 1377-9 | IVAN: IVAN_IVAN (peak), IVAN_IVAR (remolded), IVAN_TYPE, IVAN_DPTH | su(VST), St |
| Laboratory vane | D4648/D4648M | BS 1377-7 | LVAN: LVAN_VNPK, LVAN_VNRM, LVAN_SIZE | su, su,r |
| Pocket (hand) penetrometer | no ASTM standard method | – | LPEN: LPEN_PPEN (lab); IPEN: IPEN_IPEN (in situ) | index su (or qu — check instrument) |
| Fall cone | – | ISO 17892-6 | LFCN: LFCN_FCPK, LFCN_FCRM | index su |
| CPTu | D5778 | ISO 22476-1 | CPTT: CPTT_QT, CPTT_CPO, CPTT_QNET, CPTT_BQ; CPTP: CPTP_SU1, CPTP_SU2; SCPP_CSU | su = qnet/Nkt |
| SPT (correlation) | D1586/D1586M | ISO 22476-3 | ISPT: ISPT_NVAL, ISPT_ERAT, ISPT_N60 | N60 → 5.4 |

ASTM designations without year — confirm the current edition before citing.

## 5. Derivations and correlations

### 5.1 UU / unconfined
$$s_u = q_f/2 = (\sigma_1-\sigma_3)_f/2\qquad(\text{TRIT\_DEVF}/2;\ \text{UCS: LUCT\_UCS}/2)$$
- **Valid for:** saturated, intact specimens; φu ≈ 0 in total stress. Check TRIT_CU against TRIT_DEVF/2.
- **Note:** UU su is at the field stress state but includes disturbance (often low) and fissure effects.

### 5.2 Field vane with Bjerrum correction
$$s_{u,\text{field}} = \mu\, s_u(\text{VST}),\quad \mu = f(PI)\ \ (\mu\approx 1.0\ \text{at low PI, falling to}\approx 0.6\text{–}0.7\ \text{at PI}\approx 80\text{–}100)$$
- **Inputs:** IVAN_IVAN, PI. Commonly fitted μ = 1.7 − 0.54 log PI [U].
- **Source:** [1] Fig. 4-48, p. 4-52 (Bjerrum μ, update after Ladd et al. 1977) [V figure; numeric range read
  from the figure, U].

### 5.3 Pocket penetrometer
$$s_u \approx \text{reading}/2\ \ \text{if the instrument is scaled in }q_u\ \text{(kg/cm}^2\text{ or tsf)}$$
- Index test only: small volume, surface of sample, no standard. Use to rank, not to set design su.
  _[Judgment — for review]_

### 5.4 SPT — Stroud (1974)
$$s_u = f_1\,N_{60}$$
- **Inputs:** N60, PI. f1 ≈ 4–6 kPa (≈ 4.4 kPa for PI > 30 %, rising as PI falls toward 15 %).
- **Valid for:** insensitive stiff clays and weak rocks (UK data); su from UU triaxial on 100 mm specimens.
- **Scatter:** large; local f1 calibration recommended.
- **Source:** [3] (Fig. relating f1 to PI) [U for f1 values]; bibliographic data [V] via [1] Section 6 ref. 16.

### 5.5 SHANSEP — Ladd & Foott (1974); Ladd (1991)
$$\frac{s_u}{\sigma'_{v0}} = S\cdot OCR^{\,m}$$
- **Typical:** DSS mode S ≈ 0.22, m ≈ 0.80 for lean–plastic sedimentary clays of low–moderate sensitivity
  (Ladd & DeGroot 2003) — [2] Eq. 1.4 [V]. Jamiolkowski et al. (1985): S = 0.23 ± 0.04, m = 0.8 — [1] Eq. 4-38,
  p. 4-37 [V]; m falls from ≈ 0.85 to 0.75 with increasing OCR ([1] p. 4-37) [V].
- **CSSM form:** S = ½ sin φ′ OCR^Λ with Λ = 1 − Cs/Cc ≈ 0.8 ± 0.1 — [2] Eq. 1.3 [V].
- **Inputs:** σ′v0 (01), OCR or σ′p (06). Not for fissured, cemented or highly structured clays (fissured: su
  may be ½ or less, [2] p. 2789).
- **Source:** [4], [5] [V bibliographic]; values as above.

### 5.6 CPTu cone factor
$$s_u = \frac{q_t - \sigma_{v0}}{N_{kt}},\quad N_{kt}\approx 10\text{–}18\ (\text{average }14)$$
- Nkt rises with plasticity and falls with sensitivity; Nkt = 10.5 + 7 log Fr (Robertson 2012).
- **Source:** [6] p. 41 [V]; also Lunne, Robertson & Powell (1997) [7] [U]. Calibrate Nkt to site lab/vane su.

### 5.7 Mode, rate and anisotropy factors (to convert between tests)
$$s_u/s_u(1\%/\text{h}) = 1.0 + 0.1\log\dot\varepsilon\ (\%/\text{h})$$
- Mode ratios to CIUC (linear approx., 20° < φ′tc < 40°): CK0UC 1.13 − 0.0094 φ′tc; DSS 0.77 − 0.0064 φ′tc;
  CK0UE 0.56 − 0.0046 φ′tc.
- **Source:** [1] Eq. 4-54, p. 4-48 and Table 4-9, p. 4-50 [V].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Face stability in clay (Broms & Bennermarius stability ratio N = (σv − σT)/su) | resisting term directly | **High** — N > ~6 indicates face instability (Broms & Bennermarius 1967 [U]); linear in su |
| Tunnel FE, undrained (Tresca / undrained HS) | yield stress; extent of plastic zone; E/su ratios | **High** for convergence and volume loss near failure (load factor) |
| Settlement / volume loss (e.g. VL vs load factor N/Nc) | VL rises sharply as load factor → 1 | High when N/Nc > ~0.5 _[Judgment — for review]_ |
| Lining loads (short term) | ground relaxation before support | Moderate |
| Groundwater inflow | none | Low |

**Typical variability:** su COV ≈ 13–40 % (Duncan 2000 [8]) [U]; Phoon & Kulhawy (1999) give inherent COV of
roughly 10–55 % depending on test (UU, UC, VST) [10] [U]. Correlations add transformation uncertainty: Stroud f1
and CPT Nkt each typically vary ±30 % or more between sites _[Judgment — for review]_.

## 7. Pitfalls and QA checks
- State the mode (TC, DSS, TE, vane, CPT) for every su; do not average across modes without 5.7 factors.
- UU on fissured or silty/sandy clays gives scattered, often low su; UU in partially saturated soil is not su.
- Check for disturbance (low strain at failure, bulging, sample-quality Δe/e0 — see [06](06-preconsolidation-and-compressibility.md)).
- Vane in silty or stony clay, or with St high, needs care; apply μ only to field vane.
- SHANSEP needs a reliable σ′p profile; it inherits all of 06's uncertainty.
- Pocket penetrometer: confirm whether the reading is qu or su (factor 2).
- SPT N in clay: confirm N vs N60; energy ratio (ISPT_ERAT) is often missing.
- Sanity check: su/σ′v0 vs OCR should follow 5.5; outliers flag disturbance or wrong σ′v0.

## References
[1] Kulhawy, F.H. & Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800.
https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] Eqs. 4-18, 4-22, 4-38, 4-54; Table 4-9;
Fig. 4-48; Stroud reference.
[2] Mayne, P.W., Coop, M.R., Springman, S.M., Huang, A.-B. & Zornberg, J.G. (2009). Geomaterial behavior and
testing. Proc. 17th ICSMGE, Alexandria, 2777–2872. https://doi.org/10.3233/978-1-60750-031-5-2777 — [V] Eqs. 1.3–1.5
(p. 2789).
[3] Stroud, M.A. (1974). The standard penetration test in insensitive clays and soft rocks. Proc. European Symp.
on Penetration Testing (ESOPT), Stockholm, Vol. 2.2, 367–375. — [U] (values); citation [V] via [1].
[4] Ladd, C.C. & Foott, R. (1974). New design procedure for stability of soft clays. J. Geotech. Eng. Div. ASCE
100(GT7), 763–786. https://doi.org/10.1061/AJGEB6.0000066 — [V] bibliographic (TRID/ASCE record).
[5] Ladd, C.C. (1991). Stability evaluation during staged construction (22nd Terzaghi Lecture). J. Geotech. Eng.
117(4), 540–615. https://doi.org/10.1061/(ASCE)0733-9410(1991)117:4(540) — [V] bibliographic.
[6] Robertson, P.K. & Cabal, K. (2022). Guide to Cone Penetration Testing, 7th ed. Gregg Drilling.
https://insitutek.com/wp-content/uploads/2024/08/CPT-Guide-to-Cone-Penetration-Testing-7th-Edition-Robertson-Cabal.pdf
— [V] p. 41 (Nkt).
[7] Lunne, T., Robertson, P.K. & Powell, J.J.M. (1997). Cone Penetration Testing in Geotechnical Practice.
Blackie / Spon. — [U]
[8] Duncan, J.M. (2000). Factors of safety and reliability in geotechnical engineering. J. Geotech. Geoenviron.
Eng. 126(4), 307–316. https://doi.org/10.1061/(ASCE)1090-0241(2000)126:4(307) — [U]
[9] groundhog documentation, SPT correlations (Terzaghi & Peck 1967 consistency classes).
https://groundhog.readthedocs.io/en/dev/site_investigation/spt_correlations.html — [V] secondary.
[10] Phoon, K.-K. & Kulhawy, F.H. (1999). Characterization of geotechnical variability. Can. Geotech. J. 36(4),
612–624. — [U]
