# Hardening Soil stiffness

| | |
|---|---|
| **Parameters** | E50 (secant modulus at half the peak), ε50, Rf (failure ratio); Eoed and Eur,oed (oedometer); the Hardening Soil set: E50ref, Eoedref, Eurref, m, pref, νur |
| **Material** | Soil |
| **Models that use it** | Hardening Soil and HS-small (with G0ref and γ0.7 from [small-strain stiffness](10-small-strain-stiffness.md)) |
| **Depends on** | [Drained shear strength](04-drained-shear-strength-soil.md) (c′, φ′); [preconsolidation and compressibility](06-preconsolidation-and-compressibility.md) (Cc, Cs, σ′p); [at-rest earth pressure](07-at-rest-earth-pressure.md) (K0nc); [elastic stiffness](08-elastic-stiffness-soil.md) |
| **Feeds** | Numerical models (Hardening Soil, HS-small); [small-strain stiffness](10-small-strain-stiffness.md) (the G0 against Gur check) |

## What it is

In primary loading, a soil's stiffness falls along a near-hyperbolic stress–strain curve; on unloading and
reloading it is much stiffer and nearly elastic. The Hardening Soil model describes the triaxial curve by a
hyperbola (PLAXIS 2D 2026.1 Material Models Manual, §6.1, Eq. 6–3 and Fig. 6–1, pp. 68–69):

$$
-\varepsilon_1 = \frac{1}{E_i}\,\frac{q}{1 - q/q_a}, \qquad
E_i = \frac{2E_{50}}{2 - R_f}, \qquad q_a = \frac{q_f}{R_f}
$$

(Eqs. 6–3, 6–4 and 6–6). E50 is the secant modulus from the origin to half the peak deviator stress. The failure
ratio Rf sets how far the asymptote q_a lies above the failure stress q_f: Rf is "smaller than or equal to 1", and
PLAXIS takes 0.9 by default (p. 69).

The model's moduli rise with confining stress by a power law with exponent m, and it takes three of them at a
reference stress pref: E50ref (triaxial primary loading), Eoedref (one-dimensional primary compression) and
Eurref (unloading and reloading). The oedometer gives the constrained moduli Eoed and Eur,oed directly, at each
increment's stress.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Numerical models of excavations and tunnels (Hardening Soil, HS-small) | Eurref governs the elastic unloading around the works and the heave of a base; E50ref the shear hardening around them; m the stiffness profile with depth | High for displacements |
| Consolidation settlement | Eoedref and m control one-dimensional compression | High |
| Rf | shapes the hyperbola near failure | Low |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| E50, Eoed, Eur,oed, E50ref, Eoedref, Eurref, pref, q_a | kPa, MPa | psf, ksf, psi | 1 MPa = 20.885 ksf = 145.04 psi; 1 ksf = 47.88 kPa |
| ε50 | % | % | strain |
| Rf, m, νur | – | – | dimensionless |

## Typical values

| Material | Range | Source |
|---|---|---|
| Rf, default | 0.9 | PLAXIS 2D 2026.1 Material Models Manual, p. 69 |
| Rf, most soils | 0.75–1.0 (about 0.9 on average) | Obrzud & Truty (2018), §3.3.3, p. 106 |

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Triaxial CD and CU | D7181; D4767 | ISO 17892-9; BS 1377-8 | `TRET`: `TRET_E50`, `TRET_EP50`, `TRET_DEVF` | the lab's E50 and ε50 (`p.triaxial()`); the q–ε1 curve itself from the readings |
| Incremental oedometer, with unloading and reloading | D2435/D2435M | ISO 17892-5; BS 1377-5 | `CONS`: `CONS_INCF`, `CONS_IVR`, `CONS_INMV` | Eoed and Eur,oed per increment |

AGS 4.2 has no group for a triaxial test's readings during shearing. hangtu reads them from the file's
user-defined groups through the readings map, or from a CSV (`ht.template("triaxial_readings")`).

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| E50 and ε50, the secant to half the peak (PLAXIS 2026.1, Eqs. 6–3, 6–4, Fig. 6–1) | the q–ε1 readings | triaxial compression stages | [`ht.analysis.triaxial_stiffness_from_readings()`](../reference/analysis.md#hangtu.analysis.triaxial_stiffness_from_readings) |
| Rf from the hyperbola in transformed form (Obrzud & Truty 2018, Eq. 2.11) | the q–ε1 readings | triaxial compression stages | [`ht.analysis.triaxial_stiffness_from_readings()`](../reference/analysis.md#hangtu.analysis.triaxial_stiffness_from_readings) |
| Eoed and Eur,oed = 1/mv per increment | the oedometer increments | tested specimens | [`ht.analysis.oedometer_increments()`](../reference/analysis.md#hangtu.analysis.oedometer_increments) |
| Eur from an unload–reload loop | the q–ε1 readings | stages with a loop | later |
| E50ref and m across σ′3; Eoedref, Eurref; the Hardening Soil set | the moduli above | by geology unit | later |

**E50** is read at half the stage's largest q, whatever the failure criterion: that is how labs report it (AGS
`TRET_E50`), so hangtu's value and the lab's can be set side by side. It is Eu50 on an undrained stage and E′50 on
a drained one, as `test_type` says, and neither is converted into the other. The strain at half the peak is
interpolated between readings, so E50 differs from a smooth curve's by about 1 % at typical reading spacing.

**Rf** comes from the slope of ε1/q against ε1, fitted to the readings between 0.7 and 0.95 of the failure stress
(`failure_ratio_range=`). The range is hangtu's rule, stated as such: the sources give the transformed line, not
which readings to fit. It leaves out the start, where bedding errors dominate, and the approach to failure, where
the curve leaves the hyperbola. A stage with fewer than 3 readings in the range gets no Rf and a reason, and an Rf
above 1 is kept and counted in a warning. The equations and limits are in the reference entry.

On the example project, hangtu's E50 from the readings beside the lab's, where the lab reported one, with Rf and
the dilatancy angle ψ of each drained stage ([dilatancy](09-dilatancy.md)):

```python
--8<-- "hardening-soil-stiffness.py"
```

``` { .text .no-copy }
--8<-- "hardening-soil-stiffness.txt"
```

hangtu's E50 matches the lab's to its reported place on every stage that has one: the example lab computed it from
the same readings. On a real file, a difference says the lab read its secant differently, at another peak or from
another origin.

## How the methods compare

E50 from the curve and the lab's reported E50 are the same quantity, and on a test with both, a difference is a
question for the lab. E50 and Eoed are not interchangeable: one is a triaxial secant, the other a constrained
modulus in one-dimensional compression, and each comes from its own test. Choosing a design value is selection:
[`ht.stats.select()`](../guides/selection.md).

## Variability

Rf from lacustrine soft soils ranges 0.73–0.88 in drained and 0.70–0.99 in undrained triaxial tests (Obrzud &
Truty 2018, §3.3.3, p. 106, after Kempfert 2006).

## Pitfalls

- E50 from an undrained test is Eu50, not a drained E′50. Don't enter it as one without a conversion and judgment.
- A later stage of a multistage test shears a specimen already sheared in an earlier one: its E50 is stiffer and
  not a first-loading value. `multistage_test` and `test_stage` say which rows those are.
- An Rf above 1 says the curve isn't a hyperbola over the fitted range. hangtu keeps it and warns, with a count.
- A curve without its zero reading has no origin to measure E50 from: hangtu leaves it blank with a reason rather
  than extrapolating.
- Eoed at σ′v0 in an overconsolidated soil lies on the reloading branch; Eoedref is a primary loading value.

## References

- Seequent (2026). *PLAXIS 2D 2026.1 Material Models Manual*, Ch. 6, The Hardening Soil model.
- Obrzud, R.F. and Truty, A. (2018). *The Hardening Soil Model: A Practical Guidebook.* Z_Soil.PC 100701 report,
  revised 21.10.2018, Zace Services.
