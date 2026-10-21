# 11 — Hardening Soil stiffness

| | |
|---|---|
| **Parameters** | Eoed, Eur,oed at σ′v0 (oedometer); HS set: E50ref, Eoedref, Eurref, m, pref, Rf, νur |
| **Material** | Soil |
| **Constitutive models that use it** | HS, HS-small (with G0ref, γ0.7 from sheet 10) |
| **Depends on** | [03-specific-gravity-and-void-ratio](03-specific-gravity-and-void-ratio.md) (e0), [04-drained-shear-strength-soil](04-drained-shear-strength-soil.md) (c′, φ′), [06-preconsolidation-and-compressibility](06-preconsolidation-and-compressibility.md) (Cc, Cs, σ′p), [07-at-rest-earth-pressure](07-at-rest-earth-pressure.md) (K0nc), [08-elastic-stiffness-soil](08-elastic-stiffness-soil.md) |
| **Feeds** | [10-small-strain-stiffness](10-small-strain-stiffness.md) (G0/Gur check), tunnel FE input sets |

## 1. Phenomenon
In primary loading soil stiffness falls along a near-hyperbolic stress–strain curve; on unloading and reloading it is
much stiffer and nearly elastic. Both stiffnesses grow with confining stress by a power law with exponent m (about 0.5
in sands and silts, about 1 in soft clays, i.e. logarithmic compression) [1, §6.1]. The HS model (Schanz, Vermeer &
Bonnier 1999) captures this with three independent reference moduli at pref: E50ref (triaxial shear, primary loading),
Eoedref (1-D primary compression, cap) and Eurref (elastic unload-reload), plus the failure ratio Rf that sets the
hyperbola's asymptote qa = qf/Rf [1][2]. The oedometer gives the constrained moduli Eoed (loading) and Eur,oed
(unload-reload) at the in situ stress directly; the triaxial curves give E50 and Eur.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Eoed, Eur,oed, E50ref, Eoedref, Eurref, pref | kPa, MPa | psf, ksf, psi | 1 MPa = 20.885 ksf = 145.04 psi; 1 ksf = 47.88 kPa |
| mv (oedometer) | m²/MN (= 1/MPa) | ft²/kip | Eoed (MPa) = 1/mv (m²/MN) |
| m, Rf, νur | – | – | – |

pref is a stress: the PLAXIS default 100 kPa (= 2.089 ksf, computed) [1, p. 72]. Keep pref and all moduli in one unit.

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| m — gravels and sands / silts / clays, organic soils, peat | ≈ 0.4–0.9 / 0.6–0.9 / 0.85–1.0; values by soil type in [3] Tables 3.7 and 3.25 (after von Soos 1991) | [3] Tables 3.7, 3.25 [V] |
| m — soft clays (logarithmic compression); Norwegian sands and silts | 1.0; ≈ 0.5 (Janbu 1963) | [1] §6.1 p. 66–67 [V] |
| Eurref/E50ref — default; granular (avg 3); loose sand; dense sand; cohesive (avg 4) | 3; 2–6; 3–6; 2–4; 3–6; always > 2 | [1] p. 67, 72 [V]; [3] Eqs. 3.23, 3.64 [V] |
| Eoedref/E50ref | ≈ 1 (no data); = K0nc^m if σoed,ref is defined as σref | [3] Eqs. 3.27, 3.29, 3.77 [V] |
| E50ref, three quartz sands (Schanz & Vermeer 1998) | ≈ 11–47 MPa (digitized ± 1 MPa) | [3] Fig. 3.26 [V] via an extract of the source |
| Rf — most soils; lacustrine soft soils CID / CIU (Kempfert 2006) | 0.75–1.0 (avg 0.9); 0.73–0.88 (avg 0.82) / 0.70–0.99 (avg 0.89) | [3] §3.3.3 [V] |
| Rf default; νur default; pref default; K0nc default | 0.9; 0.2; 100 kPa; 1 − sin φ | [1] p. 72 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Incremental oedometer (with unload-reload) | D2435/D2435M | ISO 17892-5; BS 1377-5 | CONG/CONS: CONS_INCF, CONS_IVR, CONS_INCE, CONS_INMV; CONG_IVR | Eoed = 1/mv per increment; Eur,oed on unload; e–log σ′ (Cc, Cs) |
| CRS oedometer | D4186/D4186M | – | CONG/CONS (as above) | Continuous Eoed(σ′v) |
| Drained triaxial CID (± unload-reload loop) | D7181 | ISO 17892-9; BS 1377-8 | TREG/TRET: TRET_E50, TRET_EP50, TRET_DEVF, TRET_CONP, TRET_CRP | E50 at σ′3; Eur from loop; qf; Rf (q–ε1 curve not in AGS 4.2) |
| Undrained triaxial CIU / CAU | D4767 | ISO 17892-9; BS 1377-8 | TRET as above; TRET_CU, TRET_PWPF | E50,u (convert to drained E50 via 08 §5.4 only with care) |
| Pressuremeter unload-reload loops | D4719 | ISO 22476-4, -6 | PMTL: PMTL_GAA, PMTL_STRA, PMTL_PINC | Gur in situ → Eur = 2Gur(1+νur) |
| Flat dilatometer | D6635 | ISO 22476-11 | DMTP: DMTP_VDM, DMTP_ED | Constrained modulus M (≈ Eoed at σ′v0) |

## 5. Derivations and correlations

### 5.1 HS stress dependence — Schanz, Vermeer & Bonnier (1999); PLAXIS
$$E_{50} = E_{50}^{ref}\left(\frac{c\cos\varphi - \sigma_3'\sin\varphi}{c\cos\varphi + p^{ref}\sin\varphi}\right)^m,\qquad E_{ur} = E_{ur}^{ref}\left(\frac{c\cos\varphi - \sigma_3'\sin\varphi}{c\cos\varphi + p^{ref}\sin\varphi}\right)^m$$
$$E_{oed} = E_{oed}^{ref}\left(\frac{c\cos\varphi - \frac{\sigma_3'}{K_0^{nc}}\sin\varphi}{c\cos\varphi + p^{ref}\sin\varphi}\right)^m$$
- **Inputs:** σ′3 (negative in compression in PLAXIS), c′, φ′, m, pref, K0nc
- **Note:** E50ref is at −σ′3 = pref; Eoedref is a tangent at −σ′1 = −σ′3/K0nc = pref (vertical stress) [1, p. 73–74]
- **Source:** [1] Eqs. 6–5, 6–7, 6–19, pp. 66–73 [V]; [2] [U] (page range from [1] reference list)

### 5.2 E50 and Rf from a drained triaxial q–ε1 curve
$$-\varepsilon_1 = \frac{1}{E_i}\frac{q}{1-q/q_a},\quad E_i = \frac{2E_{50}}{2-R_f},\quad q_a = \frac{q_f}{R_f},\quad q_f = \frac{2\sin\varphi}{1-\sin\varphi}\,(c\cot\varphi - \sigma_3')$$
- **Procedure:** E50 = secant from origin to q = 0.5 qf at the test's σ′3 (TRET_E50 = TRET_DEVF/2 ÷ TRET_EP50);
  Eur = secant slope of an unload-reload loop; Rf = qf/qa from a hyperbolic fit (transformed plot ε1/q vs ε1)
- **Reference value:** convert E50 at σ′3 to E50ref with 5.1, or fit E50ref and m to tests at several σ′3 (log–log
  fit when c′ = 0) _[Judgment — for review]_
- **Source:** [1] Eqs. 6–3, 6–4, 6–6, Fig. 6–5, pp. 66–73 [V]

### 5.3 Eoed and Eur,oed at σ′v0 from the oedometer
$$E_{oed} = \frac{\Delta\sigma_v'}{\Delta\varepsilon_v} = \frac{1}{m_v},\qquad E_{oed} = \frac{\ln 10\,(1+e_0)\,\sigma_v'}{C_c}\ \text{(virgin)},\qquad E_{ur,oed} = \frac{\ln 10\,(1+e_0)\,\sigma_v'}{C_s}\ \text{(unload-reload)}$$
- **Procedure:** tangent at σ′v0: interpolate between the two CONS increments that bracket σ′v0 on the loading
  branch; Eur,oed from the unload (or reload) stage at the same σ′v
- **Valid for:** e–log σ′ linear branches; ln 10 = 2.303 (computed); e at the stress level is better than e0
- **Source:** standard 1-D compression; PLAXIS uses the same form at pref (5.4) [1] [V]

### 5.4 HS reference moduli from Cc, Cs — PLAXIS "alternative parameters"
$$C_c = \frac{2.3(1+e_{init})\,p^{ref}}{E_{oed}^{ref}},\qquad C_s \approx \frac{2.3(1+e_{init})(1+\nu_{ur})(1-2\nu_{ur})\,p^{ref}}{(1-\nu_{ur})\,E_{ur}^{ref}\,K_0},\qquad E_{50}^{ref} = 1.25\,E_{oed}^{ref}$$
- **Valid for:** soft soils, m set to 1 automatically; K0 = K0nc assumed (lightly OC) [1]
- **Source:** [1] §6.4.2 Eqs. 6–20 to 6–22, p. 74 [V]. Obrzud & Truty give similar Cc/e0-based expressions for
  cohesive soils [3] [U] (not in the extract of the source)

### 5.5 Ratios when one modulus is missing — Obrzud & Truty (2018)
$$E_{oed}^{ref} \approx E_{50}^{ref};\quad E_{oed}^{ref} = E_{50}^{ref}\,(K_0^{nc})^m\ (\sigma_{oed}^{ref} = \sigma^{ref});\quad E_{ur}^{ref} = k\,E_{50}^{ref},\ k = 2\text{–}6\ \text{(granular, avg 3)},\ 3\text{–}6\ \text{(cohesive, avg 4)}$$
- **Valid for:** lack of test data; check Eurref/E50ref > 2
- **Source:** [3] Eqs. 3.23, 3.27, 3.29, 3.64, 3.77 [V] via an extract of the source and page images

### 5.6 E50 from a "static" Es at 0.1 % strain — Obrzud & Truty (2018)
$$E_s = \frac{q}{0.001} = \left(\frac{1}{2E_{50}} + \frac{0.001\,R_f}{q_f(\varphi, c)}\right)^{-1}$$
- **Valid for:** using tabulated "static" Es (e.g. from SPT, guidebook Table 3.4/3.5, Fig. 3.25) to back out E50;
  at σ3 = 100 kPa, Es/E50 ≈ 1.58–1.86 (c = 0, φ 15–45°) from Fig. 3.22
- **Source:** [3] Eq. 3.24, Fig. 3.22 [V] via an extract of the source (chart values digitized ± 0.02)

### 5.7 Sands from relative density — Brinkgreve, Engin & Engin (2010)
$$E_{50}^{ref} = E_{oed}^{ref} = 60\,000\,\tfrac{RD}{100},\ E_{ur}^{ref} = 180\,000\,\tfrac{RD}{100}\ (\text{kPa}),\ m = 0.7 - \tfrac{RD}{320},\ R_f = 1 - \tfrac{RD}{800}$$
- **Valid for:** quartz sands, first estimate only
- **Source:** [4] [U] (cited in [1] §7.4 but formulas not read)

### 5.8 Constrained ↔ Young's unload-reload modulus (elastic)
$$E_{ur} = E_{ur,oed}\,\frac{(1+\nu_{ur})(1-2\nu_{ur})}{1-\nu_{ur}}$$
- Computed factor: νur = 0.15 → 0.947; 0.2 → 0.900; 0.25 → 0.833. Valid for Eur only (elastic); there is no fixed
  relation between E50 and Eoed in HS [1, p. 73].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE (HS, HS-small) — surface settlement | Eurref governs elastic unloading around the opening and invert heave; E50ref governs shear hardening ahead of and around the face; m sets the depth profile | High for Eur and E50; HS gives deeper, narrower troughs than MC; Eur/E50 ratio changes trough shape [1, §3.3.1] _[Judgment — for review]_ [6] [U] |
| Volume loss (if from FE, not prescribed) | Through E50 and Eur near the face | High |
| Face stability / support pressure | Strength governs collapse; E50 affects face extrusion at service pressures | Low (collapse) to moderate (deformation) |
| Lining loads | Ground reaction stiffness ≈ Eur at σ′ around the lining | Moderate |
| Consolidation settlement / cap behavior | Eoedref and m control volumetric hardening | High for 1-D compression; low for pure unloading |
| Rf, νur, pref | Rf shapes the hyperbola; νur the elastic ratio; pref is only a reference | Low (Rf, νur); none (pref, if consistent) |

**Typical variability:** Eoed and E50 from good-quality lab tests: inherent COV commonly of order 20–50 %
_[Judgment — for review]_ [5] [U]. Ratio-based estimates (Eur ≈ 2–6 × E50) span a factor of 3 [3]; tabulated m ranges are
0.05–0.2 wide within a soil class (computed from the row widths of Tables 3.7 and 3.25) [3].

## 7. Pitfalls and QA checks
- Eoed at σ′v0 in an OC soil lies on the reload branch; Eoedref is primary loading. Take Eoedref from the virgin branch
  beyond σ′p, or Eur,oed from the reload branch, not a mix.
- Reference stress definitions differ between codes (PLAXIS: Eoedref at σ′1 = pref; Z_Soil may use σoed,ref = σref/K0nc,
  [3] Eq. 3.28). Check before transferring values.
- Sign convention: PLAXIS σ′3 is negative in compression [1].
- PLAXIS rejects some combinations of Eoedref/E50ref, K0nc and νur [1, §6.4.3].
- Sample disturbance lowers E50 and Eoed and hides σ′p; check Eurref against Gur from pressuremeter loops and G0
  (G0/Gur ≤ 20) [1, §7.5].
- Do not use E50 from undrained tests as drained E50 without conversion and judgement.
- Keep m consistent between E50, Eoed, Eur and G0 (one m in HS).

## References
[1] Bentley/Seequent (2025). *PLAXIS 2D 2025.1 Material Models Manual*, Ch. 6 (Hardening Soil), §3.3, §7.5, pp. 34–89.
https://files.seequent.com/PLAXIS/Manuals/PLAXIS_2D/English/PLAXIS_2D_3_Material%20Models%20Manual.pdf — [V]
equations and text read
[2] Schanz, T., Vermeer, P.A., Bonnier, P.G. (1999). The hardening soil model: formulation and verification. In
Brinkgreve (ed.), *Beyond 2000 in Computational Geotechnics*, Balkema, Rotterdam, 281–290. — [U] (citation via [1])
[3] Obrzud, R.F., Truty, A. (2018). *The Hardening Soil Model – A Practical Guidebook*. Z_Soil.PC 100701 report,
revised 21.10.2018, Zace Services. — [V] Tables 3.7, 3.25; Eqs. 3.23, 3.24, 3.27–3.29, 3.64, 3.77; Fig. 3.22, 3.26;
§3.3.3 via an extract of the source and its page images
[4] Brinkgreve, R.B.J., Engin, E., Engin, H.K. (2010). Validation of empirical formulas to derive model parameters for
sands. *NUMGE 2010*, Trondheim, 1, 137–142. — [U] (page range differs in [1] reference list)
[5] Phoon, K.K., Kulhawy, F.H. (1999b). Evaluation of geotechnical property variability. *Can. Geotech. J.* 36(4),
625–639. https://doi.org/10.1139/t99-039 — [U] (values not read)
[6] Möller, S.C. (2006). *Tunnel Induced Settlements and Structural Forces in Linings*. PhD thesis, Univ. Stuttgart.
— [U]
