# Judgments and vertical stress

Keep a project's unit weights and water levels in one file, with their units and reasons, and compute the vertical stress at each test from it.

```python
--8<-- "judgments.py"
```

``` { .text .no-copy }
--8<-- "judgments.txt"
```

![Effective vertical stress against depth, colored by geology unit](../img/generated/judgments.png){ width="440" }

## Judgments have no defaults

A unit weight or a water level is the engineer's call, not a property of the data, so hangtu never supplies one. Each analysis that needs a judgment takes it, in order, from:

1. the argument on the call, such as `unit_weight="19 kN/m3"`;
2. `judgments=`, a judgments file (`ht.judgments(path)` or the path itself);
3. the project's judgments file, set with `p.set_judgments(path)` and carried by every dataset in `df.attrs["judgments_file"]`;

and otherwise stops with an error that names the judgment and the ways to give it. An argument replaces that whole judgment, with a warning when the file has it too; the other judgments still come from the file.

Merging or concatenating DataFrames drops `df.attrs`, and with it the project's file. Pass `judgments=p.judgments` then.

## The judgments file

```yaml
unit_weight:
  by: geology_unit
  units: {bulk_unit_weight: pcf, saturated_unit_weight: pcf}
  project: {bulk_unit_weight: 120, reason: "median of all LDEN tests, n=41"}
  values:
    Fill: {bulk_unit_weight: 120, reason: "compacted sandy lean clay fill, typical"}
    Alluvium: {bulk_unit_weight: 110, saturated_unit_weight: 112}
water_level:
  units: {depth: ft}
  by_hole:
    B-1: {depth: 8.0, reason: "encountered while drilling, 2026-08-10"}
```

- **`unit_weight`** entries take `bulk_unit_weight` and, optionally, `saturated_unit_weight`, used below the water level. `by:` names the stratigraphy column the keys match: `geology_unit`, or another such as `uscs_symbol` on a stratigraphy you have edited.
- **`water_level`** entries take one of `depth` or `elevation`, by hole. A negative depth is water above ground, a flooded load case: its weight is added to the total stress, with a warning.
- **`units:`** gives the unit of every field, as in `df.attrs["units"]`. Nothing is assumed.
- **`project:`** is optional and needs a `reason`. It is used for every unit or hole the keyed entries don't list, with a warning that names them. Without it, a unit or hole with no value is an error that lists them all.
- **Keys** match exactly, by case too. An entry for a unit or hole that isn't in the stratigraphy warns, since it is likely a typo.
- **Quote** a reason with a comma in it, and a key YAML would read as something else (`"yes"`, `"1"`).

`ht.judgments(path)` checks the file when it is opened, and an error names the file, the judgment and the entry. Printed, it lists every value with its unit and reason. Analyses read the file again on each call, so an edit shows up in the next result.

## Plasticity index by geology unit

Some correlations read the plasticity index of the soil at each SPT, which is rarely tested at that depth. PI is then a judgment, one value per geology unit, in the same file:

```yaml
plasticity_index:
  by: geology_unit
  units: {plasticity_index: "%"}
  values:
    Alluvium: {plasticity_index: 28, reason: "median of 9 Atterberg tests"}
```

`ht.analysis.add_judgment(spt, "plasticity_index")` puts it on the rows as a `plasticity_index` column, which a correlation then reads like any input. The value comes from, first that applies:

1. `value=` on the call: one number, or `{"Alluvium": 28}` by geology unit;
2. a `plasticity_index` column already on the rows, where filled. Its blanks are filled from the file, with a warning counting the rows where the column and the file differ;
3. the judgments file;
4. otherwise an error naming the judgment.

The nearest Atterberg test is never used in its place. To see what the tests say before you choose, `ht.stats.describe(p.atterberg(), value="plasticity_index", by="geology_unit")` gives each geology unit's count, mean, standard deviation, median, minimum, maximum and percentiles, and counts the non-plastic specimens it leaves out.

## The significance level

`ht.stats.compare()` and `ht.stats.compare_groups()` test at a significance level α, which is a judgment like any other: there is no default, because 0.05 is a convention rather than a property of the data. It is one value for the whole project, with no keys, and its reason is required:

```yaml
significance_level:
  project: {significance_level: 0.05, reason: "the usual convention"}
```

It must lie strictly between 0 and 1, and warns outside 0.001 to 0.2. `values:` or `by:` under it is an error. `significance_level=` on a call replaces it, with a warning. It sets the note's conclusions and the intervals' level, 1 − α; the p-values don't depend on it. See [comparing groups](statistics.md#comparing-groups).

## The log

Vertical stress is integrated through each hole's log, `p.stratigraphy()` or a table in the shape of `ht.template("stratigraphy")`. It is always passed explicitly, because it's data you may have edited, such as layers reclassified by USCS.

The log must run from 0 down to the hole's deepest test, with no gap or overlap of more than 0.01 m. Otherwise the call stops, listing every hole and depth range. The example site's B-4 has a gap planted in its log, which `p.qc()` reports as G002, and `vertical_stress()` stops on it:

``` { .text .no-copy }
The stratigraphy can't be integrated down to the deepest test in this hole:
  B-4: a gap from 9 ft to 10 ft
Each hole's log must run from 0 down to its deepest test, with no gap or overlap of more than 0.033 ft. p.qc() lists the gaps and overlaps in a project's file (G002, G003). Fix the layers in the stratigraphy table and call again.
```

A test below the base of the log takes the last layer down to it, with a warning.

## What the result records

`df.attrs["judgments"]` holds, for each judgment, where it came from (the argument, or the file's path and SHA-256), the column its keys match, and only the values the call used, with their units and reasons. `df.attrs["vertical_stress"]` records the pore pressure method (hydrostatic) and the unit weight of water used.

The unit weight of water is the setting `ht.settings.water_unit_weight`, 9.81 kN/m³ by default and converted as needed (62.45 pcf). Set `"62.4 pcf"`, or a seawater value, where the design uses one.

## See also

- [`ht.judgments`](../reference/data.md#hangtu.judgments), [`ht.analysis.vertical_stress`](../reference/analysis.md#hangtu.analysis.vertical_stress)
- [Unit weight and vertical stress](../parameters/01-unit-weight-and-vertical-stress.md): the equations, typical values and pitfalls
- [Datasets](datasets.md), [property profile](../plots/profile.md)
