# Datasets

A dataset is a table with one row per test, with its depth, elevation and geology unit joined on, ready for the plots.

```python
--8<-- "datasets.py"
```

``` { .text .no-copy }
--8<-- "datasets.txt"
```

## The datasets

| Dataset | One row per | Plots it feeds |
|---|---|---|
| `p.spt()` | SPT test | [SPT profile](../plots/spt-profile.md), [SPT histogram](../plots/spt-histogram.md) |
| `p.atterberg()` | Atterberg specimen, with its water content | [Property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.grain_size()` | Point on a grading curve | |
| `p.permeability()` | Permeability test, lab or field | [Property profile](../plots/profile.md) |

Each comes in the project's display units, or in `display_units="SI"` or `"US"` if you ask.

## Depth, elevation and geology

- **Depth** is the depth of the test. An SPT is placed at the middle of its test drive; `depth_basis` says how each depth was found.
- **Elevation** is the hole's ground level minus the depth.
- **Geology unit** comes from the geology log at that depth. `p.set_geology_map("strata.csv")` maps the file's geology codes to the units you report on, with their order and colors.

## Filters

Every dataset takes the same filters:

- `holes=["B-1", "B-2"]` and `geology=["Alluvium"]`;
- `depth=(0, 30)` or `elevation=(10, 40)`, in the dataset's units, or with units: `depth=("0 ft", "30 ft")`;
- `where={"soil_class": "coarse"}` for any column;
- `contains="sand"` to search the geology descriptions.

A record with a blank required field is left out, with a warning that counts them; `include_incomplete=True` keeps it.

## See also

- [`ht.Project`](../reference/project.md)
- [AGS files and data checks](ags-and-qc.md)
