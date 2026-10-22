# m13a-judgments

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). It splits in two units: **(a)**, this one, the judgments file
and `vertical_stress()`; **(b)** C_N / (N1)60, the hammer-efficiency changes, the correlations framework and the
first correlation set.

**Goal:** a project's judgments (unit weights, water levels) in one file with units and reasons, read the same way
by every analysis that needs them (SPEC §4: judgments have no defaults), and the first such analysis: total, pore
and effective vertical stress, integrated through each hole's log.

**SPEC and TODO touched:** §2.6 (units in the file), §4 (judgments, precedence), §10 (`p.stratigraphy()`), §12.4
(M13); TODO #30 (settled here), #33 (closed: hammer efficiency is data). `docs/drafts/analysis.md` §4.1 (the depth
profile and `interpolation=` go away).

### Draft shape of `judgments.yaml`
```yaml
# judgments.yaml: this project's judgments (SPEC §4)
unit_weight:
  by: geology_unit            # the log column the values are matched on (geology_unit, uscs_symbol, ...)
  units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
  values:
    Fill:     {bulk_unit_weight: 18.5, reason: median LDEN, n=12}
    Alluvium: {bulk_unit_weight: 19.0, saturated_unit_weight: 20.0, reason: ...}
  # or, for a quick look: project: {bulk_unit_weight: 19.0, reason: ...}
water_level:
  units: {depth: m}
  project: {depth: 3.0, reason: ...}      # optional
  by_hole:
    BH01: {depth: 2.5, reason: standpipe reading 2026-09-14}
    BH02: {depth: 3.0, reason: assumed equal to BH01, no record}
```

### Decided
1. **Units inside the file:** a required `units:` block per judgment; SPEC §2.6 resolution; missing → error naming
   the judgment.
2. **Unit weight is by stratigraphy, not by depth.** Parameters are generally on an engineering-unit basis.
   - Values per unit, matched by string on a configurable log column (`by:`), so user-defined units or USCS
     classes both work, provided the log carries that column.
   - `bulk_unit_weight` required; `saturated_unit_weight` optional, used below the water table where given.
   - One project-wide value is allowed, with a required `reason`.
   - `interpolation=` and the depth profile from analysis draft §4.1 go away; "by geology unit" moves from Later
     into this unit.
3. **σv is integrated through each hole's log**, so the log is an input: from the M7 geology joins for a
   `Project`; for CSV, a per-hole strata table (`loca_id, depth_top, depth_base, <unit column>`).
4. **Water level:** `by_hole` entries plus an optional project-wide value with a required `reason`.
   - An unlisted hole uses the project value, with a warning naming the holes.
   - An unlisted hole with no project value → **error** naming the holes.
5. **Precedence:** direct argument (`unit_weight=...`) → `judgments=j` → the Project's judgments carried in
   `df.attrs` → error. An argument overriding a file value warns. `judgments=j` differing from the Project's file
   warns.
6. **Lookup:** a `Judgments` object, `j = ht.judgments("judgments.yaml")`, re-read on each call; `p.judgments` on a
   Project, carried by its datasets in `df.attrs`. When attrs are lost (merge, concat) the error says to pass
   `judgments=`.
7. **Recorded on the result:** each judgment's value, key and source (argument, or path + SHA-256) in
   `df.attrs["judgments"]`.
8. **Hammer efficiency is data, not a judgment** (closes TODO #33). `ISPT_ERAT` → `energy_ratio` is already used
   first. Unit (b) adds: a warning when the argument or setting fills blanks, naming the holes; values by hole
   (`hammer_efficiency={"BH01": 80}`).
9. **γw stays a setting** (`ht.settings.water_unit_weight`). New TODO: γw as a judgment for sites that need two
   values (seawater and fresh).

10. **String matching:** a unit in the log with no value → error; a judgment for a unit not in the data → warning.
11. **Log edges:** a gap between layers, a log starting below 0, or a hole with no log → error naming the hole and
    depth range. A test below the log base carries the last layer down, with a warning.
12. **CSV log is a new template, per hole** (`loca_id` required). The P01 `strata` overlay template is not
    extended: it stays a single stratigraphy with forgiving rules, while the stress log is complete and strict.
    An idealized profile applied to every hole is not in this unit.
    The overlay's bands now take the points' colors, from the data's palette first (`plot-review-fixes`), so a
    table that went through the geology map colors the same as the points.
13. **Template name:** `ht.template("stratigraphy")`: `loca_id, depth_top, depth_base, geology_unit` (the `by:`
    column may be another, e.g. `uscs_symbol`). `log` was rejected: it collides with `log=True` for log axes.

14. **`p.stratigraphy()` is a public dataset**, in the same shape as `ht.template("stratigraphy")` (SPEC §2.6
    template rule): GEOL layers with `geology_unit` through the geology map (datasets.md §5.2), `soil_class`,
    `geology_description`, `source_line`. Users can inspect it, export it, edit it (reclass by USCS, say) and pass
    it back. New section in `docs/data/datasets.md`.
15. **The log is always passed explicitly:** `vertical_stress(p.spt(), stratigraphy=p.stratigraphy(),
    judgments=p.judgments)`. It's data the user may have edited, so it's never picked up from attrs.
16. **Overlapping layers (QC G003) → error** naming the holes and depths and pointing to `p.qc()`. This differs
    from the datasets' placement rule (deepest top wins, datasets.md §5.4) because stress can't be integrated
    through two layers at once.

17. **Publishing (TODO #30) is settled in unit (a)'s spec**, with sheet 01 as the first page promoted to
    `docs/site/parameters/`. Starting point: values with citations, short sets of class boundaries; no whole
    tables or charts reproduced. Sheet 01's [U] items (ISRM 1979, Duncan 2000's COV table, ISO 18674-4) are
    verified or cut.

### Names (agreed; checked against `columns.yaml`, `defaults.yaml` and the plot arguments; no collisions)
`water_level` replaces `groundwater` everywhere, including the file sample above. `stratigraphy` is in depth only
(no elevation pair).

| Name | Kind | Quantity | Label | Notes |
|---|---|---|---|---|
| `total_vertical_stress` | column | stress | Total vertical stress, σ_v0 | |
| `pore_pressure` | column | stress | Pore pressure, u_0 | In situ; hydrostatic in M13, the method in attrs. Test-specific pore pressures get a test prefix (`cpt_…`, `triaxial_…`) |
| `effective_vertical_stress` | column | stress | Effective vertical stress, σ′_v0 | |
| `saturated_unit_weight` | column / file field | unit_weight | Saturated unit weight, γ_sat | Beside the existing `bulk_unit_weight` |
| `water_level` | argument + judgment key | – | – | Replaces `groundwater` from the draft: P01 already has `water_level=` with a per-hole `loca_id, depth\|elevation` DataFrame, so the same format serves both |
| `unit_weight` | argument + judgment key | – | – | |
| `water_unit_weight` | setting | unit_weight | Unit weight of water, γ_w | 9.81 kN/m³ / 62.4 pcf |
| `stratigraphy` | template, argument | – | – | `vertical_stress(df, *, stratigraphy=..., judgments=...)` |
| `ht.judgments(path)` → `Judgments`; `p.judgments` | API | – | – | |

### Open
- **`strata=` and `p.stratigraphy()`.** The overlay takes one stratigraphy with a depth or elevation pair;
  `p.stratigraphy()` is per hole and in depth only. Either `strata=` accepts it (for one hole, or with a
  `loca_id` filter), or the user picks one hole's layers. Settle in the spec step.

## Spec

The judgments file, `ht.judgments()`, `p.stratigraphy()` and `ht.analysis.vertical_stress()`. Numbered items
refer to the intent's decisions; this section settles the details and the open item.

### Changes
- **SPEC §2.6:** a judgments file declares its units in a `units:` block per judgment, read like `df.attrs["units"]`;
  the template list gains `stratigraphy`.
- **SPEC §4:** the "Effective vertical stress" bullet is rewritten (by stratigraphy, from the judgments, Decision 6).
  "Judgment inputs": the resolution gains `judgments=` and the Project's file carried in `df.attrs` (intent 5); a
  project-wide value, where a judgment allows one, fills unlisted keys with a warning (Decision 2); the file format is
  in this file until a later unit moves it to a topic doc; the `hammer_efficiency` sentence becomes "hammer
  efficiency is data, not a judgment (intent 8); `hammer_efficiency` stays a session setting".
- **SPEC §8.3:** the interval rule's overlap sentence adds "except `vertical_stress()`, which errors (intent 16)".
- **SPEC §10.1–10.2:** `p.set_judgments(path)`, `p.judgments` and `p.stratigraphy()`. **§11:** the Phase 2 sketch
  gains the judgments and `vertical_stress()` lines. **§12.4:** M13's row names its two units.
- **`docs/drafts/analysis.md` §4.1:** replaced by a pointer to this section, keeping the (N1)60 paragraph and the
  open C_N question for unit (b).
- **`docs/data/datasets.md`:** §2 lists `p.stratigraphy()`, `p.set_judgments()` and `p.judgments`; new §6.7
  `p.stratigraphy()` (Decision 4); §11 the registry changes.
- **`columns.yaml`:** the four columns of the intent's names table; the `stratigraphy` template; `depth_top` and
  `depth_base` describe any interval (a tested zone or a layer) and add `GEOL.GEOL_TOP` / `GEOL.GEOL_BASE`.
  **`defaults.yaml`:** the `water_unit_weight` setting; presets for the three stresses (`start_at_zero`, typical
  0–500 kPa) so `ht.plot.profile(df, value="effective_vertical_stress", preset=...)` works.
- **TODO:** #29 records the two keys settled here; #30 and #33 move to Done; new items: γw as a judgment (intent 9),
  and P01's `strata=` taking a per-hole stratigraphy directly (Decision 8).
- **Docs site:** sheet 01 promoted to `docs/site/parameters/01-unit-weight-and-vertical-stress.md` (Decision 9); a
  guide `docs/site/guides/judgments.md` with its example; reference entries for every new public name.
- **Parameter index:** at the close-out, 01's stage B becomes **part built** (vertical stress, M13); stage A, a
  dataset of measured unit weights, stays W1 (M14).

### Decisions
1. **The file.** YAML, top-level keys are judgment names. This unit knows `unit_weight` and `water_level`; any other
   key is an error listing the known ones (later waves add theirs). An empty file is valid and holds no judgments.
   ```yaml
   unit_weight:
     by: geology_unit
     units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
     project: {bulk_unit_weight: 19.0, reason: median LDEN of all units, n=41}   # optional
     values:
       Fill:     {bulk_unit_weight: 18.5, reason: median LDEN, n=12}
       Alluvium: {bulk_unit_weight: 19.0, saturated_unit_weight: 20.0}
   water_level:
     units: {depth: m}                 # or {elevation: ft}, or both if entries mix them
     project: {depth: 3.0, reason: highest standpipe reading, 2026-09}           # optional
     by_hole:
       BH01: {depth: 2.5, reason: standpipe reading 2026-09-14}
   ```
   - **Fields.** `unit_weight` entries: `bulk_unit_weight` (required), `saturated_unit_weight`, `reason`.
     `water_level` entries: exactly one of `depth` or `elevation`, and `reason`. Values are numbers, > 0 for unit
     weights. A water level above ground (depth < 0) is allowed, since it can be a required load case; it warns
     (Decision 6, "Standing water").
   - **`reason`** is required on a `project` entry (intent 2, 4) and optional on keyed ones.
   - **`by:`** is required with `values:`. **`units:`** is required and must give a unit for every field used, in
     the hangtu aliases (`kN/m3`, `pcf`, `m`, `ft`), checked against the field's quantity kind.
   - Keys (`Fill`, `BH01`) are strings matched exactly and case-sensitively, like the geology map. YAML turns some
     bare keys into other types (`1`, `yes`, `null`); the error for such a key says to quote it.
   - **Errors** name the file, the judgment and the entry ("judgments.yaml, unit_weight, values.Fill: …"): unknown
     key or field, missing `units`, `by` or `reason`, a unit that isn't one or is the wrong kind, a value that isn't
     a positive number, a YAML syntax error (with its line). They are raised when the file is read.
2. **Project values fill in, with a warning.** For both judgments a `project` entry is used for every key the data
   needs and `values` / `by_hole` doesn't list, with one warning naming them ("unit_weight: 'Made Ground', 'Peat'
   not in values; the project value 19.0 kN/m3 is used (median LDEN of all units, n=41)."). Without a `project`
   entry an unlisted key is an error naming them all (intent 4, 10). A keyed entry for something absent from the
   stratigraphy (a unit not in its `by` column, a hole not in its `loca_id`) is a warning, as it's likely a typo.
3. **`ht.judgments(path)` → `Judgments`.** Reads and checks the file at once, so errors show up where it's opened.
   - `j.path`; `repr(j)` lists each judgment, its key, its values with units and reasons.
   - Each analysis call re-reads the file and records the SHA-256 it read (intent 6, 7).
   - `judgments=` also takes a path, the same as `ht.judgments(path)`.
4. **`p.stratigraphy()`.** One row per GEOL layer: `loca_id, depth_top, depth_base, geology_unit, soil_class,
   geology_description, source_line`, ordered by hole and top, in the project's display units with
   `df.attrs["units"]` and `palette`, `geology_unit` mapped and ordered as in the other datasets (datasets.md §5.2).
   - Filters: `holes=`, `geology=`, `where=`, `contains=`, `geology_fields=` (adds the code columns, §5.3),
     `include_incomplete=`, `display_units=`. No `depth=` or `elevation=`: a cut log can't be integrated.
   - Layers are as written: overlaps and gaps are kept (QC reports them, G002, G003), unmapped codes warn as in
     every dataset. No GEOL group → empty with the usual warning.
   - `ht.template("stratigraphy")` is the same columns without `source_line`, so the template rule (SPEC §2.6)
     holds: `loca_id, depth_top, depth_base, geology_unit, soil_class, geology_description`. Only the first three and
     the `by:` column are needed by `vertical_stress()`.
5. **`p.set_judgments(path)` and `p.judgments`.** Stores the path (never the content) with the project, like the
   geology map: `None` removes it, and a rebuild with `overwrite=True` starts without one.
   - A relative path is stored relative to the database's folder, so a project folder can move whole.
   - Setting a path reads the file once, so a bad file errors there.
   - `p.judgments` is a `Judgments`, or None when no file is set; a file that has gone missing is an error naming
     the path and `p.set_judgments`.
   - Every dataset carries the resolved path in `df.attrs["judgments_file"]` when one is set.
6. **`ht.analysis.vertical_stress()`.**
   ```python
   vertical_stress(df, *, stratigraphy, judgments=None, unit_weight=None, water_level=None,
                   units=None, display_units=None) -> pd.DataFrame
   ```
   - **Input:** `df` needs `loca_id` and `depth` (units: `units=`, then `df.attrs`, else error). `stratigraphy`
     needs `loca_id, depth_top, depth_base` and the `by:` column, with its own declared units (error otherwise;
     unlike P01's overlays, nothing is assumed for an analysis).
   - **Output:** a copy of `df` with `total_vertical_stress`, `pore_pressure` and `effective_vertical_stress`, in
     the stress unit of `display_units` (default `ht.settings.display_units`, not a Project's, so it is predictable
     from the call alone), recorded in `df.attrs["units"]`. No row
     is dropped or reordered. Existing columns of those names are replaced, with a warning naming them. A row with a
     blank `depth` or `loca_id` gets blank stresses, counted in one warning.
   - **Calculation** (sheet 01 §5.2): σv0 = Σ γi Δzi from 0 to the test depth; above the water level γ =
     `bulk_unit_weight`, below it `saturated_unit_weight` where given, else `bulk_unit_weight`. u0 = γw max(0, z − zw)
     with γw = `ht.settings.water_unit_weight`, a quantity string with one default, `"9.81 kN/m3"`, converted as
     needed (62.45 pcf), so the display system never changes a result; a US user who wants 62.4 sets
     `"62.4 pcf"`. σ′v0 = σv0 − u0. A water level in elevation is converted with the
     hole's `ground_level` from `df` (one value per hole, else an error naming the holes).
   - **Standing water:** with the water level above ground (zw < 0), the water column is a load on the ground
     surface: σv0 gains γw |zw| and u0 = γw (z − zw) as before, so σ′v0 is what it would be with the water level at
     ground level. One warning per call names the holes and heights ("BH03: water level 1.2 m above ground; its
     weight is added to the total vertical stress"), and `df.attrs["vertical_stress"]` records it.
   - **Arguments** (intent 5): `unit_weight=` is a quantity string (`"19 kN/m3"`, every layer) or a dict
     `{geology_unit: "19 kN/m3" | {"bulk_unit_weight": ..., "saturated_unit_weight": ...}}`, matched on
     `geology_unit`. `water_level=` is P01's format: a number in `df`'s depth unit, a quantity string, a dict
     `{loca_id: number | string}` that must list every hole, or a DataFrame `loca_id, depth|elevation` with its own
     units (else `df`'s depth unit, with P01's warning). An argument replaces that whole judgment, with a warning
     when the file also has it; the other judgment still comes from the file.
   - **Missing judgment:** an error naming it, what it's keyed by and both ways to set it, with an example; when
     `df.attrs` has no `judgments_file` it adds "if df came from a Project dataset, merge and concat drop
     df.attrs: pass judgments=p.judgments".
   - **Recorded** (intent 7): `df.attrs["judgments"]` = `{name: {"source": "argument" | path, "sha256": ...,
     "by": ..., "values": {key: {field: "18.5 kN/m3", "reason": ...}}}}`, holding only the keys used, and
     `df.attrs["vertical_stress"]` = `{"pore_pressure": "hydrostatic", "water_unit_weight": "9.81 kN/m3"}`.
   - **Docstring:** the TEMPLATE checklist, including the assumptions of analysis draft §4.1 (level ground,
     geostatic, hydrostatic, not conservative in a fixed direction) and the judgments taken.
7. **The log** (intent 11, 16), checked per hole in `df`, from 0 down to that hole's deepest test:
   - a hole in `df` with no layers; a first top that isn't 0; a gap; an overlap; a layer with a blank top, base or
     `by` value; a layer whose base is above its top → error, one per call, listing every hole and depth range and,
     for gaps and overlaps, pointing to `p.qc()` (G002, G003).
   - Gaps and overlaps up to 0.01 m (QC G002/G003's default `depth_tolerance`) are rounding: the boundary is taken
     at the upper layer's base. Problems below a hole's deepest test don't stop the call.
   - A test below the log's base uses the last layer, with one warning naming the holes and depths (intent 11).
8. **`strata=` and `p.stratigraphy()`** (the open item). P01 doesn't change: the user picks one hole's layers and
   passes them, `strata=strata[strata["loca_id"] == "BH01"]`. P01 already reads only `geology_unit` and one depth
   or elevation pair and ignores other columns, so a filtered `p.stratigraphy()` works as it is. `strata=` taking a
   per-hole table directly (one hole, or a `loca_id` filter) is a new TODO, for later.
9. **Publishing (TODO #30).** A site page may reproduce: single values and ranges with their citation and locator;
   short sets of class boundaries as commonly cited (about ten rows or fewer); equations, with their source. It
   doesn't reproduce: a source table or chart whole, values read off a chart beyond the few a method needs, a
   chart's descriptors (GSI), or quoted text beyond a sentence. Figures on the site are hangtu's own. Sheet 01 is
   promoted under this rule, and Table 2-8 stays a citation. Its [U] items, settled in this step: ISRM (1979) and
   ISO 18674-4:2020 verified (the TRID record; iso.org); Duncan (2000)'s COV table, the Robertson & Cabal 2010
   symposium paper and the note on ASTM rock density cut, since the page has verified COV values (Ching &
   Schweckendiek 2021) and cites the CPT equation from the verified guide.

### Acceptance criteria
1. **Golden values** (SI, γw = 9.81 kN/m³): BH01 with Fill 0–2 m (γ 18), Clay 2–6 m (γ 19, γsat 20), Sand
   6–10 m (γ 19.5), water level 3.0 m:

   | z (m) | σv0 (kPa) | u0 (kPa) | σ′v0 (kPa) |
   |---|---|---|---|
   | 0 | 0 | 0 | 0 |
   | 1.0 | 18.00 | 0 | 18.00 |
   | 2.5 | 45.50 | 0 | 45.50 |
   | 3.0 | 55.00 | 0 | 55.00 |
   | 5.0 | 95.00 | 19.62 | 75.38 |
   | 8.0 | 154.00 | 49.05 | 104.95 |
   | 12.0 (below the log, warns) | 232.00 | 88.29 | 143.71 |

   The US twin (ft, pcf, the default γw, display US) agrees after conversion to 0.1 %; the same data with the water
   level in elevation gives the same result. With the water level 1.0 m above ground, z = 5.0 m gives σv0 =
   9.81 + 18 × 2 + 20 × 3 = 105.81, u0 = 58.86, σ′v0 = 46.95, and the standing-water warning.
2. **Precedence:** argument → `judgments=` → `df.attrs["judgments_file"]` → error, per judgment; the override and
   different-file warnings fire; a merged frame without attrs gives the error with the `judgments=p.judgments` hint.
3. **Fallbacks:** project values fill unlisted units and holes with the warning; without them the error names
   every missing key; a keyed entry absent from the stratigraphy warns.
4. **Log errors:** each case in Decision 7 raises with the hole and depth range; a 0.005 m gap doesn't; a gap
   below the deepest test doesn't.
5. **File errors:** each case in Decision 1 raises naming file, judgment and entry; an unquoted `yes` key gets the
   quoting hint.
6. **Recorded:** `attrs["judgments"]` holds the values and keys used, the source, and the SHA-256 of the file as
   read; editing the file between two calls changes the hash and the result without reopening the project.
7. **`p.stratigraphy()`** on the example and test files matches GEOL row for row, mapped; the template test holds;
   overlaps from `qc_defects.ags` are kept in the dataset and make `vertical_stress()` raise for BH3.
8. **`p.set_judgments`:** a relative path survives moving the folder with the database; `None` removes it; a bad
   file errors when set.
9. **P01:** `strata=` with one hole of `p.stratigraphy()`, filtered as in Decision 8, draws unchanged.
10. **Docs:** the reference test passes for every new public name; the guide example runs in `prepare_site.py`;
    `zensical build --strict` passes with the parameter page.

## Plan

Eight commits, each green (ruff and pytest); one refactor ahead of the new behavior. Each step that adds a public
name adds its reference entry in the same commit, since `tests/docs/test_site.py` fails without it. The spec commit
already updated SPEC, `datasets.md`, the analysis draft and TODO; the build brings the code, config, tests and site
up to them.

### 1. `config: share the YAML file reader`
A refactor, on its own: `qc._settings.read_yaml(path, what)` moves to `_config.read_yaml(path, what, guide)`, where
`what` names the file in errors ("QC rules", "accepted findings") and `guide` is the doc the syntax error points to.
QC's messages don't change. No behavior change; the QC tests pass as they are.

### 2. `registry: stress columns, the stratigraphy template, water_unit_weight`
- `src/hangtu/columns.yaml`:
  - `total_vertical_stress`, `pore_pressure`, `effective_vertical_stress` (`quantity: stress`, `scale: ratio`,
    labels from the intent's names table, `ags: ["derived: docs/work/m13a-judgments.md"]`) and
    `saturated_unit_weight` (`unit_weight`, "Saturated unit weight, γ_sat", the judgments file).
  - `depth_top` / `depth_base`: "Top (base) of an interval: a tested zone or a geology layer"; `ags` gains
    `GEOL.GEOL_TOP` / `GEOL.GEOL_BASE`.
  - Template `stratigraphy: [loca_id, depth_top, depth_base, geology_unit, soil_class, geology_description]`.
- `src/hangtu/config/defaults.yaml`: `water_unit_weight: 9.81 kN/m3` under settings; presets
  `total_vertical_stress`, `pore_pressure`, `effective_vertical_stress` (stress, linear, `start_at_zero`, typical
  `[0, 500]`).
- `src/hangtu/_settings.py`: `_water_unit_weight(value)`: a quantity string read with `units.parse_quantity(...,
  "unit_weight")`, positive, kept as written; errors show `ht.settings.water_unit_weight = "62.4 pcf"`.
- Tests: `tests/test_registry.py` picks up the new columns and template through its existing rules;
  `tests/test_settings.py`: the default, a pcf value, a bare number and a stress unit rejected, `reset()`;
  `tests/plot/` preset test (whichever checks every preset) covers the three stresses.

### 3. `M13: read and check the judgments file`
- New `src/hangtu/judgments.py`:
  - `Judgments` (thin; `__slots__`): `path`; `read() -> Read`, which re-reads the file, checks it and returns the
    parsed judgments with the SHA-256 of the bytes read; `__repr__` lists each judgment, its key (`by:` or "hole"),
    its values with units and reasons (Spec Decision 3).
  - `judgments(path) -> Judgments` checks the file once on creation (Decision 3).
  - The parsed form, private: per judgment `by`, `units` (field → unit string), `project` (entry or None), `values`
    (key → entry); an entry is `{field: float, "reason": str | None}`. Unit strings are checked with
    `units.parse_unit` and `check_dimension` against the field's kind (`unit_weight`, `length`).
  - Every error of Decision 1, each starting `"judgments.yaml, unit_weight, values.Fill: "`; non-string keys get
    the quoting hint; the reader is `_config.read_yaml(path, "judgments", "docs/work/m13a-judgments.md")`.
  - `as_path(value) -> Judgments | None` for `judgments=` (a `Judgments`, a path or None).
- `src/hangtu/__init__.py`: export `judgments` and `Judgments`.
- `docs/site/reference/data.md`: a "Judgments" section with both.
- Tests (new `tests/test_judgments.py`, YAML written to `tmp_path`): the spec's sample file reads; an empty file
  holds no judgments; each Decision 1 error with its file, judgment and entry (AC 5); `yes:` as a key gets the
  hint; a water level with a negative depth reads (it warns later, in step 6); `repr` lists values, units and
  reasons; `read()` after editing the file returns the new values and a new hash (half of AC 6).

### 4. `M13: p.stratigraphy()`
- New `src/hangtu/datasets/_stratigraphy.py`: one row per `GEOL` row with `location_id`, `loca_id`, `depth_top`,
  `depth_base`, `_line`; geology columns from the layer's own code (not `place_in_geology`): a `Build` helper
  `_layer_geology(frame, geol)` factored out of `_geology` so both use one mapping path (map, unmapped warning,
  categorical, `soil_class`, palette). `depth` is not a column, so `finish` gets a `depth=None` path that skips
  `ground_level` and `elevation`; `depth=` / `elevation=` aren't parameters (Decision 4). Sorted by hole, then top.
  If the factoring touches `_geology` beyond a move, it goes in its own refactor commit first.
- `src/hangtu/project.py`: `Project.stratigraphy(*, holes, geology, where, contains, geology_fields,
  include_incomplete, display_units)`, docstring per the other datasets, noting that `geology=` leaves gaps.
- `src/hangtu/datasets/__init__.py`: export it.
- Tests: new `tests/datasets/test_stratigraphy.py`: `site.ags` gives one row per GEOL row, mapped and ordered,
  units in attrs, `source_line`s matching (AC 7); `qc_defects.ags` keeps BH3's overlap and the BH1 gap; no GEOL
  group → empty with the warning; unmapped codes warn. `tests/test_registry.py`: `DATASETS` gains
  `stratigraphy`, so the template rule is tested. `tests/plot/test_profile_overlays.py`: `strata=` with one hole of
  `p.stratigraphy()` draws (AC 9).

### 5. `M13: p.set_judgments() and p.judgments`
- `src/hangtu/project.py`:
  - `set_judgments(path | None)`: reads the file once (`judgments(path)`), stores it in `meta_project` under
    `judgments_path` (relative to the database's folder when it's inside it, else absolute; Decision 5); `None`
    removes it.
  - `judgments` property: a `Judgments` resolved against the database's folder, or None; a missing file is an
    error naming the path and `p.set_judgments`.
  - `ProjectSettings.__getattr__` / `__repr__` skip `judgments_path`, as they do `vertical_datum_source`.
- `src/hangtu/datasets/_frame.py`, `finish` (and `_empty`): `attrs["judgments_file"]` = the resolved path when
  one is set.
- Tests (`tests/test_project.py`): set, read back, remove; a relative path still resolves after moving the folder
  holding the database and the file (AC 8); a bad file errors on set and nothing is stored; every dataset carries
  `judgments_file`; `from_ags(overwrite=True)` starts without one.

### 6. `M13: vertical_stress() from arguments`
- New `src/hangtu/analysis/_vertical_stress.py`, exported from `ht.analysis`:
  - Input checks: `df` columns and length units (`units.resolve_units(..., analysis=True)`); `stratigraphy`
    columns and its own units (Decision 6).
  - `_log(stratigraphy, holes, deepest)` → per hole, layers in m with tolerance 0.01 m: the Decision 7 errors, one
    call-level error listing every hole and depth range, gaps and overlaps pointing to `p.qc()`; checks stop at each
    hole's deepest test; returns the layers with the last one extended down and the holes/depths that needed it.
  - `_water_levels(...)`: P01's four argument forms to depth in m per hole, elevations through `ground_level`.
  - `_integrate(layers, weights, water_depth, depths)` → σv0, u0, σ′v0 in kPa: bulk above the water level,
    saturated below where given; standing water adds γw |zw| (Decision 6). Pure function on arrays, so the golden
    table tests it alone.
  - `vertical_stress(df, *, stratigraphy, judgments=None, unit_weight=None, water_level=None, units=None,
    display_units=None)`: in this step only `unit_weight=` and `water_level=` are read; a missing one raises the
    Decision 6 error (without the file half). Output in the display stress unit, columns replaced with a warning,
    blanks counted; warnings for below-the-log and standing water; `attrs["vertical_stress"]`.
  - Docstring: the TEMPLATE checklist (equation, inputs, valid for, assumptions, judgments, source: Loehr et al.
    2016 eqs. 11.26–11.29).
- `docs/site/reference/analysis.md`: `::: hangtu.analysis.vertical_stress`.
- Tests (new `tests/analysis/test_vertical_stress.py`): the golden table at each depth, to 0.01 kPa (AC 1); the US
  twin within 0.1 %; the water level in elevation; standing water (105.81 / 58.86 / 46.95 and the warning); the
  below-the-log warning; each log error, a 0.005 m gap passing, a gap below the deepest test passing (AC 4);
  `qc_defects.ags` BH3 raising through `p.stratigraphy()` (AC 7); no row dropped or reordered, blanks counted,
  replaced columns warned; `attrs["units"]` for the three columns.

If this step passes about 300 lines it splits after `_integrate` and its golden test.

### 7. `M13: vertical_stress() reads the judgments`
- `src/hangtu/analysis/_vertical_stress.py`:
  - Per judgment, argument → `judgments=` → `df.attrs["judgments_file"]` → error (intent 5), with the override and
    different-file warnings and the merge hint (Decision 6).
  - Unit weights matched on the file's `by:` column of the stratigraphy (an error if it's not a column); water
    levels by `loca_id`; project fallbacks with their warnings, missing keys as errors, unused keyed entries
    warning (Decision 2).
  - `attrs["judgments"]` per Decision 6: source, SHA-256, `by`, and only the keys used, values as quantity strings.
- Tests (same file): AC 2 (precedence per judgment, both warnings, a `pd.concat` frame raising with the hint), AC 3
  (fallbacks, missing keys, unused entries), AC 6 (recorded values and hash; edit the file between calls and the
  result and hash change without reopening the project); `by: uscs_symbol` on an edited stratigraphy.

### 8. `M13: judgments guide, examples and close-out`
- `tests/data/_make_examples.py` writes `judgments.yaml` into `src/hangtu/examples/data/` (pcf and ft, by
  `geology_unit` for Fill, Alluvium and Terrace, a water level for each hole); regenerate. `ht.examples` docstring
  lists it.
- `docs/site/guides/judgments.md` and `docs/site/examples/judgments.py`: open the example project, set the map
  and the judgments, `vertical_stress(p.spt(holes=...), stratigraphy=p.stratigraphy())` leaving out B-4 (its
  planted gap; the guide says why and shows the error text), print a few rows and `attrs["judgments"]`, and plot
  `effective_vertical_stress` with P01. Runs with no warnings (`test_page_example_runs_clean`). In the nav under
  Guides.
- `docs/site/parameters/01-unit-weight-and-vertical-stress.md`: the Methods table links
  `ht.analysis.vertical_stress` in the API reference, and the page links the guide.
- Close-out: parameter index row 01 stage B → **part built** (vertical stress, M13); `CLAUDE.md` status
  paragraph (m13a done, M13 unit (b) next).
- Check: `uv run python docs/prepare_site.py` and `zensical build --clean --strict` pass.
