# M18 (f): the model-set base and the Mohr–Coulomb set

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4). Units (a)–(e) are done: refusals, representative values, P09,
sources compared, and the selection as a judgment (`ht.stats.select()`). **(f), this unit, is the last one:** the
base that every model set is built on, and the first set, Mohr–Coulomb.

**Goal:** per geology unit, one Mohr–Coulomb parameter set (c′, φ′, ψ, with E′ and ν′ blank until M23). Each
value records where it came from: c′ and φ′ from the `selection` judgment, ψ by Bolton (1986) or 0. The set is a
result like any other, with SPEC §5's views, in the shape the later sets and the AGSi export will read.

**Why:**
- **Stage D ends in a model set** (SPEC §1, §5, decided 2026-10-21). `select()` gives one parameter at a time, but
  an engineer hands a numerical modeler a set per unit, so the pieces have to be put together, checked against
  each other, and recorded in one place. Today that happens in a spreadsheet.
- **The pair c′–φ′ is only consistent when both come from one fit.** `select()` sees one parameter, so it can't
  warn when c′ and φ′ of one unit come from different sources or methods (M18 (e), decision 17). The set sees
  both, so it warns.
- **ψ is the one MC parameter nothing in hangtu gives yet,** and it's usually set by a rule of thumb whose
  assumptions are hidden. TODO #32 (decided 2026-11-02) picks Bolton (1986) for coarse-grained units, with
  φ′cv the engineer's `critical_state_friction_angle` judgment (M18 (d)), and 0 for fine-grained units; the
  practice rule ψ = max(0, φ′ − 30°) is not offered (sheet 09, §5.2–5.3).
- **What depends on it:** the Soft Soil set (M20), the generalized Hoek–Brown set (M22) and the HS and HS-small
  sets (M23) are built on the same base; the AGSi export (Later) and the program exporters (Later) read
  `.to_dict()`. So the base is designed against every wave 2 fit: `mohr_coulomb_fit()` and the converted shear
  box now, `hoek_brown_fit()` (σci, mi) plus judgments (GSI, D) for M22.

**Scope:**
- **The model-set base:** a result of kind *parameter* on the shared base (SPEC §5): per geology unit, each of the
  model's parameters by its registry name, with its value (constant only, decision 4), unit,
  where it came from (a selection with its method and source, a rule with its citation, or blank with a reason),
  and the judgments used. Views: `.to_frame()` (one row per unit), `.to_dict()`, the printed summary. A model set
  defines which parameters it has and how each is reached; the base doesn't know any model.
- **The Mohr–Coulomb set:**
  - **c′ and φ′** from `select()`, one call per parameter, reading the same judgments file. A unit whose c′ and
    φ′ aren't both `fitted` from the same source gets a warning and a note (M18 (e), decision 17).
  - **ψ:** for a unit whose `soil_class` is coarse-grained, Bolton (1986), ψ = (φ′ − φ′cv) / 0.8, floored at 0
    (with a note when the floor applies), φ′ the selected value and φ′cv the `critical_state_friction_angle`
    judgment. For a fine-grained unit, 0. The relation is for plane strain and a peak φ′; with a triaxial φ′ or a
    cautious selected φ′ it is an approximation, and the result says which φ′ it used.
  - **E′ and ν′** are in the set, blank, with the reason "wave 5 (M23)".
- **`soil_class` gains its first defined values** (decision 5 of (e), TODO #3): at least `coarse` and `fine`,
  read from the geology map. The example map already uses `coarse`, `fine`, `fill` and `rock`.
- **Golden values:** ψ by hand from Bolton's equation for the example Terrace (coarse) and 0 for the Alluvium
  (fine); the set's c′ and φ′ equal to `select()`'s for the same file (one calculation, many views).
- **Bolton (1986)** verified against the primary, *Géotechnique* 36(1), 65–78, in the spec step (TODO #32; now
  [V] only through Kulhawy & Mayne (1990) and a secondary source).
- **Docs:** sheet 09 promoted to a site page (soil part only), a "Model sets" section in the selection guide, the
  API reference, `docs/analysis/statistics.md`, and the example site's `judgments.yaml` (c′ and φ′ selections,
  φ′cv for Terrace).

**Constraints:**
- SPEC §4: judgments have no defaults and resolve argument → `judgments=` → the project's file; each one used is
  recorded with its value, key and source.
- SPEC §5: one calculation, many views; "engineers choose, hangtu reports"; the set follows the model's published
  description, never a program's input format; the selections are `select()`'s, not re-implemented.
- SPEC §8.3: the geology map is matched exactly, and hangtu never falls back to another heading. ψ reads coarse or
  fine from the map's `soil_class`, never from USCS or the data.
- SPEC §1.4: hangtu stops at the set. No partial factors, no design values, no program input files.
- No new dependencies.

**Out of scope:**
- **The other model sets** (Soft Soil, Hoek–Brown, HS, HS-small): each with its wave (TODO #32).
- **ψ from test curves** (sheet 09 §5.1, needs wave 0's curves), from I_R with Dr and p′ (§5.2, needs relative
  density, not yet placed), and for rock masses (§5.4–5.5, M22).
- **The practice rule** ψ = max(0, φ′ − 30°) (TODO #32).
- **E′ and ν′ values** (M23), **unit weights** (the `unit_weight` judgment already is their selection, M18 (e),
  decision 18), and a tension cut-off.
- **Named design cases** (TODO #56): one set per run until a case key exists.
- **Renaming `soil_class`** and the full category list (organic, intermediate): TODO #3 keeps them, as a unit of
  their own.
- **Exporters and AGSi export** (SPEC §1.3, Later). No figure of its own: P09 and `.profile()` already draw a
  selection.

**SPEC and TODO touched:**
- SPEC §5: "Model sets" from decided-in-principle to built: the base, the Mohr–Coulomb set, ψ; the function list.
- SPEC §8.3: `soil_class`'s defined values and what reads them.
- SPEC §12.4: M18 done; moves to the Done table.
- `src/hangtu/columns.yaml`: ψ's column (name for the spec), `soil_class`'s description and values.
- TODO #32: the Mohr–Coulomb part moves into SPEC §5 and is deleted; TODO #3: the classes this unit defines.
- `docs/drafts/parameters/README.md`: stage D of sheet 04, and sheet 09's soil row.
- `CLAUDE.md`: the "next" sentence (wave 0, M16, waiting on TODO #31; else wave 3, M19).

### Decisions (intent review, 2026-11-06)
1. **Fill, rock, organic or a blank `soil_class` is an error for ψ,** naming the unit and its class and saying
   to give ψ as a `value` selection. A rock unit's error names the Hoek–Brown set (M22), where rock belongs.
   Guessing coarse or fine for these would put a rule where only the engineer can judge.
2. **ψ can be selected instead of the rule.** A `selection` entry for ψ (`method: value` with a reason, or a
   `representative()` method once ψ has data) replaces Bolton or 0 for that unit, and the set records which.
   This keeps "engineers choose" for a unit the rule doesn't fit (a loose sand, a dense fill).
3. **The set takes the sources and reads the selections itself** (`mohr_coulomb_set(*sources, judgments=…)`),
   rather than two `SelectionResult`s, so the whole set follows from one file and can't mix two judgments
   files. The name and home (`ht.stats`?) are for the spec, checked against the registry.
4. **Constant values only, for now.** A c′ or φ′ selection that gives a line with depth (`trend:`) is an error
   in a set, naming the unit and parameter. Lines in a set (and ψ following a φ′ line) wait until a project
   needs them; `select()` still gives the line on its own. This settles (e)'s decision 4 for this unit.

## Spec
Decisions 5–21 below; numbering follows the intent review's. 🟡 marks a proposal the review should confirm, and
🔬 a citation still to check. The behavior is documented in `docs/analysis/statistics.md` §7 at close.

### What changes
- **A model-set base** (`hangtu/stats/_model_set.py`, private) that every set is built on (decisions 5–8).
- **`ht.stats.mohr_coulomb_set()`**, returning a `MohrCoulombSet` of kind *parameter* (decisions 9–17).
- **`soil_class`'s first defined values,** read from the geology map (decisions 18–19).
- **`select()` with no source** for a parameter nothing measures yet, so ψ (and E′, ν′) can be selected by
  `value` (decision 20).
- **SPEC §5 and §8.3**, in this commit (decision 21).

### Sources (checked in this step)
| Claim | Source | Status |
|---|---|---|
| The Mohr–Coulomb model's parameters: Young's modulus, Poisson's ratio, cohesion, friction angle and dilatancy angle, perfectly plastic with non-associated flow | Vermeer & de Borst (1984), *Heron* 29(3), Summary, p. 3 | [V] |
| φ′tc = φ′cv + 0.8 ψ, "Bolton's approximation" | Kulhawy & Mayne (1990), EPRI EL-6800, Eq. 4-16, p. 4-20 | [V] |
| φ′ − φ′cv = 5 I_R (plane strain), 3 I_R (triaxial); I_R "should be limited to 4 unless detailed laboratory test data indicate otherwise" | Kulhawy & Mayne (1990), Eqs. 4-5, 4-6, p. 4-10 | [V] |
| ψ = 15° is typical of a very dense sand; loose sands have a few degrees; "normally consolidated clays show no dilatancy at all" | Vermeer & de Borst (1984), p. 13 | [V] |
| For cohesive soils, ψ = 0 when normally or lightly overconsolidated, φ′/6 when overconsolidated, φ′/3 when heavily overconsolidated | Obrzud & Truty (2018), Z_Soil report, §3.3.4, p. 107 (a software vendor's guidebook) | [V], cited only as the reason a fine unit may need a selected ψ |
| φ′max − φ′crit = 0.8 ψmax, and the stress condition it was derived for | Bolton (1986), *Géotechnique* 36(1), 65–78 | 🔬 not at hand (paywalled) |

**The sources disagree on the stress condition.** Sheet 09 and TODO #32 (through the groundhog docs) give the
0.8 relation for plane strain. Kulhawy & Mayne write it with φ′tc, and Obrzud & Truty apply 0.8 in both
(ψ = 3.75 I_R triaxial, 6.25 I_R plane strain, §3.2.7, p. 86), which is K&M's 3 I_R and 5 I_R divided by 0.8. The
hand calculation is the same in every reading. Only the note on the result changes. Until the primary is read,
hangtu cites K&M Eq. 4-16, the [V] source, and its note gives the equation as K&M state it, for triaxial
compression, the basis of hangtu's `effective_friction_angle` (SPEC §5: the shear box conversion targets φ′tc).
Plane strain isn't mentioned. The intent's "plane strain; an approximation with a triaxial φ′" is withdrawn
unless the primary says so. 🔬 Bolton (1986) is checked before the build's ψ step, or the close-out records it
as still to check in TODO #32.

### The model-set base
5. **A set is a table of values, one per geology unit and parameter, each with its origin.** The base is a frozen
   dataclass on the shared result base (SPEC §5) with `kind = "parameter"`, the model (its name and citation),
   its parameters in order (registry names), and one record per unit and parameter:

   | Field | What |
   |---|---|
   | `geology_unit`, `parameter` | the key |
   | `value`, `unit` | a constant (decision 4), in the parameter's unit; blank when there is none |
   | `origin` | `selection`, `rule`, `judgment` or `blank` |
   | `selection` | for `selection`: the `parameter_source`, `selection_method`, `selection_reason` from `select()` |
   | `rule` | for `rule`: its name, its citation, and its inputs, each with value, unit and origin |
   | `judgment` | for `judgment`: the judgment's name, key and source (SPEC §4) |
   | `no_value_reason` | for `blank`, and for a rule or selection that gives no value |
   | `notes` | what the reader must see (a floor applied, a pair not from one fit) |

   `judgment` is unused by Mohr–Coulomb. It's in the base now because the generalized Hoek–Brown set (M22) takes
   GSI and D as judgments directly, and its m_b, s and a by rule from them and m_i. So the base is checked against
   wave 2's fits and M22's inputs, not just MC.
6. **A set defines its parameters and how each is reached; the base knows no model.** A set is a function that
   builds records and a thin subclass that names the model. The base gives the views (decision 7), the checks
   common to every set (decision 8), and the reading of selections through `select()`. So Soft Soil (M20),
   Hoek–Brown (M22) and HS (M23) add a function and a subclass, not a new result shape.
7. **Views, one calculation.**
   - `.to_frame()`: one row per geology unit, one column per parameter (registry names), values only,
     `attrs["units"]` as usual. This is the table a modeler is handed.
   - `.provenance()`: one row per unit and parameter: `geology_unit`, `parameter`, `value`, `unit`,
     `parameter_origin`, `parameter_source`, `selection_method`, `rule_name`, `rule_citation`, `reason` (the
     selection's reason, or the rule's inputs in one line: "φ′ 35.3 deg (selected), φ′cv 32 deg (judgment)"),
     `no_value_reason`.
   - `.selections`: `{parameter: SelectionResult}` for each parameter read by `select()`, so
     `.selections["effective_friction_angle"].profile(geology_unit=…)` draws one, as (e) does.
   - `.to_dict()`: the model, every record with every field, the selections' `.to_dict()`, the judgments, the
     notes and the version. It's what the AGSi export (Later) reads: one record per unit and parameter, keyed by
     registry name, never a program's field name.
   - The printed summary: the `.to_frame()` table, then one origin line per unit and parameter that isn't a
     plain selection, then the notes.

   🟡 The new column names (`parameter_origin`, `rule_name`, `rule_citation`) check clean against the registry
   and the code today, and are result columns only. They're checked again in the build.
8. **Checks every set makes.**
   - **Constant only** (decision 4): a selection that gives a line (`trend:`) is an error naming the unit and
     parameter, and saying `select()` gives the line on its own.
   - **A unit is in the set** when any of its parameters' selections lists it. The set takes the units in the
     selections' order (the comparison's, so the geology map's), then units only a `value` names.
   - **Every source must give at least one of the set's parameters.** A source that gives none is an error naming
     it, as in `select()`. Each parameter's `select()` gets only the sources that carry it: a DataFrame with that
     column, or a fit or conversion that gives it (`select()` errors on a source without the column, as seen
     with the example's SPT correlations and `effective_cohesion`).

### The Mohr–Coulomb set
```python
ht.stats.mohr_coulomb_set(
    *sources,                          # as select(): DataFrames, MohrCoulombFit, ShearBoxConversion
    selection=None,                    # {parameter: {geology_unit: entry}}, overrides the file per parameter
    critical_state_friction_angle=None,  # number or {geology_unit: number}, deg; overrides the file
    geology_map=None,                  # a path to the mapping CSV, or the map's DataFrame (p.geology_map)
    include_assumed=False,
    judgments=None,
    units=None,
    display_units=None,
) -> MohrCoulombSet
```
9. **Name and home: `ht.stats.mohr_coulomb_set()`, returning `MohrCoulombSet`.** It sits with `select()`, which
   it calls, and SPEC §5 is "Statistics and model sets". `_set` (not `_fit`) keeps it apart from
   `ht.analysis.mohr_coulomb_fit()`, which is one of its sources. Both names are new to the code, registry and
   docs. Later sets follow the pattern: `soft_soil_set()`, `hoek_brown_set()`, `hardening_soil_set()`.
10. **Its parameters, in this order:** `effective_cohesion` (c′), `effective_friction_angle` (φ′),
    `dilatancy_angle` (ψ, new), `drained_youngs_modulus` (E′, exists) and `drained_poissons_ratio` (ν′, new).
    The model's citation is Vermeer & de Borst (1984), p. 3, which names exactly these five. 🟡 The two new
    registry entries: `dilatancy_angle` (angle, ratio scale, label "Dilatancy angle, ψ") and
    `drained_poissons_ratio` (dimensionless, label "Drained Poisson's ratio, ν′"). Neither collides with an
    existing name.
11. **c′ and φ′: from `select()`, one call each, required.** Each runs on the sources that carry it, with the
    set's `selection=` entry for it (if given), `judgments=`, `include_assumed=`, `units=` and `display_units=`,
    so its errors and resolution are `select()`'s. A unit listed for one of the pair and not the other is an
    error naming the unit and the missing parameter, and saying to add an entry (`value: 0` with a reason for a
    c′ of zero, or `none`).
12. **The pair is checked** (M18 (e), decision 17). For a unit where c′ and φ′ aren't both `fitted` from the same
    `parameter_source`, the set warns once, naming the units, and notes per unit: "Terrace: c′ (value) and φ′
    (Mohr-Coulomb fit, fitted) don't come from one fit, so they aren't one envelope's pair." A unit where both
    are `none` isn't warned about.
13. **ψ, in this order:**
    1. **A selection for `dilatancy_angle`** listing the unit (decision 2 of the intent) is used and recorded as
       `selection`: `value` or `none` now, or a `representative()` method once a source carries ψ.
    2. **Else, when the unit has no φ′ value** (`none`, or a method that gave none), ψ is blank: "no φ′ selected".
       Its `soil_class` isn't read. 🟡 This narrows the intent's decision 1: a `fill` or `rock` unit with no φ′
       isn't an error, because no rule is applied to it. It also means the example's Alluvium (φ′ `none`,
       designed undrained) gets a blank ψ, not 0, so the fine-grained golden value moves to a hand-built frame
       (G5).
    3. **Else by the unit's `soil_class`** (decision 18):
       - **`coarse`: Bolton's relation,** ψ = (φ′ − φ′cv) / 0.8 (Kulhawy & Mayne 1990, Eq. 4-16), with φ′ the
         set's selected φ′ and φ′cv the `critical_state_friction_angle` judgment (argument → `judgments=` → the
         Project's file → an error naming the unit, as for the shear box conversion).
         - **Floor:** φ′ < φ′cv gives ψ = 0 with a note: "φ′ 30.0 deg is below φ′cv 32.0 deg, so ψ is 0 (the
           relation gives −2.5 deg)". No warning: a cautious φ′ at or below φ′cv is a normal case.
         - **Validity limit, 🟡 proposed:** φ′ − φ′cv above 12° (3 I_R with I_R ≤ 4, K&M Eqs. 4-6 and p. 4-10, on
           the triaxial basis) is beyond the data the relation was drawn from. ψ is then blank with the reason
           ("φ′ − φ′cv = 13.0 deg, above the 12 deg of I_R = 4 (Kulhawy & Mayne 1990, p. 4-10); give ψ as a
           value selection") and a warning naming the units. It's never clipped to 15° (SPEC §4: never a clipped
           input). At exactly 12° the relation applies: ψ = 15°.
         - The rule records its inputs: φ′ with its source and method (so the reader sees that a cautious φ′ gave
           a smaller ψ), and φ′cv with the judgment's source.
       - **`fine`: 0,** citing Vermeer & de Borst (1984, p. 13) for normally consolidated clays. The note says an
         overconsolidated clay may dilate (Obrzud & Truty 2018, p. 107) and that ψ is then given as a selection.
       - **`fill`, `rock`, `organic`, blank, or any other value: an error** (intent decision 1) naming the unit and
         its class and saying to give ψ as a `value` selection. For `rock` it adds that rock belongs in the
         Hoek–Brown set (M22).
14. **E′ and ν′:** a selection for `drained_youngs_modulus` or `drained_poissons_ratio` that lists the unit is
    used, as for ψ. Otherwise the value is blank: "no selection; derived values come with wave 5 (M23)".
    🟡 This reads the intent's "blank until M23" as "no rule until M23". An engineer's E′ from a report, or a
    `characteristic` of the SPT E′ correlations (M13 b3) already in `drained_youngs_modulus`, isn't ignored
    silently. Blank E′ and ν′ don't warn.
15. **Units.** c′ is in its selection's unit (`display_units`, else its comparison's), and E′ in its own. φ′ and ψ
    are in degrees, ν′ is dimensionless, and a blank E′ has no unit.
16. **What's recorded.** `judgments` merges each selection's judgments (the `selection` entries used, their file
    and SHA-256), `critical_state_friction_angle` for each unit the rule read it for, and the geology map's
    `soil_class` per unit with where it came from (the argument or the sources).
17. **It stops at the set** (SPEC §1.4): no partial factors, design values, tension cut-off or program file.

### `soil_class`
18. **The defined values:** `coarse` and `fine` are read by ψ's rule. `fill`, `rock` and `organic` are named,
    recognized and read by nothing yet. Any other value is still accepted by the map (0.1.0's maps keep opening)
    and is an error only where a rule needs a class (decision 13). `intermediate` and the column's rename stay
    with TODO #3.
19. **Where the set reads it** (SPEC §8.3: from the map, never USCS or the data): `geology_map=` (a path, read
    with the map's own checks, or `p.geology_map`) → the classes the sources carry → an error naming the unit and
    saying to pass `geology_map=`. 🟡 To carry them, a Project's datasets record `attrs["soil_classes"]`
    (`{geology_unit: soil_class}`, from the map, beside `attrs["palette"]`), and the fits and the conversion keep
    it, as they keep `judgments_file`. Two sources that carry different classes for a unit are an error. An
    argument that differs from what the sources carry warns, as a judgment argument does. The rows' own
    `soil_class` column isn't read: a fit has no rows, and a CSV's column is the user's text.

### `select()` with no source
20. **`select(value=…)` with no sources** is allowed when every entry is `value` or `none`: there is nothing to
    compare or place, `.comparison` is None, `.positions()` is empty, and the unit is `display_units`, else the
    selection's `units:`. Any other method is an error saying no source carries the parameter. The set uses this
    for ψ, E′ and ν′, so their selections are read by `select()`, not re-implemented (SPEC §5).

### SPEC changes in this commit
21. - §5, the function list: `mohr_coulomb_set` (M18 (f)). "Model sets": the base and its origins (selection,
      rule, judgment, blank), the Mohr–Coulomb set (its five parameters and its citation), ψ's rule and limit,
      the c′–φ′ check, constants only, and `select()` with no source.
    - §8.3: `soil_class`'s defined values and that ψ reads them (decisions 18–19).
    - §12.4 and the TODO deletions wait for the close-out.

### Golden values
Hand calculations; SI, angles in degrees.

- **G1, the example Terrace.** The set's c′ and φ′ equal `select()`'s for the same sources and file (161.811 psf,
  35.2902 deg; one calculation). Its φ′cv is 32 deg from `judgments.yaml`. ψ = (35.2902 − 32) / 0.8 = 3.2902 / 0.8
  = **4.1128 deg** (±0.0005, rounding of the selected φ′).
- **G2, the floor.** (e)'s G3 fit (c′ = 5 kPa, φ′ = 30°, three CD stages), both `fitted`, unit `Sand` (`coarse`),
  φ′cv = 32: (30 − 32) / 0.8 = −2.5 → **ψ = 0** with the floor's note. The pair is from one fit, so no warning.
- **G3, a value pair.** `Sand`: φ′ `value` 38 deg, c′ `value` 0 kPa, φ′cv 32: ψ = 6 / 0.8 = **7.5 deg**. The pair
  isn't `fitted` from one source: a warning, and the note.
- **G4, at and beyond the limit.** φ′ 44, φ′cv 32: 12 / 0.8 = **15.0 deg**. φ′ 45: 13 > 12, so ψ is blank with the
  reason, and a warning.
- **G5, fine.** `Clay` (`fine`), φ′ `value` 26 deg, c′ `value` 5 kPa: **ψ = 0**, citing Vermeer & de Borst (1984).
- **G6, ψ selected.** `Sand` as G3 with `dilatancy_angle: {method: value, value: 2, reason: …}`: **ψ = 2 deg**,
  origin `selection`; φ′cv isn't read or recorded.

### Acceptance criteria
1. G1: the example's set gives the Terrace c′ 161.811 psf and φ′ 35.2902 deg, equal to `select()`'s, and
   ψ 4.1128 deg, with E′ and ν′ blank for the reason in decision 14.
2. G2: ψ = 0 with the note, and no warning.
3. G3: ψ = 7.5 deg, and the pair warning names `Sand`.
4. G4: 15.0 deg at the limit; beyond it ψ is blank with the reason and a warning, never 15.
5. G5 and G6 hold; G6 records `selection` as ψ's origin and no `critical_state_friction_angle`.
6. A `fill`, `rock`, `organic`, blank or unknown `soil_class` with a φ′ and no ψ selection is an error naming the
   unit and class; `rock`'s names the Hoek–Brown set. The same unit with φ′ `none` gives a blank ψ and no error.
7. A coarse unit without φ′cv is an error naming the unit and the judgment; an argument overrides the file with a
   warning.
8. `soil_class` resolves `geology_map=` → the sources' `attrs["soil_classes"]` → an error; two sources that
   disagree are an error; a Project's datasets and a `mohr_coulomb_fit()` of them carry the classes.
9. A `trend:` selection of any parameter in the set is an error naming the unit and parameter.
10. A unit listed for c′ and not φ′ (or the reverse) is an error naming both; a source that gives none of the
    five parameters is an error.
11. `select()` with no source accepts `value` and `none`, refuses any other method, and converts a `value` to
    `display_units`.
12. Views agree: `.to_frame()`, `.provenance()`, `.to_dict()` and the printed summary give the same values;
    `.selections[...]` are the `SelectionResult`s the set used; on a Project's categorical `geology_unit`,
    nothing warns.
13. Docs: the selection guide's "Model sets" section runs from the example site's `judgments.yaml`; sheet 09's
    soil part is a site page; `mohr_coulomb_set` and `MohrCoulombSet` have API reference entries; the docstring
    gives the equation, inputs, the limit and the sources above.

### Changes to other docs
- `docs/analysis/statistics.md`: §7, the model sets and `mohr_coulomb_set()`; §6, `select()` with no source.
- `src/hangtu/columns.yaml`: `dilatancy_angle`, `drained_poissons_ratio`; `soil_class`'s description and values.
- `docs/site/`: the selection guide's "Model sets" section; `parameters/09-dilatancy.md` (the soil part of
  sheet 09: 5.2's Bolton relation as built, the ψ = 0 convention, the limit; 5.1, the practice rule and the rock
  part stay in the draft); page 04's stage D; `reference/stats.md`; the `nav`.
- `docs/drafts/parameters/09-dilatancy.md`, in this commit: [5] Vermeer & de Borst (1984) becomes [V] (pp. 3,
  13); K&M Eq. 4-16, p. 4-20 is added to 5.2; the stress-condition disagreement and Obrzud & Truty (2018) p. 107
  are recorded.
- `docs/TODO.md`, in this commit: #32 records what was verified here and that Bolton (1986) is still to check.
  At close, its Mohr–Coulomb part moves to SPEC §5 and is deleted, and #3 records the defined classes.
- `docs/drafts/parameters/README.md`, `CLAUDE.md`, SPEC §12.4: at close (intent's list).
