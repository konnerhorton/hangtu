# M14 (b): phase relations

## Intent
M14 is wave 1's second milestone (SPEC §1.3, §12.4). (a) built the density data: `p.density()`, with each
specimen's own water content and its sample's particle density, and `p.particle_density()`. This unit, (b), is
stage B for sheet 03 (Gs, e0, n) and the rest of stage B for sheets 01 (γ from phase relations) and 02 (activity).

**Goal:** from the rows `p.density()` gives (or a CSV in `ht.template("density")`'s shape), an engineer gets each
specimen's void ratio, porosity and degree of saturation, with the Gs each row used and where it came from. A
specimen whose values don't agree with each other is flagged. Where no particle density was measured, Gs is a
judgment the engineer writes down, never a default 2.65. Separately, activity A = PI / clay fraction is added to
the index properties.

**Why:**
- **e0 is the input the later waves ask for.** Wave 3's Soft Soil set (λ*, κ* from Cc, Cs and 1 + e0), the
  void-ratio functions in G0 correlations (wave 5) and k–e (wave 6) all need it (sheet 03 "Feeds"). It is normally
  back-calculated from γ, w and Gs, because sampling and trimming disturb a measured e0 (sheet 03 §1).
- **The pairing is already settled.** (a) put γ, w and ρs from one specimen and its sample on one row (M14 (a),
  decisions 3 and 4), so (b) builds formulas on that row and settles no data questions.
- **Phase relations are the best consistency check on density data.** S = w Gs / e well above 1 below the water
  table points to a wrong Gs, an under-measured γ, or a w from another specimen (sheet 03 §5.2, §7). (a) left the
  checks across values to (b) (decision 8).
- **Gs is chosen, often without a test.** Sheet 03 §1: Gs "is often assumed rather than measured". SPEC §4 says
  hangtu never fills a judgment in, so a missing Gs has to come from the judgments file, keyed and recorded, like
  `unit_weight` (M13). M14 (a) decision 3 decided this; (b) builds it.
- **Activity is the last of sheet 02's stage B.** LI and Ic are already analyses (M8). Activity separates clay
  minerals (kaolinite ≈ 0.4 to Na-montmorillonite ≈ 8, sheet 02 §3) and feeds the swelling screen in wave 3.

**Scope:**
- **Phase relations** as an analysis on a DataFrame (sheet 03 §1, §5.1–5.2): from γ, w and Gs per row, the void
  ratio, porosity, degree of saturation, dry unit weight (where the row has none) and saturated unit weight. The
  identities are exact; the source of each is cited from sheet 03's [V] references.
- **Consistency checks** on the result: S above 1 by more than a tolerance; γd given against γ / (1 + w) on CSV
  rows (B001 already checks AGS rows).
- **The `specific_gravity` judgment**, keyed by geology unit, used only where a row has no measured particle
  density. Every row says which Gs it used and where it came from (measured, assumed in the file with `#`, or the
  judgment).
- **Activity** A = PI / CF (Skempton 1953, via sheet 02 [2] eq. 4.16 [V]), with CF the clay content < 0.002 mm,
  which is the `iso14688` fraction system's `clay_content`.
- **Site pages:** sheet 03 promoted to `docs/site/parameters/03-*.md`, and the activity section added to a page
  for sheet 02 (promoted here, or only the part (b) builds; a spec question). Each with its example in
  `docs/site/examples/`.
- **Test data:** values in the test files and the example file whose golden values are hand-calculated, including
  a specimen with S > 1.

**Out of scope:**
- Relative density from emax/emin or SPT (not yet placed; M14 (a) decision 4).
- The initial void ratio measured on strength or oedometer specimens (`CONG_IVR`, `TRET_IVR`, …): waves 2 and 3.
  They are compared with e0 from phase relations, never pooled (sheet 03 §7).
- Rock porosity from `RDEN` (wave 4, M21).
- Gs from mineralogy (sheet 03 §5.3 is [U] and a judgment input, not a hangtu calculation).
- The coarse-fraction weighted Gs (sheet 03 §7, last but one bullet): noted in the docstring, not computed.
- A unit weight *derived* from phase relations replacing the `unit_weight` judgment in `vertical_stress()`. The
  result gives the engineer the values to choose from; the judgment stays a judgment.
- New plots: e0, n and S feed P01 and P07 as they are.
- TODO #45 (Gs carried in a user-defined AGS heading).

**SPEC and TODO touched:**
- SPEC §4 (the `specific_gravity` judgment joins the list of judgments), §10.3 (registry names), §12.4 (M14 row),
  §2.6 if a template changes.
- TODO #29 (the key for Gs: settled here).
- Parameter index rows 01, 02, 03 at the close-out; the 03 page and the 02 page or section on the site.

### Decisions (intent review, 2026-10-28)
1. **One analysis, `ht.analysis.phase_relations(df, *, judgments=None, ...)`**, a plain function on the
   density rows that returns them with new columns, the way `vertical_stress()` does. Activity is a separate
   function (or a column `plasticity()` adds when `clay_content` is present), because its rows come from
   `p.index_properties()`, not `p.density()`.
2. **Gs = ρs / ρw with ρw from `ht.settings.water_unit_weight` / g**, so γw used in e0 = Gs γw (1 + w) / γ − 1
   and ρw used in Gs are the same water and cancel: e0 = ρs (1 + w) / ρ − 1, exactly. (a) left this to (b)
   (decision 2). With that form, the e0 of an AGS row doesn't depend on γw or g at all.
3. **The `specific_gravity` judgment is keyed by geology unit**, with an optional project-wide value that needs a
   `reason` (as `unit_weight` is, SPEC §4). Order for each row: a measured particle density on the row → an
   assumed (`#`) one on the row, with a warning counting them → the judgment → NaN with a count. The judgment
   never overrides an assumed `#` value: the file's value is the one the lab used, so it stays the row's value,
   flagged as assumed.
4. **S > 1 is flagged, not corrected.** Rows keep their values; a column (or the result's attrs) marks those
   beyond the tolerance, with a warning naming them. The tolerance (sheet 03 says about ±5 %, marked as judgment)
   is an argument with a default, since it is a reporting threshold, not a design input. To settle in the spec.
5. **Activity's CF is the < 0.002 mm fraction**, read only from `clay_content` with `fraction_system` =
   `iso14688`; another system is an error, not a conversion, as `uscs()` checks its own system. NP gives a
   distinct flag, not 0.

### Open (for the spec step)
- Names against the whole registry: `specific_gravity` (and the column saying where it came from), `void_ratio`
  or `initial_void_ratio`, `porosity`, `degree_of_saturation`, `saturated_unit_weight`, `activity` (which may
  read as ambiguous: `clay_activity`?).
- Whether S > 1 is checked against the water level (only below it is S ≈ 1 expected), which needs the
  `water_level` judgment and a ground level, or simply S > 1 anywhere, which is impossible regardless.
- Whether rows with `sample_condition = RECOMPACTED` get e0 (they do in the arithmetic; the docstring says what
  it means).
- Field (`IDEN`) rows have no particle density: they take the judgment by geology unit.
- Whether the example file needs a `specific_gravity` entry in its `judgments.yaml`.
- The verification of each [U] citation the unit relies on (Skempton 1953 original; the rest of sheet 03's
  formulas are [V]).

## Spec
Two analyses, one judgment and one dataset column. Numbered items refer to this section's decisions; "intent n"
to the intent's. 🟡 marks a value proposed here, awaiting review.

### Changes
- **SPEC §4:** a "Phase relations" bullet (Decisions 1–3: Gs from ρs and γw so e0 doesn't depend on γw, the order
  of Gs sources); the judgments list gains `specific_gravity` by geology unit.
- **SPEC §10.2:** `p.index_properties()` gains `clay_activity` (Decision 7).
- **`docs/data/datasets.md` §6.6:** the `clay_activity` row and its rule.
- **Registry (`columns.yaml`):** `specific_gravity`, `specific_gravity_source`, `void_ratio`, `porosity`,
  `degree_of_saturation`, `oversaturated`, `clay_activity`; `saturated_unit_weight` and `dry_unit_weight` gain
  `derived: ht.analysis.phase_relations()` as a source. Checked against the whole registry, `defaults.yaml`
  and the plot arguments: no collisions. Presets for `void_ratio`, `porosity` and `degree_of_saturation`, so P01
  draws them with sensible limits.
- **Judgments (`_judgments.py`):** the `specific_gravity` kind (Decision 4).
- **TODO #29:** Gs by geology unit, settled.
- **Docs site** (separate docs commits after this one, as for pages 04–10): sheet 03 promoted to
  `docs/site/parameters/03-specific-gravity-and-void-ratio.md` and sheet 02 to `02-index-properties.md`, with
  verified content only (Decision 9).
- **Parameter index** at the close-out: 01 B gains γ, γd and γsat from phase relations; 02 B **built**; 03 B
  **built**.

### Decisions
1. **`ht.analysis.phase_relations()`.**
   ```python
   phase_relations(df, *, specific_gravity=None, judgments=None, saturation_tolerance=5,
                   units=None, display_units=None) -> pd.DataFrame
   ```
   - **Input:** `bulk_unit_weight` and `water_content` (required), `particle_density` and
     `particle_density_assumed` (optional, read together), `dry_unit_weight` (optional), and the judgment's key
     column (`geology_unit`, or the file's `by:`) where a row needs the judgment. These are `p.density()`'s
     columns and `ht.template("density")`'s, so AGS and CSV rows go through one function. Units: `units=`, then
     `df.attrs["units"]`, else an error naming the column (SPEC §2.6).
   - **Output:** a copy of `df`, no row dropped or reordered, with `specific_gravity`,
     `specific_gravity_source`, `void_ratio`, `porosity`, `degree_of_saturation`, `saturated_unit_weight` and
     `oversaturated`, and `dry_unit_weight` filled where it was blank (a given value is kept). Unit weights in
     the unit weight unit of `display_units` (default `ht.settings.display_units`, as `vertical_stress()`),
     recorded in `df.attrs["units"]`. Existing output columns are replaced, with a warning naming them.
   - **Equations** (sheet 03 §1, §5.1–5.2; GEC 5 §4.7 eqs. 4.9–4.10 p. 4-8 and EPRI EL-6800 eq. 2-9 p. 2-17, both
     [V]), with w as a decimal:
     - e = Gs γw (1 + w) / γ − 1
     - n = e / (1 + e), in percent
     - S = w Gs / e, in percent
     - γsat = γw (Gs + e) / (1 + e): the unit weight at the same void ratio, fully saturated
     - γd = γ / (1 + w)
   - **Blanks:** a row with blank γ, w or Gs, or γ ≤ 0, gets blank outputs, counted by reason in one warning.
     γ is required even where γd is given: e from γd alone would leave S without its consistency check.
   - **Recorded:** `df.attrs["phase_relations"]` = `{"water_unit_weight": "9.81 kN/m3", "gravity":
     "9.80665 m/s2", "saturation_tolerance": 5}`, and `df.attrs["judgments"]` as `vertical_stress()` records
     it, with only the keys used.
   - **Docstring:** the TEMPLATE checklist: equations, inputs, the judgment taken, and the assumptions (one
     specimen's γ and w; a recompacted specimen's e is the specimen's, not in situ; the coarse fraction above
     4.75 mm isn't in a pycnometer Gs, sheet 03 §7).
2. **Gs from particle density, so γw cancels** (intent 2). Gs = ρs / ρw, with ρw = γw / g, γw =
   `ht.settings.water_unit_weight` and g = 9.80665 m/s² (the same g as `p.density()`, M14 (a) decision 2). Then a
   row with a measured ρs has e = ρs (1 + w) / ρ − 1 exactly, whatever γw is set to. With the default γw = 9.81
   kN/m³, ρw = 1.000342 Mg/m³, so Gs = 2.68 Mg/m³ / 1.000342 = 2.6791. A Gs from the judgment is a number and
   enters e with γw as written.
3. **Where each row's Gs comes from** (intent 3), first that applies, named in `specific_gravity_source`:
   1. `particle_density` on the row, not assumed → `measured`;
   2. `particle_density` on the row, assumed (`#` in the file) → `assumed`, with one warning counting the rows.
      The judgment never replaces it: it is the value the lab used;
   3. the `specific_gravity` judgment: `specific_gravity=` (a number, or `{geology_unit: number}`), else
      `judgments=`, else the project's file in `df.attrs` → `judgment`;
   4. a judgment missing for a key a row needs is an error naming the judgment, the keys and how to set it (SPEC
      §4); a row whose key is blank gets a blank Gs, counted.

   - The judgment is read only when some row needs it: a frame where every row has a particle density needs no
     judgments file.
   - `specific_gravity=` warns when the file also has the judgment (SPEC §4, an argument overriding the file). It
     never replaces a row's particle density.
   - 🟡 `particle_density` without a `particle_density_assumed` column is an error saying to add it, since hangtu
     can't tell measured from assumed. A blank cell in that column is read as not assumed: `p.density()` writes
     True or False on every row with a particle density, so a blank only comes from a hand-made CSV, and the
     docstring says so.
4. **The `specific_gravity` judgment.** Keyed `values`, `by:` a stratigraphy column (usually `geology_unit`),
   field `specific_gravity`, with an optional `project` value that needs a `reason`, as `unit_weight` (SPEC §4):
   ```yaml
   specific_gravity:
     by: geology_unit
     values:
       Alluvium: {specific_gravity: 2.68, reason: "median of 6 LPDN, measured only"}
     project: {specific_gravity: 2.70, reason: "quartz and feldspar sands, GEC 5 p. 4-8"}
   ```
   - 🟡 **No `units:` block.** Gs is a ratio with no unit, and a `%` would be accepted as dimensionless by the
     unit check, which would be wrong by a factor of 100. `units:` for this judgment is an error saying it takes
     none.
   - The value must be > 0 (error). Outside 2.0–3.2, QC B003's particle density range, it warns, naming the key
     and saying what lies outside (peat lower, ores higher).
   - The docstring shows how to inform it: `ht.analysis.summary_by(pd_rows[~pd_rows.particle_density_assumed],
     "particle_density")`, measured values only (sheet 03 §7: assumed values are never pooled with measured).
5. **Oversaturated rows are flagged, not corrected.** `oversaturated` is True where S > 100 % +
   `saturation_tolerance` percentage points (🟡 default 5, sheet 03 §5.2's ±5 %, marked there as judgment; it is a
   reporting threshold, not a design input). One warning names the rows (hole, depth) and the likely causes from
   sheet 03 §5.2: a wrong Gs, an under-measured γ, or w from another specimen.
   - Checked everywhere, without the water level: S > 100 % is impossible above or below it.
   - S well under 100 % isn't flagged: above the water table, or with gas or swelling, it is real.
6. **A given γd that disagrees with γ / (1 + w)** beyond QC B001's `dry_density_tolerance` (0.03 Mg/m³, read from
   the QC rules and taken as a unit weight × g = 0.294 kN/m³) warns, naming the rows. The given value is kept and
   not used: e uses γ and w. On AGS rows B001 has already reported it; the warning says so when
   `df.attrs` shows the rows came from a project.
7. **Activity.** `ht.analysis.clay_activity(df)` adds `clay_activity` = PI / CF (Skempton 1953, as given in GEC 5
   eq. 4.16 p. 4-14 [V]), with CF the percentage by dry mass finer than 0.002 mm.
   - Reads `plasticity_index`, `non_plastic` and `clay_content`, with `fraction_system` = `iso14688` (the system
     whose clay is < 0.002 mm). A missing or other `fraction_system` is an error, as `uscs()` checks its own
     (intent 5).
   - NP rows, a blank PI or CF, and CF = 0 get a blank, counted by reason in one warning. NP is never A = 0.
   - **`p.index_properties()` gains `clay_activity`**, from `gradation(fractions="iso14688")` on the same chosen
     `GRAT` specimen, which isn't returned, as the `aashto` fractions aren't (datasets.md §6.6). A curve that
     doesn't reach 0.002 mm (a sieve-only grading) gives a blank, by `gradation()`'s rule of never extrapolating;
     that blank isn't warned about, as a sample with no grading isn't classified.
   - Docstring: PI is measured on the < 425 µm fraction and CF on the whole sample; the ratio is used as
     published, not corrected. Typical values (GEC 5 Table 4-6) are on page 02.
8. **Field and recompacted rows** go through like the others. A field (`IDEN`) row has no particle density, so it
   takes the judgment by geology unit. A `RECOMPACTED` row's e is the recompacted specimen's, which the docstring
   says; `sample_condition` stays on the row to filter it.
9. **Pages 02 and 03** are promoted with verified content only (SPEC §1.3 publishing rule, M13 (a) decision 9).
   - **03:** GEC 5, EPRI EL-6800, Robertson & Cabal 2022 and Ching & Schweckendiek 2021 are [V]; ISRM (1979) was
     verified in M13 (a). Left in the sheet, not on the page: the PLAXIS λ*, κ* expressions (a vendor's), the
     mineral Gs values (Mitchell & Soga, [U]), Gs COV "a few %" ([U], no source), and the error-propagation
     figures marked as judgment.
   - **02:** Kulhawy & Mayne, GEC 5 and Ching & Schweckendiek are [V]; the methods table links `plasticity()`,
     `gradation()`, `uscs()`, `aashto()` and `clay_activity()`. Left out: the Skempton (1953) original (cited
     through GEC 5), Mayne et al. (2009) (its FC–Ic equation is wave 5's CPT work, not built), Hollmann & Thewes
     (2013) (P18, not placed), and the drying temperature note.
   - Neither page reproduces a source table whole: GEC 5 Table 4-6 (activity by mineral) gives the range and two
     end values with the locator, as sheet 02 §3 does.

### Sources
- Phase relations: Loehr et al. (2016), GEC 5, FHWA NHI-16-072, §4.7 eqs. 4.9–4.10 p. 4-8; Kulhawy & Mayne
  (1990), EPRI EL-6800, eq. 2-9 p. 2-17. Both [V] in sheet 03; the other expressions are identities from the
  definitions.
- Activity: GEC 5 eq. 4.16 p. 4-14 and Table 4-6 [V]; Skempton (1953) named as the original, not checked.
- Standard gravity g = 9.80665 m/s² (exact).
- No correlation is used: every equation is an identity, so there is no validity range beyond the inputs being
  physical (γ > 0, Gs > 0, w ≥ 0).

### Acceptance criteria
Golden values hand-calculated with γw = 9.81 kN/m³ and g = 9.80665 m/s², so ρw = 1.0003416 Mg/m³. Tolerance 1e-6
relative (the hand calculation carries seven figures), unless a criterion says otherwise.
1. **Measured Gs** (`site_si.ags`, BH1-U1: ρ 1.95 Mg/m³, w 25 %, ρs 2.68): γ = 19.122967 kN/m³;
   `specific_gravity` 2.679085, `measured`; `void_ratio` 0.717949 (= 2.68 × 1.25 / 1.95 − 1); `porosity`
   41.7910 %; `degree_of_saturation` 93.2896 %; `saturated_unit_weight` 19.398075 kN/m³; `dry_unit_weight` the
   row's own 15.298374 (1.56 × g); `oversaturated` False.
2. **γw cancels:** with `ht.settings.water_unit_weight = "10 kN/m3"`, AC 1's `void_ratio` and `porosity` are
   unchanged (1e-12 relative) and `specific_gravity` is 2.68 × 9.80665 / 10 = 2.628182.
3. **Assumed Gs** (BH2-U2: ρ 2.02, w 18 %, ρs `#2.65`, `RECOMPACTED`): `specific_gravity` 2.649095, `assumed`;
   `void_ratio` 0.548020; `porosity` 35.4013 %; `degree_of_saturation` 87.0109 %; the assumed-value warning;
   with a `specific_gravity` judgment of 2.70 for its unit, the values don't change.
4. **Judgment Gs** (the field row, BH1 at 0.50 m: ρ 1.85, w 15 %, no ρs; judgment 2.70 for its geology unit):
   `specific_gravity` 2.70, `judgment`; `void_ratio` 0.678952; `porosity` 40.4390 %; `degree_of_saturation`
   59.6508 %; `saturated_unit_weight` 19.742984 kN/m³; `dry_unit_weight` filled, 15.775915 kN/m³;
   `attrs["judgments"]` holds the key and value used.
5. **Oversaturated** (CSV: γ 20.0 kN/m³, w 30 %, `specific_gravity=2.70`): `void_ratio` 0.721655,
   `degree_of_saturation` 112.2420 %, `oversaturated` True, and the warning naming the row; with
   `saturation_tolerance=15`, False and no warning.
6. **US twin:** `site_us.ags` gives AC 1, 3 and 4 after conversion (1e-9 relative between twins); with
   `display_units="US"` the unit weights are in pcf and e, n and S unchanged.
7. **Precedence:** argument → `judgments=` → `attrs["judgments_file"]` → error, as SPEC §4; the override warning
   fires; a frame where every row has ρs runs with no judgments file; a missing key errors naming it; a project
   value fills an unlisted unit with the warning.
8. **Judgment file checks:** `units:` under `specific_gravity` is an error; a value ≤ 0 is an error; 1.5 warns.
9. **Input checks:** `particle_density` without `particle_density_assumed` is an error; a missing
   `bulk_unit_weight` unit is an error naming the column; blank γ, w or Gs give blanks counted by reason.
10. **γd check:** a CSV row with γ 19.0 kN/m³, w 20 % and γd 17.0 (expected 15.833) warns; with γd 15.9 (within
    0.294) it doesn't.
11. **Activity:** PI 30, CF 40 → 0.75; PI 28, CF 12 → 2.333333; NP → blank, counted as non-plastic; CF 0 →
    blank, counted; `fraction_system = "astm_uscs"` → error.
12. **`p.index_properties()`:** a sample with a hydrometer curve reaching 0.002 mm gets `clay_activity` (golden
    value from the test file's PI and the curve's P(0.002), hand-calculated in the plan); a sieve-only sample gets
    a blank and no warning.
13. **Feeds the plots:** `ht.plot.profile(phase_relations(p.density(), ...), "void_ratio")` and
    `geology_unit_comparison(..., "void_ratio")` run with no warning beyond the analysis's own.
14. **Docs:** the reference test passes for `phase_relations` and `clay_activity`; pages 02 and 03 and their
    examples build with `zensical build --clean --strict`.

## Plan
Seven build commits, each with ruff and pytest green, then the two page commits (docs, with approval) before the
close-out. Reused, not rebuilt:
- `analysis/_judgment_values.py`: `read_judgments()`, `from_file()`, `take()`, `warn_unused()`, `Values`;
- `vertical_stress()`'s `_water_unit_weight()` and its missing-judgment message (`_missing()`), moved to
  `_judgment_values.py` in step 2 if a second caller needs them as they are;
- `_data.numeric_column()`, `rows_text()`; the unit resolution `vertical_stress()` uses (`units=` → attrs → error);
- `gradation()` and `summarize_curves()` in `datasets/_index.py`, as the `aashto` fractions are run.

### 1. `registry: phase relation and activity columns, with presets`
- `columns.yaml`: `specific_gravity` (dimensionless), `specific_gravity_source` (text: measured, assumed,
  judgment), `void_ratio` (dimensionless), `porosity` and `degree_of_saturation` (percent), `oversaturated`
  (bool), `clay_activity` (dimensionless); `derived: ht.analysis.phase_relations()` on `saturated_unit_weight` and
  `dry_unit_weight`.
- `config/defaults.yaml`: presets `void_ratio` (0–2), `porosity` (0–100) and `degree_of_saturation` (0–120,
  so oversaturated rows show inside the axis), each `start_at_zero`.
- Tests: the registry and preset tests that exist (names, kinds, presets resolve); no behavior yet.

### 2. `M14: the specific_gravity judgment`
- `_judgments.py`: `KINDS["specific_gravity"]` (keyed `values`, field `specific_gravity`, `by:` from the file); a
  `unitless` flag on `Kind`, so `units:` is an error for it and its fields need none (Decision 4); `POSITIVE`
  gains it; a value outside 2.0–3.2 warns when the file is read, naming the entry. `ht.judgments()`'s docstring
  shows the entry.
- `_judgment_values.py`: `from_file()` leaves a unitless field as given.
- Tests (`tests/test_judgments.py`): AC 8; a valid entry reads; `repr` shows it without a unit.

### 3. `M14: phase_relations() with Gs from particle density`
- New `analysis/_phase_relations.py`, exported as `ht.analysis.phase_relations`; reference entry in
  `docs/site/reference/analysis.md`.
- Units in, as Decision 1; γ and γd worked in kN/m³, γw from `ht.settings.water_unit_weight`, g = 9.80665 (the
  constant `p.density()` uses, imported, not repeated). Gs from `particle_density` (Mg/m³) as Decision 2, sources
  `measured` and `assumed` with the assumed warning. Rows with no particle density get a blank Gs, counted, in
  this step.
- The equations, blanks by reason, `oversaturated` and its warning, the γd check (Decision 6, reading B001's
  default from the QC rules), replaced-column warning, `attrs` record, output in `display_units`.
- Full docstring (TEMPLATE checklist), including the judgment, which step 4 wires.
- Tests (new `tests/analysis/test_phase_relations.py`): AC 1, 2, 3 (without the judgment part), 5, 6, 9, 10, and
  13 (P01 and P07 on the result).

### 4. `M14: phase_relations() takes the specific_gravity judgment`
- Rows with no particle density take `specific_gravity=` (number or `{key: number}`), else the file, by the
  file's `by:` column; the override warning; the missing-judgment error naming the keys; a blank key counted;
  the file read only when a row needs it.
- Tests: AC 3 (a judgment doesn't replace an assumed value), 4, 7; judgments files written in `tmp_path`.

### 5. `M14: add clay_activity()`
- New `analysis/_clay_activity.py`, exported as `ht.analysis.clay_activity`; reference entry. Checks
  `fraction_system == "iso14688"` as `uscs()` checks its own; blanks counted by reason (NP, blank PI or CF,
  CF = 0).
- Tests (new `tests/analysis/test_clay_activity.py`): AC 11.

### 6. `M14: clay_activity in p.index_properties()`
- `datasets/_index.py`: `gradation(fractions="iso14688")` on the chosen curves, not returned, its warnings not
  shown (as the second run is today); `clay_activity()` on the combined row; `clay_activity` in `COLUMNS` after
  `aashto_group_index`.
- `tests/data/ags/_make_files.py`, `joins.ags`: a hydrometer grading for J2-U1 specimen 2 at 2.20 m, the same
  specimen as its water content and its second `LLPL` (LL 40, PL 20, so PI 20): a `GRAG` row and `GRAT` points
  2.00 mm 100 %, 0.063 85, 0.020 60, 0.0063 40, 0.002 25. **Golden:** CF = P(0.002) − P(0) = 25 − 0 = 25 (on a
  point), so `clay_activity` = 20 / 25 = **0.80**. J1-B4's sieve-only curve gives a blank, with no warning.
  - The six new lines move `joins.ags`'s `LDEN` and `LPDN` lines by 6; the tests that name them follow
    (`test_density.py` AC 10's line 96 becomes 102). J2-U1 now has a grading, so it gets a USCS symbol (fines
    ≥ 85 %, LL 40, PI 20 above the A-line: CL); tests that expected it blank follow.
- `ht.template("index")` is unchanged if it isn't `p.index_properties()`'s shape; if it is, it gains
  `clay_activity` under the SPEC §2.6 rule and `test_registry.py` follows.
- Tests: AC 12 in `tests/datasets/test_index_properties.py`.

### 7. `M14: Gs judgment in the example project; close out (b)`
Comes after the two page commits below, so the close-out can state the pages built.
- `src/hangtu/examples/data/judgments.yaml`: a `specific_gravity` entry by geology unit, with a reason, so the
  page 03 example runs end to end on `ht.examples` (`p.density()` → `phase_relations()` → P01 of `void_ratio`).
- **Close-out:** the parameter index (01 B, 02 B built, 03 B built); the `CLAUDE.md` status paragraph; SPEC §12.4's
  M14 row if its wording needs "done". `docs/TODO.md` (#29) is left to the user, uncommitted.
- **Look at the output:** P01 of `void_ratio` and `degree_of_saturation` on the example project, US and SI.
- **Verification:** each AC reported met or not, with its test; the lowest-versions run; the strict docs build
  (AC 14).

### Pages (docs commits, between steps 6 and 7, each shown for approval)
- `docs: page 03, specific gravity and void ratio`: promoted from sheet 03 as Decision 9, with
  `docs/site/examples/phase-relations.py`, linked in `zensical.toml`'s `nav`.
- `docs: page 02, index properties`: promoted from sheet 02 as Decision 9, with
  `docs/site/examples/clay-activity.py` (a small frame built in the example, since the example file has no
  hydrometer data), linked in the `nav`.
