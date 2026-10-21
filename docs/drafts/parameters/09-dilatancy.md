# 09 — Dilatancy

| | |
|---|---|
| **Parameters** | ψ (dilatancy / dilation angle), soil and rock mass; I_R (Bolton relative dilatancy index) |
| **Material** | Both |
| **Constitutive models that use it** | MC (non-associated flow), HS / HS-small (with dilatancy cut-off), HB (plastic potential), strain-softening MC/HB |
| **Depends on** | [03 Specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (e, Dr), [04 Drained shear strength](04-drained-shear-strength-soil.md) (φ′, φ′cv), [16 GSI and disturbance](16-gsi-and-disturbance.md), [17 Rock mass strength](17-rock-mass-strength.md) (equivalent φ′), [13 Intact rock strength](13-intact-rock-strength.md) (σci) |
| **Feeds** | Tunnel FE inputs; [11 Hardening Soil stiffness](11-hardening-soil-stiffness.md) (HS set); [19 Post-peak rock mass](19-post-peak-rock-mass.md) |

## 1. Phenomenon
Dilatancy is the plastic volume increase that accompanies shearing of dense or interlocked material: particles or
rock blocks must ride over one another. ψ is the angle of the plastic strain-increment vector (sin ψ = −ε̇p_v /
γ̇p_max in a Mohr-Coulomb sense) and is less than φ′ (ψ = φ′ would be associated flow, which over-predicts volume
increase). In soils it rises with relative density and falls with mean effective stress, reaching zero at the
critical state; loose sands and NC clays are contractant (ψ ≤ 0). In rock masses ψ is highest for good-quality
interlocked rock at low confinement, falls with confinement and with accumulated plastic strain, and is near zero
for very poor rock. ψ is not a constant in reality; constant-ψ models are a simplification.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| ψ | degrees (°) | degrees (°) | 1 rad = 57.2958° |
| I_R, −dεv/dε1 | – | – | dimensionless |
| p′ in Bolton I_R | kPa (inside ln) | — (convert psf → kPa first: 1 psf = 0.047880 kPa) | equation is unit-specific |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Sand φ′ > 30° (rule of thumb) | ψ ≈ φ′ − 30° (0–15°) | [1] [V] |
| Clays (NC or OC) | ψ ≈ 0 | [1] [V] |
| Loose sand | ψ ≤ 0 (negative only for loose sands) | [1] [V] |
| Sand, Dr 0.5 / 0.8 at p′ = 100 kPa, plane strain (Bolton) | ψmax ≈ 11° / 21° (computed, 5.2) | [2] [V] via [3] |
| Very good quality hard rock mass (GSI 75, φ′ 46°) | ψ = φ′/4 = 11.5° | [4] p. 12 [V] |
| Average rock mass (GSI 50, φ′ 33°) | ψ = φ′/8 = 4° | [4] p. 12 [V] |
| Very poor rock mass (GSI 30) | ψ = 0 | [4] p. 13 [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| CD triaxial with volume change | D7181 | ISO 17892-9; BS 1377-8 | TREG: TREG_TYPE (CD, CIDC…); TRET: TRET_STV (volumetric strain at failure), TRET_STRN, TRET_DEVF | dεv/dε1 at peak → ψ (5.1); needs full curves, not only failure values |
| Direct shear with vertical displacement | D3080/D3080M | ISO 17892-10; BS 1377-7 | SHBT: SHBT_PDIN (vertical displ. at peak), SHBT_PDIS (horizontal displ. at peak), SHBT_NORM | tan ψ ≈ −δy/δx at peak |
| Pressuremeter (sands) | D4719 | ISO 22476-4 / -6 | PMTP: PMTP_AD (angle of dilation), PMTP_AF, PMTP_AFCV, PMTP_AFDM | ψ from expansion curve |
| Rock triaxial with volumetric strain | D7012 | ISRM SM (triaxial compression) | no rock-triaxial group in AGS 4.2 (user-defined) | post-peak εv–ε1 → ψ(γp) |

ASTM designations without year — confirm the current edition before citing.

## 5. Derivations and correlations

### 5.1 From test curves (definition)
$$\text{Triaxial: } \sin\psi = \frac{-\dot\varepsilon_v/\dot\varepsilon_1}{2-\dot\varepsilon_v/\dot\varepsilon_1}\ \ (\text{compression positive}),\qquad \text{Direct shear: } \tan\psi \approx -\frac{\delta y}{\delta x}$$
- **Inputs:** plastic (or total, near peak) strain increments; dilation makes ε̇v negative.
- **Source:** Vermeer & de Borst (1984) [5] [U]; reproduced as ψ = arcsin[ε̇p_v/(−2ε̇p_1 + ε̇p_v)] in [6] Eq. 15,
  p. 484 [V] (equivalent to the form above). Use plastic strains (subtract elastic parts, [6] p. 485).

### 5.2 Sands — Bolton (1986) relative dilatancy index
$$I_R = D_r\,(Q - \ln p') - R,\quad Q=10,\ R=1\ (\text{quartz/feldspar; } p'\ \text{in kPa}),\quad 0\le I_R\le 4$$
$$\varphi'_{max}-\varphi'_{cv} = 0.8\,\psi_{max} = 5 I_R\ (\text{plane strain});\qquad \varphi'_{max}-\varphi'_{cv} = 3 I_R\ (\text{triaxial});\qquad (-d\varepsilon_v/d\varepsilon_1)_{max}=0.3 I_R$$
- **Inputs:** Dr (from e, emax, emin, or from N1,60 — see [04](04-drained-shear-strength-soil.md)), p′ at failure
  (≈ 2 σ′v0 for preliminary use, [7] p. 4-10).
- **Valid for:** clean sands (17 sands in the database); Q lower for crushable grains (8 limestone, 5.5 chalk).
- **Source:** [2]; [7] Eqs. 4-5 to 4-7, p. 4-10 [V]; ranges and 0.3 I_R via [3] [V].

### 5.3 Sands / clays — practice rule
$$\psi = \max(0,\ \varphi' - 30^\circ)\ \ \text{(sands, gravels)};\qquad \psi = 0\ \ \text{(clays, fill)}$$
- **Source:** [1] [V]; same rule in the PLAXIS Material Models Manual [8] [U]. Use φ′ in degrees; peak φ′, so ψ is
  a peak value.

### 5.4 Rock mass — Hoek & Brown (1997) by quality
$$\psi = \varphi'/4\ (\text{very good, e.g. GSI}\approx 75);\quad \varphi'/8\ (\text{average, GSI}\approx 50);\quad 0\ (\text{very poor, GSI}\approx 30)$$
- **Inputs:** equivalent MC φ′ of the rock mass ([17](17-rock-mass-strength.md)); GSI band.
- **Valid for:** "starting point" values for numerical analysis, not a general rule; very good rock is brittle
  (post-peak φ′ ≈ 38°, c′ = 0), very poor rock perfectly plastic.
- **Source:** [4] pp. 12–13 (typical-property lists, Fig. 9) [V]; Alejano & Alonso call it "a calculated guess
  … on the basis of expert opinion" [6] p. 489 [V].

### 5.5 Rock mass — Alejano & Alonso (2005) peak and decay
$$\psi_{peak} = \frac{\varphi}{1+\log_{10}\sigma_{ci}}\,\log_{10}\!\frac{\sigma_{ci}}{\sigma_3+0.1}\quad(\sigma\ \text{in MPa})$$
$$K_\psi = 1 + (K_{\psi,peak}-1)\,e^{-\gamma^p/\gamma^{p*}},\quad K_\psi = \frac{1+\sin\psi}{1-\sin\psi}$$
- **Inputs:** peak φ (slope of HB envelope at σ3), σci, σ3; γp* a rock-specific plasticity constant.
- **Valid for:** confinement- and plasticity-dependent ψ in strain-softening models; gives ψpeak = φ at σ3 = 0.
- **Source:** [6] Eq. 28 (p. 493), Eq. 29 (p. 494) [V]. Note corrigendum IJRMMS 43 (2006) 836 [U content].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel convergence / ground reaction curve in weak rock (MC/HB, strain-softening) | plastic volumetric strain in the plastic zone | **High** — radial displacement at the wall grows strongly with ψ when the plastic zone is large ([6]) |
| Tunnel FE in drained sand (MC/HS) | volume change near face and crown; stress arching | Moderate — affects settlement trough and arching; ψ > 0 reduces settlement |
| Undrained effective-stress FE | ψ > 0 drives negative Δu and unlimited strength gain | **High (pitfall)** — use ψ = 0 or a dilatancy cut-off |
| Face stability (limit analysis) | upper-bound solutions assume associated flow (ψ = φ′); non-associated reduces capacity | Moderate |
| Lining loads | via convergence and loosening | Moderate |
| Groundwater inflow | none | Low |

**Typical variability:** no COV is commonly published for ψ; it is derived from φ′ (COV ≈ 2–13 %, see
[04](04-drained-shear-strength-soil.md)), so ψ = φ′ − 30° carries the full absolute uncertainty of φ′ (±2–4°
on a value of 0–10°) _[Judgment — for review]_. Rock-mass ψ by GSI band (5.4) is order-of-magnitude.

## 7. Pitfalls and QA checks
- ψ must not exceed φ′; ψ > φ′ − φ′cv is suspect for sands.
- Use peak ψ with peak φ′; with φ′cv use ψ = 0.
- Constant ψ gives unlimited dilation — use a dilatancy cut-off (e.g. emax in HS) or the decay of 5.5.
- Undrained analyses in effective stress with ψ > 0 overstate strength.
- Bolton: p′ must be in kPa; cap I_R at 4; p′ < 150 kPa inflates I_R ([3]).
- Reading ψ from lab curves needs the full εv–ε1 record (not only TRET_STV at failure).
- Rock: check which φ′ (peak equivalent MC over which σ3 range) is used in φ′/4 or φ′/8.

## References
[1] Fine spol. s r.o. GEO5 Online Help — Angle of dilation. https://www.finesoftware.eu/help/geo5/en/angle-of-dilation-01/
— [V] ψ = φ − 30° for φ > 30° (non-cohesive), clays ψ ≈ 0, negative only for loose sands (secondary source).
[2] Bolton, M.D. (1986). The strength and dilatancy of sands. Géotechnique 36(1), 65–78.
https://doi.org/10.1680/geot.1986.36.1.65 — [V] via [7] p. 4-10 and [3].
[3] groundhog documentation, cohesionless soils (Bolton 1986 functions).
https://groundhog.readthedocs.io/en/dev/site_investigation/cohesionless.html — [V] equations, 0 < I_R < 4, 0.3 I_R.
[4] Hoek, E. & Brown, E.T. (1997). Practical estimates of rock mass strength. Int. J. Rock Mech. Min. Sci. 34(8),
1165–1186. https://doi.org/10.1016/S1365-1609(97)80069-X (DOI [U]) — [V] preprint at
https://www.rocscience.com/assets/resources/learning/hoek/Practical-Estimates-of-Rock-Mass-Strength-1997.pdf,
pp. 12–13 (preprint pagination; journal page numbers not checked).
[5] Vermeer, P.A. & de Borst, R. (1984). Non-associated plasticity for soils, concrete and rock. Heron 29(3), 1–64. — [U]
[6] Alejano, L.R. & Alonso, E. (2005). Considerations of the dilatancy angle in rocks and rock masses. Int. J.
Rock Mech. Min. Sci. 42(4), 481–507. https://doi.org/10.1016/j.ijrmms.2005.01.003 — [V] Eqs. 15, 28, 29; p. 489.
[7] Kulhawy, F.H. & Mayne, P.W. (1990). Manual on Estimating Soil Properties for Foundation Design. EPRI EL-6800.
https://restservice.epri.com/publicdownload/EL-6800/0/Product — [V] Eqs. 4-5–4-7, p. 4-10.
[8] Bentley Systems. PLAXIS 2D/3D Material Models Manual (Mohr-Coulomb and Hardening Soil chapters). — [U]
