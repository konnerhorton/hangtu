# Triaxial shearing

Each triaxial stage's readings during shearing: deviator stress against axial strain, or the measured stress path in s′–t or p′–q with the envelope fitted to the same stages. It's the check on the failure points that the [failure envelope](failure-envelope.md) fits.

```python
--8<-- "triaxial-shearing.py"
```

![Deviator stress and excess pore pressure against axial strain for the example project's CU stages](../img/generated/triaxial-shearing.png){ width="560" }

## Where the readings come from

AGS files carry only the values at failure, so the readings come from a CSV that you prepare from the lab's export, one row per strain step, laid out like `ht.template("triaxial_readings")`. The stage's values (`specimen_id`, `test_stage`, `test_type`, `cell_pressure`, `back_pressure`) repeat on each of its rows, and the readings are `axial_strain`, `deviator_stress` (as the lab corrected it), `excess_pore_pressure` (Δu from the start of shearing) and `volumetric_strain` (positive in compression). The example file's readings are synthetic, made to end at the example project's failure values.

## The failure reading

Each stage's failure reading is marked with a dot, the same reading in every view and in the fit. There is no default way of picking it, because on an undrained curve the two usual criteria pick different readings:

- `failure_criterion="max_deviator_stress"`: the reading with the largest q;
- `failure_criterion="max_stress_ratio"`: the reading with the largest σ′1/σ′3;
- without either, the reading the lab marked in `reported_failure_reading`.

`ht.analysis.triaxial_failure_from_readings()` returns those readings as one row per stage, in `p.triaxial()`'s shape, so `ht.plot.failure_envelope()` and `ht.analysis.mohr_coulomb_fit()` take them as they are. To compare the readings with an AGS file, call it beside `p.triaxial()`.

## Three spaces

| `space=` | Draws |
|---|---|
| `"stress_strain"` (default) | q against axial strain; `second_axis="excess_pore_pressure"` or `"volumetric_strain"` adds a dashed line on a second y axis |
| `"s_t"` | the path in s′ = (σ′1 + σ′3)/2, t = q/2, with the fitted envelope |
| `"p_q"` | the path in p′ = (σ′1 + 2σ′3)/3, q, with the same envelope transformed |

At each reading σ′3 = cell pressure − (back pressure + Δu); in a drained stage a blank Δu is 0. In s′–t a drained path at constant cell pressure rises at slope 1, and an undrained path bends left as pore pressure rises (contractive) or right as it falls (dilative).

```python
--8<-- "triaxial-shearing-paths.py"
```

![Measured stress paths in s′–t for the example project, with one envelope per geology unit](../img/generated/triaxial-shearing-paths.png){ width="560" }

Stages a path can't show, such as UU tests in effective stress or extension tests, are left out of the path and counted in the footnote. The fit's options (`group_by=`, `cohesion=`, `multistage=`, `pool=`, `envelopes=`, `fit=False`) work as on the [failure envelope](failure-envelope.md).

## See also

- [`ht.plot.triaxial_shearing`](../reference/plot.md#hangtu.plot.triaxial_shearing), [`ht.analysis.triaxial_failure_from_readings`](../reference/analysis.md#hangtu.analysis.triaxial_failure_from_readings)
- [Failure envelope](failure-envelope.md)
- [Drained shear strength](../parameters/04-drained-shear-strength-soil.md), the parameter page
- [Templates and columns](../guides/templates.md)
