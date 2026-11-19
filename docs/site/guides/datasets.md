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
| `p.oedometer()` | Oedometer increment: the stress at its end, the void ratio at its start and end, the lab's m_v and c_v, and whether it is on the loading, unloading or reloading branch; a swelling test with no increments is one row | [Consolidation curve](../plots/consolidation-curve.md) with `ht.analysis.oedometer_fit()`, [property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.triaxial()` | Triaxial stage at failure, effective stress (CU, CD) or total stress (UU): cell pressure, deviator stress and pore pressure, the principal stresses from them, the mode of failure, and the lab's own c′ and φ′ | [Failure envelope](../plots/failure-envelope.md), [Hoek–Brown envelope](../plots/hoek-brown-envelope.md), [property profile](../plots/profile.md), [property by geology unit](../plots/geology-unit-comparison.md) |
| `p.triaxial_readings()` | Reading during a triaxial stage's shearing (q, Δu or ε_v against axial strain), from the file's own groups through the readings map, with its stage's values | [Triaxial shearing](../plots/triaxial-shearing.md) |
| `p.shear_box_readings()` | Reading during a shear box stage (τ or vertical displacement against horizontal displacement), through the readings map | None yet |

Each comes in the project's display units, or in `display_units="SI"` or `"US"` if you ask.

## Depth, elevation and geology

- **Depth** is the depth of the test. An SPT is placed at the middle of its test drive; `depth_basis` says how each depth was found.
- **Elevation** is the hole's ground level minus the depth.
- **Geology unit** comes from the geology log at that depth. `p.set_geology_map("strata.csv")` maps the file's geology codes to the units you report on, with their order and colors.

## Readings during a test

AGS has no group for the readings taken while a specimen is sheared, so a file that carries them puts them in groups of its own, named by whoever wrote it. Tell hangtu which groups those are with a readings map, a CSV with one row per heading it reads:

```
group,dataset,heading,column
XTDS,triaxial_readings,XTDS_TESN,test_stage
XTDS,triaxial_readings,XTDS_STRN,axial_strain
XTDS,triaxial_readings,XTDS_DEVF,deviator_stress
```

`p.set_readings_map("readings_map.csv")` checks it against the file and stores it with the project. Each group must be a user-defined group whose `DICT` entry gives it a triaxial or shear box test as its parent (`TREG` or `TRET`, `TRIG` or `TRIT`, `SHBG` or `SHBT`), and each mapped heading a unit hangtu converted on ingest that fits the column. Then `p.triaxial_readings()` and `p.shear_box_readings()` give one row per reading, with only the values its group gives, in the file's order. The example project's map is `ht.examples.path("readings_map.csv")`.

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
