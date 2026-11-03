# M18 (a): SPT refusals in `fit()` and the correlations

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4). It splits into four units, data first
(`docs/reference/process.md`, "Stages and waves"):
- **(a) this unit:** SPT refusals, so the data selection reads carry what the tests showed;
- **(b)** representative values: `ht.stats.characteristic()` (EC7) and the views US practice uses (a lower
  percentile, mean − k·s), constant per geology unit or as a depth trend, in the `design_lines` shape P01 draws;
- **(c)** P09, the characteristic and design-line profile;
- **(d)** selection and the Mohr–Coulomb set (not yet scoped; it needs M17 (b), the shear box fit). The selection
  itself is a judgment (decided 2026-11-02): per geology unit and parameter, the judgments file names a method
  hangtu computes, or gives a value with a reason, and the set records which.

(a) builds the two refusal decisions of 2026-11-02 (SPEC §4, §5; formerly TODO #49 and #54).

**Goal:**
- `fit()` takes an optional judged upper limit for refusals per geology unit. With it, a refusal is fitted as
  lying between its value and the limit; without it, as today, at least its value.
- An SPT correlation gives a row whose N is beyond its range, a refusal or a measured value, an estimate marked
  "at least" (or "at most", below the range) at the range limit, instead of a blank, so a parameter set derived
  from SPT keeps its densest and loosest tests, and `describe()`, `fit()` and P01 treat that estimate as the
  bound it is (decision 1).

**Why:**
- **The fitted tail above the cap is the distribution's, not the data's.** In the example Terrace, 11 of 40 tests
  are refusals at N60 66.7, and the fits put 24–27 % of their probability above it (lognormal P99 137). Each of
  those refusals is 50 blows for 11 in of total penetration, about N60 160 scaled to a foot. The engineer who
  knows what the refusals hit can bound the tail; hangtu shouldn't (SPEC §4: a judgment, no default). Without the
  limit, right-censoring is the test's result as ASTM D1586 defines refusal, not a judgment (SPEC §5).
- **Derived sets lose the dense end today.** Every correlation leaves a refusal blank with the reason "refusal"
  (`correlations/_framework.py`), and a value beyond its range blank with "above range". Counted, not dropped,
  but in the docs site's correlations example (the Terrace in five holes, 2026-11-02) Hatanaka & Uchida gives φ′
  for 12 of 33 tests: 9 are refusals and 12 more have (N1)60 above 39. The 21 missing are the strongest.
  Selection compares that set with lab results (M18 (d)); a set biased low by construction would read as a real
  difference.
- **Every SPT correlation rises with N**, so the estimate at a refusal's N is a lower bound of the estimate at
  its true N. Checked from the equations on 2026-11-02 (to confirm in the spec, correlation by correlation):
  φ′ (Hatanaka & Uchida 1996; Kulhawy & Mayne 1990), s_u (Terzaghi & Peck 1967, by class; Stroud 1974), σ′p and
  OCR (Mayne & Kemper 1988), K0 (Kulhawy et al. 1989), E (AASHTO 2004; Kulhawy & Mayne 1990) and Vs (Imai &
  Tonouchi 1982; Ohta & Goto 1978).
- **Most refusals, and many measured values, are beyond a correlation's range.** The Terrace's (N1)60 at
  refusal is above Hatanaka & Uchida's 39, and so are 12 measured values. A correlation never extrapolates
  (SPEC §4), so the honest statement is "at least the estimate at the range limit": a bound inside the range the
  source supports.

**Scope:**
- **The refusal upper limit**, a judgment keyed by geology unit (a project-wide value allowed with a reason),
  read by `fit()` as `refusal_upper_limit=` → `judgments=` → the project's file. Unset is not an error: refusals
  stay right-censored, and the note says the tail is the distribution's. 🟡 The limit is given as field N
  (blows per foot) and converted per row by the row's own factors (value / `spt_n`), so one limit serves N60 and
  (N1)60 alike and the engineer judges in the units the log shows.
- **Bounded estimates** in every SPT correlation (decision 1):
  - a refusal: at least the estimate at the row's N (as capped), or at the upper range limit when N is beyond it;
  - a measured N above the range: at least the estimate at the upper limit; below it, at most the estimate at the
    lower limit;
  - only for the N input, since each correlation rises with N; a row outside the range of another input (σ′v,
    PI), outside the soil groups, or with an input blank keeps its NaN and reason.
- **Statistics read the flag:** `describe()` counts the rows as bounds, `fit()` censors them, P01 draws
  them as it draws a refusal or a `<`/`>` value. 🟡 How the flag is carried is for the spec: with bounds both ways,
  a qualifier of the estimate's own (`<`/`>`, as a lab value's) fits better than widening `spt_refusal`, which
  only says "at least".
- Golden values on the example Terrace for both; docstrings, the statistics and correlations guides.

**Constraints:**
- SPEC §4: correlations never extrapolate their input (a bound at the limit is not an extrapolation); a judgment
  has no default; judgments resolve argument →
  `judgments=` → the project's file, and are recorded on the result.
- SPEC §5: the input rules (counts add up; flags come from the registry); statistics are designed for lab data,
  so this stays the simple treatment: a bound per row, an interval per unit, nothing modeled.
- Never drop data silently: rows given a bounded estimate are counted in the correlation's notes.

**Out of scope:**
- **Extrapolating blows from penetration** (decided 2026-11-02, SPEC §5). An engineer may use it to choose the
  limit; hangtu doesn't compute it.
- **Interval estimates from the correlations** (the estimate at the cap to the estimate at the limit). The limit
  bounds N in `fit()` only; a correlation's estimate stays "at least".
- **Censored comparisons in `compare()`** (TODO #51, for lab data).
- **Representative values, P09 and the model set:** M18 (b)–(d).

**SPEC and TODO touched:**
- SPEC §4 (the refusal bullet: widened to every row beyond the N range, decision 1, then built; the correlations'
  "NaN with a count outside its range" becomes a bound at the limit for N; the judgment's name in the judgments
  list), §5 (Fitting: built; model sets:
  selection is a judgment), §12.4 (M18 split into (a)–(d)).
- `docs/drafts/analysis.md` §4 if it describes the refusal reason; the correlations and statistics guides on the
  site.

### Decisions (intent review, 2026-11-02)
1. **Every row beyond a correlation's N range gets a bound, not only refusals.** In the docs site's Terrace
   example, 12 of the 21 rows Hatanaka & Uchida leaves blank are measured (N1)60 above 39, not refusals. The
   reasoning that bounds a refusal holds for them too: N is known to be past the limit and the estimate rises
   with N. So above the upper limit a row gets "at least the estimate at the limit", below the lower limit "at
   most", and a refusal within the range "at least the estimate at its N". This changes SPEC §4's rule for the N
   input only: other inputs (σ′v, PI) keep NaN with a count, because a correlation needn't be monotonic in them.

## Spec
Numbered items are this section's decisions; "intent decision 1" is the review's. 🟡 marks what the review hasn't
agreed yet.

### Changes
**1. The refusal upper limit in `fit()`.**
```yaml
# judgments.yaml
spt_refusal_upper_limit:
  by: geology_unit
  values:
    Terrace: {spt_n: 120, reason: "50 blows for 5 in of the test drive at refusal, scaled to a foot"}
    Alluvium: {spt_n: none, reason: "refusals on cobbles in the gravel lens, not the clay"}
```
- `fit(..., spt_refusal_upper_limit=None, judgments=None)` (both new arguments): the argument (a number, or `{unit: number}`), then
  `judgments=`, then the project's file the frame carries. Not found anywhere: refusals stay right-censored, with
  the note "the tail above the refusals is the distribution's; set spt_refusal_upper_limit to limit it" (decision 1).
- **Not the cap.** `spt_cap` (and `spt_n_capped`) is where a refusal is recorded, the bottom of its interval; the
  upper limit is the engineer's judgment of its top. The docstring and the judgments guide say so.
- Read only when `value` is an SPT N column (`spt_n`, `spt_n_capped`, `spt_n60`, `spt_n1_60`: those
  `spt_refusal` flags). For another value, an argument is an error; a file entry is ignored.
- **The limit is field N, blows per foot** (decision 2). Each refusal row's limit is `limit × value / spt_n`, its
  own factors (ER / 60, then C_N), so one limit serves every N column. A frame without `spt_n` is an error naming
  it. A row whose limit isn't above its value is an error naming the row, the value and the limit.
- **Keys are geology units**, matched to the rows' `geology_unit`, whatever `by=` groups on. The usual judgment
  rules apply (SPEC §4): a `project:` entry with a reason fills unlisted units with a warning; without one, a unit
  with refusals that the entry doesn't list is an error naming it. `none` keeps that unit right-censored, on purpose
  (decision 3).
- **Fitted as interval-censored** between the row's value and its limit: the likelihood term is
  ln[F(limit) − F(value)], beside SciPy's `CensoredData(interval=...)` for the starting fit, so AICc still compares.
- The result counts them (`count_interval_censored`, beside `count_at_least` and `count_at_most`, and inside
  `count_censored`, which becomes left + right + interval; not `count_range`, which counts bands left out), records the judgment
  (value, key, source, reason) and notes "11 refusals fitted between their N60 and the limit (120 blows/ft)".
- **Plotting positions** (P08's Q-Q panel) treat an interval as right-censored at its lower end (Kaplan–Meier, as
  today). That is exact when every interval lies above every measured value of its group, as it does for refusals
  at one cap; otherwise the note says the positions approximate.
- No Anderson–Darling check with intervals, as for any censored value.

**2. Bounded estimates in the SPT correlations** (intent decision 1).
- **Each SPT correlation declares its N input** in `config/correlations.yaml` (`bound_by:`): `spt_n1_60`,
  `spt_n60`, `spt_n`, or the term `normalized_n` (N pa / σ′v0, for OCR and K0, whose ranges are given on it): an
  input or a term, as `range:` already mixes them, which the file's header comment says. A new
  framework step, `_framework.bound()`, runs between `inputs()` and the equation:
  - **A refusal** (`spt_refusal` True) within the range: the estimate at its N, "at least".
  - **N above an inclusive upper limit** (`at_most`), refusal or not: N is set to the limit, "at least".
  - **N below an inclusive lower limit** (`at_least`) above 0: N is set to the limit, "at most". A refusal below
    the lower limit has no bound (it is at least a value under the range) and keeps NaN, "refusal".
  - **A strict limit** (`greater_than`, `less_than`) and a lower limit of 0 don't bound: below them N isn't a
    test result (decision 4).
  - **Another input** out of its range or blank, or the row outside the soil groups: NaN and reason, as today,
    whatever N is. Those reasons come first.
- **Every SPT correlation rises with N** at fixed other inputs, so the bound holds. From the equations: φ′ =
  √(15.4 (N1)60) + 20° and arctan[(N60 / (12.2 + 20.3 σ′v/pa))^0.34]; s_u by Terzaghi & Peck's classes (bands
  non-decreasing in N) and Stroud's f1 N60 pa / 100; σ′p = 0.47 N pa; OCR = 0.58 normalized_n; K0 = 0.073
  normalized_n; E = C (N1)60 pa or C N60 pa; Vs = a N60^b with b > 0. A property test checks each (criterion 9).
- **Bands** (Terzaghi & Peck, Stroud below PI 30) are computed at the bounded N, both ends qualified alike. Bands
  are still left out of the statistics (SPEC §5).
- **The output:** the estimate as computed at the bounded N, `correlation_qualifier` (`>` at least, `<` at most,
  blank otherwise) and `correlation_note` saying why ("at least: refusal", "at least: (N1)60 above 39, estimated
  at 39", "at most: (N1)60 below 4.55, estimated at 4.55"). One warning per call counts the bounded rows by kind,
  beside today's count of rows with no estimate.
- The docstrings' "No estimate" paragraph splits into "Bounded estimates" and "No estimate". `correlation_note`'s
  registry description ("why a correlation gave no estimate") widens to "why a correlation gave no estimate, or a
  bound".
- Wording: the docs call the source's `at_most`/`at_least` the range's "upper end" and "lower end", so "upper
  limit" means only the refusal judgment.

**3. The statistics and P01 read `correlation_qualifier`.**
- Registry: `correlation_qualifier`, text, `statistics: {role: qualifier, values: [<every SPT correlation's
  target>]}`. `describe()` counts its rows as at least or at most; `fit()` censors them; P07 draws them as it
  draws `qualifier` (carets).
- **The qualifier rule changes** (decision 5). Today a qualifier column that names its values is the only one read
  for them, everywhere (`stats/_rows.py`), so `correlation_qualifier` naming `undrained_shear_strength` would stop
  the generic `qualifier` (a lab's `>x`) being read for s_u, in every frame. The rule becomes explicit: a
  qualifier column that replaces the generic one for its values says so (`replaces: qualifier`, naming the
  column `qualifier`, not the role), as `remolded_qualifier` does; any other is read alongside it. `correlation_qualifier` doesn't replace, so a pooled
  frame of lab and SPT s_u reads each row's own.
- **P01** (`plot/_values.py`, `qualifiers()`) reads `correlation_qualifier` for a correlation's target as it reads
  `qualifier`, so a bounded estimate is drawn with its caret and counted in the footnote. 🟡 P01 doesn't read
  `remolded_qualifier` today either; fixing that is out of scope.

### Decisions
1. **No upper limit is not an error.** Right-censoring is the test's result (SPEC §5, decided 2026-11-02), so the
   judgment is optional, the one exception to "judgments have no defaults", because leaving it out adds nothing
   beyond the data. The note says what the tail then is.
2. **The limit is in field N.** The engineer judges refusals from the log, where N is blows per foot; a limit in
   N60 or (N1)60 would mean converting by each hole's ER and each depth's C_N by hand. Scaling by the row's own
   `value / spt_n` applies exactly the factors hangtu applied to the value.
3. **`none` per unit** keeps a unit right-censored on purpose, so a file that bounds one unit isn't an error for
   another with refusals of a different cause (cobbles, rock), and the choice is recorded with its reason.
4. **Only inclusive limits above 0 bound.** A source's `at_most 39` says the data reached 39; `greater_than 0` says
   the equation means nothing at 0. A bound at a limit the data never reached would be a bound in name only.
5. **Qualifiers replace only when they say so.** The vane's `remolded_qualifier` replaces the generic one because
   the generic one on that row is about the peak; a correlation's qualifier is about a different row's kind of
   value, so the two are read together. Explicit in the registry, rather than inferred from `values:`.
6. **The bound is on the estimate, not on N.** `spt_refusal` says N is at least its value; `correlation_qualifier`
   says the estimate is at least (or at most) its value. They are different columns because they bound different
   quantities, and a measured N above a range bounds the estimate without being censored itself.

### Names
Checked by subagent on 2026-11-02 against `src/` (registry, config, judgments, stats, analysis), `SPEC.md`,
`docs/` and `tests/`: none in use.
- New: judgment `spt_refusal_upper_limit` (field `spt_n`) and the `fit()` argument of the same name, as
  `significance_level=` is its judgment's; `judgments=` on `fit()`; result field `count_interval_censored`
  (SciPy's term); column `correlation_qualifier`, in the `correlation_*` family; key `replaces:` under
  `statistics:`, beside `role`, `values`, `when`; config key `bound_by:`; framework step `_framework.bound()`.
- Near names kept apart in the docs: `spt_cap` (decision above), `bounds=` and `probability_*_bound` on `fit()`
  (physical bounds of the property), `count_range` (bands), `correlation_input` (an upstream correlation).

### Golden values
Hand-calculated from the equations (pa = 100 kPa, as `correlations/_framework.py` and `_overburden.py`).
| Correlation | Row | Expected |
|---|---|---|
| Hatanaka & Uchida | (N1)60 45 | φ′ ≥ √(15.4 × 39) + 20 = 44.507142° (`>`) |
| Hatanaka & Uchida | (N1)60 3 | φ′ ≤ √(15.4 × 4.55) + 20 = 28.370783° (`<`) |
| Hatanaka & Uchida | (N1)60 30, refusal | φ′ ≥ √(462) + 20 = 41.494185° (`>`) |
| Hatanaka & Uchida | (N1)60 3, refusal | NaN, "refusal" |
| Kulhawy & Mayne φ′ | N60 70, σ′v 100 kPa | φ′ ≥ arctan[(60 / 32.5)^0.34] = 50.929025° (`>`) |
| Kulhawy & Mayne φ′ | N60 70, σ′v 400 kPa | NaN, "above range" (σ′v beyond 300) |
| Mayne & Kemper σ′p | N 250 | σ′p ≥ 0.47 × 200 × 100 = 9400 kPa (`>`) |
| Mayne & Kemper σ′p | N 0.3 | σ′p ≤ 0.47 × 0.5 × 100 = 23.5 kPa (`<`) |
| Mayne & Kemper OCR | N 40, σ′v 20 kPa (normalized N 200) | OCR ≥ 0.58 × 100 = 58 (`>`) |
| Mayne & Kemper OCR | N 1, σ′v 200 kPa (normalized N 0.5) | OCR ≤ 0.58 × 1 = 0.58 (`<`) |
| Kulhawy et al. K0 | N 40, σ′v 20 kPa (normalized N 200) | K0 ≥ 0.073 × 60 = 4.38 (`>`) |
| Terzaghi & Peck | N 50, refusal | band ≥ 2.0 × 100 = 200 kPa, upper blank (`>`); no range limit on N to bound at |
| Stroud | N60 66.7, PI 35, refusal | s_u ≥ 4.5 × 66.7 × 100 / 100 = 300.15 kPa (`>`) |
| Kulhawy & Mayne E | N60 66.7, refusal, `sands_with_fines` (C = 5) | E ≥ 5 × 66.7 × 100 = 33,350 kPa (`>`) |
| AASHTO E | (N1)60 0 | NaN, "below range" (strict limit) |
| Imai & Tonouchi | N60 500 | Vs ≥ 93.7 × 447^0.31 = 621.34803 m/s (`>`) |
| Ohta & Goto | N60 300 | Vs ≥ 82.1 × 223^0.35 = 544.81601 m/s (`>`) |
| Ohta & Goto | N60 1.5 | Vs ≤ 82.1 × 2.23^0.35 = 108.70508 m/s (`<`) |

Tolerance 1e-9 relative for exact products, 1e-7 for the rounded powers and angles: closed-form arithmetic.

**`fit()`:** N60 12, 18, 25, 31, 40 measured, and two refusals at N60 66.7 with `spt_n` 50 (ER 80 %), Terrace
limit 120: each refusal's limit is 120 × 66.7 / 50 = 160.08. Each fit's parameters equal SciPy's
`fit(CensoredData(uncensored=[...], interval=[[66.7, 160.08], [66.7, 160.08]]))` to 1e-6, and ln L equals
Σ ln f(xᵢ) + 2 ln[F(160.08) − F(66.7)] at those parameters (SciPy as reference, as m15c-fit.md's criterion 4).

### Acceptance criteria
1. Without the judgment, `fit()` on the example Terrace gives today's result, plus the note on the tail.
2. With `spt_refusal_upper_limit` (argument or file), the golden `fit()` case above holds; `count_interval_censored` is 2;
   the judgment is recorded with its source and reason.
3. The limit scales by `value / spt_n`: the same file gives each N column its own limit (N60 and (N1)60 on one
   frame).
4. Errors, each naming what to fix: `spt_refusal_upper_limit=` with a non-N value; no `spt_n`; a limit not above a row's value;
   a unit with refusals the entry doesn't list (no `project:`); a key not a geology unit in the rows.
5. `none` keeps a unit right-censored, and the note says it was set.
6. Every golden correlation row above holds, with its qualifier and note.
7. A row out of another input's range, outside the soil groups, or with a blank input keeps NaN and its reason
   whatever its N.
8. `describe()`, `fit()` and P01 read `correlation_qualifier`; a frame of lab s_u with `qualifier` `>` pooled with
   bounded Stroud estimates counts both (decision 5); `remolded_qualifier` still replaces the generic one.
9. A property test (hypothesis) shows each SPT correlation's estimate is non-decreasing in its `bound_by` input,
   other inputs fixed, over the range.
10. The docs site's correlations example: Hatanaka & Uchida gives an estimate or a bound for 33 of 33 Terrace
    tests, 21 of them bounded; the figure is looked at.
11. Docstrings (each correlation's "Bounded estimates"; `fit()`'s argument), the statistics and correlations guides,
    and SPEC §4 and §5 updated; no new public function, so no new reference entry.
