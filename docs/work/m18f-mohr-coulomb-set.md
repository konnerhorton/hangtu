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
