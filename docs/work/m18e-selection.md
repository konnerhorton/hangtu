# M18 (e): the selection as a judgment

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4). Its units: (a) SPT refusals, (b) representative values,
(c) P09 and (d) sources compared are done. The old (e) is split in two (decision 1): **(e), this unit, the
selection as a judgment**, and (f) the model-set base and the Mohr–Coulomb set, built on it.

**Goal:** per geology unit and parameter, the engineer writes down in the judgments file which source and which
method give the selected value (or gives the value with a reason). hangtu computes it, and records what was
chosen, from what, and what the other sources gave.

**Why:**
- **Stage D ends in a value, and today that value isn't recorded anywhere.** `compare_sources()` (M18 (d)) puts
  the sources side by side, and `representative()` (M18 (b)) computes a view, but the choice between them is made
  in the engineer's head or a spreadsheet. SPEC §5 decided (2026-11-02) that "the selection is a judgment": the
  judgments file names a method hangtu computes, with its inputs, or a value with a reason, and the set records
  which. (b) left the view's inputs as required arguments for this unit to move into the file.
- **A selection is reviewed, so it belongs in the reviewable file.** SPEC §4 puts judgments in a plain
  `judgments.yaml` under version control, recorded with its SHA-256 on every result. A selection written there is
  one diff a checker can read, and re-running gives the same value.
- **The other sources are part of the answer.** A selected φ′ of 34° from the triaxial fit reads differently when
  the SPT correlations give 38° and the converted shear box 31°. The (d) intent says the selection's result "says
  what the other sources gave"; `compare_sources()` already computes it.
- **What depends on it:** (f) builds the Mohr–Coulomb set from these selections, and every later wave's model
  sets (Soft Soil in M20, Hoek–Brown in M22, HS and HS-small in M23) read them the same way. The AGSi export
  (Later) writes them.

**Scope:**
- **The selection judgment.** A judgment keyed by geology unit and parameter (a registry column:
  `effective_friction_angle`, `effective_cohesion`, `undrained_shear_strength`, `bulk_unit_weight`, …). Each entry
  gives either:
  - **a method hangtu computes:** the source it reads (a `parameter_source` label, as `compare_sources()` writes
    it) and a `representative()` view with every input that view requires (estimate, side, distribution, V_X,
    θ and L, k, p, trend), or a fit's value taken as fitted; or
  - **a value with a reason** (EC7's nominal value, an engineer's cautious estimate, a value from a report), with
    its unit.

  No field has a default (SPEC §4). The judgment's name and file layout, and whether a depth range or a named
  design case is an allowed key (SPEC §4 lists both), are for the spec (decision 4).
- **The selection result.** One function takes the sources (the same arguments `compare_sources()` takes) and the
  judgments, and returns, per unit and parameter: the selected value (constant, or a line with depth), the method
  and source, the inputs and the `representative()` result behind it, and the comparison rows for the other
  sources. Kind *parameter*, on the shared base, with SPEC §5's views (one calculation, many views). A unit with no
  selection entry is listed with its reason, never filled in. Its name and home (`ht.stats.select()`?) are for the
  spec, checked against the registry (decision 4).
- **c′ and φ′ from one fit.** Selecting both as the fit's values keeps the pair on one line; selecting each by a
  view of its own doesn't give a joint fractile, and the docs say so (decision 3).
- **Parameters exercised:** sheet 04 (φ′, c′), sheet 05 (s_u, uncorrected) and sheet 01 (unit weight, one
  source). Sheets 02, 03, 15 and 22 can be selected by the same judgment, with no extra work.
- **Golden values:** a selection on the example site's Terrace and the clay unit, hand-built from the
  `representative()` and `compare_sources()` values it reads; the JRC worked examples that (b) reproduces,
  reached through the judgments file instead of arguments, so the two routes give the same number. The example
  data keeps its site-like scatter.
- Docs: a "Selection" guide (from sources compared to a selected value), site pages 01, 04 and 05, the judgments
  page, the API reference, and the example site's `judgments.yaml`.

**Constraints:**
- SPEC §4: judgments have no defaults; they resolve argument → `judgments=` → the project's file; a value at a
  coarser key than allowed is an error; each judgment used is recorded with its value, key and source.
- SPEC §5: the result computes once and its views can't disagree; the input rules (flags from the registry,
  counts add up, sources never pooled unawares, H&F 7, units) hold as in `representative()` and
  `compare_sources()`, which this unit calls rather than re-implements. "Engineers choose, hangtu reports": no
  source, method or side is picked for them.
- SPEC §5, derived results: a shear box φ′ is selectable only through `friction_angle_from_shear_box()`, as in
  `compare_sources()`.
- SPEC §1.4: hangtu stops at the selected value. No partial factors or design values.
- No new dependencies.

**Out of scope:**
- **The model-set base, the Mohr–Coulomb set and ψ:** M18 (f) (decision 1), with decision 5 settled for it.
- **Bjerrum's μ** (decision 2): not placed. The field vane is selected as measured, and the source label says so.
- **The other model sets** (Soft Soil, Hoek–Brown, HS, HS-small): each with its wave (TODO #32).
- **A joint (bivariate) c′–φ′ characteristic value** (decision 3).
- **An undrained (φ = 0, s_u) model set** (decision 3).
- **Exporters to a program's input format and AGSi export** (SPEC §1.3, Later). `.to_dict()` keeps the shape they
  will read.
- **A figure of its own.** P09 draws a selected line, P01 and P07 the sources (M18 (c), (d)).

**SPEC and TODO touched:**
- SPEC §4: the selection judgment in the judgments list (`src/hangtu/_judgments.py`).
- SPEC §5: "The selection is a judgment" (from decided-in-principle to built); the function list.
- SPEC §12.4: the M18 row becomes (a)–(f), with (e) the selection and (f) the model-set base and the
  Mohr–Coulomb set; (e) done at close.
- `docs/drafts/parameters/README.md`: sheet 05's stage D no longer names Bjerrum's μ for M18; stage D of sheets
  01, 04 and 05 at close.
- `CLAUDE.md`: the "next" sentence (M18 (f)).

### Decisions (intent review, 2026-11-06)
1. **The old (e) is split in two.** (e) is the selection as a judgment and its result; (f) is the model-set base
   and the Mohr–Coulomb set (c′ and φ′ from the selections, ψ by Bolton (1986), E′ and ν′ blank until M23,
   TODO #32). Together they are too much to review in one sitting, and the sets read the selection as their
   input, so it comes first.
2. **Bjerrum's μ is left out for now,** and not placed. SPEC §4 keeps it in the list of judgments, and it gets
   a unit of its own when it's needed.
3. **Agreed as proposed:** no bivariate c′–φ′ selection (the docs say how to keep the pair consistent), and no
   undrained φ = 0 model set.
4. **Left for the spec:** whether a depth-trend line can enter a model set, and how it is recorded; the
   judgment's name, file layout and keys; the function's name and home.
5. **For (f): coarse- or fine-grained comes from the geology map's `soil_class`,** which gains those classes, so
   ψ (Bolton (1986) for coarse-grained units, 0 for fine-grained) reads the map, never USCS or the data. This
   touches TODO #3 (the cohesive/cohesionless split). Bolton (1986) is verified against the primary
   (*Géotechnique* 36(1), 65–78) in (f)'s spec step.

## Spec
Decisions 6–19 below; numbering follows the intent review's. The behavior is documented in
`docs/analysis/statistics.md` §6 at close.

### What changes
- **A `selection` judgment** in the judgments file, checked by `ht.judgments()` when the file is opened
  (decisions 6–10).
- **`ht.stats.select()`**, returning a `SelectionResult` of kind *parameter* (decisions 11–17).
- **SPEC §4, §5 and §12.4**, in this commit (decision 19).
- **Sheet 01 isn't exercised** (decision 18): unit weight already has its selection, the `unit_weight` judgment.

### The judgment
```yaml
selection:
  effective_friction_angle:          # the parameter: a numeric registry column
    by: geology_unit                 # always; may be left out
    units: {value: deg}              # only when an entry gives a value
    values:
      Terrace:
        source: "Mohr-Coulomb fit (CD, CU)"   # a parameter_source label
        method: fitted
        reason: "three CD and two CU stages, consistent with the converted shear box"
      Alluvium:
        method: value
        value: 26
        reason: "lean clay, no drained tests; CU tests on the same deposit, adjacent project"
      Fill:
        method: none
        reason: "not used in design: removed under the structure"
  undrained_shear_strength:
    values:
      Alluvium:
        source: "laboratory, UU"
        method: characteristic
        estimate: mean
        side: low
        distribution: lognormal
        trend: depth
        reason: "settlement-controlled embankment base: a mean over a long slip surface"
```

6. **One judgment, `selection`, keyed by parameter, then by geology unit.** The parameter level is new in the
   file. It's needed because a selection is per unit *and* parameter (SPEC §5), and a flat key such as
   `selection_effective_friction_angle` would be one judgment name per registry column. The parameter must be a
   numeric registry column with a quantity kind; anything else is an error naming the column and the registry.
   `by:` is `geology_unit` always, written or left out (decision 9), as for `critical_state_friction_angle`.
7. **Every entry has a `method` and a `reason`.** There is no default method, and a selection is the judgment a
   checker reads most closely, so the reason is required everywhere, as for φ′cv. The methods:

   | `method` | Fields | What hangtu does |
   |---|---|---|
   | `characteristic`, `percentile`, `standard_deviations` | `source`, and `representative()`'s inputs for that method under the same names (`side`, `distribution`, `trend`, `estimate`, `coefficient_of_variation`, `scale_of_fluctuation`, `failure_length`, `sensitivity_index`, `percentile`, `standard_deviations`) | calls `representative()` on that source's rows in the unit |
   | `fitted` | `source`, a fit | takes the fit's value in the unit as fitted |
   | `value` | `value`, with the parameter's `units:` | takes the engineer's value |
   | `none` | — | lists the unit with no value, on purpose |

   The field names are `representative()`'s argument names, so a reader moves between the file and the call
   without a translation table. `representative()`'s own rules apply unchanged: every input a method needs is
   required, and none has a default.
8. **The file is checked when it's opened, as far as it can be without the data.** `ht.judgments()` raises,
   naming the file, the parameter, the unit and the field, for: an unknown method; a field the method doesn't take
   (`percentile` under `characteristic`); a missing field the method requires (by `representative()`'s rules); a
   field of the wrong type; a missing `source`, `value`, `reason` or `units`; a unit whose dimension doesn't
   match the parameter's quantity kind. Checks that need the data (whether a source exists in the unit, whether a
   fit has one value there) are made by `select()` (decision 13).
9. **The key is the geology unit only.** No `project:` value: one selection for every unit would be coarser
   than SPEC §5's "per geology unit and parameter". No depth-range key: a depth trend (`trend: depth`) covers
   variation with depth inside a unit, and a depth band is a geology question for the map. **Named design cases**
   (a Type A value for a slope and a Type B for a footing in the same unit) are deferred: SPEC §4 lists them as a
   possible key, but nothing reads them yet, and the `selection=` argument (decision 12) or a second judgments
   file passed as `judgments=` serves one case at a time meanwhile. TODO #56 records it.
10. **An unlisted unit is an error, and `method: none` lists one on purpose.** This changes the intent's "listed
    with its reason, never filled in", to follow SPEC §4: with no project-wide value allowed, a key that the file
    doesn't list is an error. `select()` names every unit the sources have that the selection doesn't list, and
    says to add an entry, or `method: none` with a reason. A `none` unit is listed with its reason and no value.
    A `value` entry for a unit that no source has is allowed (a unit with no tests, a value from a report) and is
    listed. A `characteristic`, `percentile`, `standard_deviations` or `fitted` entry for a unit that no source
    has is an error.

### The function
```python
ht.stats.select(
    *sources,                 # as compare_sources(): DataFrames, MohrCoulombFit, ShearBoxConversion
    value,                    # the parameter, e.g. "effective_friction_angle"
    selection=None,           # {geology_unit: entry}, overrides the file's selection for value
    include_assumed=False,
    judgments=None,
    units=None,
    display_units=None,
) -> SelectionResult
```
11. **The name is `ht.stats.select()`, returning `SelectionResult`.** It lives in `ht.stats` beside
    `representative()` and `compare_sources()`, which it calls. "Select" is SPEC §1.3's word for stage D. The name
    checks clean against the registry and the `ht.stats` names. There is no `by=`: a selection is by geology unit
    (decision 9).
12. **Resolution follows SPEC §4.** `selection=` → `judgments=` → the Project's file that the sources carry →
    an error that names the parameter and shows an entry. `selection=` is the whole selection for `value`, a
    mapping of unit to entry in the file's shape, with a value as a quantity string (`"500 psf"`), read as QC
    thresholds are (SPEC §9.2). It replaces the file's selection for that parameter, never merging unit by unit,
    with a warning when the file has one. It's checked by the same rules as the file (decision 8).
13. **It runs `compare_sources()` once, then each unit's method on the same rows.**
    - **The comparison** is `compare_sources(*sources, value=value, by="geology_unit", include_assumed=…,
      units=…, display_units=…)`, kept on the result. Its errors are `select()`'s (a `ShearBoxFit` is refused,
      SPEC §5).
    - **A `source`** must be a `parameter_source` label in the comparison (repeats included, as in
      `"… (source 2)"`). Otherwise it's an error listing the labels that have rows in that unit.
    - **A `representative()` method** calls `representative()` on that source's own rows in the unit, the frame
      as passed, filtered to the rows that carry that label. So `spt_n`, the flags and the bands reach it as they
      reach `fit()`, and `spt_refusal_upper_limit` resolves from `judgments=` and the file. Its `by` is
      `geology_unit` and it gets the method's fields as arguments. A fit source fitted per sample (several values
      in the unit) gives its values from `.values()`, n the number of samples. A source with one fit value in the
      unit is an error that says to use `fitted`.
    - **`fitted`** needs a fit source with exactly one value in the unit. A row source, or a fit with several
      values, is an error that names the methods that take it.
    - **Units:** every value is in the comparison's unit (`display_units`, else its first source's). A
      `representative()` result in another unit is converted, and so is a `value` from its `units:`. Angles are
      in degrees.
    - **A unit whose method gives no value** (fewer than 2 values, every row left out, the fit's
      `no_fit_reason`) is listed with that reason in `no_value_reason`, and `select()` warns, naming the units.
      It's never an error, and never filled from another source.
14. **The selected value, against the other sources: a position, never a test.** For each unit with a constant
    selected value, and each other source in the unit:
    - for a row source with counted values: `position` (below, within or above its lowest to highest value) and,
      within that range and from 4 values, `percentile_rank`, as `compare_sources()` places a fit (M18 (d),
      decision 13), by the same function;
    - for a fit source: its value and `difference` (selected − fit), with no position, because a single value has
      no spread.

    A line (`trend`) has no single value to place, so its rows give `position` blank with the reason "a line
    with depth". The selected source isn't placed against itself.
15. **The result, `SelectionResult`,** has kind *parameter*, on the shared base (SPEC §5):
    - `.to_frame()`: one row per unit, in the comparison's order, then `value` units no source has. Columns:
      `geology_unit`, `parameter_source` (blank for `value` and `none`), `selection_method`, `value`
      (constant), `line_intercept`, `line_slope`, `depth_top`, `depth_base`, `value_top`, `value_base`
      (a line, named as in `RepresentativeResult.to_frame()`), `count` (values behind it: the rows, the fit's
      points, or blank for `value`), `selection_reason`, `no_value_reason`. `attrs["units"]` as usual.
    - `.positions()`: one row per unit and other source, as in decision 14.
    - `.comparison`: the `SourceComparison`. `.representative(geology_unit)` gives that unit's
      `RepresentativeResult` (an error for another method).
    - `.design_lines()`: P01's frame, one line per unit with a value. A `representative()` method gives that
      result's lines; `fitted` a constant over its points' depths; `value` a constant over the depths of every
      source's rows in the unit, and no line when there are none, with a note. Labels are
      `"<unit>: selected, <method>"`.
    - `.profile(geology_unit=…, **kwargs)`: the comparison's `.profile()` of that unit with
      `design_lines=self.design_lines()` for it, so the figure shows the sources and the line chosen from them.
    - `.to_dict()` holds every field, the comparison's and each `representative()` result's `.to_dict()`
      included. The printed summary gives the table, then the positions, then the notes.
    - Every new column name (`selection_method`, `selection_reason`, `difference`) is checked against the
      registry in the build. `difference` is a result column only, and is added to the registry only if it
      collides with nothing.
16. **What's recorded.** `judgments` holds the selection used for `value` (each unit's entry, and its source:
    `selection=`, or the file's path and SHA-256), merged with the sources' judgments and each
    `representative()` result's, such as `spt_refusal_upper_limit`. A note per unit says what was chosen in one
    line: "Terrace: Mohr-Coulomb fit (CD, CU), fitted: 33.6 deg (three CD and two CU stages, …)".
17. **`c′` and `φ′` stay consistent through `fitted`.** Two `select()` calls, one per parameter, each `fitted`
    from the same `MohrCoulombFit`, give one line's pair. When the two selections of one unit name different
    sources, or a method other than `fitted` for either, the result's notes don't warn (a `select()` sees one
    parameter). The selection guide says that c′ and φ′ selected separately aren't a joint fractile (decision 3).
    (f)'s Mohr–Coulomb set, which sees both, warns.
18. **Sheet 01 is left out:** the `unit_weight` judgment (M13) already is unit weight's selection, a value with a
    reason per unit, and `vertical_stress()` reads it. A second home for the same choice could disagree with it.
    Selecting `bulk_unit_weight` with `select()` still works, and the guide says the `unit_weight` judgment is the
    one analyses read. The parameter index records sheet 01's stage D as the judgment. Sheets 04 and 05 are
    exercised.
19. **SPEC changes in this commit:**
    - §4: `selection` joins the judgments list, keyed by parameter and geology unit, with no project-wide value.
    - §5: "The selection is a judgment" names `select()`, its methods and its resolution. `select` joins the
      function list, marked M18 (e).
    - §12.4: the M18 row becomes (a)–(f): (e) the selection; (f) the model-set base and the Mohr–Coulomb set, with
      ψ reading coarse or fine from `soil_class` (decision 5).

### Golden values
Hand-built frames in SI, so each number is checked by hand, not by running the code.

- **G1, a characteristic value through the file.** Unit `Sand`, source A (`correlation_name` "A"), φ′ = 34, 36,
  37, 38, 40 deg; `method: characteristic, estimate: mean, side: low, distribution: normal`, V_X computed
  (Case 2).
  - x̄ = 37.0; s = √((9 + 1 + 0 + 1 + 9) / 4) = √5 = 2.2361.
  - k_n = t₀.₉₅,₄ · √(1/5) = 2.1318 × 0.44721 = 0.95339 (JRC Formula 4.5 with Γ² = 0, as (b)).
  - X_k = 37.0 − 0.95339 × 2.2361 = **34.868 deg** (±0.001).
- **G2, its position.** Source B ("B") in `Sand`: 33, 35, 36, 39, 41 deg. G1's 34.868 lies between x₍₀₎ = 33 and
  x₍₁₎ = 35: h = 0 + 1.868 / 2 = 0.934, rank = 100 × 0.934 / 4 = **23.35 %**, `position` "within".
- **G3, `fitted`.** A `MohrCoulombFit` of `Sand`, three CD stages on t = 4.3301 + 0.5 s′ (c′ = 5 kPa, φ′ = 30°:
  c′ cos φ′ = 4.3301, sin φ′ = 0.5), at s′ = 100, 200, 300 kPa (t = 54.330, 104.330, 154.330). Selected `fitted`:
  **φ′ = 30.000 deg**, and **c′ = 5.000 kPa** from the same fit (decision 17). Against G1's selection, the fit's
  `difference` = 34.868 − 30.000 = **4.868 deg**.
- **G4, `value` with a conversion.** s_u for `Clay` in a comparison in kPa, `value: 500` with
  `units: {value: psf}`: 500 × 0.0478803 = **23.940 kPa** (1 psf = 0.0478803 kPa, pint's definition).
- **G5, through the file and through the arguments.** One of (b)'s JRC golden cases
  (`tests/stats/test_representative.py`) run through `select()` from a judgments file gives (b)'s value, so the
  two routes give one number.

### Acceptance criteria
1. A file with each method's entry opens; each error in decision 8 raises on open, naming the file, parameter,
   unit and field.
2. G1: `select()` gives 34.868 deg for `Sand`, with `selection_method` "characteristic" and `parameter_source`
   "A"; `.representative("Sand")` equals `representative()` called with the same rows and arguments.
3. G2: `.positions()` gives source B "within" at 23.35 %.
4. G3: `fitted` gives 30.000 deg and 5.000 kPa; a `fitted` entry on a row source, or a `representative()` method
   on a single fit value, is an error naming the methods that take it; the `difference` is 4.868 deg.
5. G4: a `value` entry gives 23.940 kPa and is listed for a unit no source has; a `value` without `units:` fails
   on open.
6. A unit the sources have and the selection doesn't list is an error naming it; `method: none` lists it with its
   reason and no value; a method other than `value` for a unit no source has is an error.
7. A `source` not in the comparison is an error listing the labels in the unit; a `ShearBoxFit` source is refused
   as by `compare_sources()`.
8. Resolution: `selection=` overrides the file with a warning; without either, the error names the parameter and
   shows an entry; the result records the file's path and SHA-256, or the argument.
9. A refusal row selected by `characteristic` uses `spt_refusal_upper_limit` from the file, as `representative()`
   does, and the judgment is recorded.
10. A unit whose method gives no value is listed with `no_value_reason` and a warning, and is never filled from
    another source.
11. A `trend: depth` selection gives the line from `representative()`, `.positions()` blank with "a line with
    depth", and `.design_lines()` equal to that result's.
12. G5 holds.
13. Views agree: `.to_frame()`, `.to_dict()` and the printed summary give the same values; `.profile()` draws
    the comparison's rows with the selected line; on a Project's categorical `geology_unit`, nothing warns.
14. Docs: the selection guide's example runs from the example site's `judgments.yaml` (φ′ for the Terrace, s_u
    for the Alluvium); `select` has an API reference entry; the judgments docstring lists `selection`.

### Changes to other docs
- `docs/analysis/statistics.md`: §6 `select()`.
- `src/hangtu/_judgments.py` docstring (published): the `selection` judgment.
- `docs/site/`: a "Selection" guide after "Sources compared"; pages 04 and 05, stage D; the judgments page;
  `docs/site/reference/stats.md`.
- `src/hangtu/examples/data/judgments.yaml`: a selection for the Terrace's φ′ and c′ and the Alluvium's s_u, with
  `none` for the other units the sources have.
- `docs/drafts/parameters/README.md`: sheet 05's stage D no longer names Bjerrum's μ; sheets 01, 04 and 05
  at close.
- `docs/TODO.md`: #56, named design cases as a selection key (decision 9).

## Plan
Six build commits, each with ruff, mypy and the tests it touches green, and the whole suite run once before
committing. Steps 1–3 run on Opus in one session, 4–5 on Sonnet in a new session, and 6 on Opus.

### 1. `M18: add the selection judgment to the judgments file` (Opus)
- `src/hangtu/_judgments.py`: `selection` in `KINDS`, read by its own checker because it has a parameter level.
  The parameter must be a numeric registry column with a quantity kind. `by:` is `geology_unit` or left out, with
  no `project:` value. Each entry has a `method` from the four, a `reason`, the fields that method takes (the
  input rules shared with `_representative._check`, so the two can't differ), and a `units: {value: …}` checked
  against the parameter's quantity kind (decisions 6–9). Add `selection` to the published docstring.
- `src/hangtu/stats/_representative.py`: split the input checks into a function the file checker can call
  without data (no change in behavior).
- Tests: `tests/test_judgments_selection.py`: each method's entry opens; each error in decision 8 names the file,
  parameter, unit and field (AC 1); a `value` without `units:` fails on open (AC 5, second half).

### 2. `M18: add ht.stats.select() for computed and given values` (Opus)
- `src/hangtu/stats/_select.py` (new): resolution `selection=` → `judgments=` → the file the sources carry (via
  `df.attrs["judgments_file"]` or `fit.judgments_file`, `read_judgments_file`) → an error showing an entry
  (decision 12). Runs `compare_sources()` once, checks the `source` labels and units (decisions 10 and 13), and
  calls `representative()` on each frame's rows filtered to the label, with its `judgments=` passed through.
  `value` is converted to the comparison's unit, `none` is listed with its reason, and `no_value_reason` comes
  with a warning.
- `src/hangtu/stats/_compare_sources.py`: expose each row source's frame and its label mask on `_Source` so
  `select()` can filter rows (no change in behavior).
- `src/hangtu/stats/__init__.py`: export `select` and `SelectionResult` (a minimal result, with `.to_frame()`
  and `.representative()`).
- Tests: `tests/stats/test_select.py`: G1 (AC 2), G4 and a `value` for a unit with no rows (AC 5), unlisted
  units and `none` (AC 6), an unknown source and `ShearBoxFit` (AC 7), resolution with the warning and the
  path and SHA-256 recorded (AC 8), refusals with `spt_refusal_upper_limit` from the file (AC 9), no value
  never filled from another source (AC 10), and G5 against `test_representative.py`'s JRC case (AC 12).

### 3. `M18: select a fit's value and place the selection` (Opus)
- `src/hangtu/stats/_select.py`: `fitted` (one fit value in the unit; a row source or several values is an
  error naming the methods that take it). A per-sample fit goes to `representative()` from its values. Add
  `.positions()` with `position`/`percentile_rank` by `percentile_rank()` and the fit's `difference`; a line
  gives a blank position with "a line with depth" (decision 14).
- Tests: `tests/stats/test_select_fitted.py`: G2 (AC 3), G3 with c′ and φ′ from one fit, the errors and
  `difference` (AC 4), and the trend's positions (AC 11, first half).

### 4. `M18: add SelectionResult's views` (Sonnet)
- `src/hangtu/stats/_select.py`: complete `SelectionResult` (decision 15): `.to_frame()` columns and order,
  `.to_dict()` with the comparison's and each `representative()` result's, the printed summary and HTML repr,
  `.design_lines()`, `.profile()`, a note for each unit (decision 16).
- `src/hangtu/columns.yaml`: no change, decided in the build. `selection_method`, `selection_reason`,
  `selected_source`, `selected_value`, `fit_value` and `difference` collide with nothing in the registry, but
  they are result columns, and the registry holds data columns only: `RepresentativeResult`'s
  `line_intercept` and `no_value_reason`, and `compare()`'s own `difference` (the same meaning, one value
  minus another) aren't in it either, and `difference` has no single quantity kind.
- Tests: `tests/stats/test_select_views.py`: the views agree, `.profile()` draws the selected line, and a
  Project's categorical `geology_unit` raises no warning (AC 13); a trend's `.design_lines()` equals
  `representative()`'s (AC 11, second half).

### 5. `M18: document the selection` (Sonnet)
- `docs/site/guides/selection.md` (new, after "Sources compared" in `zensical.toml`) with
  `docs/site/examples/selection.py`: φ′ for the Terrace, s_u for the Alluvium, from the example site's file. It
  says c′ and φ′ selected separately aren't a joint fractile, and that the `unit_weight` judgment is the one
  analyses read.
- `src/hangtu/examples/data/judgments.yaml`: the Terrace's φ′ and c′ (`fitted`), the Alluvium's s_u, and
  `none` for the other units.
- `docs/site/guides/judgments.md`, `docs/site/reference/stats.md`, `docs/site/parameters/` pages 04 and 05
  (stage D), `docs/analysis/statistics.md` §6.
- Tests: the reference-entry test and `docs/prepare_site.py` run clean (AC 14).

### 6. `M18: close out (e), the selection` (Opus)
- Check every acceptance criterion and golden value, and look at the guide's figure.
- Close-out: SPEC §12.4 marks (e) done (§4 and §5 were changed in the spec commit, decision 19; check they
  still match what was built). `docs/drafts/parameters/README.md` gets stage D for sheets 01 (the
  `unit_weight` judgment), 04 and 05, and sheet 05 no longer names Bjerrum's μ. `docs/TODO.md` gets #56
  (named design cases as a selection key). `CLAUDE.md`'s "next" sentence moves to M18 (f).
