# Selection

Choose each geology unit's value of a parameter, and record the choice where a checker reads it: in the judgments file, with the source it comes from, the method that gives it and your reason. `ht.stats.select()` computes the value, and shows it against what the other sources gave.

```python
--8<-- "selection.py"
```

``` { .text .no-copy }
--8<-- "selection.txt"
```

![Undrained shear strength of the example project's Alluvium by test type, with the selected characteristic value drawn as a dashed line over the UU tests' depths](../img/generated/selection.png){ width="480" }

## From sources compared to a selected value

[`compare_sources()`](../parameters/04-drained-shear-strength-soil.md#comparing-the-sources) puts a parameter's sources side by side, and [`representative()`](representative-values.md) computes a cautious value from one of them. The choice between them, which source and which view, is yours. The selection is that choice written down: hangtu never picks a source, a method or a side for you, and a unit the selection doesn't list is an error, not a value filled in from somewhere.

`select()` takes the same sources as `compare_sources()` (DataFrames of values, a `MohrCoulombFit`, a `ShearBoxConversion`) and the parameter, runs the comparison once, then computes each unit's value from the source its entry names.

## The selection in the judgments file

```yaml
selection:
  effective_friction_angle:          # the parameter: a numeric registry column
    values:
      Terrace:
        source: "Mohr-Coulomb fit (CDM, CD)"
        method: fitted
        reason: "the triaxial fit over all 15 stages"
      Alluvium:
        method: none
        reason: "soft clay: designed undrained, with s_u"
  undrained_shear_strength:
    units: {value: psf}              # only for an entry that gives a value
    values:
      Alluvium:
        source: "lab, UU"
        method: characteristic
        estimate: mean
        side: low
        distribution: lognormal
        reason: "slip surfaces through the whole layer: a cautious estimate of the mean"
      Fill:
        method: value
        value: 1000
        reason: "from the 2019 report for the adjacent site; no tests here"
```

It is keyed by parameter, then by geology unit. Each entry has a `method` and a `reason`, both required:

| `method` | Fields | What hangtu does |
|---|---|---|
| `characteristic`, `percentile`, `standard_deviations` | `source`, and `representative()`'s inputs for that method, by the same names (`estimate`, `side`, `distribution`, `trend`, `coefficient_of_variation`, `scale_of_fluctuation`, `failure_length`, `sensitivity_index`, `percentile`, `standard_deviations`) | calls [`representative()`](representative-values.md) on that source's rows in the unit |
| `fitted` | `source`, a fit | takes the fit's value in the unit as fitted |
| `value` | `value`, with the parameter's `units:` | takes your value, converted to the comparison's unit |
| `none` | — | lists the unit with no value, on purpose |

- **`source`** is a `parameter_source` label exactly as `compare_sources()` prints it: `"lab, UU"`, `"Mohr-Coulomb fit (CDM, CD)"`, a correlation's name. A label that isn't in the comparison is an error listing those with rows in the unit.
- **Every unit the sources have needs an entry.** Give `method: none` with a reason for a unit you don't design with. A `value` (or `none`) entry may name a unit no source has, such as a unit with no tests; a computed method for one is an error.
- **The key is the geology unit only.** There is no `project:` value, and no depth range: a `trend: depth` covers a value that changes with depth inside a unit. One value per unit is one design case; for a second (a fractile for a footing beside a mean for a slope in the same unit), use a second judgments file passed as `judgments=`, or `selection=`.
- **`representative()`'s rules hold unchanged:** every input a method needs is required, and none has a default. A refusal row reads `spt_refusal_upper_limit` from the same file, as `representative()` does.

`ht.judgments(path)` checks the selection when the file is opened, as far as it can without the data: an unknown method, a field the method doesn't take, a missing field, a `value` without `units:` or in a unit of the wrong kind. The error names the file, the parameter, the unit and the field. Whether a source exists in a unit, and whether a fit has one value there, are checked by `select()`.

## Where the selection comes from

As every judgment ([judgments](judgments.md)): `selection=` on the call, then `judgments=`, then the Project's file the sources carry, and otherwise an error that names the parameter and shows an entry to add. `selection=` is the whole selection of that parameter, in the file's shape, with a value given with its unit as text:

```python
ht.stats.select(
    tests,
    value="undrained_shear_strength",
    selection={
        "Alluvium": {"method": "value", "value": "500 psf", "reason": "cautious"},
    },
)
```

It replaces the file's selection of the parameter for every unit, with a warning when the file has one; it never merges unit by unit.

## The methods

- **A view** (`characteristic`, `percentile`, `standard_deviations`) is `representative()` on that source's rows in the unit, as passed, so the flags, bands and refusals reach it as they reach `fit()`. `result.representative("Alluvium")` gives that unit's `RepresentativeResult`, with every statistic behind the number. A fit made per sample (several values in the unit) gives its values to the view.
- **`fitted`** takes a fit's one value in the unit. A source of rows, or a fit with several values in the unit, is an error naming the methods that take it.
- **`value`** is converted to the comparison's unit (`display_units=`, else the first source's).
- **A method that gives no value** (fewer than 2 values, every row left out, a fit that failed) lists the unit with `no_value_reason` and a warning. It is never filled from another source.

## c′ and φ′ together

`select()` selects one parameter. To keep c′ and φ′ on one Mohr–Coulomb line, select both as `fitted` from the same fit, as the example does for the Terrace: the pair is then the fit's own. c′ and φ′ each selected by a view of their own (a characteristic c′ and a characteristic φ′) aren't a joint characteristic value: each is cautious on its own, and the pair together is more cautious than either, by an amount neither number shows. hangtu doesn't compute a joint value.

## Against the other sources

`result.positions()` places each unit's selected value among each other source's values in the unit, as `compare_sources()` places a fit: `position` below, within or above their range and, within it and from 4 values, `percentile_rank`. Against a fit's one value it gives the `difference` (selected − fit) instead. A selected line with depth has no single value to place, so its positions are blank, with the reason. It places the value; it tests nothing.

In the example, the Terrace's φ′ of 35.3° from the triaxial fit is below the range of both SPT correlations and 1.3° above the converted shear box; the Alluvium's characteristic s_u of 551 psf is within each other test's values, at the 13th to the 47th percentile.

## What the result records

`print(result)` gives the table, then the positions, then one note per unit saying what was chosen, from what and why. `result.to_frame()` has one row per unit: `parameter_source`, `selection_method`, the `value` (or a line's `line_intercept`, `line_slope`, ends and values at its ends), `count`, `selection_reason` and `no_value_reason`. `result.comparison` is the `SourceComparison`, and `result.to_dict()` holds all of it, the comparison and each `representative()` result included. `result.judgments` records the selection used, each unit's entry and where it came from (the file's path and SHA-256, or the argument), with the judgments the methods read.

`result.design_lines()` gives each unit's selected line in the frame P01's `design_lines=` draws, labeled `"Alluvium: selected, characteristic"`: a view's own line, a fitted value over its points' depths, a given value over the depths of every source's rows in the unit. `result.profile(geology_unit=...)` draws the unit's sources, as the comparison does, with that line, against depth.

## Unit weight

Unit weight already has its selection: the [`unit_weight` judgment](judgments.md#the-judgments-file), a value with its reason per unit, which `vertical_stress()` reads. `select()` works on `bulk_unit_weight` too, to compare a value with the tests, but the `unit_weight` judgment is the one analyses read.

hangtu stops at the selected value. Partial factors and design values are the design's.

## See also

- [`ht.stats.select`](../reference/stats.md#hangtu.stats.select), [`ht.stats.SelectionResult`](../reference/stats.md#hangtu.stats.SelectionResult)
- [Representative values](representative-values.md): the views a selection computes
- [Drained shear strength](../parameters/04-drained-shear-strength-soil.md#selecting-a-value), [undrained shear strength](../parameters/05-undrained-shear-strength.md#selecting-a-value): the sources compared and selected
