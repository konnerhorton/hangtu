# 19 — Post-peak (residual) rock mass

| | |
|---|---|
| **Parameters** | GSIr (residual GSI); mr, sr, ar (residual HB constants); post-peak behavior type (elastic-brittle / strain-softening / elastic-perfectly-plastic) |
| **Material** | Rock |
| **Constitutive models that use it** | Strain-softening and elastic-brittle-plastic HB / MC (FE, FDM); convergence-confinement with softening |
| **Depends on** | [16-gsi-and-disturbance](16-gsi-and-disturbance.md) (GSI), [17-rock-mass-strength](17-rock-mass-strength.md) (peak mb, s, a; HB equations), [15-hoek-brown-mi](15-hoek-brown-mi.md), [13-intact-rock-strength](13-intact-rock-strength.md) |
| **Feeds** | [09-dilatancy](09-dilatancy.md) (post-peak ψ), tunnel FE and GRC calculations |

## 1. Phenomenon
After peak strength, a rock mass loses strength with further strain. The amount and rate depend on rock mass
quality [1][2]. Very good hard rock behaves elastic-brittle (sudden drop to a low residual). Average rock
strain-softens. Very poor, soft rock is close to elastic-perfectly-plastic (residual ≈ peak) [2]. The loss comes
from breaking interlock and asperities and from reducing block size, which Cai et al. (2007) represent as a lower,
residual GSI [3]. In massive to sparsely jointed hard rock under high stress, failure is instead stress-induced
spalling (extension fracturing). GSI does not describe that mechanism [4][5]. Residual and softening parameters
control how far the plastic zone grows and how large convergence becomes. They are rarely measured, so they are a
dominant source of model uncertainty [6].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| GSIr | – | – | – |
| mr, sr, ar | – | – | – |
| Residual σc,r, c′r | MPa | psi / ksi | 1 MPa = 145.04 psi = 0.14504 ksi |
| Softening parameter (plastic shear strain to residual, e.g. γp*) | – (strain) | – | – |

## 3. Typical values
Computed with Cai (2007) + HB2002, mi = 10, D = 0. Illustrative only.

| Peak GSI | GSIr | mr/mi | sr | ar | σc,r/σci (peak σc/σci) | Source |
|---|---|---|---|---|---|---|
| 30 | 20.1 | 0.058 | 1.4e-4 | 0.544 | 0.008 (0.017) | computed, [3][7] |
| 50 | 25.6 | 0.070 | 2.6e-4 | 0.530 | 0.013 (0.060) | computed |
| 70 | 27.4 | 0.075 | 3.1e-4 | 0.527 | 0.014 (0.188) | computed |
| GSIr maximum | 27.45 at GSI = 1/0.0134 = 74.6. GSIr falls slowly above that (26.2 at GSI 100) | computed. The 27.453 example in [8] Table 6 matches [V] |

| Rock mass quality | Suggested post-failure model | Source |
|---|---|---|
| Very good quality hard rock | elastic-brittle | [2] Fig. 10(a) [V] |
| Average quality | strain softening | [2] Fig. 10(b) [V] |
| Very poor quality soft rock | elastic-(perfectly) plastic | [2] Fig. 10(c) [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Post-peak (servo-controlled) triaxial on intact rock | D7012 (peak only; post-peak not standardized) [U] | ISRM SM complete stress–strain curve (Fairhurst & Hudson 1999) [U] | **No rock triaxial group in AGS 4.2** [checked] | Intact residual strength, brittleness (not rock mass) |
| Direct shear of joints (lab) | D5607 [U: edition] | ISRM SM (1974/2014) [U] | SHBG: SHBG_PCOH, SHBG_PHI, SHBG_RCOH, SHBG_RPHI (kPa, deg) | Residual joint φr, cr (sheet 22) |
| In situ block shear | D4554 [U: edition] | ISRM SM in situ shear [U] | none [checked] | Field-scale peak/residual c, φ. Cai et al. (2007) validation data [3] |
| Back-analysis of convergence / extensometers | – | – | – | Residual and softening parameters at project scale (preferred) |

## 5. Derivations and correlations

### 5.1 Residual GSI — Cai, Kaiser, Tasaka & Minami (2007)
$$\mathrm{GSI}_r=\mathrm{GSI}\;e^{-0.0134\,\mathrm{GSI}}$$
- **Inputs:** peak GSI.
- **Basis:** the peak GSI is moved on the GSI chart to a residual block volume and residual joint condition
  factor, and the exponential is a fit to that procedure [3] (abstract) [V].
- **Valid for:** jointed hard rock masses. Validated against in situ block shear tests at three cavern sites and a
  slope back-analysis [3] (abstract, via search summaries) [V].
- **Source:** [3] (equation number not seen; cited elsewhere as eq. 8 [U]). The equation was seen in [8]
  (Sci. Rep. 2022, citing [3]) [V via [8]].

### 5.2 Residual HB constants from GSIr
$$m_r=m_i\exp\frac{\mathrm{GSI}_r-100}{28-14D},\quad s_r=\exp\frac{\mathrm{GSI}_r-100}{9-3D},\quad a_r=\tfrac12+\tfrac16\left(e^{-\mathrm{GSI}_r/15}-e^{-20/3}\right)$$
- **Inputs:** mi (unchanged), GSIr, D.
- **Source:** HB2002 eqs. 3–5 [7] [V] applied with GSIr, as in [8] eq. 10 (D = 0) [V]. Whether [3] keeps mi
  unchanged and how it sets D for residual is [U]. [8] used its own fitted mi(GSI) instead, so check before reuse.
- Residual c′r, φ′r follow from sheet 17 eqs. 5.4–5.5 with mr, sr, ar. The same σ3max should be used for
  consistency. _[Judgment — for PE review]_

### 5.3 Post-peak behavior by rock-mass quality — Hoek & Brown (1997); Hoek (2007)
- Elastic-brittle (very good hard rock): drop to residual with ψ high. Strain-softening (average). Perfectly
  plastic (very poor, ψ = 0) [2] Fig. 10 [V], after [1] [U: figure number in [1]].
- Hoek gives these as a "starting point" only: "no definite rules" exist [2] [V].

### 5.4 Strain-softening and ground reaction — Alonso et al. (2003); Alejano et al. (2009)
- The ground reaction curve of a softening mass lies between the elastic-perfectly-plastic curves for peak and for
  residual parameters. Its position depends on the softening parameter (plastic strain to reach residual) and on
  dilatancy [9][10] [U: specific figures].
- Alejano et al. (2009) compute GRCs for the three post-failure types by rock quality [10] [V: citation via [8]
  reference list]. Crowder & Bawden (2004) review post-peak parameters and their use in numerical models [11] [U].

### 5.5 Brittle failure / spalling (massive to moderately jointed hard rock) — Martin et al. (1999); Diederichs (2007)
$$\frac{R_f}{a}=0.49(\pm0.1)+1.25\,\frac{\sigma_{max}}{\sigma_{ci}},\qquad \text{onset at }\sigma_{max}/\sigma_{ci}\gtrsim0.4,\quad \text{brittle HB: } m_b=0,\ s=0.11$$
- **Inputs:** σmax = 3σ1 − σ3 (maximum elastic tangential boundary stress of a circular opening, with σ1, σ3 the
  far-field principal stresses in the plane of the section), σci, opening radius a; Rf = radius of failure.
- **Valid for:** massive to moderately fractured hard rock. It replaces GSI-based residual parameters in that regime.
  Diederichs (2007) gives a damage-initiation / spalling-limit composite envelope for numerical models [5].
- **Source:** [12] [V via UBC EOSC 547 notes [13]: threshold, m = 0, s = 0.11, and the coefficients 0.49 / 0.1 /
  1.25, layout garbled]. [5] [V via [13], method outline].

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Tunnel FE, strain-softening HB | residual yield surface (mr, sr, ar) and softening rate | **High** for plastic zone extent and convergence in average-to-poor rock. Low where the mass stays elastic |
| Convergence-confinement (GRC) | residual strength sets the far part of the GRC. Brittle → largest plastic radius | **High**. Residual results can be several times the peak-only convergence [9][10] [U: magnitude] |
| Support / lining loads | via convergence before support and the loosening zone | Moderate–high. Late or soft support carries load from the broken zone |
| Face stability | residual strength in the failing wedge or chimney | Moderate |
| Spalling depth (hard rock) | brittle m = 0, s = 0.11 envelope | High to σmax/σci near 0.4 |
| GSIr vs peak GSI | dGSIr/dGSI = e^(−0.0134GSI)(1 − 0.0134GSI) | Low: 0.40 at GSI 30, 0.17 at 50, 0.02 at 70 (computed). GSI uncertainty barely moves GSIr at GSI > 60 |

**Typical variability:** no published COV for GSIr or mr, sr was found. From 5.1, a GSI SD of 2.5–5 (sheet 16)
gives a GSIr SD of ≈ 1–2 at GSI 30 and < 0.5 at GSI ≥ 60 (computed from the derivative above). The real
uncertainty is in the **method**: the choice of residual model, softening parameter and post-peak dilatancy. That
is transformation and model uncertainty, not inherent variability. Bracket it with alternative models (EPP-peak,
EPP-residual, softening) rather than a COV. _[Judgment — for PE review]_

## 7. Pitfalls and QA checks
- GSIr from Cai (2007) caps at ≈ 27.5. High-GSI masses (GSI 70–90) all get similar residuals. Check whether that
  is credible for the rock type, or whether the behavior is brittle (5.5) instead.
- Do not use GSI-based residuals for spalling-prone massive hard rock. Use the brittle (m = 0, s = 0.11 or DISL)
  approach [4][12].
- Residual mi: state whether mi is kept or reduced. Keep D for residual consistent with peak (D = 0 for TBM).
- Elastic-brittle with very low residual makes numerical models mesh-dependent and unstable. Check mesh
  sensitivity and the softening length. _[Judgment — for PE review]_
- Use consistent σ3max for peak and residual MC conversion.
- Calibrate against convergence monitoring where available. Residual parameters are best back-analyzed.

## References
[1] Hoek, E., Brown, E.T. (1997). Practical estimates of rock mass strength. Int. J. Rock Mech. Min. Sci. 34(8), 1165–1186. — [V] bibliographic data via HB2002 reference list; [U] figure locator
[2] Hoek, E. (2007). Practical Rock Engineering, ch. 11 "Rock mass properties", "Post-failure behaviour", Fig. 10. https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf — [V]
[3] Cai, M., Kaiser, P.K., Tasaka, Y., Minami, M. (2007). Determination of residual strength parameters of jointed rock masses using the GSI system. Int. J. Rock Mech. Min. Sci. 44(2), 247–265. https://doi.org/10.1016/j.ijrmms.2006.07.005 — [U] primary text not accessed; abstract content via search
[4] Hoek, E., Brown, E.T. (2019). The Hoek-Brown failure criterion and GSI – 2018 edition. J. Rock Mech. Geotech. Eng. 11(3), 445–463. https://doi.org/10.1016/j.jrmge.2018.08.001 — [V] Fig. 8 caption (GSI not applicable to spalling), §5
[5] Diederichs, M.S. (2007). The 2003 Canadian Geotechnical Colloquium: mechanistic interpretation and practical application of damage and spalling prediction criteria for deep tunnelling. Can. Geotech. J. 44(9), 1082–1116. — [U] (method outline via [13])
[6] Hoek, E., Diederichs, M.S. (2006). Empirical estimation of rock mass modulus. Int. J. Rock Mech. Min. Sci. 43, 203–215. — [V] §7 (D varied with strain in failure zone; parametric studies advised)
[7] Hoek, E., Carranza-Torres, C., Corkum, B. (2002). Hoek-Brown failure criterion – 2002 edition. Proc. NARMS-TAC, 267–273. https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf — [V] eqs. 3–5
[8] (2022). Evaluation of input geological parameters and tunnel strain for strain-softening rock mass based on GSI. Scientific Reports 12. https://doi.org/10.1038/s41598-022-23587-x (PMC9708675) — [V] GSIr equation attributed to [3], residual eq. 10, Table 6
[9] Alonso, E., Alejano, L.R., Varas, F., Fdez-Manín, G., Carranza-Torres, C. (2003). Ground response curves for rock masses exhibiting strain-softening behaviour. Int. J. Numer. Anal. Meth. Geomech. 27, 1153–1185. — [U] (journal as cited in [8] appeared garbled)
[10] Alejano, L.R., Rodríguez-Dono, A., Alonso, E., Fdez-Manín, G. (2009). Ground reaction curves for tunnels excavated in different quality rock masses showing several types of post-failure behaviour. Tunn. Undergr. Space Technol. 24(6), 689–705. https://doi.org/10.1016/j.tust.2009.07.004 — [V] citation via [8]; [U] content
[11] Crowder, J.J., Bawden, W.F. (2004). Review of post-peak parameters and behaviour of rock masses: current trends and research. RocNews, Fall 2004. — [U]
[12] Martin, C.D., Kaiser, P.K., McCreath, D.R. (1999). Hoek-Brown parameters for predicting the depth of brittle failure around tunnels. Can. Geotech. J. 36(1), 136–151. — [V] via [13]
[13] University of British Columbia, EOSC 547 course notes, Part 3 supplementary notes. https://www.eoas.ubc.ca/courses/eosc547/lecture-material/Part3-SupplementaryNotes.pdf — [V] reproduction of [12] and outline of [5]
