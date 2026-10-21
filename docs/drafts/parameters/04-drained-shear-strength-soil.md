# 04 — Drained shear strength of soil

| | |
|---|---|
| **Parameters** | φ′ (effective friction angle: peak φ′p, critical-state φ′cv, residual φ′r), c′ (effective cohesion intercept) |
| **Material** | Soil |
| **Constitutive models that use it** | MC, HS / HS-small, Modified Cam Clay (via M = 6 sin φ′cv / (3 − sin φ′cv)) |
| **Depends on** | [01 Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (σ′v0 for SPT normalization), [02 Index properties](02-index-properties.md) (PI, fines), [03 Specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (state, Dr) |
| **Feeds** | [05 Undrained shear strength](05-undrained-shear-strength.md) (CSSM su ratio), [07 At-rest earth pressure](07-at-rest-earth-pressure.md), [09 Dilatancy](09-dilatancy.md), [11 Hardening Soil stiffness](11-hardening-soil-stiffness.md) (Rf, failure line) |

## 1. Phenomenon
Drained strength is frictional resistance on the effective-stress failure envelope τ = c′ + σ′n tan φ′. Peak φ′p
= φ′cv + a dilatancy component that grows with density (Dr) and shrinks with confining stress (Bolton 1986, see
[09](09-dilatancy.md)); φ′cv is a material constant set by mineralogy and grading; φ′r (clays with PI ≳ 25–30 %
after large displacement) reflects platy-particle alignment and can be much lower. The intercept c′ of a straight
fit is mostly an artefact of envelope curvature plus true bonding (cementation, OC structure); it is stress-range
dependent and is often taken as zero for NC/uncemented soils. Strength also depends on loading mode (triaxial
compression < plane strain; extension and direct shear differ).

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| φ′ | degrees (°) | degrees (°) | 1 rad = 57.2958° |
| c′ | kPa | psf, psi | 1 kPa = 20.8854 psf = 0.14504 psi; 1 psf = 0.047880 kPa |
| s′, t (stress-path coords.) | kPa | psf | as c′ |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Sand, very loose / loose / medium / dense / very dense (SPT N 0–4 / 4–10 / 10–30 / 30–50 / >50) | φ′tc < 28° / 28–30° / 30–36° / 36–41° / > 41° | [1] Table 4-3, after Peck, Hanson & Thornburn (1974) [V] |
| NC clay, φ′cv vs PI: PI 10 / 20 / 40 / 80 % | ≈ 36° / 31° / 27° / 23° (computed from 5.4) | [1] Fig. 4-20 [V] |
| Residual φ′r, high-plasticity clays | can fall to ≈ 5–15° | [1] Fig. 4-24 (ring shear) [U for the range] |
| c′, uncemented NC soils | ≈ 0 | _[Judgment — for PE review]_ |
| c′, stiff OC / fissured clays (peak fit) | typically 0 to a few tens of kPa; strongly fit-range dependent | _[Judgment — for PE review]_ |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| CD triaxial (drained, volume change) | D7181 | ISO 17892-9; BS 1377-8 | TREG: TREG_TYPE (CD, CIDC, CADC…), TREG_PHI, TREG_COH, TREG_FCR; TRET: TRET_CELL, TRET_DEVF, TRET_PWPF, TRET_CONP, TRET_STV, TRET_STRN, TRET_TESN | σ′1f, σ′3f per specimen → s′–t fit |
| CU triaxial with pore pressure | D4767 | ISO 17892-9; BS 1377-8 | as above (TREG_TYPE CU, CIUC, CAUC, CUM…); TRET_PWPF; TRET_MEAN | effective stresses at failure; also su (TRET_CU) |
| Direct shear (shear box) | D3080/D3080M | ISO 17892-10; BS 1377-7 | SHBG: SHBG_TYPE, SHBG_PHI, SHBG_PCOH, SHBG_RPHI, SHBG_RCOH; SHBT: SHBT_NORM, SHBT_PEAK, SHBT_RES, SHBT_PVST, SHBT_RVST | τ–σ′n pairs (peak and residual) |
| Ring shear (residual) | D6467 (drained residual); D7608 (fully softened) | BS 1377-7 | SHBG_TYPE = SMALL / LARGE RSHEAR; SHBG_RPHI, SHBT_RES | φ′r |
| SPT (correlation input) | D1586/D1586M; energy D4633; D6066 | ISO 22476-3 | ISPT: ISPT_NVAL, ISPT_ERAT, ISPT_N60 | N, N60 → 5.3–5.5 |
| CPTu / PMT (alternatives) | D5778 | ISO 22476-1 | CPTP_PHI1; PMTP_AF, PMTP_AFCV | correlated φ′ |

ASTM designations without year — confirm the current edition before citing.

## 5. Derivations and correlations

### 5.1 s′–t (MIT) envelope fit from triaxial
$$s' = \tfrac{1}{2}(\sigma'_{1f}+\sigma'_{3f}),\quad t = \tfrac{1}{2}(\sigma'_{1f}-\sigma'_{3f}),\quad t = a + s'\tan\alpha$$
$$\sin\varphi' = \tan\alpha,\qquad c' = a/\cos\varphi'$$
- **Inputs:** σ′3f = TRET_CELL − TRET_PWPF (CD: pwp = back pressure); σ′1f = σ′3f + TRET_DEVF (kPa). Least-squares
  line through all specimens of a unit. Where pore pressure at failure is not reported, Δu_f = Af·q_f is a
  derivation, not data — flag it.
- **Valid for:** saturated specimens (check TRET_BVAL), one consistent failure criterion (TREG_FCR: max q vs max
  σ′1/σ′3); report fit with and without multistage stages.
- **Scatter:** report n, R², and the stress range of the fit (c′ is only valid over that range).
- **Source:** standard p–q (s′–t) construction, e.g. Lambe & Whitman (1969) [10] [U]; identity sin φ′ = tan α
  follows from the Mohr circle geometry.

### 5.2 Direct shear envelope
$$\tau_f = c' + \sigma'_n\tan\varphi'\quad(\text{least squares on SHBT\_PEAK vs SHBT\_NORM})$$
- **Valid for:** drained (rate per D3080); gives plane-strain-like strength on a forced plane.
- **Conversion:** tan φ′ds = tan φ′ps cos φ′cv; φ′ps ≈ 1.10 φ′tc (NC cohesive soils).
- **Source:** [1] Eq. 4-10 and Table 4-5, p. 4-25 [V].

### 5.3 SPT — Wolff (1989), fit to Peck, Hanson & Thornburn (1974)
$$\varphi' = 27.1 + 0.3\,N_{1,60} - 0.00054\,N_{1,60}^2$$
- **Inputs:** N1,60 (blows/0.3 m); **Valid for:** clean sands; conservative chart basis.
- **Source:** [2] [U]; equation [V] via groundhog `frictionangle_spt_PHT` [9] (some reproductions print 0.00053).

### 5.4 SPT — Kulhawy & Mayne (1990), after Schmertmann
$$\varphi' = \tan^{-1}\left[\frac{N}{12.2 + 20.3\,(\sigma'_{v0}/p_a)}\right]^{0.34}$$
- **Inputs:** N (EPRI uses field N; GEC 5 practice uses N60), σ′v0, pa ≈ 100 kPa (2116 psf).
- **Valid for:** NC uncemented quartz sands; not for depths < 1–2 m (conservative there).
- **Source:** [1] Eq. 4-11, p. 4-14 [V locator; equation as reproduced in [9] — the EPRI scan's equation image
  is not legible].

### 5.5 SPT — Hatanaka & Uchida (1996)
$$\varphi' = \sqrt{20\,N_{1,60}} + 20\quad(\text{deg})$$
- **Valid for:** fine to medium sands, N1,60 ≈ 3.5–30; fitted to triaxial tests on frozen (undisturbed) samples.
- **Source:** [3] [U]; listed in [4] Table 2.2.1 (fine to medium sands, recommended by GEC 5) [V].

### 5.6 φ′cv of NC clays from PI
$$\sin\varphi'_{cv} \approx 0.8 - 0.094\ln PI\quad(PI\ \text{in}\ \%)$$
- **Source:** [1] Fig. 4-20, p. 4-21 (after Mitchell) [V]. Scatter large (figure band).

### 5.7 Peak from critical state + dilatancy — Bolton (1986)
$$\varphi'_p - \varphi'_{cv} = 3 I_R\ (\text{triaxial}),\ 5 I_R\ (\text{plane strain})$$
- See [09 Dilatancy](09-dilatancy.md) for I_R. **Source:** [5]; [1] Eqs. 4-5 to 4-7, p. 4-10 [V].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel face stability / support pressure (limit equilibrium, e.g. wedge-silo) | resisting shear on wedge and silo; required pressure falls steeply with tan φ′ and c′ | **High** — a few degrees or a small c′ changes required pressure by large factors in sands/silts |
| Tunnel FE (MC, HS) | yield surface; extent of plastic zone; HS failure line q_f | **High** for plastic zone and convergence; moderate for elastic-dominated cases |
| Settlement / volume loss | through plasticity around the face/tail | Moderate — stiffness usually dominates unless near failure |
| Lining loads | ground arching, loosening load (Terzaghi) | Moderate–high in soft/loose ground |
| Groundwater inflow | none directly | Low |

**Typical variability:** φ′ COV ≈ 2–13 % (Duncan 2000 [6]) [U]; ≈ 5–15 % for sands, wider for clays (Phoon &
Kulhawy 1999 [7]) [U]. c′ is far more variable (COV often > 40 %) and should be treated separately
_[Judgment — for PE review]_. SPT-based φ′ adds transformation uncertainty on top of N variability; the three SPT
correlations above differ by several degrees for the same N (5.3–5.5).

## 7. Pitfalls and QA checks
- Fit s′–t per unit, not per test; report the stress range — never extrapolate c′ to σ′ = 0 near the surface.
- Check saturation (TRET_BVAL ≥ 0.95) and drainage rate; CU without pore pressure cannot give φ′.
- Do not mix failure criteria (peak q vs max stress ratio) or peak with residual points in one fit.
- Multistage stages are affected by prior shearing; run the fit with and without them.
- Laboratory direct shear φ′ ≠ triaxial φ′; convert (5.2) before combining.
- SPT: confirm N vs N60 vs N1,60 basis for each correlation; SPT in gravel/cobbles overstates φ′.
- Printed TREG_PHI / TREG_COH or SHBG_PHI from the lab: recompute from TRET / SHBT data and compare.
- Use φ′cv (not peak) for large-strain or progressive-failure problems and for ψ = 0 analyses.

## References
[1] Kulhawy, F.H. & Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800,
Electric Power Research Institute, Palo Alto. https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V]
Table 4-3, Table 4-5, Eqs. 4-5–4-7, 4-10, 4-11 (locator), Fig. 4-20 checked in the EPRI scan.
[2] Wolff, T.F. (1989). Pile capacity prediction using parameter functions. In Predicted and Observed Axial
Behavior of Piles, ASCE GSP 23, 96–106. — [U]
[3] Hatanaka, M. & Uchida, A. (1996). Empirical correlation between penetration resistance and internal friction
angle of sandy soils. Soils and Foundations 36(4), 1–9. https://doi.org/10.3208/sandf.36.4_1 — [U] (bibliographic
data seen in citing papers only)
[4] National Academies of Sciences, Engineering, and Medicine (2024). Design of Piles for Downdrag, Ch. 2.
https://doi.org/10.17226/27863 — [V] Table 2.2.1 (Hatanaka & Uchida listed for fine–medium sands).
[5] Bolton, M.D. (1986). The strength and dilatancy of sands. Géotechnique 36(1), 65–78.
https://doi.org/10.1680/geot.1986.36.1.65 — [V] via [1] p. 4-10.
[6] Duncan, J.M. (2000). Factors of safety and reliability in geotechnical engineering. J. Geotech. Geoenviron.
Eng. 126(4), 307–316. https://doi.org/10.1061/(ASCE)1090-0241(2000)126:4(307) — [U] (COV table not seen)
[7] Phoon, K.-K. & Kulhawy, F.H. (1999). Characterization of geotechnical variability. Can. Geotech. J. 36(4),
612–624; and Evaluation of geotechnical property variability, 625–639. https://doi.org/10.1139/t99-038 — [U]
[8] Peck, R.B., Hanson, W.E. & Thornburn, T.H. (1974). Foundation Engineering, 2nd ed. Wiley. — [V] via [1] Table 4-3.
[9] groundhog (Python library) documentation, SPT correlations.
https://groundhog.readthedocs.io/en/dev/site_investigation/spt_correlations.html — [V] equations of 5.3, 5.4
(secondary reproduction).
[10] Lambe, T.W. & Whitman, R.V. (1969). Soil Mechanics. Wiley. — [U]
