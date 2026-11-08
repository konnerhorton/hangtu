# Judgments: the file, how a value resolves, and each judgment

| | |
|---|---|
| **Status** | Living spec. The file and `vertical_stress()` (M13 a); `plasticity_index` (M13 b2), `specific_gravity` (M14 b), `significance_level` (M15 d), `fixed_intact_compressive_strength` (M17 c), `spt_refusal_upper_limit` (M18 a), `critical_state_friction_angle` (M18 d) and `selection` (M18 e) built |
| **Parent** | SPEC §4, "Judgment inputs": judgments have no defaults, the resolution order, keys and the project-wide value, recording, and the two optional judgments |
| **Related** | [`m13a-judgments.md`](../work/m13a-judgments.md) (the file, resolution, `vertical_stress()`), [`m13b2-spt-strength-history.md`](../work/m13b2-spt-strength-history.md) (decision 11), [`m14b-phase-relations.md`](../work/m14b-phase-relations.md) (decision 4), [`m15d-compare.md`](../work/m15d-compare.md) (decision 8), [`m17c-hoek-brown-fit.md`](../work/m17c-hoek-brown-fit.md) (decision 8), [`m18a-refusals.md`](../work/m18a-refusals.md) (decisions 1–3), [`m18d-sources-compared.md`](../work/m18d-sources-compared.md) (decisions 5, 17), [`m18e-selection.md`](../work/m18e-selection.md) (decisions 6–12). The code: `src/hangtu/_judgments.py` (`KINDS`, the checks) and `src/hangtu/analysis/_judgment_values.py` (lookup and record). The user's guide: [`docs/site/guides/judgments.md`](../site/guides/judgments.md) |

Update this file in the same commit as any change to the file format, a judgment's keys or checks, or how a value
resolves, and SPEC §4 if the change alters a rule there. A new judgment gets an entry in §5.

## 1. The file
- **One YAML file per project,** usually `judgments.yaml` beside the project. Top-level keys are judgment names; any
  other key is an error listing the known ones. An empty file is valid and holds no judgments.
- **`ht.judgments(path)` → `Judgments`** reads and checks the whole file at once, so a mistake shows where it is
  opened. It holds the path, not the values: each analysis re-reads the file, so an edit shows in the next call,
  and records the SHA-256 of the bytes it read. `repr()` lists each judgment, its key, and its values with units
  and reasons. `judgments=` on an analysis takes a `Judgments` or a path.
- **`p.set_judgments(path)`** stores the path (never the content) in the project database, as the geology map is
  stored: a path inside the database's folder is stored relative to it, so the folder can move whole; setting it
  reads the file once, so a bad file errors there; `None` removes it, and a rebuild with `overwrite=True` starts
  without one. `p.judgments` is a `Judgments`, or None; a file that has gone missing is an error naming the path
  and `p.set_judgments`. Every dataset carries the resolved path in `df.attrs["judgments_file"]`.
- **Sections** of a judgment: `by:` (the column its keys match), `units:`, `project:` (one value for every key)
  and the keyed entries, under `values:` or, for `water_level`, `by_hole:`. Which sections a judgment takes is
  in §5.
- **`units:`** gives a unit for every field used, in hangtu's aliases (`kN/m3`, `pcf`, `m`, `ft`, `MPa`, `deg`),
  checked against the field's quantity kind. It is required except for the pure numbers (`specific_gravity`,
  `significance_level`, `spt_refusal_upper_limit`, and a selection of a count or dimensionless column), where it
  is an error: a `%` would pass the dimension check and read the value as a ratio, 100-fold off.
- **Values** are finite numbers, positive or in range as §5 says. A field may be `none` only where §5 allows it.
- **Keys** (`Fill`, `BH01`) are text matched exactly and by case, like the geology map. A key YAML reads as
  another type (`1`, `yes`, `null`) is an error saying to quote it.
- **Errors** name the file, the judgment and the entry ("judgments.yaml, unit_weight, values.Fill: …") and say
  what to write. A field that isn't one, with an empty value, is likely a comma inside an unquoted reason, and the
  error says to quote it.
- **Plausibility warnings** where a range has been checked: `specific_gravity` outside 2.0–3.2 (QC B003's particle
  density range), `significance_level` outside 0.001–0.2. None for φ′cv, because no range has been verified.

## 2. How a value resolves
1. **The argument** named after the judgment (`unit_weight=`, `significance_level=`, …; `add_judgment()`'s is
   `value=`). It replaces the whole judgment, never merging key by key, with a warning when the file has it too.
   Other judgments of the same call still come from the file.
2. **`judgments=`,** a `Judgments` or a path. When it differs from the Project's file the input carries, it is
   used, with a warning.
3. **The Project's file** the input carries: `df.attrs["judgments_file"]` on a dataset, or, on a derived result,
   the file its input carried (the shear box fit keeps it for `friction_angle_from_shear_box()`; the sources keep
   it for `select()` and `mohr_coulomb_set()`).
4. **An error** naming the judgment, what it is keyed by and both ways to set it, with an example entry. When the
   input carries no file, it adds that merge and concat drop `df.attrs`, so pass `judgments=p.judgments`.

Two exceptions to step 4, where absence means something:
- **`spt_refusal_upper_limit`:** without it, `fit()` keeps refusals right-censored, the test's result, and notes
  that the tail above them is the distribution's.
- **`fixed_intact_compressive_strength`:** without it, `hoek_brown_fit()` makes its free fit, which is the result,
  and the fit with σci fixed is missing with the reason "no σci given".

A judgment's checker may skip the lookup when nothing needs it: `phase_relations()` reads `specific_gravity` only
for rows with no particle density, and warns that `specific_gravity=` isn't used when every row has one;
`friction_angle_from_shear_box()` and `mohr_coulomb_set()` read φ′cv only for the groups or units that need it.

There is no session level (`ht.settings`): a judgment belongs to a project, and a session value would follow the
user to the next one.

## 3. Keys and the project-wide value
- **Each judgment declares its key** (§5): a column given in `by:` (`geology_unit`, `uscs_symbol`, or another
  column of the rows or stratigraphy), a fixed column (`geology_unit`, `loca_id`), or none (`significance_level`).
  A fixed `by:` may be written, as itself, or left out; another value is an error.
- **`by:` is required with keyed values** where the column isn't fixed.
- **A `project:` value**, where allowed, needs a `reason`. It fills every key the data needs and the keyed entries
  don't list, with one warning naming the keys ("unit_weight: the project value 19 kN/m3 is used for the geology
  units 'Made Ground', 'Peat' not listed (median LDEN of all units)."). A file with only a `project:` value uses it
  for every key, with a warning.
- **Without one, an unlisted key is an error** naming every key missing and saying to add them, or a `project:`
  entry with its reason. An argument mapping has no project value: a key it doesn't list is an error.
- **`project_only`** (`significance_level`): only `project:`, no keys, no `by:`.
- **`keyed_only`** (`critical_state_friction_angle`, `selection`): no `project:` value, because one value for
  every unit would be coarser than the judgment allows. An argument given as one number for several groups is an
  error for the same reason.
- **A keyed entry the data doesn't have** (a unit not in the stratigraphy, a hole not in its `loca_id`) warns, as
  it is likely a typo, where the reader sees the whole set of keys (`vertical_stress()`, `add_judgment()`). Readers
  that see only some of the project's rows (`phase_relations()`, `fit()`) don't warn.
- **`reason`** is required on a `project:` entry, on every entry of `fixed_intact_compressive_strength`,
  `critical_state_friction_angle` and `selection`, and optional elsewhere.
- **`none_allowed`** (`spt_refusal_upper_limit`): a field written `none` is a choice, recorded with its reason, not
  a missing value.

## 4. What a result records
- Every judgment used, with its source (`"argument"`, or the file's path and SHA-256), its key (`by`) and the keys
  used with their fields as written with units (`"18.5 kN/m3"`) and reasons, in `df.attrs["judgments"]` for a
  frame and `judgments` on a result object: `{name: {"source", "sha256", "by", "values": {key: {...}}}}`. A
  project value records the keys it was used for (`used_for`).
- Only the keys used are recorded. `significance_level` records its value, source and reason. A selection
  records each unit's entry and its source, merged with the sources' judgments and each `representative()`
  result's.
- A result built on others (`select()`, a model set) merges the judgments of its inputs, so the set records every
  judgment behind it.

## 5. The judgments
| Judgment | Key | `project:` | `units:` | Fields and checks | Absent |
|---|---|---|---|---|---|
| `unit_weight` | `by:` a stratigraphy column | optional | required | `bulk_unit_weight` (required), `saturated_unit_weight` (used below the water level); > 0 | error |
| `water_level` | `loca_id` (`by_hole:`) | optional | required | exactly one of `depth` or `elevation`; a negative depth is water above ground, allowed with a warning | error |
| `plasticity_index` | `by:` a column of the rows | optional | required (`"%"`) | `plasticity_index` ≥ 0 | error |
| `specific_gravity` | `by:` a column of the rows | optional | none | `specific_gravity` > 0; warns outside 2.0–3.2 | error, for the rows that need it |
| `significance_level` | none | required, the only section | none | `significance_level`, 0 < α < 1; warns outside 0.001–0.2 | error |
| `spt_refusal_upper_limit` | `geology_unit` | optional | none | `spt_n`, field N in blows per foot, > 0 or `none` | refusals stay right-censored |
| `fixed_intact_compressive_strength` | `by:` a `group_by` column of the fit | optional | required | `intact_compressive_strength` > 0; `reason` on every entry | no fixed fit, with a reason |
| `critical_state_friction_angle` | `geology_unit` | not allowed | required | `critical_state_friction_angle`, 0° < φ′cv < 90° in any angle unit; `reason` on every entry | error, for the groups or units that need it |
| `selection` | parameter, then `geology_unit` | not allowed | `{value: …}`, for `value` entries | `method` and `reason` on every entry; §5.9 | error |

### 5.1 `unit_weight`
Read by `ht.analysis.vertical_stress()`, matched on the stratigraphy's `by:` column. Above the water level a
layer's γ is `bulk_unit_weight`; below it, `saturated_unit_weight` where given, else `bulk_unit_weight`. A unit in
the log with no value and no project value is an error. The argument is a quantity string for every layer or a
mapping `{geology_unit: "19 kN/m3" | {"bulk_unit_weight": …, "saturated_unit_weight": …}}`, matched on
`geology_unit`. Unit weight's selection is this judgment: it is a value with a reason by unit already, so sheet 01
has no `selection` entry.

### 5.2 `water_level`
Read by `vertical_stress()`, by hole. A hole the entries don't list takes the project value with a warning, else is
an error naming the holes. A level in elevation is converted with the hole's `ground_level` from the rows. A level
above ground adds its water column to σv and warns, naming the holes and heights. The argument is P01's format: a
number in the rows' depth unit, a quantity string, a mapping by hole that lists every hole, or a frame `loca_id,
depth|elevation`.

### 5.3 `plasticity_index`
Put on the rows by `ht.analysis.add_judgment(df, "plasticity_index")`, for a correlation that reads PI at an SPT
(Stroud 1974). Order: `value=` (one number, or `{geology_unit: number}`) → a `plasticity_index` column already on
the rows, where filled, with its blanks filled from the file and one warning counting filled rows where the two
differ → the file → an error. `ht.stats.describe()` by geology unit shows each unit's tested PI to inform it.

### 5.4 `specific_gravity`
Read by `ht.analysis.phase_relations()` only for rows with no particle density: a row's measured ρs comes first,
then its assumed (`#`) ρs, which the lab used and a judgment never replaces, then this judgment.
`specific_gravity_source` names which. The keyed column must be on the rows (`p.density()` has `geology_unit` when
the project has a geology map). Inform it from measured values only.

### 5.5 `significance_level`
Read by `ht.stats.compare()` and `compare_groups()`, which test at α and give intervals at 1 − α. The confidence
level is not set on its own, so the note and the interval can't disagree. α changes the note's conclusions and the
intervals, not the p-values. The resolution takes the Project's file from the first input frame that carries one.

### 5.6 `spt_refusal_upper_limit`
Read by `ht.stats.fit()` (and `representative()` and `select()` through it) when the value is an SPT N column that
`spt_refusal` flags. The limit is field N, the log's blows per foot, and each refusal row's limit is
`limit × value / spt_n`, its own factors, so one limit serves `spt_n`, `spt_n60` and `spt_n1_60`. A refusal is
then fitted as interval-censored between its value and its limit. It is the top of a refusal's interval, not the
cap (`spt_cap`), which is its bottom. Keys are geology units, matched on the rows' `geology_unit` whatever `fit()`
groups by. `none` keeps a unit right-censored on purpose, so a file that bounds one unit isn't an error for
another whose refusals have a different cause (cobbles, rock). For a column that isn't an SPT N, an argument is an
error and a file entry is ignored. A row whose limit isn't above its value is an error naming the row.

### 5.7 `fixed_intact_compressive_strength`
Read by `ht.analysis.hoek_brown_fit()` for its second fit, with σci fixed; the free fit is always made. `by:` must
be one of the fit's `group_by` columns, else each group's fixed fit is missing with a reason naming the column to
group by. The argument is a quantity string (a bare number is an error asking for the unit) for every group, or a
mapping from a group's key (a value, or a tuple with several `group_by` columns); a key that matches no group
warns, and a group the mapping doesn't list has no fixed fit, with that reason. It isn't named
`intact_compressive_strength` so that the selected σci can take that name.

### 5.8 `critical_state_friction_angle`
φ′cv, set by mineralogy and grading, so keyed by geology unit with no project value. The reason says whether it came
from a ring shear test, a correlation from PI, or the literature. Read by:
- `ht.analysis.friction_angle_from_shear_box()` (Kulhawy & Mayne 1990, Eq. 4-10; [`strength.md`](strength.md) §8),
  for every group the conversion needs, keyed on the fit's `geology_unit`;
- `ht.stats.mohr_coulomb_set()`, for ψ by Bolton's relation in each `coarse` unit ([`statistics.md`](statistics.md)
  §7).

The argument is a mapping by geology unit, or one number when only one group or unit needs it.

### 5.9 `selection`
Read by `ht.stats.select()` and the model sets through it. Keyed by parameter (a numeric registry column with a
quantity kind; anything else is an error naming the registry), then by geology unit, with `by:` written as
`geology_unit` or left out. Every entry has a `method` and a `reason`, and no method has a default:

| `method` | Fields | What hangtu does |
|---|---|---|
| `characteristic`, `percentile`, `standard_deviations` | `source`, `side`, `distribution`, and the inputs `representative()` takes for that method under its argument names (`trend`, `estimate`, `coefficient_of_variation`, `scale_of_fluctuation`, `failure_length`, `sensitivity_index`, `percentile`, `standard_deviations`) | `representative()` on that source's rows in the unit |
| `fitted` | `source`, a fit | the fit's value in the unit |
| `value` | `value`, in the selection's `units: {value: …}` | the engineer's value |
| `none` | — | the unit, listed with no value on purpose |

- `source` is a `parameter_source` label as `compare_sources()` writes it.
- **Checked when the file is opened,** as far as it can be without the data: an unknown method, a field the method
  doesn't take (the error names the methods that take it), a missing field the method needs (by `representative()`'s
  own rules, with no defaults), a field of the wrong type, a missing `source`, `value`, `reason` or `units`, a unit
  of the wrong dimension. Whether a source exists in the unit, or a fit has one value there, is checked by
  `select()`.
- **A unit the sources have and the selection doesn't list is an error;** `method: none` lists one on purpose. A
  `value` or `none` may name a unit no source has; another method there is an error.
- **`selection=`** on `select()` is the whole selection of the parameter, in the file's shape with values as
  quantity strings (`"500 psf"`), checked by the same rules. It replaces the file's selection for that parameter,
  with a warning when the file has one.
- No depth-range key (a depth trend is `trend: depth` in the entry) and no named design case yet (TODO #56): pass
  `selection=` or a second file as `judgments=` for one case at a time.

### 5.10 Not judgments
- **Hammer efficiency is data:** `ISPT_ERAT` (`energy_ratio`) is used first; `hammer_efficiency` is an argument and
  session setting that fills blanks, with a warning naming the holes, and takes values by hole.
- **γw is a setting,** `ht.settings.water_unit_weight` (default `"9.81 kN/m3"`), a quantity string converted as
  needed, so the display system never changes a result. A judgment for sites with two values (seawater and fresh)
  is in `docs/TODO.md`.
