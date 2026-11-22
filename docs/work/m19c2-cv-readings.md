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
     in the M19 (c) intent), so c_v matches a BS lab's to the figure. ASTM D2435's T50 = 0.197 and T90 = 0.848 give
     values 0.4 % apart; the docstring says so. Double drainage is assumed (intent decision 4).
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
    in minutes in both systems. No other kind has its dimension. In AGS 4.0.3–4.2, 30 standard headings have a
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
  M = π(2m + 1)/2, the standard series; T50 = 0.197 and T90 = 0.848 as the c1 intent checked them. 🔬 To cite in the
  docstring: a textbook with the series and its table, verified against the source before the build (sheet 06's
  bibliography first).
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
