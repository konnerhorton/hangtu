# M13 (b1): (N1)60, hammer efficiency by hole and the correlations framework

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Unit (a) (`docs/work/m13a-judgments.md`) built the judgments
file, `p.stratigraphy()` and `vertical_stress()`. Unit (b) is split in two:
- **(b1)**, this one: the overburden correction and (N1)60, hammer efficiency by hole, the correlations framework,
  and the first correlations on it, φ′ from SPT (stage C of sheet 04).
- **(b2)**: the rest of the first SPT set on the same framework: s_u (sheet 05), σ′p/OCR (06), K0 (07), E (08) and
  Vs (10).

**Goal:** from a project's SPT data, its stratigraphy and its judgments, an engineer gets (N1)60 and estimates of φ′
from published SPT correlations. Each estimate names its correlation, states the N it was derived with and its
range, and returns NaN with a count where it doesn't apply, so several estimates compare on P01 (`color_by=`) or
P07.

**Why:** SPT is often the only strength data on a US project, and these correlations are what engineers apply to it
by hand, often without checking the N basis (field N, N60 or (N1)60) or the range. The framework is built and
reviewed once, on one parameter, before b2 adds five more.

**SPEC and TODO touched:** §4 (correlations; hammer efficiency by hole), §10.3 (new registry columns), §12.4 (M13
splits into a, b1, b2); TODO #20 (the φ′ part settled here; the rest in b2). `docs/drafts/analysis.md` §4 is
finished as this unit's spec (§4.1 "which C_N" is settled here).

### Decided
1. **(N1)60 = N60 × C_N**, from the σ′v column `vertical_stress()` returns. **C_N is chosen with `method=`**:
   Liao & Whitman (1986) and Kayen et al. (1992) to start, each with the cap its source gives (for Liao & Whitman,
   1.7 per Youd et al. 2001, to verify). The method and cap are recorded in `df.attrs`. A blank N60 or σ′v leaves
   (N1)60 blank, with a count.
2. **Rod-length, borehole-diameter and sampler corrections (C_R, C_B, C_S) are out of scope.** The docstring says
   they aren't applied. They come back when AGS rod and sampler data are read.
3. **Hammer efficiency by hole** (unit (a), Decision 8; SPEC §4): `hammer_efficiency=` also takes values by hole
   (`{"BH01": 80}`). `ISPT_ERAT` (`energy_ratio`) is still used first. When the argument or
   `ht.settings.hammer_efficiency` fills blanks, a warning names the holes. Applies to `ht.analysis.spt()`,
   `p.spt()` and the plots that take `hammer_efficiency=` (P02, P03).
4. **The correlations framework** follows SPEC §4 and analysis draft §4: `ht.analysis.correlations`, one function
   per published correlation, named after its source; metadata in one config file (proposed
   `config/correlations.yaml`) feeding the docstring checklist, `df.attrs` and plot footnotes; an explicit input
   (a column that doesn't match the correlation's N basis is an error, never a silent correction); NaN with a count
   by reason outside the range; long-format output with a column naming the correlation; correlations that give a
   range return lower and upper values. It is built general enough for b2's correlations, which take PI, a soil
   type or σ′v besides N.
5. **φ′ correlations** (sheet 04): Wolff (1989) fit to Peck, Hanson & Thornburn (1974); Kulhawy & Mayne (1990),
   after Schmertmann; Hatanaka & Uchida (1996). A correlation whose equation, constants or range can't be verified
   against its source is cut, not built.
6. **Wave spec step** (process.md, "Stages and waves"): promote sheet 04 to `docs/site/parameters/`, verify the
   [U] citations the φ′ correlations and C_N use and hand-calculate golden values from them, apply the publishing
   rule (TODO #30), and propose the new names against the registry.

### Out of scope
- b2's correlations (s_u, σ′p/OCR, K0, E, Vs) and sheets 05–08 and 10.
- C_R, C_B, C_S (Decision 2); the mid-drive test depth (analysis draft §1.2, Phase 2).
- Correlations from other inputs (PI, CPT qt, Is50): the framework allows them, M14 and later waves build them.
- Relative density (Skempton 1986; Meyerhof 1957): sheet 03 is M14's.
- New plots. Comparison is P01 and P07 as they are.
- Liquefaction triggering, and selection between estimates (stage D, M18).

### Open
- **Names** (to check against `columns.yaml` in the spec step): `spt_n1_60`, the C_N column
  (`spt_overburden_correction`?), the column naming the correlation (`correlation`?; `method` is taken), and the
  lower/upper columns for range outputs.
- **Soil type.** The φ′ correlations apply to sands. Whether a correlation reads `soil_class` / `uscs_symbol` from
  the row and returns NaN with a count for other soils, or the user filters the rows as `spt_class()` does
  (analysis draft §1.4, "which table is the user's call"). Decided here, since b2's correlations depend on it more.
- **Kulhawy & Mayne's N basis:** EPRI uses field N, practice (GEC 5) uses N60. Settle from the source in the spec
  step.
- **Hammer efficiency by hole as a DataFrame** (`loca_id, hammer_efficiency`) as well as a dict, to match how
  `water_level=` takes per-hole values.

## Spec

C_N and (N1)60, hammer efficiency by hole, `ht.analysis.correlations` and the φ′ correlations. Numbered items
refer to this section's decisions unless they say "intent".

### Sources checked in this step
| Item | Source and locator | Result |
|---|---|---|
| C_N, Liao & Whitman (1986) | Youd et al. (2001), JGGE 127(4), 297–313, Eq. 9 and Table 2, p. 300 | [V] C_N = (pa/σ′v)^0.5, pa ≈ 100 kPa, C_N ≤ 1.7 |
| C_N, Kayen et al. (1992) | Youd et al. (2001), Eq. 10, p. 300 | [V] C_N = 2.2 / (1.2 + σ′v/pa); "limits the maximum C_N value to 1.7" |
| C_N range | Youd et al. (2001), p. 300 | [V] Eq. 9 fits to about 200 kPa, Eq. 10 to 300 kPa; above 300 kPa "(9) should not be applied … C_N should be estimated by other means" |
| φ′, Hatanaka & Uchida (1996) | Soils and Foundations 36(4), 1–9: Eq. 6 and the text, p. 3; Eq. 8, p. 7; Conclusions, p. 8 | [V] φ′ = (20 N1)^0.5 + 20, most data within ±3°, for 3.5 ≤ N1 ≤ 30. N1 = N / (σ′v/98)^0.5 with σ′v in kPa (Liao & Whitman, no cap given), measured with the Japanese "tombi" trip hammer at 78 % energy. Drained triaxial compression on in situ frozen samples of sands from six sites, including volcanic Shirasu |
| The same, at 60 % energy | FHWA GEC 5 (Loehr et al. 2016, FHWA-NHI-16-072), Eq. 7.23, p. 7-55 | [V] φ′ = (15.4 (N1)60)^0.5 + 20°, for "relatively clean sands", not micaceous or gravelly soils. 15.4 = 20 × 60/78, rounded |
| φ′, Kulhawy & Mayne (1990) after Schmertmann (1975) | GEC 5 Eq. 7.22 and Fig. 7-41, p. 7-54 to 7-55; EPRI EL-6800 Eq. 4-11 (locator) | [V] tan φ′ = [N60 / (12.2 + 20.3 σ′v/pa)]^0.34, an approximation of Schmertmann's chart, which is drawn for σ′v up to 300 kPa and N60 up to 60, and "somewhat conservative, especially for depths less than 6 ft". GEC 5 settles the N basis as N60 (sheet 04 §5.4's open point) |
| φ′, Wolff (1989) | ASCE GSP 23, 96–106 | **Not verified.** Neither the paper nor an agency manual giving the equation was found; secondary copies disagree on a coefficient (0.00054 or 0.00053). Cut (intent 5; Decision 11), TODO #36 |

Also noted: NASEM (2024) Table 2.2.1 lists Hatanaka & Uchida with (N1)60 and the constant 20, without GEC 5's energy
rescaling. hangtu follows the original and GEC 5, and the docstring says why.

### Changes
- **SPEC §4:** the "Correlations" bullet gains "an input of the wrong variant is an error; a correlation published at
  another energy is used in its 60 % form, from a cited source" (Decision 7). The "Effective vertical stress" bullet's
  last sentence becomes "(N1)60 (`ht.analysis.spt_n1_60()`, C_N by `method=`, Decision 1) and the correlations take
  its σ′v column." The `hammer_efficiency` sentence adds "by hole as `{loca_id: ER}`, filling blanks with a warning
  naming the holes" (Decision 4). **§12.4:** M13's row names three units (a, b1, b2).
- **`docs/drafts/analysis.md` §4:** §4 and §4.1 point here for the framework and C_N; §4.2 keeps the candidates for
  b2 with φ′ marked done.
- **`columns.yaml`:** `spt_overburden_correction`, `spt_n1_60`, `effective_friction_angle`, `correlation_name`,
  `correlation_note` (Decision 9). **`defaults.yaml`:** a preset for `effective_friction_angle` (20–50°) and for
  `spt_n1_60` like `spt_n60`'s.
- **New config:** `config/correlations.yaml` (Decision 6).
- **TODO:** #20 records the φ′ set and that the rest is b2's; new #36 (verify Wolff 1989) and #37 (soil types
  mapped to each correlation's), from Decision 11.
- **Docs site:** sheet 04 promoted to `docs/site/parameters/04-drained-shear-strength-soil.md` (Decision 10); a guide
  section on (N1)60 and correlations with its example; reference entries for every new public name.
- **Parameter index:** at the close-out, 04's stage C becomes **part built** (SPT: M13).

### Decisions
1. **`ht.analysis.spt_n1_60()`.**
   ```python
   spt_n1_60(df, *, method, units=None) -> pd.DataFrame
   ```
   - **Input:** `spt_n60` (from `ht.analysis.spt()` or `p.spt()`) and `effective_vertical_stress` (from
     `vertical_stress()`), with its units resolved per SPEC §2.6. A missing column is an error naming it and the
     function that adds it.
   - **`method=`** is `"liao_whitman_1986"` or `"kayen_1992"`, required, with no default (Decision 11): the two differ by
     up to about 12 % between 25 and 300 kPa, and the choice is the engineer's.
   - **Output:** a copy of `df` with `spt_overburden_correction` (C_N) and `spt_n1_60` = N60 × C_N. C_N is capped at
     1.7 for both methods (Youd et al. 2001); pa = 100 kPa, converted with pint, so US input gives the same result.
   - **Out of range:** σ′v > 300 kPa gives blank C_N and (N1)60 (Youd et al. 2001); σ′v < 0 is an error naming the
     rows; a blank N60 or σ′v gives blanks. One warning counts the rows by reason. Liao & Whitman between 200 and
     300 kPa is computed, and the docstring says Youd et al. find it uncertain there.
   - **Recorded:** `df.attrs["spt_n1_60"]` = `{"method": ..., "cap": 1.7, "pa": "100 kPa", "source": ...}`.
   - **Not applied:** C_R, C_B, C_S (intent 2), stated in the docstring with Youd et al. Table 2's ranges cited, not
     reproduced.
2. **Refusals.** (N1)60 is computed for refusals, as N60 is (analysis.md §1.3). Correlations give no estimate for a
   refusal (`correlation_note` "refusal"), read from `spt_refusal` when the column is there.
3. **Wrong-variant check.** Each function reads the one column its correlation was derived with, by its registry
   name, and has no argument to point it at another (`n=` would let field N into an (N1)60 correlation, SPEC §4). A
   missing column is an error naming it and how to make it ("run ht.analysis.spt_n1_60(df, method=...) first").
4. **Hammer efficiency by hole** (intent 3).
   - `hammer_efficiency=` takes a number (every hole) or a dict `{loca_id: ER}`, in `ht.analysis.spt()`, `p.spt()`,
     `ht.plot.spt_profile()` and `ht.plot.spt_histogram()`. The setting stays one number.
   - Order per row, unchanged: the row's `energy_ratio` → its hole's dict value, or the number → the setting → blank.
     A hole not in the dict falls through to the setting.
   - **Warning** whenever the argument or the setting fills a blank: one per call, naming the holes, the value and
     the number of tests ("energy ratio 80 % used for BH01 (12 tests), BH02 (9 tests): no energy_ratio in the data.
     Measured values (ISPT_ERAT) are used first."). Without `loca_id` in `df` it gives the count. A dict key not in
     the data warns, as a likely typo. A dict without `loca_id` in `df` is an error.
   - `p.spt()`'s `energy_source` is "hammer_efficiency" for every row filled by the argument or the setting.
   - Existing tests and examples that set `hammer_efficiency` assert the new warning.
5. **Correlation functions.** `ht.analysis.correlations.<source>()`, named after the source, one per published
   correlation: `hatanaka_uchida_1996` and `kulhawy_mayne_1990` in this unit.
   ```python
   hatanaka_uchida_1996(df, *, units=None, display_units=None) -> pd.DataFrame
   kulhawy_mayne_1990(df, *, units=None, display_units=None) -> pd.DataFrame
   ```
   - **Output:** a copy of `df` with the estimate in the target property's registry column
     (`effective_friction_angle`, in degrees), `correlation_name` (the function's name) and `correlation_note` (blank, or
     the reason there's no estimate: "input blank", "refusal", "below range", "above range"). No row is dropped or
     reordered. Several correlations compare with `pd.concat([...])`, one row per test and correlation, drawn with
     `ht.plot.profile(est, value="effective_friction_angle", color_by="correlation_name")`.
   - **Out of range:** NaN, never clipped or extrapolated (SPEC §4), with one warning counting the rows by reason.
   - **Recorded:** `df.attrs["correlations"]` = `{name: {equation, inputs, range, applies_to, source}}`, from the
     config, for **every** correlation in it, not only the one run (changed in the build, step 5: pandas 2.3's
     `concat` keeps attrs only when they are identical, so a per-correlation record dropped `attrs["units"]` too
     and the comparison plot lost its depth units; `correlation_name` says which entry each row used). A helper
     `ht.analysis.correlations.describe(name)` returns the same entry for when attrs are lost.
   - **Soil type** isn't read (Decision 11): the docstring says what the correlation applies to, and the user passes the
     rows it applies to, as `spt_class()` does.
6. **`config/correlations.yaml`** holds the facts the code uses, one entry per correlation: target column, input
   columns and their variant, range per input in the source's units, constants' units, applies to, not for, scatter,
   and the source with its locator. Docstrings are written by hand (mkdocstrings reads them statically), and a test
   checks each docstring names the entry's source, locator and range, so the two can't drift.
7. **The two φ′ correlations.**
   - **`hatanaka_uchida_1996`:** φ′ = (15.4 (N1)60)^0.5 + 20 (GEC 5 Eq. 7.23, the source's Eq. 8 at 60 % energy).
     Input `spt_n1_60`. Range: the source's 3.5 ≤ N1 ≤ 30 at 78 % energy, which is 4.55 ≤ (N1)60 ≤ 39.0. Scatter
     ±3° (most data, source p. 7). Applies to relatively clean fine to medium sands; not micaceous sands or gravels
     (GEC 5 p. 7-55). The docstring notes the source's N1 has no C_N cap, and that NASEM (2024) prints the 78 % form
     against (N1)60, which would overstate φ′.
   - **`kulhawy_mayne_1990`:** φ′ = arctan{[N60 / (12.2 + 20.3 σ′v/pa)]^0.34} (GEC 5 Eq. 7.22, after Schmertmann
     1975; Kulhawy & Mayne 1990 Eq. 4-11). Inputs `spt_n60`, `effective_vertical_stress`. Range: the chart's axes,
     0 < σ′v ≤ 300 kPa and N60 ≤ 60. Applies to relatively clean sands; conservative above about 6 ft (1.8 m) depth
     (GEC 5 p. 7-55), stated, not corrected.
8. **pa** is one constant, 100 kPa (Youd et al. 2001), used by C_N and Kulhawy & Mayne, converted with pint.
   Hatanaka & Uchida's 98 kPa is inside its rescaled form, so it isn't used separately.
9. **Names** (checked against `columns.yaml`, `defaults.yaml`, the settings and the plot arguments; no collisions):

   | Name | Kind | Quantity | Label | Notes |
   |---|---|---|---|---|
   | `spt_overburden_correction` | column | dimensionless | Overburden correction, C_N | |
   | `spt_n1_60` | column | count | SPT (N1)60 | |
   | `effective_friction_angle` | column | angle | Effective friction angle, φ′ | Peak, unless the source says otherwise; measured values (W2) use it too |
   | `correlation_name` | column | – | – | The function's name; text. Not `correlation`, which reads as a statistic once M15 lands |
   | `correlation_note` | column | – | – | Why there's no estimate; text |
   | `spt_n1_60()`, `correlations.<source>()`, `correlations.describe()` | API | – | – | |
10. **Sheet 04 promoted** to `docs/site/parameters/04-drained-shear-strength-soil.md` under the publishing rule
    (TODO #30). Table 4-3's five class boundaries stay (a short set, cited); Fig. 7-41 is cited, not reproduced. The
    methods table links the two functions; the triaxial and shear box methods say "W2". Its [U] items: Hatanaka &
    Uchida now [V]; Wolff stays on the page as [U], not built (TODO #36); Duncan (2000), Phoon & Kulhawy (1999), Lambe & Whitman (1969) and the residual
    range are verified or cut, as in unit (a). Sheet §5.5's form with (N1)60 and 20 is corrected.

### Acceptance criteria
1. **C_N golden values** (pa = 100 kPa, cap 1.7):

   | σ′v (kPa) | Liao & Whitman | Kayen et al. |
   |---|---|---|
   | 0 | 1.7000 (cap) | 1.7000 (cap; 1.8333 uncapped) |
   | 25 | 1.7000 (cap) | 1.5172 |
   | 50 | 1.4142 | 1.2941 |
   | 100 | 1.0000 | 1.0000 |
   | 200 | 0.7071 | 0.6875 |
   | 300 | 0.5774 | 0.5238 |
   | 300.1 | blank, counted | blank, counted |

   The US twin (σ′v in psf) agrees to 0.1 %.
2. **φ′ golden values:**

   | N60 | σ′v (kPa) | (N1)60, L&W | φ′ H&U (L&W) | (N1)60, Kayen | φ′ H&U (Kayen) | φ′ K&M |
   |---|---|---|---|---|---|---|
   | 20 | 50 | 28.284 | 40.87 | 25.882 | 39.96 | 43.92 |
   | 10 | 100 | 10.000 | 32.41 | 10.000 | 32.41 | 33.82 |
   | 30 | 200 | 21.213 | 38.07 | 20.625 | 37.82 | 39.53 |
   | 5 | 25 | 8.500 | 31.44 | 7.586 | 30.81 | 33.27 |

   (N1)60 of 4.0 and 40.0 give NaN with "below range" and "above range"; N60 of 61 and σ′v of 301 kPa give NaN in
   K&M; a refusal gives NaN with "refusal".
3. **Wrong variant:** a frame with `spt_n60` but no `spt_n1_60` makes `hatanaka_uchida_1996` raise, naming
   `spt_n1_60` and `ht.analysis.spt_n1_60`; neither function has an argument choosing the N column.
4. **Hammer efficiency by hole:** `{"BH01": 80}` fills BH01's blanks only; a row's `energy_ratio` wins; BH02 falls
   to the setting or stays blank; the warning names the holes and counts; an unknown key warns; a dict without
   `loca_id` raises; `energy_source` is right per row.
5. **Recorded:** `attrs["spt_n1_60"]` and `attrs["correlations"]` hold the method, cap, pa and the config entries;
   `describe()` returns the same entry.
6. **Config and docstrings:** the drift test passes, and fails if a docstring's range or locator is changed.
7. **Comparison:** `pd.concat` of both correlations on the example project draws with `profile(color_by=
   "correlation_name")`, with refusals and out-of-range rows counted in the footnote.
8. **Docs:** reference entries for every new public name; the guide example runs in `prepare_site.py`; `zensical
   build --strict` passes with page 04.

11. **Settled in review:**
    - **Wolff (1989) is cut** from b1. It stays on page 04 as [U], with no function, and TODO #36 tracks verifying
      it against GSP 23.
    - **`method=` is required** for `spt_n1_60()`, with no default.
    - **Soil type:** the user passes the rows a correlation applies to; nothing is read from `uscs_symbol` or
      `soil_class`. A mapping from classes to each correlation's soil types is TODO #37, for later.
    - **The column is `correlation_name`**, not `correlation`.
    - **Hammer efficiency by hole is a dict only.** A DataFrame form waits until a file of hammer calibrations needs
      it.

## Plan

Eight commits, each green (ruff and pytest), with one refactor ahead of the new behavior. Each step that adds a
public name adds its reference entry in the same commit, since `tests/docs/test_site.py` fails without it. The spec
commit already updated SPEC, the analysis draft and TODO; the build brings the code, config, tests and site up to
them. "Decision n" and "AC n" refer to the Spec.

### 1. `M13: one helper for the energy ratio per row`
A refactor, on its own. `analysis/_spt.py` gains `_energy_ratios(df, hammer_efficiency) -> (energy, filled)`: the
row's `energy_ratio`, else the argument, else the setting, and a mask of the rows the argument or setting filled.
`spt()` uses it, and `datasets/_spt.py` builds `energy_source` from `filled` instead of repeating the precedence
with its `efficiency` variable. No behavior change; the tests pass as they are.

### 2. `M13: hammer efficiency by hole, with a warning when it fills blanks`
- `analysis/_spt.py`:
  - `_check_energy_ratio` accepts a dict `{loca_id: ER}`, each value checked as now; the error example shows both
    forms. A dict with no `loca_id` column in `df` raises (Decision 4).
  - `_energy_ratios` maps the dict by `loca_id`; holes not in it fall to the setting.
  - One `HangtuWarning` per call when `filled.any()`, naming holes, values and test counts, or the row count without
    `loca_id`; one for dict keys not in the data.
  - The docstring's N60 bullet and `hammer_efficiency` parameter describe both forms and the warning.
- The signatures and docstrings of `Project.spt`, `datasets/_spt.spt`, `plot.spt_profile` and `plot.spt_histogram`
  take `float | Mapping[str, float] | None`.
- Tests: `tests/analysis/test_spt.py` gains AC 4 (dict fills one hole only; `energy_ratio` wins; an unlisted hole
  falls to the setting or stays blank; the warning text; unknown key; dict without `loca_id`). Every existing test
  that passes `hammer_efficiency` or sets the setting with blank energy ratios asserts the warning with
  `pytest.warns` (`tests/analysis/test_spt.py`, `tests/datasets/test_spt.py`,
  `tests/datasets/test_datasets_acceptance.py`, `tests/plot/test_spt_histogram.py`,
  `tests/plot/test_spt_refusals.py`, `tests/plot/test_spt_profile_acceptance.py`). `tests/datasets/test_spt.py`
  checks `energy_source` per row with a dict.
- Docs: `docs/site/guides/spt.md` (N60 list: the argument by hole, the warning) and
  `docs/site/plots/spt-profile.md` (the argument's row).

### 3. `registry: (N1)60, φ′ and the correlation columns`
- `columns.yaml`, under SPT: `spt_overburden_correction` (dimensionless, ratio, "Overburden correction, C_N",
  `derived: effective_vertical_stress`) and `spt_n1_60` (count, ratio, "SPT (N1)60", `derived: spt_n60,
  spt_overburden_correction`). A new section "Strength": `effective_friction_angle` (angle, ratio, "Effective
  friction angle, φ′"). A new section "Correlations": `correlation_name` and `correlation_note` (text). All
  `ags: ["derived: docs/work/m13b1-spt-framework.md"]`, `used_by: [P01]`.
- `defaults.yaml`: presets `spt_n1_60` (as `spt_n60`) and `effective_friction_angle` (linear, typical `[20, 50]`,
  not from zero).
- Tests: `tests/test_registry.py` and the preset test pick them up through their existing rules; the columns page
  test passes once `prepare_site.py` regenerates it.

### 4. `M13: spt_n1_60() with C_N by method`
- New `analysis/_overburden.py`, exported from `ht.analysis` as `spt_n1_60`:
  - `PA = 100 kPa`, `CAP = 1.7`, `MAX_STRESS = 300 kPa`, and the two methods as small pure functions on kPa arrays.
  - `spt_n1_60(df, *, method, units=None)`: column checks naming the function that adds each (Decision 1);
    `method` checked against the two names (error lists them, with an example); `effective_vertical_stress`
    converted to kPa via `units.resolve_units(..., analysis=True)`; negative stress raises naming rows; blanks and
    > 300 kPa give NaN with one warning by reason; existing output columns replaced with a warning, as
    `vertical_stress()` does; `attrs["spt_n1_60"]` (Decision 1).
  - Docstring per the TEMPLATE checklist: both equations, the cap, the range and Youd et al.'s note on 200–300 kPa,
    C_R / C_B / C_S not applied, source with locators.
- `docs/site/reference/analysis.md`: `::: hangtu.analysis.spt_n1_60`.
- Tests (new `tests/analysis/test_spt_n1_60.py`): AC 1's table for both methods to 1e-4; the US twin (psf) within
  0.1 %; 300.1 kPa blank and counted; method required, a wrong name raising; missing columns raising with the hint;
  refusals computed; no row dropped or reordered; attrs.

### 5. `M13: the correlations framework and hatanaka_uchida_1996`
- New `config/correlations.yaml` with the `hatanaka_uchida_1996` entry (Decision 6): target, inputs with variant
  and units, range in the source's units, applies to, not for, scatter, source and locator.
- New package `analysis/correlations/`:
  - `_framework.py`: `entry(name)` (reads the config through `_config.load`); `inputs(df, entry, units)` (each
    input column present by its registry name, else the error with the hint, Decision 3; converted to the entry's
    units); `estimate(df, entry, values, notes, display_units)` builds the output: the target column,
    `correlation_name`, `correlation_note` (input blank, refusal from `spt_refusal`, below range, above range, in
    that priority), NaN where noted, the warning counting by reason, `attrs["correlations"]`, replaced columns
    warned.
  - `_friction_angle.py`: `hatanaka_uchida_1996(df, *, units=None, display_units=None)` with its docstring
    (Decision 7).
  - `__init__.py`: `__all__ = ["describe", "hatanaka_uchida_1996"]`; `describe(name)` returns a copy of the entry,
    and an unknown name lists the known ones.
- `ht.analysis.__init__` imports `correlations`, so `ht.analysis.correlations.hatanaka_uchida_1996` works.
- `tests/docs/test_site.py`: `test_every_public_name_has_a_reference_entry` recurses into submodules with
  `__all__`, so `hangtu.analysis.correlations.*` is expected. New `docs/site/reference/correlations.md` with both
  names, in the nav under Reference.
- Tests (new `tests/analysis/test_correlations.py`): AC 2's H&U column from the (N1)60 values; 4.0 and 40.0 below
  and above range; a refusal; a blank input; AC 3 (no `spt_n1_60` raises naming it; no argument chooses the
  column); AC 5 (`attrs` and `describe()` agree); the drift test (AC 6): for each config entry, the function's
  docstring contains the source, the locator and each range bound; a monkeypatched docstring fails it.

### 6. `M13: kulhawy_mayne_1990`
- `config/correlations.yaml`: its entry (inputs `spt_n60` and `effective_vertical_stress` in kPa; range 0 < σ′v ≤
  300 kPa, N60 ≤ 60).
- `_friction_angle.py`: `kulhawy_mayne_1990`, sharing `PA` from `_overburden.py`; its docstring (Decision 7, the
  shallow-depth note).
- `__all__` and `docs/site/reference/correlations.md` gain it.
- Tests: AC 2's K&M column; N60 61 and σ′v 301 kPa out of range; σ′v in psf gives the same φ′; the drift test
  covers it through the config; AC 7: `pd.concat` of both on a small frame draws with `profile(...,
  color_by="correlation_name")`, the out-of-range rows counted in the footnote.

### 7. `docs: page 04, drained shear strength of soil`
- `docs/site/parameters/04-drained-shear-strength-soil.md` from the sheet, in TEMPLATE's order (Decision 10):
  the methods table links the two functions and gives W2 for the triaxial and shear box methods; Hatanaka &
  Uchida's form corrected to GEC 5's; Wolff listed as [U], not built (TODO #36); Table 4-3's five rows kept with
  their citation; Fig. 7-41 cited.
- The remaining [U] items (Duncan 2000's COV table, Phoon & Kulhawy 1999, Lambe & Whitman 1969, the residual
  range) are verified with their locator or cut, as unit (a) did for page 01; the commit message lists which.
- The sheet `docs/drafts/parameters/04-*.md` gets the same corrections to §5.4 and §5.5, and a line pointing to
  the page. Nav entry under Parameters.

### 8. `M13: correlations guide, example and close-out`
- `docs/site/guides/correlations.md` and `docs/site/examples/correlations.py`: open the example project with the
  map and judgments as `judgments.py` does, `vertical_stress()` on the holes without B-4's gap,
  `spt_n1_60(method="liao_whitman_1986")`, keep the Terrace rows (sands; the guide says the user picks the rows a
  correlation applies to), both correlations, `pd.concat`, print a few rows, and a profile with
  `color_by="correlation_name"`. The example data carries `ISPT_ERAT`, so no hammer warning; rows are chosen so the
  example runs clean (`test_page_example_runs_clean`), and the guide shows what an out-of-range row looks like in
  text. Nav under Guides; `guides/spt.md` links it from its N60 section.
- Page 04's methods table links the guide.
- Close-out: parameter index row 04 stage C → **part built** (SPT φ′: M13 b1); `CLAUDE.md` status paragraph (b1
  done, b2 next).
- Check: `uv run python docs/prepare_site.py` and `zensical build --clean --strict` pass.

If step 2 passes about 300 lines, it splits in two: the dict by hole with its new tests first (no existing test
changes), then the warning together with the existing tests that now assert it, since the warning can't land without
them.
