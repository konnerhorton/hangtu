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
