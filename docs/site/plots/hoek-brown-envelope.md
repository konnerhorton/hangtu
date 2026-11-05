# Hoek–Brown envelope

Intact rock UCS and triaxial tests in σ1–σ3, with the Hoek–Brown curves fitted to them, free and with σci fixed, and σci and mi beside the lab's own values.

```python
--8<-- "hoek-brown-envelope.py"
```

![UCS and triaxial tests on the example project's sandstone, with the free and fixed Hoek–Brown curves](../img/generated/hoek-brown-envelope.png){ width="560" }

``` { .text .no-copy }
--8<-- "hoek-brown-envelope.txt"
```

## What it shows

One point per test, or per stage of a multistage test, at its principal stresses at failure. A UCS test has σ3 = 0, so it sits on the σ1 axis, where it can be read against the curve's intercept, σci. Single-stage tests are circles and the stages of a multistage test squares.

The curves are those `ht.analysis.hoek_brown_fit()` fits to the points, the intact criterion σ1 = σ3 + σci (mi σ3/σci + 1)^0.5 (Hoek 2007, ch. 11, eq. 5). The fit is Hoek's own regression: (σ1 − σ3)² against σ3 is a straight line with intercept σci² and slope mi σci (eqs. 6–8), fitted by least squares, UCS and triaxial points together.

- **The free fit** finds σci and mi together. It is solid over the σ3 its points cover and dashed beyond, so σ1 past the last test reads as extrapolation.
- **The fit with σci fixed** finds mi only, with σci given: drawn thin and dotted, so the two compare. σci is a judgment, so it comes from `fixed_intact_compressive_strength=` (`"61 MPa"`, or a value per group) or the project's [judgments file](../guides/judgments.md), never from a rule. Without either, only the free curve is drawn and the box says so.

The box gives each group's free σci, mi, number of points, R² and σ3 range; the fixed σci with where it came from, and its mi; the UCS tests' count and mean, the check of the free σci against the tests that measure it; and the lab's own σci and mi where the rows have them. hangtu doesn't judge the differences.

## Points left out

The criterion holds for shear failures only. Tests that split axially or failed along a defect are left out first (Hoek 2023, ch. 3, p. 6). `failure_mode` is the lab's own words, so hangtu doesn't guess which ones mean shear: when the column has values, name the shear ones with `failure_modes=`, as written. Rows with other modes stay on the figure, open, with their mode and count in the legend and the footnote.

## Multistage tests

With multistage stages in a group, the fit is made with and without them; the box gives both. The free curve drawn is the one with them unless `multistage=False`, which draws the stages open and fits the single-stage tests only. Later stages of a multistage test can give a lower σ1 than a fresh specimen would, which pulls mi down; compare the two fits before choosing.

## Range and quality

Hoek (2007, ch. 11, p. 2) gives the criterion for 0 < σ3 < 0.5 σci, from at least five well-spaced points. Points beyond 0.5 σci are kept and fitted, with a warning and a count in the footnote: to fit without them, filter the rows on σ3 and plot again. Fewer than five points and an R² below 0.9 (Hoek 2007, p. 4) are noted in the footnote too.

The fit is in total stress by default, since rock tests rarely measure pore pressure, which assumes there is none in the specimen. `stress="effective"` fits the effective stresses where the rows have them.

## Rock tests in a CSV

AGS 4 has no group for rock triaxial tests, so enter them in `ht.template("triaxial")`, one row per test or stage: the cell pressure as `cell_pressure` (0 for a UCS test) and σ1 − σ3 as `deviator_stress_at_failure`. If the lab reports σ1, subtract the cell pressure in your spreadsheet first. Leave the soil-only columns blank, and declare every stress column's unit when you read it, blank ones included, as in the example. See [templates](../guides/templates.md).

## Units

The figure keeps the frame's unit by default, MPa here. `display_units="SI"` gives kPa and `"US"` psf; for MPa or psi:

```python
with ht.settings.override(display_overrides={"stress": "psi"}):
    fig, ax, fit = ht.plot.hoek_brown_envelope(rock, ..., display_units="US")
```

mi is the same in any unit: the fit converts σ1, σ3 and σci to one unit first.

## Common options

| Argument | Does |
|---|---|
| `group_by=` | One set of curves per group, such as `"geology_unit"` or a loading direction column of your own |
| `failure_modes=` | The modes to fit, as written; `None` in the list fits rows with a blank mode |
| `fixed_intact_compressive_strength=` | σci for the fixed fit, `"61 MPa"` or `{"Sandstone": "61 MPa"}`, else the judgments file |
| `multistage=False` | Fit and draw the single-stage tests only; the stages of multistage tests are drawn open |
| `envelopes=` | Your own curves, `[(σci, mi, label)]`, σci in the plot's units |
| `pool="failure_criterion"` | Fit rows with different failure criteria together, on purpose |
| `fit=False` | The points only |

For the numbers without a figure:

```python
fit = ht.analysis.hoek_brown_fit(rock, group_by="geology_unit", failure_modes=["Shear"])
fit.to_frame()
```

## See also

- [`ht.plot.hoek_brown_envelope`](../reference/plot.md#hangtu.plot.hoek_brown_envelope), [`ht.analysis.hoek_brown_fit`](../reference/analysis.md#hangtu.analysis.hoek_brown_fit)
- [Hoek–Brown constant mi](../parameters/15-hoek-brown-constant.md): the tests, typical values and pitfalls
- [Failure envelope](failure-envelope.md), for soil triaxial stages as Mohr circles
- [Templates](../guides/templates.md): the `triaxial` template
