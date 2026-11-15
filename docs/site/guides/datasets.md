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
| `p.atterberg()` | Atterberg specimen, with its water content | [Water content profile](../plots/water-content-profile.md), [plasticity chart](../plots/plasticity-chart.md), [property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.grain_size()` | Point on a grading curve | [Grain size distribution](../plots/grain-size.md) |
| `p.permeability()` | Permeability test, lab or field | [Property profile](../plots/profile.md) |
| `p.density()` | Density test, lab or field, as bulk and dry unit weights with the specimen's own water content and its sample's particle density | [Property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.particle_density()` | Particle density test, with assumed values (`#2.65`) flagged | [Property by geology unit](../plots/geology-unit-comparison.md) |
| `p.undrained_strength()` | Undrained strength result, test by test: UU, unconfined compression, laboratory and field vane, hand penetrometer and fall cone, with s_u, the remolded s_u and sensitivity where the test gives them | [Property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.shear_box()` | Shear box or ring shear stage: the normal stresses, peak and residual shear stress, displacements and the lab's own fit | [Shear box envelope](../plots/shear-box-envelope.md), [property profile](../plots/profile.md) |
| `p.oedometer()` | Oedometer increment: the stress at its end, the void ratio at its start and end, the lab's m_v and c_v, and whether it is on the loading, unloading or reloading branch; a swelling test with no increments is one row | [Property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.triaxial()` | Triaxial stage at failure, effective stress (CU, CD) or total stress (UU): cell pressure, deviator stress and pore pressure, the principal stresses from them, the mode of failure, and the lab's own c′ and φ′ | [Failure envelope](../plots/failure-envelope.md), [Hoek–Brown envelope](../plots/hoek-brown-envelope.md), [property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |

Each comes in the project's display units, or in `display_units="SI"` or `"US"` if you ask.

## Depth, elevation and geology

- **Depth** is the depth of the test. An SPT is placed at the middle of its test drive; `depth_basis` says how each depth was found.
- **Elevation** is the hole's ground level minus the depth.
- **Geology unit** comes from the geology log at that depth. `p.set_geology_map("strata.csv")` maps the file's geology codes to the units you report on, with their order and colors.

## Gradings reported as percentages

`p.grain_size_summary()` gives one row per grading, and `p.index_properties()` classifies each sample from its grading. A grading usually comes from its curve (`GRAT`), but some labs report only the percentages of gravel, sand and fines (`GRAG`) with no curve. hangtu reads those too, once you say which fraction system the lab used:

```python
p.settings.grag_fraction_system = "astm_uscs"   # or "aashto", "iso14688"
```

The AGS dictionary describes these columns with ISO 14688 sizes (2 mm, 0.063 mm), but many labs put ASTM D2487 fractions (4.75 mm, 0.075 mm) in them, so hangtu doesn't guess. Until the setting is given, the rows are kept with blank fractions and a warning. It is read each time a dataset is built, so changing it needs no rereading of the file; `from_ags(..., grag_fraction_system="astm_uscs")` sets it at the start.

A reported grading has no D-values, and its Cu and Cc are the lab's. A fraction is filled only where the lab's size ranges make it up exactly: ASTM percentages give the AASHTO fines but not its sand split, and ISO percentages give no USCS fraction, so no USCS symbol, but they can give the clay activity. Nothing is interpolated. A blank cobbles column counts as 0 when the other percentages add up to 100 (within 2 points). The `grading_source` column says `"curve"` or `"reported"`; a sample with a curve is read from the curve.

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
