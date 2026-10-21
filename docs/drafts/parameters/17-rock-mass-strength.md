# 17 — Rock mass strength

| | |
|---|---|
| **Parameters** | mb, s, a (HB rock mass constants); σc (uniaxial strength of the rock mass, = σci s^a); σ′cm (global rock mass strength); σt,mass (rock mass tensile strength); equivalent Mohr-Coulomb c′, φ′ |
| **Material** | Rock |
| **Constitutive models that use it** | Generalized Hoek-Brown (HB2002); Mohr-Coulomb (equivalent c′, φ′); strain-softening HB/MC (with sheet 19) |
| **Depends on** | [13-intact-rock-strength](13-intact-rock-strength.md) (σci), [15-hoek-brown-mi](15-hoek-brown-mi.md) (mi), [16-gsi-and-disturbance](16-gsi-and-disturbance.md) (GSI, D), [01-unit-weight-and-vertical-stress](01-unit-weight-and-vertical-stress.md) (γ, H), [20-in-situ-stress-rock](20-in-situ-stress-rock.md) (σh for σ3max) |
| **Feeds** | [19-post-peak-rock-mass](19-post-peak-rock-mass.md), [09-dilatancy](09-dilatancy.md) (ψ from φ′) |

## 1. Phenomenon
The peak strength of a jointed rock mass is far below that of intact rock. Blocks slide and rotate on joints, and
the failure envelope is strongly curved: friction is high at low confinement and falls as σ3 rises [1][2]. The
generalized Hoek-Brown criterion scales the intact envelope (σci, mi) by GSI and D through mb, s and a. Two
"strengths" are used. σc = σci s^a is the strength at which failure *initiates* at a free boundary. σ′cm is a
*global* strength, from a Mohr-Coulomb fit over σt < σ3 < σci/4 [1]. Because the envelope is curved, equivalent
c′ and φ′ depend on the stress range fitted (σ3max). There is no single MC pair for a rock mass [1][3].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| σc, σ′cm, σt,mass, c′, σ3max | MPa | psi / ksi | 1 MPa = 145.04 psi = 0.14504 ksi |
| mb, s, a | – | – | – |
| φ′ | ° | ° | – |
| γH (for σ3max) | MPa (γ in kN/m³ × H in m / 1000) | psi | γ: 1 kN/m³ = 6.366 pcf |

## 3. Typical values
Ratios computed with HB2002 eqs. (mi = 10, D = 0). They are illustrative, not design values.

| GSI | mb/mi | s | a | σc/σci | σ′cm/σci | σt,mass/σci | Source |
|---|---|---|---|---|---|---|---|
| 30 | 0.082 | 4.2e-4 | 0.522 | 0.017 | 0.110 | −5.1e-4 | computed, [1] eqs. 3–7, 17 |
| 50 | 0.168 | 3.9e-3 | 0.506 | 0.060 | 0.174 | −2.3e-3 | computed |
| 70 | 0.343 | 3.6e-2 | 0.501 | 0.188 | 0.281 | −1.0e-2 | computed |

| Published worked example | Value | Source |
|---|---|---|
| σci 50 MPa, mi 10, GSI 45, tunnel H = 100 m, D = 0 | φ′ = 47.16°, c′ = 0.58 MPa | [1] §7 [V] |
| Same, slope H = 100 m, D = 1 | φ′ = 27.61°, c′ = 0.35 MPa | [1] §7 [V] |

The example is reproduced (47.16°, 0.583 MPa; 27.61°, 0.348 MPa) with
γ = 27 kN/m³. [1] does not state γ, so 27 kN/m³ is inferred (with 26 kN/m³ the result is 47.43°). It makes a good
unit-test case.

## 4. Tests
Rock mass strength is not measured directly in routine practice. It is built from intact tests plus GSI.

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| UCS of intact core (σci) | D7012-23 (Method C/D) [U: edition] | ISRM SM UCS (1979/2007) [U] | RUCS: RUCS_UCS | σci (sheet 13) |
| Triaxial on intact core (mi) | D7012 (Methods A/B) [U: edition] | ISRM SM triaxial (1978) [U] | **No rock triaxial group in AGS 4.2** (checked: only soil TRIG/TREG). Projects use user-defined groups | σ1–σ3 pairs → mi (sheet 15) |
| In situ block shear (rock mass/joints) | D4554 [U: edition] | ISRM SM in situ shear (1974) [U] | SHBG: SHBG_PCOH, SHBG_PHI (lab shear box; no in situ group) | c, φ at field scale (rare) |
| Back-analysis of convergence / failures | – | – | – | Calibrated GSI, D, σci [3] §9 |

## 5. Derivations and correlations

### 5.1 Generalized Hoek-Brown criterion — Hoek, Carranza-Torres & Corkum (2002)
$$\sigma'_1=\sigma'_3+\sigma_{ci}\left(m_b\frac{\sigma'_3}{\sigma_{ci}}+s\right)^a$$
$$m_b=m_i\exp\!\frac{\mathrm{GSI}-100}{28-14D},\quad s=\exp\!\frac{\mathrm{GSI}-100}{9-3D},\quad a=\tfrac12+\tfrac16\left(e^{-\mathrm{GSI}/15}-e^{-20/3}\right)$$
- **Inputs:** σci (MPa), mi, GSI, D.
- **Valid for:** isotropic, closely jointed masses (sheet 16). The 1997 "switch" at GSI = 25 is removed [1].
- **Source:** [1] eqs. 2–5 [V]. The same equations are [2] eqs. 11–13 [V] and [3] eqs. 3–6 [V].

### 5.2 Uniaxial and tensile strength of the rock mass
$$\sigma_c=\sigma_{ci}\,s^a,\qquad \sigma_t=-\,s\,\sigma_{ci}/m_b$$
- σt comes from setting σ1 = σ3 = σt (biaxial tension, taken equal to uniaxial tension for brittle rock).
- **Source:** [1] eqs. 6, 7 [V]. Also [2] eqs. 14, 15 [V].

### 5.3 Global rock mass strength σ′cm
$$\sigma'_{cm}=\sigma_{ci}\,\frac{\big(m_b+4s-a(m_b-8s)\big)\,(m_b/4+s)^{a-1}}{2(1+a)(2+a)}$$
- **Valid for:** MC fit over σt < σ′3 < σci/4. Used for pillar-type "overall" strength and in the σ3max formulae.
- **Source:** [1] eqs. 16–17 [V]. Also [2] eqs. 20–21 [V].

### 5.4 Equivalent Mohr-Coulomb c′, φ′ — area-balanced fit over σt < σ3 < σ′3max
$$\sin\phi'=\frac{6am_b(s+m_b\sigma'_{3n})^{a-1}}{2(1+a)(2+a)+6am_b(s+m_b\sigma'_{3n})^{a-1}}$$
$$c'=\frac{\sigma_{ci}\big[(1+2a)s+(1-a)m_b\sigma'_{3n}\big](s+m_b\sigma'_{3n})^{a-1}}{(1+a)(2+a)\sqrt{1+\dfrac{6am_b(s+m_b\sigma'_{3n})^{a-1}}{(1+a)(2+a)}}},\qquad \sigma'_{3n}=\sigma'_{3max}/\sigma_{ci}$$
- **Source:** [1] eqs. 12–13 [V]. Also [2] eqs. 16–17 [V]. Use with a tension cut-off [3] §1 [V].

### 5.5 Choice of σ′3max
$$\text{Tunnels: } \frac{\sigma'_{3max}}{\sigma'_{cm}}=0.47\left(\frac{\sigma'_{cm}}{\gamma H}\right)^{-0.94}\qquad \text{Slopes: } \frac{\sigma'_{3max}}{\sigma'_{cm}}=0.72\left(\frac{\sigma'_{cm}}{\gamma H}\right)^{-0.91}$$
- **Inputs:** σ′cm (5.3), γ (MN/m³), H = tunnel depth or slope height (m).
- **Valid for:** tunnels: fitted so that HB and MC give equivalent ground reaction curves (deep), or the same
  failure extent and subsidence (shallow, depth < 3 diameters, no caving to surface). If σh > σv, use σh in place
  of γH. Not for block caving. Slopes: Bishop circular analyses [1] §6 [V].
- **Source:** [1] eqs. 18, 19 [V].

### 5.6 Hoek & Brown (2019) update
- Equations unchanged. Since most software now accepts HB directly, it is preferred to equivalent MC. MC
  parameters are left to [1] and should not be used without a tension cut-off [3] §1 [V].
- HB inputs (σci, mi, GSI) are independent variables for probabilistic analysis. c′ and φ′ are correlated [2]
  ("Reliability of rock mass strength estimates") [V].
- For sparsely jointed hard rock (GSI > ~65) at high stress, eqs. 5.1 may need modified constants
  (Kaiser et al. 2010; Bewick et al. 2019) [3] §5, §10 [V].

### 5.7 Reproducing a published c′, φ′ (back-solving σci, mi, σ3max)
- A reported (c′, φ′) pair has two numbers. Behind it are at least four unknowns (σci, mi, GSI, σ3max; D usually
  0). With GSI and D fixed, any one of σci, mi, σ3max can be traded against the others, so the back-solution is
  **non-unique**. Fix two of them, for example σci from lab p50 and GSI from the report, then solve for mi and
  σ3max. Report the residual and the trade-off curve. _[Judgment — for PE review]_
- Sanity check: c′ rises and φ′ falls as σ3max increases. Example (σci 50, mi 10, GSI 45): σ3max 0.5 / 1.35 / 3 /
  6 MPa gives c′ 0.37 / 0.58 / 0.93 / 1.43 MPa and φ′ 54.2 / 47.2 / 40.8 / 35.1° (computed). A reported φ′ fixes
  σ3max strongly once mi is known.
- Check whether the source used RocLab/RSData "tunnel" σ3max (eq. 18), custom σ3max, or σci/4 (eq. 17 range).

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE, HB material | mb, s, a directly. Peak (and residual, sheet 19) yield surface | **High** to GSI and σci (s, mb exponential in GSI). Moderate to mi |
| Tunnel FE, MC material | c′, φ′ from 5.4 at the chosen σ3max | **High** to σ3max choice (above). Stress-range error if σ3max is wrong |
| Convergence-confinement / plastic radius | HB closed form [7] or MC; σcm (or c′, φ′) vs p0 = γH. Squeezing indicator ≈ σcm/p0 | **High**. Strain rises sharply as σcm/p0 falls below ~0.3 (Hoek & Marinos 2000) [5] [U] |
| Face stability (shallow, MC limit analyses) | c′ dominant at low σ3 | **High** to c′. Use σ3max from shallow-tunnel guidance; avoid tension (cut-off) |
| Support / lining load | through plastic zone size and convergence | Moderate–high. Combined with Erm (sheet 18) |
| Slopes (portals, shafts) | c′, φ′ at slope σ3max (eq. 19), D per zone | High to D in the damaged zone [1] §7 |

**Typical variability:** σ′cm, c′ and φ′ inherit uncertainty from σci (see sheet 13 for lab UCS COV), mi (COV ≈ 15 % "according to Hoek", used by Cai et al. 2004 [4] [V]) and GSI (SD ≈ 2.5–5, sheet 16).
Cai et al. (2004) found predicted means and SDs of c, φ, E "generally in good agreement" with 21 in situ block
shear and 29 plate-load tests at two Japanese caverns [4][3] [V]. Hoek's probabilistic examples treat GSI, σci
and mi as independent normal variables and propagate them by Monte Carlo [2] [V]. Inherent variability and the
transformation (HB → MC) error are separate. The MC fit adds a stress-range error that is zero only at the fitted
range. _[Judgment — for PE review]_

## 7. Pitfalls and QA checks
- Report σc (= σci s^a) and σ′cm separately. σ′cm/σc ≈ 6.4, 2.9, 1.5 at GSI 30, 50, 70 (computed from the table above).
- Always state σ3max and its basis (eq. 18 with γH or σh, eq. 19, σci/4, custom). c′ and φ′ are meaningless without it.
- Use γ in MN/m³ (kN/m³ / 1000) in γH, with H in m. A unit slip gives σ3max off by 1000.
- Apply a tension cut-off with MC parameters (σt,mass from 5.2, or 0) [3].
- D only in the damaged ring (sheet 16). D = 0 for TBM.
- Check that HB is applicable (isotropic, closely jointed). Bedding-controlled shale needs anisotropic or
  ubiquitous-joint treatment (sheet 22).
- Units test: the HB2002 worked example (5.1–5.5) should reproduce 47.16°, 0.58 MPa.
- Do not average c′ and φ′ separately across samples. Average the inputs and recompute (c′, φ′ are correlated).

## References
[1] Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, Toronto, 1, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eqs. 2–7, 12–13, 16–19, §6 text, §7 worked example, Table 1
[2] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties". https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V] eqs. 11–21, reliability section
[3] Hoek, E., Brown, E.T. (2019). The Hoek-Brown failure criterion and GSI – 2018 edition. J. Rock Mech. Geotech. Eng. 11(3), 445–463. https://doi.org/10.1016/j.jrmge.2018.08.001 — [V] §1 (HB preferred; tension cut-off), eqs. 3–6, §5, §9, §10
[4] Cai, M., Kaiser, P.K., Uno, H., Tasaka, Y., Minami, M. (2004). Estimation of rock mass deformation modulus and strength of jointed hard rock masses using the GSI system. Int. J. Rock Mech. Min. Sci. 41(1), 3–19. — [V] mi COV 15 %, Table 6 comparison text
[5] Hoek, E., Marinos, P. (2000). Predicting tunnel squeezing. Tunnels and Tunnelling International, Nov/Dec 2000. — [U]
[6] Hoek, E., Brown, E.T. (1997). Practical estimates of rock mass strength. Int. J. Rock Mech. Min. Sci. 34(8), 1165–1186. — [V] bibliographic data via [1] reference list
[7] Carranza-Torres, C., Fairhurst, C. (1999). General formulation of the elasto-plastic response of openings in rock using the Hoek-Brown failure criterion. Int. J. Rock Mech. Min. Sci. 36(6), 777–809. — [V] bibliographic data via [1] reference list
