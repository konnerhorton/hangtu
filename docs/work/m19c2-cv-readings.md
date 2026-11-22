# M19 (c2): c_v from settlement–time readings by both constructions; P15

## Intent
M19's fourth unit (M19 (c) decision 4): c_v recomputed from the readings a lab takes during each load increment, by
the log time and root time constructions of BS 1377-5:1990, 3.6.3, with P15 drawing each construction so its t50 and
t90 can be judged. It starts from the c_v parts of `docs/work/m19c-consolidation.md`'s intent.

### Goal
From a CSV of settlement against time per increment, or from a file's user-defined groups through the readings map
(`p.oedometer_readings()`), an engineer gets, per increment, c_v by log time and by root time, with each
construction's points (d0, d100, d50 and t50; d0, d90 and t90), beside the lab's reported c_v, and k from each
recomputed c_v. P15 draws the time curves with the constructions on them, so a reviewer sees where each t50 and t90
came from.

### Why
- **The lab's c_v is taken on trust.** M19 (c1) uses `reported_coefficient_of_consolidation_root_time` and
  `…_log_time` as given, for k and P14. A lab reports only the result (3.7 (i)); the construction behind it is a
  graphical judgment (3.6.3.1, note), and P14 shows the two methods can differ by a factor. The readings let an
  engineer redo it and see it.
- **The standard asks for the curves.** 3.7 (h) lists plots of compression against log time or root time for each
  increment, and (k) the fitting method used. P15 is that plot, made reproducible.
- **Sheet 12's k depends on c_v** (§5.4, built in c1 from the lab's c_v), and the HS and Soft Soil sets later need a
  consolidation rate.

### Evidence (BS 1377-5:1990, 3.6.3–3.7, printed pp. 7–8, read 2026-11-22)
- **3.6.3.1, note:** the two methods "generally show reasonable agreement"; sometimes the root plot has no straight
  line and log time works better, or the reverse (large secondary compression); root time is sometimes best for d0
  and log time for d100.
- **3.6.3.2.1, log time d0:** mark off the difference in ordinates between two points on the initial convex-upward
  portion with times in the ratio 1:4, lay off the same distance above the upper point; repeat with two other pairs
  and average. Its note: this assumes the early curve is parabolic.
- **3.6.3.2.2, d100:** the intersection of tangents to "the two linear portions": at the point of inflexion and the
  secondary compression portion. **3.6.3.2.3:** d50 midway; t50 read off the curve.
- **3.6.3.3.1, root time d0:** the best-fit line to the early portion ("usually within the first 50 % of
  compression"), extended to zero time. **3.6.3.3.2:** the line through d0 with abscissae 1.15 times the first's;
  its intersection with the curve gives d90 and t90.
- **3.6.3.2.4, 3.6.3.3.3:** c_v = 0.026 H̄²/t50 and 0.111 H̄²/t90 (m²/year, H̄ = (H1 + H2)/2 in mm, t in min),
  checked in c1 against T50 = 0.197, T90 = 0.848 and double drainage.
- **3.6.5:** C_sec reuses 3.6.3.2.2's secondary line.

So "the early portion", "the point of inflexion" and "the linear portions" are left to the person drawing them. The
constraint below is what makes them repeatable here.

### Constraints
- **The same readings give the same c_v** (c1's constraint, and SPEC §4's oedometer fit: "the split between them
  searched"). Each construction is a fixed, stated rule, overridable per increment (decision 1). The rules themselves
  (how the 1:4 pairs are chosen, how the linear portions are searched, the root time line's range) are the spec
  step's.
- **A curve the construction can't fit gets a reason, not a value:** no inflexion, no secondary portion, too few
  readings, t90 beyond the last reading. Nothing extrapolates past the readings.
- **Recomputed and reported values are kept apart** (`reported_` columns), never merged.
- **The coefficients assume double drainage** (the standard's cell; decision 4).
- **Golden values from outside the code:** readings generated from Terzaghi's solution with a known c_v, plus an
  immediate compression and a secondary slope, so the constructions should recover c_v within a stated tolerance,
  with one increment's construction points hand-calculated and written out. The docs and figure data get site-like
  scatter.
- **Units:** time needs a `time` quantity kind. By the project's rule, list the AGS headings with a time unit,
  convert each to the kind's canonical unit on ingest, and raise `db.SCHEMA_VERSION`. US files: c_v in ft²/yr
  through the existing `consolidation_coefficient` kind.
- Published text cites the standard by clause and nothing about the copy read.

### Out of scope
- C_sec (3.6.5) and the temperature correction (3.6.4): c1's decisions 5 and 6 stand.
- Rock swelling (M19 (d)); CRS and Rowe cell tests; stage D for c_v.
- Storing overrides with the project, so a rerun after a data update repeats them (TODO #77).
- A QC rule comparing the lab's c_v with the recomputed one: the construction is graphical, so a difference is
  shown on P15, not flagged.

### SPEC and docs touched
- SPEC §4: a bullet for c_v from readings, as the oedometer fit and increments have, and the three kinds of choice
  (decision 1); `docs/analysis/judgments.md` §5.10 says the same from the judgments side. §10.3: new registry columns
  (the recomputed c_v and the construction points). §2.6 if the `time` kind changes how ingest treats any heading.
- `docs/analysis/compressibility.md`: a new section for c_v from readings, and §8's k from the recomputed c_v.
- `docs/data/datasets.md`: the `oedometer_readings` template, §6.15's table with a third dataset (parent
  `CONG`/`CONS`, the increment from `CONS_INCN`) and a §6.18 for `p.oedometer_readings()`.
- `docs/data/ingest.md` §7 (the `time` kind); `src/hangtu/config/defaults.yaml`; `db.SCHEMA_VERSION`.
- `docs/plots/P15-*.md`, promoted from the README's idea row; P14's Related row if P15 adds anything P14 draws.
- Sheet 06: c_v joins its parameter list (decision 5), and the parameter index records the stage. Sheet 12 §5.4: k
  from the recomputed c_v.
- `STATUS.md`'s M19 row; `CHANGELOG.md`.

### Decisions (intent review, 2026-11-22)
1. **Reading a test's curve by a stated rule is neither a judgment nor a method choice, and it doesn't go in the
   judgments file.** hangtu has three kinds of choice, written into SPEC §4 and `judgments.md` §5.10:
   - a **judgment** about the ground or the design (`unit_weight`, φ′cv, `selection`): `judgments.yaml`, keyed by
     unit, hole or project, with no default;
   - a **method choice** the standard leaves open (`failure_criterion=`): an argument, with no default;
   - a **reading of a test by a stated rule** (Oikawa's σ′p, the c_v constructions): the analysis applies the rule,
     the docs state it, a plot shows it, and an engineer can override it.

   The c_v constructions are the third kind. Overrides are an argument, a table keyed by `specimen_id`, increment and
   method giving the time range for each line, recorded on the result. A column on every row says whether its
   points came from the rule or an override, and P15 marks the overridden increments. Reason: the judgments file
   holds a few dozen entries about the ground; picks keyed by specimen × increment × method would number in the
   hundreds and bury them. Making every pick a no-default judgment would mean hundreds of picks before any c_v, and a
   different treatment from the oedometer fit's σ′p, which already reads a curve by a searched rule. The judgment
   is whether to accept the construction, and P15 is where it's made. Casagrande's σ′p (TODO #76) follows the
   same rule.
2. **Both inputs:** the `oedometer_readings` CSV template and `p.oedometer_readings()` through the readings map
   (M16), as a third dataset in its table. Reason: the `time` kind and its ingest change are needed either way, and
   the map already reads user-defined groups for the triaxial and shear box readings.
3. **k from the recomputed c_v is built here,** beside c1's k from the lab's c_v, kept apart by name. Reason: an
   engineer who redoes the construction wants the k that follows from it, and the c1 machinery (m_v, γw, reasons)
   already exists.
4. **Double drainage is assumed and stated;** there is no drainage column. The standard's coefficients assume its
   double-drained cell, and a single-drained test is out of scope.
5. **c_v belongs to sheet 06,** added to its parameter list. Sheet 12 already takes c_v from 06.
6. **Golden values from Terzaghi's solution:** readings generated with a known c_v, an immediate compression and a
   secondary slope. Both constructions recover c_v within a stated tolerance, and one increment's construction
   points are hand-calculated and written out.
7. **Overrides are stored later (TODO #77).** The goal is to rerun an analysis exactly as before after the data
   is updated. Until then, overrides are passed on each call.

## Spec
c_v from settlement–time readings by both constructions, k from it, the `oedometer_readings` input and P15. The rules
go to their topic docs at close-out (`compressibility.md` §9, `datasets.md` §6.15 and §6.18, `ingest.md` §7); the
figure's spec is [`P15-consolidation-time-curves.md`](../plots/P15-consolidation-time-curves.md), promoted in this
commit. The three kinds of choice (intent decision 1) go into SPEC §4 and `judgments.md` §5.10 in this commit,
because they bind later units too. The choices this spec proposed were approved in review on 2026-11-22.

### Changes
- **`ht.analysis.consolidation_coefficient_from_readings()`** (new, decisions 1–9), with its reference entry. Reduces
  readings to one row per increment, as `triaxial_failure_from_readings()` reduces them to one row per stage.
- **`ht.analysis.oedometer_increments()`** gains `consolidation_coefficients=` (decision 10): the reduced rows joined on
  `specimen_id` and `test_stage`, and k from the recomputed c_v.
- **`ht.plot.consolidation_time_curves()`** (new, P15), with its spec, reference entry, site page and example.
  `docs/plots/README.md`: P15's row is renamed from `time_settlement` and becomes `draft` in this commit.
- **`p.oedometer_readings()`** (new, decision 11) and the readings map's third dataset;
  `ht.template("oedometer_readings")` and `ht.template("consolidation_overrides")`.
- **The `time` quantity kind** (decision 12): `defaults.yaml`, `ingest.md` §7, `db.SCHEMA_VERSION` 4 → 5.
- **Registry** (decision 13; each name checked on 2026-11-22 against `columns.yaml`, `src/`, `docs/` outside
  `docs/work/`, `tests/` and `SPEC.md`: none exists except `vertical_displacement`, reused, and `time_settlement`,
  P15's old README name).
- **SPEC §4** (this commit): a "Choices" bullet with the three kinds (intent decision 1), before "Judgment inputs".
  At close-out, a "c_v from readings" bullet after "Oedometer increments", linking `compressibility.md` §9.
- **`docs/analysis/judgments.md` §5.10** (this commit): a bullet saying a test read by a stated rule is not a
  judgment, with the c_v constructions and Oikawa's σ′p as examples, linking SPEC §4's bullet.
- **`docs/analysis/compressibility.md`** (close-out): §9 "c_v from readings" with decisions 1–9; §8's k bullet gains
  k from the recomputed c_v and drops "c_v from time readings is M19 (c2)'s".
- **Test files:** `_make_files.py` gives `site_si.ags` and `site_us.ags` a user-defined group `XCOT` with readings for
  BH1-U3's increments 2–6 (increment 4's are AC 1's table; the others generated the same way, not hand-calculated),
  and `tests/data/ags/readings_map.csv` maps it. `site_v404.ags` gets none.
- **Example file:** `_make_examples.py` gives `site.ags` readings for the example oedometer specimens' loading
  increments, with dial-gauge scatter (±0.002 mm, and one increment fast enough to get a reason), mapped in the
  example `readings_map.csv`; `oedometer_readings.csv` is generated from it.
- **Sheets** (close-out): 06 gains c_v in its parameter list and a §5 entry for the constructions (intent decision
  5); 12 §5.4 adds k from the recomputed c_v; the parameter index records both. Their site pages: sheet 06's page is
  published (M13 b2), so its c_v section is added there too, citing BS 1377-5 by clause.
- **`docs/TODO.md`** (close-out): #77 records what was built; P14 drawing the recomputed c_v goes to P14 §15.
- **Docs site:** the P15 page and example, `reference/analysis.md` and `reference/plot.md` entries, the readings map
  table in the AGS guide.

### Decisions
1. **Readings and increments.** One row per reading, with its increment's values on each row (as §6.16 puts the
   stage's values on each triaxial reading), so the function and P15 take one frame. Grouped by `specimen_id` and
   `test_stage`; increments in order of first appearance; readings within one increment sorted by `elapsed_time`
   (stable: unlike a triaxial unload, time order is the only order a consolidation curve has).
   - **Left out, counted in one note per kind:** a reading with a blank `elapsed_time` or `vertical_displacement`, and
     a reading with a negative `elapsed_time` (before the load was applied).
   - **Branch:** `load_branch` as given, else added by `oedometer_load_branch()` over the increments the frame holds,
     with a note. `constant_stress` increments get no c_v ("constant stress increment"). Unloading and reloading
     increments get c_v by the same constructions, oriented (decision 2), as hangtu's extension: BS 1377-5 describes
     them for load increments, and the docstring says so, as m_v's does.
2. **Orientation and datum.** `vertical_displacement` keeps the file's datum and sign (decision 13). Per increment,
   d_first is the reading at the smallest time and d_last at the largest; y = s (d − d_first) with s the sign of
   d_last − d_first, so y grows with the increment's movement. Every construction works on y and every point is
   written back as d = d_first + s y, in the file's datum. Every construction is unchanged by a shift or a change of
   sign of the readings, so a dial gauge reading down and a settlement reading up give the same c_v.
   - **The early portion:** readings with t > 0 and y ≤ ½ y_last ("usually within the first 50 % of compression",
     3.6.3.3.1, on the increment's whole movement, since d100 isn't known yet). The t = 0 reading, when given, sets
     d_first only: it is taken before the immediate compression, so it isn't on the early line.
   - y_last = 0: both blank, "no displacement over the increment". Fewer than 3 readings with t > 0: both blank,
     "fewer than 3 readings after the load was applied".
3. **Root time** (3.6.3.3), in x = √t:
   1. **The early line:** least squares of y on √t over the early portion; d0 its intercept. Fewer than 3 readings:
      "fewer than 3 readings in the first half of the increment's movement". A slope of 0 or less: "the early
      readings don't move with the increment".
   2. **The 1.15 line:** y = d0 + (b / 1.15) √t, b the early line's slope (abscissae 1.15 times the first's,
      3.6.3.3.2).
   3. **d90 and t90:** the curve is the readings joined by straight lines in √t. The first reading after the early
      portion's last at which the curve is at or below the 1.15 line, and the crossing between it and the reading
      before, interpolated linearly in √t; t90 = x², d90 the line there. The curve at or below the line at the early
      portion's last reading: "the curve is below the 1.15 line in its early portion: no straight early line"
      (3.6.3.1, note). No crossing: "t90 after the last reading".
   4. c_v = 0.111 H̄²/t90 (3.6.3.3.3).
4. **Log time** (3.6.3.2), in x = log10 t over the readings with t > 0:
   1. **The secondary line:** least squares over the readings in the last log cycle of time, t ≥ t_last / 10 (one
      cycle, as 3.6.5.2 extends the same line over one cycle for C_sec). Fewer than 3: "fewer than 3 readings in
      the last log cycle of time".
   2. **The tangent at the inflexion:** of every three consecutive readings ending before the secondary line's first,
      the least squares line with the largest slope; the earlier on a tie. None: "no three readings before the last
      log cycle". Reason: the inflexion is where the curve is steepest in log t, and three readings fit a line
      without one stray reading deciding it.
   3. **No clear secondary portion:** the tangent less than **2** times as steep as the secondary line: "no clear
      secondary portion: the tangent is less than twice as steep as the last log cycle". The same factor as
      `oedometer_fit()`'s break (compressibility.md §3).
   4. **d0 from pairs in the ratio 1:4** (3.6.3.2.1): for each reading time t_i > 0 with 4 t_i at or before the
      tangent's middle reading (the convex-upward portion ends at the inflexion), d0_i = 2 y(t_i) − y(4 t_i), y at
      4 t_i interpolated linearly in log t when no reading has that time. The three largest t_i; d0 their mean (the
      standard's "two other pairs"). Fewer than three: "fewer than 3 pairs of times in the ratio 1:4 before the
      inflexion". The largest pairs are used because their differences are largest against the gauge's
      resolution.
   5. **d100:** where the tangent and the secondary line cross (3.6.3.2.2). Its time before the tangent's middle
      reading or after the last reading: "d100 outside the readings".
   6. **d50 and t50:** d50 = (d0 + d100)/2; t50 where the curve first reaches it, interpolated linearly in log t
      (3.6.3.2.3). At or past it at the first reading: "t50 before the first reading".
   7. c_v = 0.026 H̄²/t50 (3.6.3.2.4).
5. **Interpolation is linear,** in √t for root time and log t for log time: what a hand construction on the
   standard's own plot does when it joins the points. A monotone cubic was checked on Terzaghi curves (AC 3's set):
   root time −6 % to +3 % against linear's −5 % to +8 %, log time −1 % to +2 % against 0 % to +5 %. Immediate and
   secondary compression move root time as much as the interpolation does, and log time's gain is a few percent on
   a method whose two constructions differ by more. It isn't worth values a reviewer can't follow by hand.
6. **H̄ = (H1 + H2)/2** (3.6.3.2.4), H = H0 (1 + e)/(1 + e0): H0 `specimen_height`, e0 `void_ratio` (`CONG_HIGT` and
   `CONG_IVR`, the initial pair), e1 the increment's `void_ratio_at_increment_start`, else the previous increment's
   `void_ratio_at_increment_end` in the frame (with a note, as `oedometer_increments()`), e2 its end. From the void
   ratios, not the readings: the readings' datum is the file's, and an increment's readings needn't start at its
   start. Any of them blank: c_v blank, "no specimen height or void ratio for H̄", with the construction's points and
   times still given. H̄ in mm and t in min in the standard's coefficients, which give m²/year; computed through pint
   whatever the input units.
   - **BS's coefficients, not T50 and T90:** 0.026 and 0.111 are BS 1377-5's rounding of 0.0259 and 0.1115 (checked
     in the M19 (c) intent), so c_v matches a BS lab's to the figure. Terzaghi's T50 = 0.197 and T90 = 0.848 give
     values 0.4 % apart (+0.37 % and −0.45 %); the docstring says so. Double drainage is assumed (intent decision
     4).
7. **Overrides** (intent decision 1): `overrides=`, a frame in `ht.template("consolidation_overrides")`'s shape:
   `specimen_id`, `test_stage`, `consolidation_method` (`root_time`, `log_time`), `curve_portion` (`early` for
   either method; `inflexion` and `secondary` for log time), `elapsed_time_start`, `elapsed_time_end` (inclusive, in
   the frame's declared units), `reason` (required).
   - An override replaces the rule's range for that part only. For root time `early`, the line is fitted to the
     readings in the range; for log time `early`, the pairs are taken with both times in the range (as many as fit,
     at least one), `inflexion` and `secondary` are fitted to the readings in the range (at least 2 each). The
     other steps run as the rule says.
   - Errors, each naming the override's row: a key no increment has, a duplicate key, an unknown method or portion
     (listing them), `inflexion` or `secondary` with `root_time`, start after end, a blank `reason`, times without
     units. A range too short to fit gives the c_v a reason, not an error: "the override for early holds 1
     reading".
   - **Recorded:** the overrides used, in `attrs["consolidation_coefficient_from_readings"]["overrides"]` as records,
     and `coefficient_of_consolidation_root_time_basis` (`…_log_time_basis`) is `override` where any part was
     overridden, `rule` elsewhere. An override for an increment the frame doesn't have is an error, not ignored,
     because a typo would otherwise run as the rule silently. Storing them with the project is TODO #77.
8. **The result:** one row per increment with readings, its identity and increment columns from its first reading
   (`loca_id` … `test_stage`, `load_branch`, `applied_vertical_stress`, the void ratios and the lab's c_v), and the
   columns of decision 13. Notes in `attrs["consolidation_coefficient_from_readings"]["notes"]`, as
   `oedometer_increments()` keeps its own.
9. **Units** resolve as SPEC §2.6 (`units=`, `attrs`, registry). `display_units=` converts the displacements
   (mm, in), H̄ and c_v (m²/yr, ft²/yr); times stay in minutes in both systems (the kind's display unit). Errors:
   a missing `specimen_id`, `test_stage`, `elapsed_time` or `vertical_displacement` names the column and
   `ht.template("oedometer_readings")`.
10. **k from the recomputed c_v** (intent decision 3): `oedometer_increments(df, *, consolidation_coefficients=None,
    ...)` takes the reduced rows, joins them on `specimen_id` and `test_stage` (text, exactly), and adds
    `coefficient_of_consolidation_root_time`, `…_log_time`, their `_basis` and `_reason` columns, and
    `hydraulic_conductivity_from_readings_root_time` and `…_log_time` by c1's decision 7 (k = c_v·m_v·γw, the same
    blanks and reasons, "no c_v from readings" where the c_v is blank). A reduced row matching no increment: one
    warning naming them, since it is data the call drops. An increment with no reduced row: blank, "no readings".
    Two columns beside c1's, not a replacement: lab and recomputed values stay apart.
11. **`p.oedometer_readings()`** (`datasets.md` §6.18): the readings map's third dataset, `oedometer_readings`,
    mapping `test_stage`, `elapsed_time` and `vertical_displacement` (all three required), parent `CONG` or `CONS`
    (increments from `CONS`), joined to the increment on `specimen_id` and `test_stage` matched to `CONS_INCN` as
    text. Each reading carries its increment's `p.oedometer()` values: `test_type`, `load_branch`,
    `applied_vertical_stress`, the void ratios, `specimen_height`, `void_ratio`, the lab's c_v. Rows, order, what is
    left out (a reading with no increment in `CONS`) and the empty frame as §6.16, with `CONS` for `TRET` and
    "oedometer readings" in the messages. `vertical_displacement` keeps the file's sign.
12. **The `time` kind:** canonical `minute` (the standard's unit for readings and the c_v coefficients), displayed
    in minutes in both systems. No other kind has its dimension. In AGS 4.0.3–4.2, 27 standard headings have a
    time unit (`s`, `ms`, `min`, `day`: CPT and DMT dissipation, seismic arrival times, `PLTT_TIME`, `WSTD_NMIN` and
    others) and no dataset reads one; none is in `CONS` or `CONG`. They gain the kind and keep their dictionary
    unit, as every standard heading does (`ingest.md` §7, step 4). That step's "they all match the P00 canonical
    units" is no longer true for time, so `ingest.md` §7 says time is the exception; the plan checks that each
    reader converts from the column's recorded unit, not the kind's canonical one. User-defined headings in a time
    unit convert to minutes. `db.SCHEMA_VERSION` 4 → 5, since stored columns gain a kind.
13. **Names** (checked as under Changes):

    | Column | Kind | Label |
    |---|---|---|
    | `elapsed_time` | time | Elapsed time since the load was applied, t |
    | `vertical_displacement` (existing) | small_length | Vertical displacement, δ_v; its description widens to "at a reading, from a datum and with a sign the file gives" |
    | `average_specimen_height` | small_length | Average specimen height over the increment, H̄ |
    | `coefficient_of_consolidation_root_time`, `…_log_time` | consolidation_coefficient | Coefficient of consolidation (root time), c_v |
    | `coefficient_of_consolidation_root_time_basis`, `…_log_time_basis` | text | `rule` or `override` (the `<quantity>_basis` pattern) |
    | `coefficient_of_consolidation_root_time_reason`, `…_log_time_reason` | text | |
    | `time_to_90_percent_consolidation` | time | Time to 90 % consolidation, t90 |
    | `time_to_50_percent_consolidation` | time | Time to 50 % consolidation, t50 |
    | `corrected_zero_displacement_root_time`, `…_log_time` | small_length | Corrected zero point, d0 |
    | `displacement_at_90_percent_consolidation` | small_length | d90 |
    | `displacement_at_50_percent_consolidation`, `displacement_at_100_percent_primary_consolidation` | small_length | d50, d100 |
    | `hydraulic_conductivity_from_readings_root_time`, `…_log_time` | hydraulic_conductivity | Hydraulic conductivity from c_v by readings (root time), k |
    | `hydraulic_conductivity_from_readings_root_time_reason`, `…_log_time_reason` | text | |
    | `consolidation_method`, `curve_portion`, `elapsed_time_start`, `elapsed_time_end`, `reason` | text, text, time, time, text | the overrides template |

    - The recomputed c_v takes the plain name; the lab's stays `reported_` (M19 (a) decision 4). `percent` is spelled
      out, as `percent_passing` does.
    - k from readings is named `…_from_readings_…`, and c1's `hydraulic_conductivity_root_time` (k from the lab's
      c_v) keeps its name. Renaming it `…_from_reported_…` would read more clearly, but it would rename columns c1
      just added, its tests and P14's code, for a gain the labels and descriptions already give.
    - `reason` is checked in the plan against its uses in the judgments file; if it would be read as a judgment
      field, the column is `override_reason`.
14. **P15** as its spec: one row of panels per increment, root time left and log time right, with each
    construction's lines and points and the c_v beside the lab's. It calls
    `consolidation_coefficient_from_readings()` and returns `(fig, axs)`.

### Sources
- **BS 1377-5:1990** (incorporating Amendment 1): 3.6.3.1 and its note, 3.6.3.2.1–3.6.3.2.4, 3.6.3.3.1–3.6.3.3.3,
  3.6.5.2 (the one-cycle secondary line), 3.7 items (h), (i), (k). Read 2026-11-22 (the intent's Evidence).
- **Terzaghi's solution,** for the readings the golden values start from: U(T) = 1 − Σ (2/M²) exp(−M² T),
  M = π(2m + 1)/2, the standard series; T50 = 0.197 and T90 = 0.848 as the c1 intent checked them.
- **Abuel-Naga, H. M. & Pender, M. J. (2012).** Modified Terzaghi consolidation curves with effective
  stress-dependent coefficient of consolidation. *Géotechnique Letters* 2, 43–48,
  https://doi.org/10.1680/geolett.12.00005. Table 1, p. 45, column i_cv = 0 (Terzaghi's constant c_v): T at U_avg
  10–90 % = 0.008, 0.031, 0.071, 0.126, 0.197, 0.287, 0.403, 0.567, 0.848; T_v = c_v t/H², H the longest drainage
  path (Eq. 6, p. 44). Read 2026-11-22: the series above, inverted at each U, matches all nine to the table's three
  decimals. The docstring cites it for T50 and T90; it doesn't give the series, which the tests state in full.
- **Unit factors** as c1's Sources: 1 m²/yr = 10.7639104 ft²/yr; 1 in = 25.4 mm; a year of 525 960 min.

### Acceptance criteria
**The golden increment** is BH1-U3's increment 4 (100 → 200 kPa, e 0.776 → 0.748; H0 20.00 mm, e0 0.800). H1 =
20 × 1.776/1.8 = 19.7333333 mm, H2 = 20 × 1.748/1.8 = 19.4222222 mm, H̄ = 19.5777778 mm, H̄² = 383.289383 mm². Its
readings were generated from Terzaghi's solution with c_v = 2.0 m²/yr, ρ = 0.2735 mm, an immediate compression of
0.020 mm and a secondary slope of 0.010 mm per cycle, from a datum of H0 − H1 = 0.267 mm, and rounded to 0.001 mm.
The steps below are a hand calculation from the readings as rounded. Tolerance 1e-9 relative unless stated.

| t (min) | 0 | 0.1 | 0.25 | 0.5 | 1 | 2 | 4 | 8 | 15 | 30 | 60 | 120 | 240 | 480 | 1440 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| δ_v (mm) | 0.267 | 0.306 | 0.317 | 0.330 | 0.348 | 0.374 | 0.410 | 0.460 | 0.511 | 0.552 | 0.565 | 0.568 | 0.570 | 0.573 | 0.578 |
| y (mm) | 0 | 0.039 | 0.050 | 0.063 | 0.081 | 0.107 | 0.143 | 0.193 | 0.244 | 0.285 | 0.298 | 0.301 | 0.303 | 0.306 | 0.311 |

1. **Root time.** s = +1, y_last = 0.311, half 0.1555, so the early portion is t = 0.1–4 (y 0.039–0.143; 8 min's
   0.193 is past it). Least squares of y on √t over those six: y = 0.0192330013 + 0.0619114129 √t, so d0 =
   0.286233001 mm. The 1.15 line has slope 0.0538360112. At 4 min the curve (0.143) is above it (0.126905024); at 15
   min still above (0.244 against 0.227738976, by 0.016261024); at 30 min below (0.285 against 0.314104979, by
   −0.0291049786). √t90 = √15 + (√30 − √15) × 0.016261024 / 0.0453660026 = 4.44800913, t90 = 19.7847853 min, d90 =
   0.525696071 mm. c_v = 0.111 × 383.289383 / 19.7847853 = **2.15039592 m²/yr**, basis `rule`.
2. **Log time.** The last cycle is t ≥ 144: 240, 480 and 1440 min, y = 0.278448445 + 0.0102988527 log10 t. The
   steepest three-reading line before 240 min is 4, 8, 15 min (slope 0.175780553; the next, 8–30, is 0.159859434):
   y = 0.0362299771 + 0.175780553 log10 t, 17.1 times the secondary slope. Its middle reading is 8 min, so the pairs
   are (0.5, 2), (1, 4), (2, 8): d0_i = 2 × 0.063 − 0.107 = 0.019, 2 × 0.081 − 0.143 = 0.019, 2 × 0.107 − 0.193 =
   0.021; d0 = 0.0196666667, i.e. 0.286666667 mm. d100 where the lines cross: log10 t = 1.46371754 (29.0882465 min),
   y = 0.293523057, i.e. 0.560523057 mm. d50: y 0.156594862 (0.423594862 mm), between 4 min (0.143) and 8 min (0.193):
   log10 t50 = log10 4 + log10 2 × 0.013594862/0.050 = 0.683909216, t50 = 4.82957834 min. c_v = 0.026 × 383.289383 /
   4.82957834 = **2.06343562 m²/yr**, basis `rule`.
3. **Recovery of the generating c_v:** both within 10 % of 2.0 (+7.5 % and +3.2 %). On readings generated the same
   way without rounding for c_v 0.3, 1, 2, 5 and 10 m²/yr, with no, small (0.03 mm, 0.02 mm/cycle) and large (0.08,
   0.05) immediate and secondary compression, H̄ 18 mm and the standard's times, each method is within 10 % of the
   generating c_v (in the check made for this spec, root time −5 % to +8 %, log time 0 % to +5 %). At c_v 20 the
   standard's times can't resolve the curve: log time gives "fewer than 3 pairs…" in all three cases, and root time
   "fewer than 3 readings in the first half…" unless a large immediate compression lengthens its early portion. The
   test generates these from the
   series in the test, not from hangtu.
4. **Overrides:** root time `early` 0.25–4 min gives y = 0.0190752377 + 0.0620181363 √t, t90 19.7049019 min, c_v
   2.15911359 m²/yr; log time `secondary` 120–1440 min gives y = 0.281019115 + 0.00941096958 log10 t, d100 at
   29.6044854 min, t50 4.87474524 min, c_v 2.04431687 m²/yr, d0 unchanged. Each sets its basis to `override`, the
   other method's stays `rule`, and `attrs` records both rows with their reasons.
5. **Datum and sign:** the same readings negated, or shifted by 10 mm, give the same c_v and times, and the points in
   the file's datum and sign.
6. **k from readings:** `oedometer_increments(p.oedometer(), consolidation_coefficients=…)` on `site_si.ags` gives
   increment 4 k = 2.15039592 × 0.157657658 × 9.81 × 10⁻³ / 31 557 600 = 1.05389790e-10 m/s (root time) and
   1.01127911e-10 m/s (log time), beside c1's 1.02919912e-10 and 8.82170672e-11; "no readings" on increments 1 and
   7–12.
7. **Reasons** (hand-built frames, one increment each): a constant stress increment; readings all equal; two
   readings after t = 0; an early portion of two readings; a root curve flat from the start; readings that stop at
   10 min (t90 after the last reading; fewer than 3 in the last cycle); a curve still steep in its last cycle (no
   clear secondary portion); a curve reaching d50 by its first reading; a blank `specimen_height` (c_v blank, t50
   and t90 given). Each gives its reason's wording from decisions 2–6.
8. **Readings left out:** a blank time, a blank displacement and a negative time are left out with one note each,
   counted; an unsorted increment gives the sorted increment's c_v.
9. **Overrides' errors:** each error of decision 7 raises naming the row.
10. **Dataset:** `p.oedometer_readings()` on `site_si.ags` with `tests/data/ags/readings_map.csv` gives increment 4's
    15 readings with its increment values; the readings map's checks (§6.15) reject a `XCOT` mapped without
    `elapsed_time`, and one whose `DICT_PGRP` is `TRET`; a reading whose `XCOT_INCN` matches no `CONS_INCN` is left
    out with §6.16's warning.
11. **Units and twins:** `site_us.ags` (readings in in and min) gives the same c_v as `site_si.ags` to 1e-9 in
    canonical units; `display_units="US"` gives increment 4's root time c_v 23.1466690 ft²/yr and H̄ 0.770778653 in
    (to 1e-6, the factors' precision). A user-defined time heading in `s` converts to minutes on ingest.
12. **Registry and reference:** the new columns in `columns.yaml` with their kinds, the two templates, reference
    entries for both functions and P15 (`tests/docs/test_site.py`), and docstrings giving the constructions, the
    clauses, the coefficients, the overrides and each reason's wording, with no internal file cited.
13. **P15:** its acceptance criteria (P15 §12).

## Plan
Draft, 2026-11-22. Ten commits, each green: the tests it touches, then the CI command with `-n 3`. Steps 1–6 on
Opus (the `time` kind's ingest change, the dataset that carries the golden readings, the two constructions, the
overrides' rules and errors, k), 7–9 on Sonnet (the example data, the plot and the docs site, with the spec's values
and P15 §12 deciding correctness), 10 on Opus (the figure judged against P15, the topic docs, the sheets,
close-out): two model boundaries, after 6 and after 9, and a new Opus session after step 3 to keep the first one
short. A step past about 300 changed lines without test data splits as noted. Reused, not rebuilt:
- **Oedometer:** `oedometer_load_branch()`, `branches()`, `one_value()`, `specimen_label()`, `stress_text()`
  (`analysis/_oedometer.py`); `oedometer_increments()`'s e1 fallback and its note (decision 6 reads e1 the same way).
- **Readings:** `triaxial_failure_from_readings()` (`analysis/_triaxial_readings.py`) as the pattern for reducing
  readings to one row per group, its notes in `attrs` and its input errors; the readings map (`DATASETS`,
  `_parents`) and `_readings()` (`datasets/_readings.py`); `curve_group()` and `curve_dict_rows()` in
  `tests/data/ags/_make_files.py`.
- **Units and data:** `resolve_units`, `parse_unit`, `check_dimension`, `convert`, `to_display` (`hangtu.units`);
  `numeric_column`, `rows_text` (`_data`); `ColumnError`, `HangtuError`, `warn` (`errors`); `group_keys()`.
- **Plotting:** as `plot/_consolidation_coefficients.py` (P14): `style.context`/`style_axes`, `figure_size`,
  `axis_label`, `add_legend`, `Notes`, `figure_of`, `hint_missing`, `resolve_palette`, `format_number`.

Code cites `docs/analysis/compressibility.md` §9 and `docs/data/datasets.md` §6.18, which step 10 writes, as c1's code
cited §8 before it was written; the registry's `ags` entries for the derived columns say
`"derived: docs/analysis/compressibility.md"`.

**Settled before the build:**
- **`override_reason`, not `reason`** (approved 2026-11-22) (Spec decision 13's check): `reason` is the field every judgments file entry
  carries (`_judgments.py`, `judgments.md`), so an overrides column of that name would read as a judgment field, the
  thing decision 1 says an override isn't. Step 5 names it `override_reason`; decision 7's "`reason` (required)" and
  its error ("a blank `reason`") read `override_reason`. The Spec's text is corrected in step 5's commit.
- **The Terzaghi source** (Sources, settled 2026-11-22): Abuel-Naga & Pender (2012), Table 1, for T50 and T90 and
  the docstring's "0.4 % apart" remark, in place of ASTM D2435, which isn't at hand. The Spec's decision 6 and
  Sources are corrected in this commit. Taylor (1948), the root time method's origin with the series and its table,
  was skipped: the docstring names the methods "root time" and "log time", as BS 1377-5 does, not by author.
- **`ingest.md` §7 moves to step 1,** not close-out (a deviation from the Spec's intro): step 1 makes its step 4's
  "they all match the P00 canonical units" untrue, and the text should change with the behavior.

### 1. `units: add the time quantity kind; schema version 5` (Opus)
- `src/hangtu/config/defaults.yaml`: `time`, canonical `minute`, US and SI `{unit: minute, text: min}`, after
  `consolidation_coefficient` with a comment that no other kind shares its dimension (decision 12). The aliases for
  `s`, `ms`, `min` and `day` exist (`units/aliases.yaml`).
- Ingest (`ags/_units.py`): a user-defined heading in a time unit converts to minutes through `_canonical()` unchanged.
  A standard heading keeps its dictionary unit and values; its `meta_heading.quantity` is `time` by dimension, since
  `_quantity()` matches a kind only when the unit is its canonical one. Before changing `_quantity()`, list which
  standard headings a match by dimension would change outside time (e.g. MPa headings against `modulus`'s kPa); if any
  does, the match by dimension applies to time only, and the commit says why.
- The readers: check that every dataset reader (`Build.numbers()` and the readings' `_group_readings()`) converts
  from `meta_heading.unit`, the column's recorded unit, and not from the kind's canonical one; no dataset reads a
  time heading today, so this is a check written into a test, not a fix. Record the 27 headings' count by unit in
  the commit body.
- `src/hangtu/db.py`: `SCHEMA_VERSION = 5`; the stored-project mismatch message and its test unchanged in wording.
- `docs/data/ingest.md` §7 step 4: time is the exception (standard headings keep `s`, `ms`, `day`; user-defined ones
  convert to `min`). SPEC §2.6 is read and changed only if it states the rule step 4 states.
- Tests: `tests/ags/` (the units tests): a user-defined `XTIM_TIME` heading in `s` stored in minutes (AC 11, last
  sentence); a standard `PLTT_TIME` in a hand-built file keeps its unit with quantity `time`; `tests/test_units.py`
  for the kind; `tests/test_db.py` (or wherever `SCHEMA_VERSION` is tested) for 5. The whole suite, since every
  ingest test passes through the change.

### 2. `M19: add p.oedometer_readings() and the XCOT test readings` (Opus)
- `columns.yaml`: `elapsed_time` (time) and `vertical_displacement`'s description widened (decision 13); the
  `oedometer_readings` template: `p.oedometer_readings()`'s columns without `source_line` (identity and depth
  columns, `test_type`, `test_stage`, `load_branch`, `applied_vertical_stress`, the two increment void ratios,
  `specimen_height`, `void_ratio`, the two `reported_` c_v, `elapsed_time`, `vertical_displacement`, the geology
  columns). `tests/test_registry.py` green.
- `datasets/_readings_map.py`: `DATASETS["oedometer_readings"]`: mapped and required `test_stage`, `elapsed_time`,
  `vertical_displacement`; no `one_of` (the check today requires one, so an empty `one_of` passes it); stages
  `{"CONG": "CONS", "CONS": "CONS"}`. The "readings datasets are …" message lists three.
- `datasets/_readings.py`: `ORDER["oedometer_readings"] = (("CONS",), "oedometer readings")`. The increment values
  come from `p.oedometer()`'s own builder (`datasets/_oedometer.py`, incomplete rows kept, as `_stage_rows()` keeps
  them), keyed on `specimen_id` and `CONS_INCN` as text, so each reading carries exactly the values `p.oedometer()`
  gives its increment, `load_branch` included (decision 11), rather than a second reading of `CONS` and `CONG` in a
  `Stages` entry. If `_join()` can't take that frame as it is, it gains the parameter it needs, not a copy.
- `project.py`: `Project.oedometer_readings()`, as `triaxial_readings()`: its docstring (rows, the join, what is left
  out, the sign kept, an example), and its reference entry where `triaxial_readings` has one.
- `tests/data/ags/_make_files.py`: `XCOT` (`XCOT_TESN`, `XCOT_TIME` `min`, `XCOT_DISP` `mm`) under `CONG`, for
  BH1-U3's increments 2–6: increment 4's 15 readings exactly as AC 1's table; the others from Terzaghi's series in
  the file (the same immediate and secondary terms, each increment's ρ from its void ratios, c_v near the lab's),
  rounded to 0.001 mm, with a comment that they aren't hand-calculated. `site_us.ags` converts `XCOT_DISP` to `in`
  and keeps minutes. `site_v404.ags` none. `tests/data/ags/readings_map.csv` maps `XCOT`;
  `tests/data/ags/README.md` describes it. Every other file checked unchanged (`git diff --stat tests/data/ags`).
- Tests: `tests/datasets/test_readings.py` (AC 10: increment 4's 15 readings with its increment values; a reading
  whose `XCOT_INCN` matches no `CONS_INCN` left out with §6.16's warning; the empty frame);
  `tests/datasets/test_readings_map.py` (AC 10: `XCOT` without `elapsed_time` rejected, `DICT_PGRP` `TRET`
  rejected); the twins in canonical units to 1e-9 (AC 11's dataset part).

### 3. `M19: add consolidation_coefficient_from_readings(), root time` (Opus)
- `columns.yaml`: every column of decision 13 but the overrides template's, with kinds and labels, the `ags` entry
  above, no `used_by` yet (step 8 adds it; c1's note). The log time and k columns too, so steps 4 and 6 add no
  registry change.
- `src/hangtu/analysis/_consolidation_readings.py` (new), exported in `analysis/__init__.py`:
  - inputs (decisions 1, 9): the required columns, each missing one an error naming it and
    `ht.template("oedometer_readings")`; units resolved per SPEC §2.6; grouping by `specimen_id` and `test_stage` in
    order of first appearance, readings sorted stably by `elapsed_time`; the three left-out kinds, one note each,
    counted; `load_branch` read or added with its note; `constant_stress` increments' reason;
  - orientation and datum (decision 2): s, y, the early portion, the two whole-increment reasons; every point
    written back in the file's datum and sign;
  - root time (decision 3): the early line, the 1.15 line, d90 and t90 by linear interpolation in √t, each reason
    worded as decision 3 gives it;
  - H̄ (decision 6) from the void ratios, e1's fallback with its note, the "no specimen height or void ratio for H̄"
    reason with the points still given; c_v = 0.111 H̄²/t90 in canonical units (mm, min → m²/yr), through pint where
    the input isn't canonical;
  - the result (decision 8): one row per increment, its identity and increment columns from its first reading;
    `attrs["consolidation_coefficient_from_readings"]["notes"]`; `display_units=` (decision 9). The frame has the
    root time columns only; step 4 adds the log time ones, so no placeholder column reaches a commit.
  - the docstring per `docs/drafts/parameters/TEMPLATE.md`'s checklist for root time: the construction step by step,
    BS 1377-5:1990, 3.6.3.3.1–3.6.3.3.3, the coefficient and its rounding, double drainage, the unload and reload
    increments as hangtu's extension, each reason's wording, an example on `p.oedometer_readings()`.
- `docs/site/reference/analysis.md`: `consolidation_coefficient_from_readings`.
- Tests: `tests/analysis/test_consolidation_coefficient_from_readings.py` (new), with `tests/analysis/_terzaghi.py`
  (new: the series of Sources, written from the spec, not from hangtu, and checked first against Abuel-Naga &
  Pender's Table 1, i_cv = 0, to its three decimals at U = 10–90 %): AC 1 (each number, 1e-9), AC 3's root time
  half (the 15 generated cases and c_v 20), AC 5 for root time, AC 7's reasons from decisions 2, 3 and 6, AC 8, AC 11
  (the twins on `site_si.ags`/`site_us.ags` to 1e-9; `display_units="US"` 23.1466690 ft²/yr and H̄ 0.770778653 in to
  1e-6); the docstring and reference checks (`tests/docs/test_site.py`, `tests/test_errors.py`).
- If past about 300 lines: (3a) inputs, grouping, orientation and the result's frame (AC 8, decision 2's reasons),
  then (3b) the construction, H̄ and units (AC 1, 3, 5, 7, 11).

### 4. `M19: add the log time construction to c_v from readings` (Opus)
- `_consolidation_readings.py`: decision 4 in order: the secondary line over the last log cycle, the steepest
  three-reading tangent before it (the earlier on a tie), the factor-2 check, d0 from the three largest 1:4 pairs
  (y at 4 t_i interpolated in log t), d100 at the crossing, d50 and t50; c_v = 0.026 H̄²/t50; each reason worded as
  decision 4 gives it. The t = 0 reading takes no part (no position in log t).
- The docstring's log time paragraph: BS 1377-5:1990, 3.6.3.2.1–3.6.3.2.4 and 3.6.5.2's one cycle; why the largest
  pairs; the interpolation (decision 5); the BS coefficients against T50 and T90 (decision 6's bullet, cited as the
  Abuel-Naga & Pender (2012), Table 1, as Sources gives it).
- Tests, same file: AC 2 (each number), AC 3's log time half, AC 5 for log time, AC 7's reasons from decision 4.

### 5. `M19: add overrides to consolidation_coefficient_from_readings()` (Opus)
- `columns.yaml`: `consolidation_method`, `curve_portion`, `elapsed_time_start`, `elapsed_time_end`,
  `override_reason`; the `consolidation_overrides` template.
- `_consolidation_readings.py`: `overrides=` (decision 7): validated first, every error naming the override's row
  (as the file numbers it when read from a CSV: header = 1) and what to do; the ranges in the frame's declared time
  units converted to minutes; each override replacing its part's range only; "the override for early holds 1
  reading"; the `_basis` columns; `attrs[...]["overrides"]` as records.
- The docstring's overrides paragraph: what each portion replaces, the minimum readings, the errors, that the
  overrides are recorded on the result and passed on each call.
- The Spec's decision 7 and 13: `reason` → `override_reason`.
- Tests, same file: AC 4 (each number, both bases, `attrs`), AC 9 (each error), the template (`ht.template(
  "consolidation_overrides")` columns).

### 6. `M19: add k from the recomputed c_v to oedometer_increments()` (Opus)
- `analysis/_oedometer_increments.py`: `consolidation_coefficients=` (decision 10): the reduced rows joined on
  `specimen_id` and `test_stage` as text; the four c_v columns (value, basis, reason) carried; `hydraulic_
  conductivity_from_readings_root_time` and `…_log_time` by c1's decision 7, with its blanks and reasons and "no c_v
  from readings"; "no readings" on increments with no reduced row; one warning naming the reduced rows that match
  no increment. Without the argument, the frame is as before.
- The docstring: the argument, the join, the two pairs of k columns kept apart.
- Tests: `tests/analysis/test_oedometer_increments.py`: AC 6 (both k, c1's beside them unchanged, "no readings" on
  increments 1 and 7–12), the warning (`pytest.warns`), the twins.

### 7. `M19: add oedometer readings to the example project` (Sonnet)
- `tests/data/_make_examples.py`: an `XCOT` group in the example `site.ags` for the example oedometer specimens'
  loading increments, generated from the series with the increment's void ratios and a c_v near the lab's, with
  dial-gauge scatter of ±0.002 mm (seeded) and one increment fast enough that log time gives a reason; the example
  `readings_map.csv` maps it; `oedometer_readings.csv` generated from it (the examples-AGS-first rule).
- The example project's tests (wherever `site.ags`'s groups and the CSVs are checked) updated for the new group and
  file; `ht.examples` lists the CSV if it lists the others.
- Tests: the example data tests; `consolidation_coefficient_from_readings()` on the example gives c_v on every
  loading increment but the fast one, which gives its reason.

### 8. `M19: add ht.plot.consolidation_time_curves() (P15)` (Sonnet)
- `src/hangtu/plot/_consolidation_time_curves.py` (new), exported in `plot/__init__.py`, as P15 §5–§11: calls
  `consolidation_coefficient_from_readings()` with `overrides=`, `units=` and `display_units=` and draws its rows and
  the readings, computing nothing of its own; one row of panels per increment, `methods=` columns, 2.4 in per row at
  `default`'s width, more than 6 increments an error naming `increments=`; the y axis inverted where s = +1; §7's
  marks (filled where fitted or paired, open joined otherwise, t = 0 on the root panel only), lines, points and the
  result text (3SF, the lab's as written, "(override)"); the reason centered where a construction gives none; the
  footnote from the analysis's notes; `specimen=` required with more than one specimen; returns `(fig, axs)` shaped
  (rows, columns).
- What the plot needs from the analysis that the result frame doesn't hold (which readings each line was fitted to,
  the 1:4 pairs, each line's slope and intercept): a private helper in `_consolidation_readings.py` that both the
  public function and the plot call, so the plot reads the same fit, not a second one. If the plot needs anything
  the analysis's decisions don't give, stop and hand it back to Opus.
- `columns.yaml`: `used_by: [plot.consolidation_time_curves]` on the columns it draws.
- `docs/site/reference/plot.md`: `consolidation_time_curves`.
- Tests: `tests/plot/test_consolidation_time_curves.py` (new): P15 AC 1–4 and 6–9 from the drawn artists (positions,
  fill, line styles, inverted axes, texts, the array's shape); `tests/plot/test_consolidation_time_curves_acceptance.py`
  (new): AC 5 and the example project with `display_units="US"`.
- If past about 300 lines: (8a) the grid, the readings, the lines and points, orientation and returns (AC 1–3, 7,
  8), then (8b) the result text, overrides, reasons, the footnote, units and edge cases (AC 4–6, 9).

### 9. `M19: draw the consolidation time curves on the docs site` (Sonnet)
- `docs/site/examples/consolidation-time-curves.py` (new): an example project specimen in US units, its curves for
  three increments, and the reduced frame printed; an override shown in a second figure.
  `docs/site/plots/consolidation-time-curves.md` (new): what each panel shows, the rule behind each line, why a
  construction gives a reason, overrides and when to use them, the lab's value beside hangtu's; linked in
  `zensical.toml`'s `nav` and `docs/site/plots/index.md`.
  - One or two sentences (approved 2026-11-22) on why the two methods differ: where c_v changes with stress within an increment, log
    time reads it at U = 50 % and root time at U = 90 %, so each gives a different equivalent c_v, and which is
    higher depends on whether c_v rises or falls with stress (Abuel-Naga & Pender 2012, pp. 45–47). Context for the
    reviewer judging P15, not a rule hangtu applies; their recommendation of root time isn't adopted.
- `docs/site/guides/datasets.md`: `p.oedometer_readings()`'s row; the AGS guide's readings map table gains
  `oedometer_readings` (parent `CONG`/`CONS`, the three mapped columns).
- Run `docs/prepare_site.py` and `zensical build --clean --strict`.

### 10. `M19: close out (c2)` (Opus)
- **Visual check:** `docs/plots/img/P15-si.png` (BH1-U3, increments 3–5, kPa and mm) and `P15-us.png` (an example
  specimen with scatter, in), 100 dpi, looked at against P15, committed (P15 AC 10).
- **Close-out:**
  - `docs/analysis/compressibility.md`: §9 "c_v from readings" with decisions 1–9, linking the API reference rather
    than restating the docstring; §8's k bullet gains k from the recomputed c_v and drops "c_v from time readings is
    M19 (c2)'s"; Related gains P15. `CLAUDE.md`'s `docs/analysis/` list: `compressibility.md` becomes "the
    oedometer fit, increments and c_v from readings";
  - `docs/data/datasets.md`: the `oedometer_readings` template, §6.15's table with the third dataset, §6.18;
  - SPEC §4: the "c_v from readings" bullet after "Oedometer increments"; §10.3's registry columns;
  - `docs/plots/P15-consolidation-time-curves.md` status `built` with its images; `docs/plots/README.md` P15 `built`;
    P14's Related row gains P15;
  - sheets 06 (c_v in its parameter list, a §5 entry for the constructions) and 12 §5.4 (k from the recomputed c_v);
    the parameter index; sheet 06's site page gains its c_v section, citing BS 1377-5 by clause; Abuel-Naga &
    Pender (2012) joins sheet 06's bibliography as [V] (Table 1, p. 45; pp. 45–47 if step 9 uses the remark);
  - `docs/TODO.md`: #77 records what was built; P14 drawing the recomputed c_v goes to P14 §15; anything deferred
    here with its trigger;
  - `STATUS.md`: M19 "(a), (b), (c1), (c2) done; (d) next", the Next line; `CHANGELOG.md` Unreleased:
    `p.oedometer_readings()`, `consolidation_coefficient_from_readings()`, `oedometer_increments()`'s new argument,
    `consolidation_time_curves()`, the `time` kind and the schema version (a stored project re-ingests), in the
    user's words;
  - what a future session would get wrong without being told, written where it will be read (the three kinds of
    choice are already in SPEC §4).
- **Verification:** every AC of the Spec and of P15 §12 reported as met or not, with its test; the whole suite with
  `-n 3`; ruff; mypy; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.

### Notes from the build
- **Step 1.** The standard headings with a unit of time number 27, not 30 (17 `s`, 6 `ms`, 3 `min`, 1 `day`, across
  4.0.3–4.2, numeric types only); decision 12 and step 1 are corrected. A match by dimension for every kind would
  change dozens of standard headings (MPa and GPa to `stress`, mm/s and m/hr to `hydraulic_conductivity`, kg/m³ to
  `density`, ppmv to `angle`), so `_quantity()` matches time by dimension and nothing else. The readers' check:
  `_group_readings()` converts from `meta_heading.unit`; `Build.numbers()` reads stored values, and no dataset reads
  a time heading. The test that a readings heading converts from its stored time unit is step 2's (`XCOT_TIME`).
  P00 §4.1's kind table gains `time` (`tests/test_registry.py` mirrors it).
- **Step 2.** The golden readings' generator, recovered from AC 1's table and reproducing all 15 values: y =
  0.020 + ρ U(T) + 0.010 log10(1 + t/t1), t1 the time at T = 1 (H̄/2 drainage), and ρ the increment's height change
  from its void ratios less the immediate and the secondary at 1440 min (ρ = 0.27347 mm for increment 4, the
  spec's 0.2735). `_make_files.py` uses it for increments 2–6 (c_v 3.0, 2.5, 2.0, 1.5, 1.2 m²/yr); step 3's
  `tests/analysis/_terzaghi.py` uses the same terms. The mapped stage heading is `XCOT_TESN` (as every curve group's),
  where AC 10 says `XCOT_INCN`. `joins.ags` gets an `XCOT` too, since the readings map is checked against it:
  increment 1, two readings of increment 2 (incomplete in `CONS`, so `p.oedometer()` leaves it out, but its
  readings keep its values) and two of an increment 3 that `CONS` lacks (AC 10's warning). The site files' DICT
  rows move every later line by 12; the tests that name lines are updated. `load_branch` on the readings is
  `oedometer_load_branch()` over every `CONS` row (`p.oedometer(include_incomplete=True)`'s), so it can differ from
  `p.oedometer()`'s only where an incomplete increment has a stress. The readings map's messages now say "An
  oedometer_readings group" and list three required columns as "a, b and c".
