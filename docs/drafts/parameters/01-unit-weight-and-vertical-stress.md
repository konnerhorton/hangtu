# 01 — Unit weight and vertical stress

**Promoted** (M13) to [`docs/site/parameters/01-unit-weight-and-vertical-stress.md`](../../site/parameters/01-unit-weight-and-vertical-stress.md); the page is the current text. Duncan (2000)'s COV table couldn't be checked and was cut.

| | |
|---|---|
| **Parameters** | γ (bulk / total unit weight), γsat (saturated), γd (dry), γ′ (buoyant), σv0 (total vertical stress), u0 (in situ pore pressure), σ′v0 (effective vertical stress) |
| **Material** | Both (soil and intact rock) |
| **Constitutive models that use it** | All (MC, HS, HB): self-weight, initial stress, stress-dependent stiffness |
| **Depends on** | [02-index-properties](02-index-properties.md) (w), [03-specific-gravity-and-void-ratio](03-specific-gravity-and-void-ratio.md) (Gs, e) |
| **Feeds** | [04](04-drained-shear-strength-soil.md), [05](05-undrained-shear-strength.md), [06](06-preconsolidation-and-compressibility.md) (OCR), [07](07-at-rest-earth-pressure.md), [10](10-small-strain-stiffness.md) (ρ for G0), [11](11-hardening-soil-stiffness.md) (stress level), [20](20-in-situ-stress-rock.md) |

## 1. Phenomenon
Unit weight is the weight of a unit volume of ground (solids + water + air); density is the mass equivalent
(γ = ρ g). It is controlled by mineralogy (Gs), packing (e or n) and degree of saturation, so it varies little
within a unit compared with strength or stiffness. Integrated over depth it gives the total vertical stress
σv0; subtracting the pore pressure u0 gives the effective vertical stress σ′v0 that controls soil strength,
stiffness and stress history. Pore pressure is hydrostatic only where there is no vertical flow — artesian or
under-drained conditions must come from piezometers, not from a water-table depth [2, §11.8.2].

**Definitions** (unsaturated phases ignored below the water table):

| Quantity | Expression | Source |
|---|---|---|
| Total from dry | γ = γd (1 + w) | [1] eq. 2-9 p. 2-17 [V]; [2] eq. 4.9 p. 4-7 [V] |
| Saturated (from Gs, e) | γsat = γw (Gs + e) / (1 + e) | phase relation (see sheet 03) |
| Buoyant | γ′ = γsat − γw | phase relation |
| Total vertical stress | σv0(z) = Σ γi Δzi (integral of γ over depth) | [2] eqs. 11.26–11.27 pp. 11-34–11-35 [V] |
| Hydrostatic pore pressure | u0 = γw (z − zw) for z > zw, else 0 | [2] eq. 11.28 p. 11-35 [V] |
| Effective vertical stress | σ′v0 = σv0 − u0 | [2] eq. 11.29 p. 11-36 [V] |

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| γ, γsat, γd, γ′ | kN/m³ | pcf (lbf/ft³) | 1 kN/m³ = 6.3659 pcf; 1 pcf = 0.15709 kN/m³ |
| ρ (AGS LDEN/IDEN/TRET) | Mg/m³ (= g/cm³) | lbm/ft³ | γ [kN/m³] = ρ [Mg/m³] × 9.80665; 1 Mg/m³ = 62.428 lbm/ft³ |
| ρ (AGS RDEN) | kg/m³ | lbm/ft³ | γ [kN/m³] = ρ [kg/m³] × 9.80665 / 1000 |
| σv0, u0, σ′v0 | kPa | psf / psi / ksf | 1 kPa = 20.885 psf = 0.1450 psi = 0.02089 ksf |
| Stress gradient | kPa/m | psf/ft, psi/ft | 1 kPa/m = 6.366 psf/ft; γw = 9.81 kN/m³ ≈ 0.434 psi/ft |
| γw | 9.81 kN/m³ (fresh, 4 °C: 9.806; 20 °C: 9.789; seawater 1025 kg/m³: 10.05) | 62.4 pcf | 62.4 pcf = 9.802 kN/m³ |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Soils, loosest to densest state (organic clay to well-graded gravel–sand–silt–clay) | γd 4.7–23.2; γsat 12.8–24.5 kN/m³ (30–148 / 81–156 pcf); ranges by soil type in [1] Table 2-8 | [1] Table 2-8 p. 2-18 (after Hough 1969) [V] |
| Intact rock (all types, 56 site groups) | site means 18.0–28.1 kN/m³ (95 % CI), mean 24.6 kN/m³ (157 pcf) | [3] Table 1.4 p. 12 [V] |
| Limestone (one large data set, n = 778) | 22–28.2 kN/m³, mean 26.2 | [3] Appendix p. 77 (Sabatakakis et al. 2008) [V] |

The Table 2-8 ranges (by soil type) span loosest to densest states; natural in situ values sit in the middle-upper part.
_[Judgment — for review]_

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Lab density of soil specimen (linear / immersion) | D7263 | ISO 17892-2; BS 1377-2 | LDEN: LDEN_BDEN, LDEN_DDEN (Mg/m³), LDEN_MC (%), LDEN_TYPE, LDEN_COND | ρ, ρd, w |
| Specimen initial state in strength / consolidation tests | (D4767, D7181, D2435, D3080) | ISO 17892-5, -7, -8, -9, -10 | TRET_BDEN, TRET_DDEN, TRET_IMC; TRIT_BDEN, TRIT_DDEN, TRIT_IMC; CONG_BDEN, CONG_DDEN, CONG_MCI; SHBT_BDEN, SHBT_DDEN, SHBT_MCI | ρ, ρd, w (check values) |
| Field density (shallow) | D1556 (sand cone), D2937 (drive cylinder), D6938 (nuclear) | BS 1377-9 | IDEN: IDEN_IDEN (Mg/m³), IDEN_MC, IDEN_TYPE | in-place ρ, w |
| Rock density and porosity | – (not checked; cut from the site page) | ISRM SM (1979) [4] [V] | RDEN: RDEN_BDEN, RDEN_DDEN, RDEN_PDEN (kg/m³), RDEN_PORO, RDEN_MC, RDEN_SMC (%) | ρ, ρd, n, w |
| CPT / CPTu (correlated γ, σv0) | D5778 | ISO 22476-1 | SCPT_BDEN (Mg/m³, measured or assumed), SCPT_CPO, SCPT_CPOD (kPa), SCPT_ISPP (MPa); CPTP_DUW1, CPTP_SUW1 (kN/m³) | γ estimate, σv0, σ′v0, u0 |
| Flat dilatometer (correlated γ) | D6635 | ISO 22476-11 | DMTP_BUW (kN/m³), DMTP_TVS, DMTP_EVS, DMTP_U0 (kPa); DMTG_WAT | γ estimate, σv0, u0 |
| Groundwater level / head | – | ISO 18674-4 (piezometers) [V] | MOND: MOND_TYPE = WDEP / WHD / PRES, MOND_RDNG; WSTG_DPTH; LOCA_GL | zw, measured u |
| Stratigraphy | – | – | GEOL_TOP, GEOL_BASE, GEOL_GEOL | layer thicknesses Δzi |

## 5. Derivations and correlations

### 5.1 Bulk unit weight from dry density and water content (check)
$$\gamma = \rho_d\,(1 + w)\,g$$
- **Inputs:** ρd (Mg/m³), w (decimal), g = 9.80665 m/s².
- **Valid for:** any specimen with ρd and w measured on the same specimen.
- **Scatter:** identity; error only from measurement.
- **Source:** [1] eq. 2-9 p. 2-17 [V]; [2] eqs. 4.8–4.9 p. 4-7 [V].

### 5.2 Vertical stress profile (layered, hydrostatic)
$$\sigma_{v0}=\sum_i \gamma_i\,\Delta z_i,\qquad u_0=\gamma_w\,\max(0,\,z-z_w),\qquad \sigma'_{v0}=\sigma_{v0}-u_0$$
- **Inputs:** γi (kN/m³), Δzi (m), zw (m), γw (kN/m³).
- **Valid for:** level ground, no vertical seepage; bulk γ taken as γsat below the water table.
- **Source:** [2] eqs. 11.26–11.29 pp. 11-34–11-36 [V].

### 5.3 γ from CPTu — Robertson & Cabal (2010)
$$\gamma/\gamma_w = \left[0.27\log R_f + 0.36\log(q_t/p_a) + 1.236\right]\,G_s/2.65$$
- **Inputs:** Rf = 100 fs/qt (%), qt and pa in the same units, Gs.
- **Valid for:** uncemented mineral soils; the Gs/2.65 term adjusts for non-silica soils.
- **Scatter:** not stated in the guide; treat as a check only.
- **Source:** [5] p. 39, Fig. 28 [V].

### 5.4 γ from DMT — Marchetti & Crapps chart
Chart of γ/γw from material index ID and dilatometer modulus ED.
- **Source:** [1] Fig. 2-12 p. 2-16 (after Schmertmann) [V]; note on the figure: if PI > 50, γ/γw is overestimated by about 0.1.

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE (MC / HS / HB) initial stress | σv0 from γ; σh0 = K0 σ′v0 + u0 | Moderate: linear in γ, but γ COV is small. u0 (water level) matters more. |
| HS / stress-dependent stiffness | E = Eref (σ′/pref)^m | Low–moderate: through σ′v0 (∝ γ′, not γ, below the water table) |
| Face support pressure (EPB / slurry) | target ≈ K σ′v0 + u0 at the face | Moderate for γ; high for u0 |
| Lining loads (overburden or Terzaghi arching) | load ∝ γ × cover (or arching height) | Moderate, linear |
| Uplift / flotation of the tunnel or shaft base | buoyancy (γw) vs weight of cover (γ) | High where cover is small |
| Settlement / volume loss | indirect, through stiffness and the stability ratio N = (σv0 − σT)/Su | Low–moderate |
| Groundwater inflow | through u0 (head), not γ | High for u0; none for γ |

**Typical variability:** COV of γ for soil within a unit about 1–5 % (Zhang et al. 2010, silty clay / clay /
silty sand, via [3] Table 3.3 p. 121 [V]); one clay site 3.3 % ([3] Appendix p. 31 [V]); intact rock site
COV mean 5.2 % (range 0.4–21.5 %) [3] Table 1.4 p. 12 [V].
Correlated γ (CPT, DMT) has a larger, unquantified transformation error; use as a check, not pooled.
_[Judgment — for review]_

## 7. Pitfalls and QA checks
- AGS LDEN gives **density** (LDEN_BDEN, Mg/m³), not unit weight; a kN/m³ unit-weight heading (e.g. LDEN_UWT) is a project DICT addition, not AGS 4.2 standard — check its unit.
- RDEN_BDEN is in **kg/m³** while LDEN/TRET/CONG densities are in **Mg/m³**: a factor-of-1000 trap.
- Densities from disturbed or thick-walled samples of granular soil are approximate [2] p. 4-7 [V]; flag them.
- Rock γ from small intact specimens excludes joints/voids; rock-mass γ can be lower in weathered or karstic rock.
- Check γ against γd(1 + w) and against γsat from Gs, e: S = w Gs / e should be ≈ 1 below the water table.
- Integrate σv0 continuously across layer boundaries (no jumps) [2] p. 11-35 [V]; use γ above zw, γsat below.
- Hydrostatic u0 is an assumption: artesian or under-drained heads change σ′v0 at depth; use piezometers [2] §11.8.2 [V].
- Whole-number lab values (e.g. reported to 1 kN/m³) create ties in percentiles; report the resolution.
- Use g = 9.80665 m/s² (or 9.81) consistently between ρ → γ and γw.

## References
[1] Kulhawy, F.H. and Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800, Electric Power Research Institute, Palo Alto. https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] eq. 2-9 p. 2-17, Table 2-8 p. 2-18, Fig. 2-12 p. 2-16.
[2] Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). Geotechnical Site Characterization. Geotechnical Engineering Circular No. 5, FHWA NHI-16-072, Federal Highway Administration. https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf — [V] eqs. 4.8–4.9 p. 4-7; §11.8.1–11.8.3 eqs. 11.26–11.29 pp. 11-34–11-36; authors from the title page.
[3] Ching, J. and Schweckendiek, T. (eds.) (2021). State-of-the-art review of inherent variability and uncertainty in geotechnical properties and models. ISSMGE TC304. https://doi.org/10.53243/R0001 — [V] Table 1.4 p. 12; Table 3.3 p. 121; Appendix pp. 31, 77.
[4] ISRM (1979). Suggested methods for determining water content, porosity, density, absorption and related properties and swelling and slake-durability index properties. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 16(2), 141–156 — [V] citation from the TRID record (https://trid.trb.org/View/146312).
[5] Robertson, P.K. and Cabal, K.L. (2022). Guide to Cone Penetration Testing for Geotechnical Engineering, 7th ed. Gregg Drilling LLC. https://insitutek.com/wp-content/uploads/2024/08/CPT-Guide-to-Cone-Penetration-Testing-7th-Edition-Robertson-Cabal.pdf — [V] γ/γw equation p. 39; the 2010 symposium paper it cites is not cited on the site page.
