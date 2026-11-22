# M19 (c2): c_v from settlement–time readings by both constructions; P15

## Intent
M19's fourth unit (M19 (c) decision 4): c_v recomputed from the readings a lab takes during each load increment, by
the log time and root time constructions of BS 1377-5:1990, 3.6.3, with P15 drawing each construction so its t50 and
t90 can be judged. It starts from the c_v parts of `docs/work/m19c-consolidation.md`'s intent.

### Goal
From a CSV of settlement against time per increment, or from a file's user-defined groups through the readings map
(`p.oedometer_readings()`), an engineer gets, per increment, c_v by log time and by root time, with each construction's points (d0, d100,
d50 and t50; d0, d90 and t90), beside the lab's reported c_v, and k from each recomputed c_v. P15 draws the time curves with the constructions on
them, so a reviewer sees where each t50 and t90 came from.

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
