# Hoek–Brown constant mi

| | |
|---|---|
| **Parameters** | mi (the Hoek–Brown constant of intact rock), fitted with σci (the intact compressive strength) or with σci fixed |
| **Material** | Rock |
| **Models that use it** | Hoek–Brown, intact and generalized; Mohr–Coulomb parameters equivalent to a Hoek–Brown envelope; strain-softening Hoek–Brown |
| **Depends on** | intact rock strength (σci from UCS tests, σt from tensile tests) |
| **Feeds** | rock mass strength (mb, from mi with GSI and disturbance); [discontinuity shear strength](22-discontinuity-shear-strength.md), where σci bounds a joint's wall strength |

## What it is

The intact Hoek–Brown criterion gives the major principal stress at failure of an intact rock specimen from the
minor one:

$$
\sigma_1 = \sigma_3 + \sigma_{ci}\left(m_i\,\frac{\sigma_3}{\sigma_{ci}} + 1\right)^{0.5}
$$

(Hoek 2007, ch. 11, eq. 5, p. 2). σci is the intercept at σ3 = 0, the uniaxial compressive strength of the intact
rock, and mi sets the curvature: how fast strength rises with confinement. mi grows with the ratio of compressive to
tensile strength, so coarse crystalline rocks such as granite have a high mi and fine-grained clastic rocks such as
claystone a low one. It depends on mineralogy, grain size and texture, and on the direction of loading: tabulated
values are for loading normal to bedding or foliation (Hoek 2007, ch. 11, Table 3 note, p. 7).

The criterion holds for brittle shear failure only, between σ3 = 0 and the brittle–ductile transition, around
3 < σ1/σ3 < 5 (Hoek 2023, ch. 3, p. 6). A fitted mi therefore depends on the σ3 range tested: Hoek (2007, ch. 11,
p. 2) gives 0 < σ3 < 0.5 σci.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Rock mass strength, generalized Hoek–Brown | mb is mi reduced for GSI and disturbance, so mb scales with mi | High |
| Equivalent Mohr–Coulomb (tunnel models, limit equilibrium) | the equivalent φ′ rises steeply with mi; c′ less so | High on φ′, and so on the plastic zone and convergence |
| Convergence–confinement around an opening | the envelope's curvature at low σ3 | Moderate to high |
| Rock mass tensile strength | −s σci / mb (Hoek, Carranza-Torres & Corkum 2002, eq. 7), so inversely with mi | Moderate |
| Strain-softening models | the residual constant is scaled from mi | Moderate |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| mi | – | – | dimensionless, and the same in any unit if σ1, σ3 and σci share one |
| σ1, σ3, σci | MPa | psi, ksi | 1 MPa = 145.04 psi = 0.14504 ksi |

## Typical values

| Material | mi | Source |
|---|---|---|
| Claystone; siltstone | 4 ± 2; 7 ± 2 | Hoek (2007), ch. 11, Table 3, p. 7 |
| Shale; marl (estimates) | 6 ± 2; 7 ± 2 | as above |
| Sandstone | 17 ± 4 | as above |
| Limestone: micritic, sparitic, crystalline (estimates) | 9 ± 2, 10 ± 2, 12 ± 3 | as above |
| Gypsum; anhydrite | 8 ± 2; 12 ± 2 | Cai (2009), Table 1, after Hoek (2007) |
| Granite, for scale | 32 ± 3 | Hoek (2007), ch. 11, Table 3, p. 7 |

The tabulated values place a rock roughly; tests on the rock of interest overrule them.

## Tests

| Test | ASTM | ISRM | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Triaxial compression of intact core | D7012-23, method A (B with moduli) | ISRM suggested method | **No AGS group for rock triaxial tests.** Some files use `TRIG`/`TRIT` (`TRIT_CELL`, `TRIT_DEVF`, `TRIT_MODE`, in kPa) or a user-defined group | (σ3, σ1) at failure, with the mode of failure |
| Uniaxial compression | D7012-23, method C | ISRM suggested method | `RUCS`: `RUCS_UCS`, `RUCS_MODE` | a point at σ3 = 0 |
| Brazilian or direct tension | D3967 | ISRM suggested method | `RTEN`: `RTEN_TENS`, `RTEN_MODE` | σt, a check on mi |

Hoek (2023, ch. 3, p. 6) asks for at least 3, preferably 5, triaxial tests in addition to the UCS tests, and Hoek
(2007, ch. 11, p. 2) for at least five well-spaced points over 0 < σ3 < 0.5 σci.

**Entering the results.** Until hangtu reads rock tests from AGS (wave 0 for `TRIT` and user-defined groups, wave 4
for `RUCS` and `RTEN`), enter them in a CSV in [`ht.template("triaxial")`](../guides/templates.md)'s columns, the
same template as soil triaxial stages: one row per test or per stage of a multistage test, with
`cell_pressure` as σ3, `deviator_stress_at_failure` as σ1 − σ3, `failure_mode` as the lab wrote it, and
`multistage_test` true for multistage stages. A UCS test is a row with a cell pressure of 0. If the lab reports σ1,
subtract the cell pressure in your spreadsheet first. The lab's own fit goes in
`reported_intact_compressive_strength` and `reported_intact_hoek_brown_constant`. Leave the soil-only columns
blank, and declare every stress column's unit when you read the file, blank ones included. Rock rows in `TRIT`
reach [`p.triaxial()`](../reference/project.md#hangtu.Project.triaxial) in the same shape, with `TRIT_MODE` as
`failure_mode`.

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Least squares on Hoek's line, σci and mi together (Hoek 2007, ch. 11, eqs. 6–8, p. 4) | (σ3, σ1) of UCS and triaxial tests | shear failures, 0 < σ3 < 0.5 σci | [`ht.analysis.hoek_brown_fit()`](../reference/analysis.md#hangtu.analysis.hoek_brown_fit), drawn by [`ht.plot.hoek_brown_envelope()`](../plots/hoek-brown-envelope.md) |
| As above, σci fixed, mi only | as above, with σci a judgment | few triaxial tests, or a free σci far from the UCS tests | [`ht.analysis.hoek_brown_fit()`](../reference/analysis.md#hangtu.analysis.hoek_brown_fit), which makes both fits |
| mi from σci/σt (Cai 2009; Hoek 2023, ch. 3, eq. 8) | σci, σt | brittle rocks; a check on the fit | wave 4 |
| mi from tables (Hoek 2007, ch. 11, Table 3) | rock type and texture | no tests | wave 4 |

The fit uses Hoek's regression: (σ1 − σ3)² against σ3 is a straight line with intercept σci² and slope mi σci, so
UCS tests (σ3 = 0) and triaxial tests are fitted together. With σci fixed, only the slope is fitted. σci for the
fixed fit is a judgment, given with `fixed_intact_compressive_strength=` or in the project's
[judgments file](../guides/judgments.md), never taken from the UCS tests by a rule; the result prints the UCS
tests' count and mean beside the free σci, so the check is in front of you.

`failure_mode` is the lab's own words, so name the shear failures with `failure_modes=`, as written. Rows with
other modes, and multistage stages in the single-stage fit, are left out and counted by reason. Each fit gives n,
R², the σ3 range fitted, the points beyond 0.5 σci, and the lab's own σci and mi beside the fitted ones. Each
point's back-calculated mi, eq. 5 solved for mi with the fit's σci, is on the result: a trend in it with σ3 shows
that one curve doesn't suit the group. It is ill-conditioned at small σ3/σci, so read it at the higher confining
stresses.

The example project's sandstone has four UCS tests, eight single-stage triaxial tests and a three-stage multistage
test, in MPa. One UCS test split axially and one triaxial test failed along bedding, so both are left out:

```python
--8<-- "hoek-brown-constant.py"
```

``` { .text .no-copy }
--8<-- "hoek-brown-constant.txt"
```

## How the methods compare

Tests on the rock of interest are the basis: a fit of at least five well-spaced shear failures, UCS included,
overrules the tables and σci/σt. Report the free and the fixed fit together. Where the free σci is far from the UCS
mean, or the triaxial tests are few, the fixed fit is the more stable estimate of mi. Compare the fitted mi with
the table's value for the rock type and with σci/σt; a difference of more than about half the table's value is
worth investigating _[judgment, for review]_. Choosing σci and mi for design is selection (M18).

## Variability

- Hoek's probabilistic example uses mi with a mean of 8 and a standard deviation of 1, a COV of 12.5 % (Hoek 2007,
  ch. 11, Fig. 12, p. 29).
- The ± ranges of Hoek (2007, ch. 11, Table 3) are 20 to 50 % of the tabulated value (sparitic limestone 20 %,
  sandstone 24 %, shale 33 %, claystone 50 %; computed): the uncertainty when mi comes from the table rather than
  tests.
- A per-specimen mi is very sensitive to error at small σ3/σci. With σci = 50 MPa and mi = 8, a +5 % error in σ1
  gives mi = 19.2 at σ3 = 0.5 MPa, 10.0 at 5 MPa and 9.3 at 25 MPa (computed from eq. 5).

## Pitfalls

- Remove non-shear failures, such as axial splitting or failure along bedding or a vein, before fitting (Hoek
  2023, ch. 3, p. 6). `hoek_brown_fit()` asks you to name the shear modes whenever `failure_mode` has values, and
  notes when it has none.
- Keep to 0 < σ3 < 0.5 σci: points past the brittle–ductile transition flatten the fit. The fit keeps them, counts
  them and warns; filter the rows on σ3 and refit to leave them out.
- Fit at least five well-spaced points (Hoek 2007, ch. 11, p. 2); the fit warns with fewer.
- Check R²: good data give more than 0.9 (Hoek 2007, ch. 11, p. 4). A lower R² is noted in the summary.
- Fit each rock type and loading direction on its own, with `group_by=`; don't pool shale and limestone
  interbeds.
- Compare the free σci with the UCS mean the summary prints; if they differ, report the fixed fit and say why.
- Multistage stages can give a lower σ1 than fresh specimens, which biases mi low _[judgment, for review]_. The fit
  is made with and without them, and the summary prints both.
- Rock tests rarely measure pore pressure, so the fit is in total stress by default, which assumes none in the
  specimen; `stress="effective"` fits the effective stresses where the rows have them.

## References

- Hoek, E. (2007). *Practical Rock Engineering*, ch. 11, "Rock mass properties". Rocscience.
  <https://www.rocscience.com/assets/resources/learning/hoek/Practical-Rock-Engineering-Chapter-11-Rock-Mass-Properties.pdf>
- Hoek, E. (2023). *Practical Rock Engineering*, ch. 3, "Intact rock strength". Rocscience.
  <https://static.rocscience.cloud/assets/resources/learning/hoek/3.-Intact-rock-strength_2023-06-30-120556_xiuv.pdf>
- Hoek, E., Carranza-Torres, C. and Corkum, B. (2002). Hoek–Brown failure criterion: 2002 edition. *Proc. NARMS-TAC*,
  Toronto, 267–273. <https://www.eoas.ubc.ca/courses/eosc433/lecture-material/2002-HoekBrownCriterion.pdf>
- Cai, M. (2009). A simple method to estimate tensile strength and Hoek–Brown strength parameter mi of brittle
  rocks. *ROCKENG09*, Toronto, paper 4063.
  <https://geogroup.utoronto.ca/wp-content/uploads/RockEng09/PDF/Session21/4063%20PAPER.pdf>
- ASTM D7012-23. *Standard Test Methods for Compressive Strength and Elastic Moduli of Intact Rock Core Specimens
  under Varying States of Stress and Temperatures.* <https://store.astm.org/d7012-23.html>

The criterion's original (Hoek & Brown 1980) and the tables' (Hoek & Brown 1997; Marinos & Hoek 2000, 2001) are
cited as Hoek (2007) gives them; their originals haven't been checked here.
