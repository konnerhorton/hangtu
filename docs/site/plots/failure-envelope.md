# Failure envelope

Triaxial stages at failure with the Mohr-Coulomb envelope fitted to them: Mohr circles, or points in s′–t or p′–q, with c′ and φ′ beside the lab's own values.

```python
--8<-- "failure-envelope.py"
```

![Mohr circles of the example project's triaxial stages, with one envelope per geology unit](../img/generated/failure-envelope.png){ width="560" }

## What it shows

One circle per stage at failure, centered at s′ = (σ′1 + σ′3)/2 with radius t = (σ′1 − σ′3)/2, and the envelope τ = c′ + σ′ tan φ′ that `ht.analysis.mohr_coulomb_fit()` fits to them. Here each geology unit has its own fit: the Alluvium's CU tests and the Terrace's multistage CD test.

The envelope is solid between the points where it touches the circles and dashed beyond. c′ is where the dashed line meets σ′ = 0, outside the stresses tested, so read it as an intercept, not a measured strength. The box gives each fit's c′, φ′, the number of stages, R², the range of σ′n it holds over, and the lab's own c′ and φ′ where the file reports them. hangtu doesn't judge the difference between the two.

Rows without the stresses a fit needs, such as UU tests in an effective-stress fit, are left out and counted in the footnote. A group whose points can't give φ′ (too few, all at one mean stress, or a slope no angle fits) is drawn without an envelope, and the box says why.

## Three spaces

`space=` draws the same points and the same fit three ways:

| `space=` | Points | Envelope | Intercept |
|---|---|---|---|
| `"mohr"` (default) | circles in σ′–τ | τ = c′ + σ′ tan φ′ | c′ |
| `"s_t"` | (s′, t) | t = a + s′ tan α, with sin φ′ = tan α | a = c′ cos φ′ |
| `"p_q"` | (p′, q), triaxial compression | q = q₀ + M p′, M = 6 sin φ′ / (3 − sin φ′) | q₀ = 6 c′ cos φ′ / (3 − sin φ′) |

The fit is always made in s′–t and transformed, never refitted, so the three views give one c′ and φ′. The intercept on each y axis differs: only the Mohr view's is c′. Every space has equal aspect, so circles are circles and slopes read true.

## Multistage stages

A group with multistage stages gets two fits, with and without them; the other one is drawn dotted. A later stage starts from a specimen already sheared, so compare the two before using either. `multistage=False` makes the fit without them the main one.

## Common options

| Argument | Does |
|---|---|
| `space=` | `"mohr"`, `"s_t"` or `"p_q"` |
| `group_by=` | One fit per group, such as `"geology_unit"` or `"sample_reference"` |
| `cohesion=0` | Fit the line through the origin; never done unless asked |
| `stress="total"` | Fit the total stresses, as for UU tests |
| `paths="idealized_drained"` | In s′–t or p′–q, each stage's path as a drained test at constant cell pressure would take it; drained tests only |
| `envelopes=` | Your own envelopes, `[(cohesion, friction_angle, label)]`, drawn in the same space |
| `pool=` | Fit rows with different failure criteria together, on purpose |
| `fit=False` | The circles or points only |

For the numbers without a figure:

```python
fit = ht.analysis.mohr_coulomb_fit(stages, group_by="geology_unit")
fit.to_frame()
```

## See also

- [`ht.plot.failure_envelope`](../reference/plot.md#hangtu.plot.failure_envelope), [`ht.analysis.mohr_coulomb_fit`](../reference/analysis.md#hangtu.analysis.mohr_coulomb_fit)
- [Drained shear strength](../parameters/04-drained-shear-strength-soil.md), the parameter page
- [Datasets](../guides/datasets.md): `p.triaxial()`
