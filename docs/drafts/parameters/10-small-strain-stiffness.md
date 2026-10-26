# 10 — Small-strain stiffness

Promoted to the docs site as [`docs/site/parameters/10-small-strain-stiffness.md`](../../site/parameters/10-small-strain-stiffness.md) (M13 b3); the page is current where they differ.

| | |
|---|---|
| **Parameters** | Vs (shear wave velocity), G0 = Gmax (small-strain shear modulus), G0ref (HS-small reference value), γ0.7 (threshold shear strain), γref / γr (reference strain at G/G0 = 0.5) |
| **Material** | Soil (methods also apply to rock for Vs) |
| **Constitutive models that use it** | HS-small (G0ref, γ0.7); dynamic/site response; E0 for MC via strain reduction |
| **Depends on** | [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (ρ, σ′), [02-index-properties](02-index-properties.md) (PI), [03-specific-gravity-and-void-ratio](03-specific-gravity-and-void-ratio.md) (e), [06-preconsolidation-and-compressibility](06-preconsolidation-and-compressibility.md) (OCR) |
| **Feeds** | [08-elastic-stiffness-soil](08-elastic-stiffness-soil.md), [11-hardening-soil-stiffness](11-hardening-soil-stiffness.md) |

## 1. Phenomenon
Below a very small strain (the elastic threshold, typically 0.001–0.01 %) soil is close to linear elastic with
maximum shear stiffness G0 [2, §8.5.3]. G0 is set by void ratio, mean effective stress, stress history and fabric,
and is measured best by shear wave velocity in situ: G0 = ρVs² [2, Eq. 8.1]. Beyond the threshold, the secant modulus
decays along an S-shaped curve with log strain. Plasticity shifts the curve to larger strains, confining stress shifts
it to larger strains, and rate effects matter [4][5]. γ0.7 (HS-small) is the shear strain at Gs = 0.722 G0 [1, §7.1];
γref (Vardanega & Bolton, Darendeli) is the strain at G/G0 = 0.5. Vs is largely unaffected by pore water, so it
measures the skeleton [2, §8.2].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Vs | m/s | ft/s | 1 m/s = 3.2808 ft/s |
| ρ | Mg/m³ (= t/m³) | pcf (lbm/ft³) | 1 Mg/m³ = 62.43 pcf; ρ = γt/g |
| G0, G0ref | MPa | ksf, psi | 1 MPa = 20.885 ksf = 145.04 psi |
| γ0.7, γref | – (strain) | – | often quoted in %: 1×10⁻⁴ = 0.01 % |

Example (computed): ρ = 2.0 Mg/m³, Vs = 200 m/s (656 ft/s) → G0 = 80 MPa.

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Site class E / D / C / B (Vs30, ASCE 7-16) | < 183 / 183–366 / 366–762 / 762–1524 m/s (< 600 / 600–1200 / 1200–2500 / 2500–5000 ft/s) | [9] Table 20.3-1 [U] |
| γref (static), 21 clays and silts, 67 tests | 0.00036–0.0021 (test-series averages) | [5] Table 1 [V] |
| γ0.7 from V&B, PI = 10 / 20 / 30 / 50 % | 0.61 / 1.21 / 1.82 / 3.03 ×10⁻⁴ (computed from 5.4) | [5] Eqs. 1a, 1b [V] |
| γ0.7, sands (Brinkgreve et al. 2010) | (2 − RD/100)×10⁻⁴, i.e. 1–2 ×10⁻⁴ | [1] ref. 31; formula [U] |
| G0/Gur (HS-small input check) | ≤ 20 enforced; Alpan ratio E0/Eur > 10 possible for very soft clays | [1] §7.5 p. 89 [V] |
| Gmax/ED, sands (DMT) | 2.72 ± 0.59 (calibration chamber); 2.2 ± 0.7 (field) | [2] Table 8-9 [V] |
| K2,max (Seed & Idriss), sand Dr 30–90 % | 34–70; gravels 80–180 | [2] Table 8-3 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Crosshole seismic | D4428/D4428M | – | ISTG/ISTS/ISTR/ISTA: ISTG_TYPE, ISTA_WVTY, ISTA_WVL, ISTA_TOP, ISTA_BASE | Vs, Vp per depth (best vertical resolution) [2] |
| Downhole seismic; seismic CPT; seismic DMT | D7400/D7400M (with D5778, D6635) | ISO 22476-1, -11 (CPT, DMT only) | ISTG/ISTA as above; ISTG_LINK to SCPG/DMTG | Interval Vs |
| PS suspension logging | – | – | WGPG/WGPT (WGPG_TOOL, WGPT_PARA, WGPT_RDNG) | Vs, Vp, fluid-filled hole, deep |
| SASW / MASW / ReMi (surface waves) | – | – | none in AGS 4.2 (report file) | Vs profile by inversion; resolution falls with depth [2] |
| Bender elements | D8295 | – | LDYN: LDYN_SWAV, LDYN_SG | Lab Vs, G0 (disturbance lowers it) |
| Resonant column (± torsional shear) | D4015 | – | RESG/RESD/RESP: RESP_SMOD, RESD_SM, RESD_AVSS, RESP_SMRA | G0 and G/G0–γ to ≈ 0.1 % [2, §8.7] |
| Cyclic triaxial | D3999/D3999M | – | CTRG/CTRP: CTRP_ESEC, CTRP_DAMP | E, damping at larger strains |
| Triaxial with local strain | D7181 / D4767 + local gauges | ISO 17892-9 | TRET (curves not in AGS 4.2) | Monotonic G/G0 to 10⁻⁴ % [2] |
| CPT / DMT correlated | D5778; D6635 | ISO 22476-1, -11 | CPTP: CPTP_VS1, CPTP_G01; DMTP: DMTP_VS | Correlated Vs, G0 (not a measurement) |

AGS 4.2 has no "VSPR" group; a Vs profile under that name is a user-defined group.

## 5. Derivations and correlations

### 5.1 G0 from Vs — elastic wave theory
$$G_0 = \rho V_s^2,\quad \rho = \gamma_t / g,\quad E_0 = 2G_0(1+\nu)$$
- **Inputs:** Vs (m/s), γt (kN/m³), g = 9.81 m/s² → G0 (kPa if ρ in Mg/m³ and Vs in m/s, ÷1000 for MPa)
- **Valid for:** all soils, strain < elastic threshold
- **Scatter:** from Vs measurement and ρ; G0 ∝ Vs², so a 10 % Vs error is about 21 % in G0 (computed: 1.1² − 1)
- **Source:** [2] Eqs. 8.1, 8.4 [V]

### 5.2 Hardin-type G0 from e and σ′m — Hardin & Richart (1963); Hardin (1978)
$$G_{max} = A\,F(e)\,\sigma_m'^{\,n}\ \text{(coarse)};\qquad G_{max} = A\,F(e)\,OCR^k\,p_a^{1-n}\,\sigma_m'^{\,n}\ \text{(fine)}$$
$$F(e) = \frac{1}{0.3+0.7e^2}\ \text{(Hardin 1978)};\quad \frac{(2.97-e)^2}{1+e}\ \text{(angular)};\quad \frac{(2.17-e)^2}{1+e}\ \text{(round)}$$
- **Inputs:** e, σ′m (kPa), OCR, k(PI): PI 0 → 0, 20 → 0.18, 40 → 0.30, 60 → 0.41, 80 → 0.48, ≥ 100 → 0.50
- **Coefficients:** coarse soils A = 1200–13 000, n = 0.38–0.885 (Table 8-2, Gmax and σ′m in kPa); fine soils A = 625,
  n = 0.5 (Hardin 1978)
- **Valid for:** soils like those tested; site-specific fitting reduces uncertainty a lot [2]
- **Source:** [2] Eqs. 8.7–8.10, 8.14; Tables 8-2, 8-4, pp. 8-16 to 8-18 [V]; same form in [3] Eq. 3.13
  (k = 0 sands, 0.5 high-PI clays) [V] via an extract of the source

### 5.3 HS-small G0ref and stress dependence — Benz (2006/2007); PLAXIS
$$G_0 = G_0^{ref}\left(\frac{c\cos\varphi - \sigma_3'\sin\varphi}{c\cos\varphi + p^{ref}\sin\varphi}\right)^m,\qquad G_0^{ref} \approx 33\,\frac{(2.97-e)^2}{1+e}\ \text{MPa}\ (p^{ref} = 100\ \text{kPa})$$
- **Inputs:** G0ref at pref = 100 kPa; m, c, φ as for the other HS moduli (σ′3 negative in compression); e
- **Note:** the coefficient was read as "3.2" from the 2025.1 manual's equation image (possibly a reading error;
  check the printed page). 33 is the commonly quoted PLAXIS value and agrees with the Hardin
  angular-grain relation (A = 3300, n = 0.5): at σ′m = 100 kPa, 3300·√100 = 33 000 kPa = 33 MPa (computed) [2]
- **Back-calculate G0ref from a measured G0:** invert the power law at the in situ σ′3 with the layer's m, c, φ
  _[Judgment — for review]_
- **Source:** [1] §7.5 Eqs. 7–13, 7–14, p. 88 [V]; [6] [U]

### 5.4 γref from PI — Vardanega & Bolton (2013)
$$\frac{G}{G_{max}} = \frac{1}{1+(\gamma/\gamma_{ref})^{\alpha}},\quad \gamma_{ref} = J\,\frac{I_p}{1000};\quad \text{static: } J = 2.2,\ \alpha = 0.74;\ \text{dynamic: } J = 3.7,\ \alpha = 0.94$$
- **Inputs:** Ip as a number (e.g. 0.30 for PI = 30 %) → γref as strain (0.00066); equivalently γref[%] = 2.2·PI[%]/1000
- **Convert to γ0.7:** solve G/G0 = 0.722 → γ0.7 = γref·0.385^(1/α) = 0.275·γref (α = 0.74, computed)
- **Valid for:** 67 tests, 21 clays and silts; static form for strain rates near 10⁻⁶/s (triaxial); OCR had no
  significant effect on γref [5]
- **Scatter:** ±50 % on γ0.7 is quoted from the HS guide §7.1 [3] [U]; V&B report ±1 SD bands on α [5]
- **Source:** [5] Eqs. 1a, 1b, 2a, 2b (quoting [4]) [V]; [4] [U] (original not read)

### 5.5 γr from PI, OCR, σ′m — Darendeli (2001)
$$\frac{G}{G_{max}} = \frac{1}{1+(\gamma/\gamma_r)^a},\quad \gamma_r[\%] = (\varphi_1+\varphi_2\,PI\,OCR^{\varphi_3})\,(\sigma_m'/p_a)^{\varphi_4}$$
- **Coefficients:** φ1 = 0.0352, φ2 = 0.0010, φ3 = 0.3246, φ4 = 0.3483, a = 0.919 [U]
- **Convert to γ0.7:** γ0.7 = γr·0.385^(1/a) = 0.354·γr (a = 0.919, computed)
- **Valid for:** resonant column / torsional shear data, dynamic rates; used in site response [2, §8.8]
- **Source:** [7] [U]; the equation form was seen only in secondary software documentation (groundhog), and
  GEC 5 §8.8 cites Darendeli without the equation [2]

### 5.6 HS-small modulus decay and cut-off — Hardin & Drnevich (1972), Santos & Correia (2001)
$$\frac{G_s}{G_0} = \frac{1}{1+a\,|\gamma/\gamma_{0.7}|},\ a = 0.385;\qquad \gamma_{cut\text{-}off} = \frac{1}{0.385}\left(\sqrt{\frac{G_0}{G_{ur}}}-1\right)\gamma_{0.7}$$
- At γ = γ0.7, Gs/G0 = 1/1.385 = 0.722 (computed). Tangent G stops at Gur = Eur/(2(1+νur)) [1, Eq. 7–9].
- γ0.7 from MC strength: γ0.7 ≈ [2c′(1+cos 2φ′) − σ′1(1+K0) sin 2φ′]/(9G0) [1, Eq. 7–15]
- **Source:** [1] §7.1–7.2 Eqs. 7–1 to 7–3, 7–9, 7–10, 7–15, pp. 82–89 [V]

### 5.7 Vs and G0 from SPT and CPT (preliminary only)
$$V_s = a\,N_{60}^{\,b}\ \text{(m/s), e.g. Imai \& Tonouchi (1982): } 93.7N_{60}^{0.31}\ (r^2 = 0.75);\ \text{Ohta \& Goto (1978): } 82.1N_{60}^{0.35}\ (r^2 = 0.52)$$
- **N basis and geology (corrected, M13 b3):** both are Wair et al. (2012, PEER 2012/08, Table 4.2, p. 28)'s 60 %
  forms of the sources' Japanese N at an assumed 67 % energy (97.0 N^0.31 and 85.3 N^0.35 on uncorrected N).
  93.7 N60^0.31 is Imai & Tonouchi's all-soils fit (H, P, T; alluvium and fill; n = 1654), and 82.1 N60^0.35
  Ohta & Goto's Quaternary fit. GEC 5 Table 8-5's notes column is shifted a row against Wair et al.'s table, so it
  labels the first "Tertiary" and the second "Holocene"; Wair et al. govern.
$$G_{max} = 49.4\,q_t^{0.695}e^{-1.130}\ \text{(clay, MPa; Mayne \& Rix 1993)};\quad V_s = 1.75\,q_t^{0.627}\ \text{(clay, } q_t \text{ in kPa; Mayne \& Rix 1995)}$$
- **Scatter:** r² 0.51–0.75 for Vs–N60 forms that report it [2] Table 8-5; GEC 5: "considerable variability" [2]
- **Source:** [2] Tables 8-5 to 8-8, pp. 8-20 to 8-21 [V]

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE, HS-small | G0ref and γ0.7 set stiffness at the small strains away from the tunnel | High for trough width and far-field movements (building damage); low near the opening where strains are large [1] _[Judgment — for review]_ |
| Tunnel FE, MC | E0 from G0 only after strain reduction (sheet 08) | High if E0 used unreduced: displacements underestimated |
| Settlement / volume loss (empirical) | Not used | Low |
| Face stability / support pressure | Not used | Low |
| Lining loads | Through the stiffness of ground near the lining (moderate strains) | Low to moderate |
| Vibration / seismic site response | G0 and G/G0 curve directly | High |

**Typical variability:** inherent COV of measured Vs within a uniform layer is often quoted near 10–30 %
_[Judgment — for review]_ [U]. Transformation error is larger: Vs–N60 r² = 0.51–0.75 [2]; Gmax/ED for sands
2.72 ± 0.59 (COV 22 %, computed) and 2.2 ± 0.7 (COV 32 %) [2]; Hryciw's DMT method had a 23 % average error [2].
γ0.7 from PI: ±50 % [U].

## 7. Pitfalls and QA checks
- Use the unit's total density, not dry or buoyant, in ρ = γt/g.
- Lab G0 (bender, RC) is usually lower than field G0 because of disturbance; correct with Eq. 8.5 [2, §8.2].
- γref (G/G0 = 0.5) ≠ γ0.7 (G/G0 = 0.722): convert (5.4, 5.5) before entering HS-small.
- Dynamic (RC, Darendeli; V&B dynamic) curves are stiffer and shifted vs monotonic static loading [2, §8.8][5].
- Check G0/Gur ≤ 20 (PLAXIS limit) and G0 > Gur [1].
- Downhole Vs at depth and surface-wave Vs in thin deep layers are less reliable [2].
- G0ref must be referred to pref = 100 kPa with the same m as the HS moduli; do not enter the in situ G0.

## References
[1] Bentley/Seequent (2025). *PLAXIS 2D 2025.1 Material Models Manual*, Ch. 7 HSsmall, pp. 81–89.
https://files.seequent.com/PLAXIS/Manuals/PLAXIS_2D/English/PLAXIS_2D_3_Material%20Models%20Manual.pdf — [V]
equations and text read
[2] Loehr, J.E. et al. (2016). *Geotechnical Site Characterization*, GEC 5, FHWA-NHI-16-072, Ch. 8, pp. 8-3 to 8-27.
https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] pages read
[3] Obrzud, R.F., Truty, A. (2018). *The Hardening Soil Model – A Practical Guidebook*. Z_Soil.PC 100701 report, Zace
Services. — [V] Eq. 3.13 via an extract of the source; §7.1 ±50 % statement [U]
[4] Vardanega, P.J., Bolton, M.D. (2013). Stiffness of clays and silts: normalizing shear modulus and shear strain.
*J. Geotech. Geoenviron. Eng.* 139(9), 1575–1589. https://doi.org/10.1061/(ASCE)GT.1943-5606.0000887 — [U]
(equations seen only as quoted in [5]; page range [U])
[5] Vardanega, P.J., Bolton, M.D. (2014). Stiffness of clays and silts: modeling considerations. *J. Geotech.
Geoenviron. Eng.* 140(6), 06014004. https://doi.org/10.1061/(ASCE)GT.1943-5606.0001104 — [V] Eqs. 1a–2b, Table 1 read
[6] Benz, T. (2007). *Small-Strain Stiffness of Soils and its Numerical Consequences*. PhD thesis, Univ. Stuttgart
(PLAXIS cites it as 2006). — [U]
[7] Darendeli, M.B. (2001). *Development of a New Family of Normalized Modulus Reduction and Material Damping Curves*.
PhD dissertation, Univ. of Texas at Austin. — [U] (coefficients not checked against the source)
[8] Hardin, B.O., Drnevich, V.P. (1972). Shear modulus and damping in soils: design equations and curves. *J. Soil
Mech. Found. Div.* 98(SM7), 667–692. — [V] citation via [1] reference list
[9] ASCE (2017). *Minimum Design Loads and Associated Criteria for Buildings and Other Structures*, ASCE/SEI 7-16,
Table 20.3-1. — [U] (ASCE 7-22 adds intermediate classes)
