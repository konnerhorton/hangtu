# Eurocode 7 — Summary for ags-kit

> **What this is:** a summary, in our own words, of the parts of Eurocode 7 (EN 1997) that matter to ags-kit, written to guide the design of the statistics and QC features. It is **not** a substitute for the standard. EN 1997 is copyrighted and sold by CEN member bodies (BSI, DIN, etc.). This summary relies on public secondary sources, listed at the end.
>
> **Verification flags:** clause and formula numbers marked ✅ were cross-checked against the JRC technical report (Orr et al., 2025), which quotes the published EN 1997-1:2024. Items marked ⚠️ come from draft-era (prEN/FprEN) material or general knowledge and should be checked against a purchased copy before being relied on in design.

---

## 1. Editions and status

| | 1st generation | 2nd generation |
|---|---|---|
| Parts | EN 1997-1:2004 *General rules*; EN 1997-2:2007 *Ground investigation and testing* | EN 1997-1:2024 *General rules*; EN 1997-2:2024 *Ground properties*; EN 1997-3:2025 *Geotechnical structures* |
| Basis of design | EN 1990:2002 | EN 1990-1:2023 |
| Key ground-property term | **Characteristic value** | **Representative value**, determined *either* as a characteristic value (statistical) *or* as a nominal value (cautious estimate) |
| Design approach | DA1 / DA2 / DA3, chosen per country | No Design Approaches. Instead: Material Factor Approach (MFA) or Resistance Factor Approach (RFA), with Verification Cases VC1–VC4 from EN 1990 |

- Parts 1 and 2 of the 2nd generation were published in late 2024 and Part 3 in March 2025.
- In the UK, BSI withdraws the 1st generation on **30 March 2028**, so the two generations coexist until then. Other countries set their own dates through their National Annexes. ⚠️
- In the 2nd generation, the old Part 1 is split three ways: general rules go to EN 1997-1, structure-specific rules (foundations, retaining structures, anchors, slopes) go to EN 1997-3, and the basis of design goes to EN 1990.

**ags-kit stance:** implement the 2nd-generation statistical framework as the primary method, and document how it maps to the 1st-generation terminology (section 3.6). Since the team works mostly in the US, EC7 is used as a **well-documented statistical method**, not as a code obligation.

---

## 2. The chain of values (2nd generation)

The central idea in the 2nd generation is an explicit, traceable path from data to design:

```
measured value  →  derived value  →  representative value  →  design value
(test result)      (via theory,       (characteristic Xk       (partial factors
                    correlation or     OR nominal Xnom,         applied, per
                    empiricism)        × conversion factor η)   MFA/RFA)
```

- **Measured value**: what the test reports. In AGS terms, this is the raw value in a test group (e.g. `ISPT_NVAL`, `LLPL_LL`).
- **Derived value**: a ground property obtained from test results by theory, correlation or empiricism (e.g. φ′ from SPT N60). Derived values are reported in the **Ground Investigation Report (GIR)**, and the correlations used must be documented.
- **Representative value (X_rep)**: ✅ determined *from derived values presented in the GIR* (EN 1997-1, 4.3.2.1), separately for each property, **each geotechnical unit**, and each limit state.
  - X_rep = X_k ✅ (Formula 4.1), when the data are sufficient for statistics.
  - X_rep = X_nom ✅ (Formula 4.2), when they are not. A nominal value is a cautious estimate based on site knowledge and comparable experience.
  - Optionally X_rep = η·X_k or η·X_nom ✅ (Formulae 4.3 / 4.4). η is a **conversion factor** for scale, moisture, temperature, ageing, anisotropy, stress path or strain level. η = 1.0 when those effects are already allowed for.
- **Ground Model** (new in the 2nd generation): a site-specific outline of the disposition and character of the ground and groundwater, based on ground investigation and other data. It includes the derived values for every geotechnical unit in the zone of influence. ⚠️ (wording per draft EN 1997-2)
- **Geotechnical Design Model**: the conceptual representation of the site, taken from the Ground Model, used to verify each design situation and limit state.

**ags-kit relevance:** the AGS database is effectively the raw material for the Ground Model. In our terms:
- a "geology code" maps to a **geotechnical unit**;
- a canned query result (e.g. N60 by unit) is a set of **derived values**;
- `ak.stats.characteristic()` produces a **characteristic value**.

The library must keep these concepts separate and traceable, which means recording which correlation was used, which η, and which n.

---

## 3. Characteristic values: the statistical core

### 3.1 Definition ✅
- EN 1997-1, 3.1.3.4: the statistically determined value of a ground property that affects the occurrence of a limit state, with a prescribed probability of not being attained.
- EN 1997-1, 4.3.2.2(1)–(2):
  - limit state **insensitive** to ground variability → X_k is an estimate of the **mean**;
  - limit state **sensitive** to ground variability → X_k is an estimate of the **5% fractile** (when a low value is unfavorable) or the **95% fractile** (when a high value is unfavorable).
- Statistical estimates are made at a **95% confidence level**.

### 3.2 Types of estimate (spatial variability)
Whether the mean or a fractile is appropriate depends on the size of the failure volume (L) compared with the **scale of fluctuation** (θ) of the property.

| Type | When | What it estimates | Sensitivity index Γ² = θ/L |
|---|---|---|---|
| **A** | Large failure volume averages out variability (e.g. long slip surface in one unit, pile shaft) | Mean value (95% confidence) | Γ² = 0 |
| **B** | Local failure; failure zone ≤ scale of fluctuation (e.g. pile base) | 5% or 95% fractile | Γ² = 1 (capped) |
| **C** | Intermediate: most real cases | Between A and B | 0 < Γ² < 1 |

- The JRC guidance suggests using **Type A only when θ/L < 0.05**, **Type B only when θ/L > 0.85**, and Type C otherwise.
- The Type C generalization (Γ²) comes from the JRC report (following Vanmarcke 1983), not from the standard's main formula. The standard itself gives Types A and B.

### 3.3 Formula (normal distribution) ✅
EN 1997-1, Formula (4.5):

```
X_k = X_mean · (1 ∓ k_n · V_X)        V_X = s_X / X_mean,   s_X = sample std dev (n−1 denominator, Formula A.4)
```

Use "−" for an inferior (low) value and "+" for a superior (high) value.

**k_n factors.** These depend on n, on the type of estimate, and on what is known about V_X. They come from EN 1997-1 Annex A (Tables A.3–A.7), as restated by the JRC:

| V_X knowledge | Type A (mean) | Type B (fractile) | Type C (intermediate) |
|---|---|---|---|
| **Case 1** V_X known (prior knowledge) | N₉₅·√(1/n) | N₉₅·√(1 + 1/n) | N₉₅·√(Γ² + 1/n) |
| **Case 3** V_X assumed (indicative value) | same as Case 1 | same as Case 1 | same as Case 1 |
| **Case 2** V_X unknown (computed from data) | t₉₅,ₙ₋₁·√(1/n) | t₉₅,ₙ₋₁·√(1 + 1/n) | t₉₅,ₙ₋₁·√(Γ² + 1/n) |

- N₉₅ = 1.645, the standard normal value at 95%.
- t₉₅,ₙ₋₁ is the one-sided Student-t value at 95% with n−1 degrees of freedom. It falls from 6.31 at n = 2 to about 1.66 at n = 100.
- The JRC labels the combinations A1, B1, A2, B2, etc. For example, **B2** is a 5% fractile with V_X unknown, the most conservative common case.
- The JRC and the standard's notes point out that in practice **Case 3**, an assumed conservative upper V_X, is often better than Case 2, because V_X computed from a small sample is unreliable. Case 1 (truly known V_X) is rare.

### 3.4 Indicative coefficients of variation
From EN 1997-1 Annex A, Tables A.1 and A.2, as reproduced in the JRC report (CC BY 4.0). These are the defaults ags-kit will use for Case 3.

| Property / test parameter | V_X (%) |
|---|---|
| Weight density γ (all) | 5–10 |
| Undrained shear strength c_u (fine-grained) | 30–50 |
| Effective cohesion c′ (peak or residual) | 30–50 |
| Coefficient of friction tan φ′ | 5–15 |
| Shear strength at failure τ_f | 15–25 |
| Unconfined compressive strength q_u | 20–80 |
| Modulus E or G | 20–70 |
| Consolidation coefficient c_v / c_h (fine-grained) | 30–70 |
| Hydraulic conductivity K | 70–250 (Formula 4.5 should **not** be used) |
| **SPT blow count (coarse soils)** | **15–45** |
| Pressuremeter limit pressure p_l | 5–15 |
| CPT cone resistance q_c, sleeve friction f_s | 5–15 |

### 3.5 Other distributions and procedures
- ✅ 4.3.2.2(3): X_k should be determined from a **normal or log-normal** distribution, as appropriate. Annex A gives log-normal versions (Formulae A.5–A.7 ⚠️ numbering per JRC worked examples). The simplest approach is to transform to ln(X), apply the normal formulae, and transform back. For the **mean** of log-normal data, exponentiating gives the *median*, not the mean. The JRC gives Angus's (1988) approximation for a proper confidence bound on the mean.
- ✅ 4.3.2.2(5): **other statistical procedures** are acceptable. Relevant ones:
  - **Schneider (1997)**: X_k ≈ X_mean − 0.5·s (that is, k_n = 0.5), a simple Type A estimate.
  - **Simplified fractile**: X_k ≈ X_mean − 1.75·s, a simple Type B estimate (JRC Eq. 23).
  - **Depth-dependent properties** (e.g. c_u increasing with depth): fit a linear regression with least squares. The characteristic mean trend uses the **confidence interval** of the regression line. The characteristic fractile trend uses the **prediction interval**, with t at n−2 degrees of freedom. The assumptions to check are constant variance, random scatter and normal residuals; if residuals are skewed, use ln(X).
  - **Dependent properties** (c′ and φ′ together): bivariate methods. Case 3 is usually the only practical option here.
- **Negative or near-zero X_k** with a normal fit and high V_X is a signal that the data may be log-normal (JRC 5.1.3).

### 3.6 Mapping to the 1st generation (EN 1997-1:2004)
- **1st gen 2.4.5.2**: the characteristic value is a *cautious estimate* of the value affecting the limit state. When statistics are used, it is derived so that the probability of a worse governing value is **not greater than 5%**.
  - The mean-vs-local distinction (large vs small volume of ground) already existed.
  - The 2nd generation formalizes it and adds the *nominal* vs *characteristic* split under the umbrella of the *representative value*.
- In practice, "characteristic value" in a 1st-gen report corresponds to the 2nd-gen *representative value*. That could have been either a statistical X_k or a cautious nominal estimate.
- 1st-gen EN 1997-2:2007 also used **derived values** and required the correlations to be documented.

### 3.7 How many data points? (JRC 5.1, guidance not normative)
The standard sets **no hard minimum n**. The JRC offers several criteria:
- **Non-negative X_k**: for B2 (fractile, V_X unknown), n ≥ 3 / 4 / 5 / 10 for V_X = 20 / 30 / 40 / 50 %.
- **Ratio criterion**: X_k from n samples should be within 20% of X_k from n = 100.
- **Gradient criterion**: the change in X_k/X_mean per added sample should be under 1%.
- **Accuracy of V_X** (JRC Table 17): B2 needs about 11–33 samples, depending on the accuracy wanted.
- With few samples: if n is too small, use a nominal value, or cross-check X_k against a nominal value and engineering judgment.

---

## 4. Ground investigation (EN 1997-2)

- **Scope (2024)**: rules for determining ground properties, and for presenting GI results and derived values in the **Ground Investigation Report**.
- **Geotechnical Category** = a function of **Consequence Class** (CC1–CC3) and **Geotechnical Complexity Class** (GCC1 lower / GCC2 normal / GCC3 higher). It drives the extent of investigation, checking and supervision.
  - A preliminary GCC is set at desk-study stage. ⚠️ (EN 1997-2, 5.2.1 per draft guidance)
  - **GCC3** covers considerable uncertainty about ground conditions, difficult ground, complex geology, or significant groundwater sensitivity.
  - **GCC1** requires negligible uncertainty, uniform ground and well-established methods.
- **Records** (draft wording ⚠️): the position and elevation of investigation points must be recorded with the grid and datum used. Sample quality must be assessed and recorded before specimens are tested.
- **Sampling** (1st gen 2007, still useful):
  - Sampling categories A/B/C per EN ISO 22475-1.
  - Laboratory quality classes 1–5. Category A can achieve class 1, while category C reaches only class 5.
  - Samples at every change of stratum, at spacing typically ≤ 3 m. ⚠️
- **Spacing of investigation points** (1st gen 2007, informative Annex B.3 ⚠️):
  - Buildings up to about 10 storeys: roughly 15–40 m grid, with at least 3 holes per site.
  - Taller buildings: about 10–30 m.
  - Whether the 2024 edition keeps these values is unverified.
- **Correlations**: 1st-gen EN 1997-2 annexes gave example correlations (e.g. SPT → relative density, φ′). The 2nd generation moves many test-specific correlations into EN 1997-2 annexes, organized by ground property. ⚠️ (details unverified)

**ags-kit relevance:**
- The QC module should check what the GIR needs: a location and datum for every hole (LOCA_NATE/NATN/GL, LOCA_GREF), sample quality and type (SAMP_TYPE), and a geotechnical unit for every test.
- Analyses that use correlations must record which correlation was applied.

---

## 5. Design verification (context only)

ags-kit does **not** do limit-state design. For orientation:

- **1st gen**: Design Approaches DA1 (two combinations), DA2 and DA3. Each country chose one or more.
- **2nd gen**: Design Approaches are removed. ULS verification is E_d ≤ R_d, with:
  - **Material Factor Approach (MFA)**: partial factors on ground properties, R_d = R(η·X_k/γ_M; a_d; ΣF_Ed). Typically Verification Case VC3 with set M2.
  - **Resistance Factor Approach (RFA)**: partial factors on the resistance, R_d = R/γ_R. Typically VC1 or VC4 with set M1.
  - Indicative M2 factors (from draft-era slides ⚠️):
    - tan φ′ (peak): 1.25·k_M
    - c′: 1.25·k_M
    - tan φ′ (critical state): 1.1·k_M
    - c_u: 1.4·k_M
  - k_M (like k_F on actions) depends on the consequence class. Example values for k_F are 1.1 for CC3, 1.0 for CC2 and 0.9 for CC1.
- Other verification routes: prescriptive rules, testing, the observational method, and reliability-based methods.
- **Why this matters for ags-kit:** the partial factor is applied to the *representative* value. A characteristic value that is too optimistic (wrong type, wrong k_n, V_X underestimated) carries straight through into an unsafe design value. That is why the stats output must state the type, the case, n and V_X explicitly.

---

## 6. Data quality expectations

The themes that recur in both generations, translated into ags-kit QC requirements:

| EC7 expectation | ags-kit check / feature |
|---|---|
| Derived values are traceable to measured values and the correlation used | Provenance columns (source file and line); analysis outputs record the method, correlation and parameters |
| Representative values are set **per geotechnical unit** | Every test must map to a geology unit; `missing_geology` and `straddles_boundary` QC rules |
| Sufficiency of data (quantity, quality, spatial distribution) decides characteristic vs nominal | `characteristic()` warns when n is below the JRC guidance and reports the n needed |
| Sample quality is recorded | Completeness checks on SAMP_TYPE; a sample-quality filter is a possible later feature |
| Position and elevation recorded with grid and datum | `LOCA_NATE/NATN/GL/GREF` completeness; datum carried as metadata |
| Data distribution checked (normal vs log-normal) | `ak.stats.fit()` with goodness of fit; `characteristic()` takes `distribution="normal"|"lognormal"` |
| Depth trends handled separately | `characteristic(..., trend="depth")` using a regression prediction interval |
| Comparison of derived values from different sources in one unit (EN 1997-1, Table 4.6 ✅) | `ak.stats.compare()` (Welch t / Mann-Whitney); box plots by unit and source |

---

## 7. Proposed ags-kit API (feeds into SPEC.md §7)

```python
res = ak.stats.characteristic(
    values,                    # array/Series of derived values in one geotechnical unit
    estimate="mean",           # "mean" (Type A) | "fractile" (Type B) | "intermediate" (Type C, needs gamma2)
    side="low",                # "low" (inferior, default) | "high" (superior)
    vx=None,                   # None → Case 2 (computed); float → Case 1/3 (known/assumed)
    vx_source="assumed",       # "known" | "assumed" (labels the case in output)
    distribution="normal",     # "normal" | "lognormal"
    gamma2=None,               # sensitivity index θ/L for Type C
    method="ec7",              # "ec7" | "schneider" | "simplified_fractile"
)
res.value      # X_k
res.summary()  # n, mean, s, V_X, k_n, case/type combination (e.g. "B2"), warnings (small n, negative X_k, high V_X)
```

**Golden tests:** the JRC report's worked examples (Annexes I–III: Coca slope, Göta älv c_u, Perniö clay) give published inputs and outputs we can use for regression tests.

---

## Sources

- European Commission JRC: Orr, T., Sorgatz, J., Estaire, J., et al. (2025). *Determination of representative values from derived values for verification with limit states with EN 1997*. EUR 40260, JRC141453. doi:10.2760/0980105. CC BY 4.0. [PDF](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2025-03/JRC141453_01.pdf). **Primary source for sections 2–3.**
- Bond, A. (Geocentrix). *Decoding Eurocode 7 – 2nd-generation update* (lecture slides). [PDF](https://www.geocentrix.co.uk/lectures/downloads/Eurocode%207%20-%202nd-generation%20update.pdf)
- University of Stuttgart IGS (2025). *The second generation of Eurocode 7*. [PDF](https://www.igs.uni-stuttgart.de/institut/publikationen/Publikationen/2025/DFIEFFC25-210-THE_SECOND_GENERATION_OF_EUROCODE_7-250510_final.pdf)
- Orr, T. (2024). CEN/TC250/SC7 Seminar, *Design with second generation Eurocode 7*. [PDF](https://www.nen.nl/media/PDF/2-Trevor_Orr_SC7_Paris_Day1_Session1_9AM_Present2-TO_1.pdf)
- Sorgatz, J. (2025). Bestimmung repräsentativer Baugrundkenngrößen nach dem neuen Eurocode 7. *geotechnik*. [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/gete.70009)
- ISSMGE: *Eurocode 7 – second generation: determination of representative values*. [PDF](https://www.issmge.org/uploads/publications/51/126/913_C_eurocode_7__second_generation_determination_of_rep.pdf)
- Schuppener, B. *Ground investigation and testing – EN 1997-2* (JRC Eurocodes background). [PDF](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/04-Schuppener-Ground-investigation&testing-EN1997-2.pdf)
- groundhog (open-source Python): EC7 parameter selection formulas. [docs](https://groundhog.readthedocs.io/en/dev/standards/parameter_selection.html). Useful as a cross-check implementation.
- Schneider, H.R. (1997). Definition and determination of characteristic soil properties. *Proc. 14th ICSMFE*, Hamburg. (Cited via JRC.)
- Frank, R., Bauduin, C., Driscoll, R., Kavvadas, M., Krebs Ovesen, N., Orr, T., Schuppener, B. (2004). *Designers' Guide to EN 1997-1*. Thomas Telford.
- Bond, A. & Harris, A. (2008). *Decoding Eurocode 7*. Taylor & Francis.
