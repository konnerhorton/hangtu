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
