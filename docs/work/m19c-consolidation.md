# M19 (c): m_v, c_v, k and the oedometer moduli; P14–P15

## Intent
M19's third unit (M19 (a) decision 1, with Eoed and Eur,oed moved here by M19 (b) decision 1): stage B for sheet 11's
oedometer moduli and sheet 12's k from c_v·m_v, and the QC rule E003 that waited on m_v's definition (TODO #73).
🟡 marks a choice proposed here, awaiting review. Decision 4 splits (c): this branch builds (c1); the c_v
readings, constructions and P15 below are (c2)'s, kept here as the starting point for its intent.

**Goal:** from `p.oedometer()` (or a CSV in the `oedometer` template), an engineer gets, per increment, m_v recomputed
from the void ratios beside the lab's, the constrained modulus on loading (Eoed) and on unloading and reloading
(Eur,oed), and k from c_v·m_v·γw. From a CSV of settlement against time per increment, they get c_v by the root time
and log time methods, with each construction's points, and P15 draws them so the fit can be judged. P14 draws c_v and
m_v against log σ′v. QC E003 warns when a lab's m_v doesn't follow from its own void ratios.

**Why:**
- **The lab's m_v and c_v arrive but aren't checked or used.** M19 (a) reads `CONS_INMV`, `CONS_CVRT` and
  `CONS_CVLG` into `reported_` columns so they can be recomputed and compared (M19 (a) decision 9), as M11 (a) did for
  c′ and φ′. E003 was designed in M19 (a) (decision 7) but not built, because m_v's definition hadn't been checked
  against a standard. It now has been (under "Evidence").
- **Sheets 11 and 12 list these as W3.** Sheet 11 §5.3: Eoed = 1/m_v on the virgin branch, Eur,oed on the unload or
  reload at the same σ′v. Sheet 12 §5.4: k = c_v·m_v·γw from the increment spanning σ′v0, whose source is still [U].
- **c_v depends on a graphical construction.** Both methods locate a point on the time curve by a stated
  construction (BS 1377-5:1990, 3.6.3.2 and 3.6.3.3). A lab reports only the result, so P15 is how an engineer sees
  whether the construction found a believable t50 or t90.

**The derivation** (sources under "Evidence"):
- **m_v per increment** = (e1 − e2) / ((1 + e1)(σ′2 − σ′1)), e1 and σ′1 at the increment's start, e2 and σ′2 at its
  end: the void-ratio form of BS 1377-5:1990, 3.6.2.2.4 (decision 1). Unloading and reloading increments use the same
  formula, as hangtu's extension (decision 2).
- **Eoed = 1/m_v** on loading increments; **Eur,oed = 1/m_v** on unloading or reloading increments. 🟡 In the spec
  step: the stress each is reported at (the increment's end, its arithmetic mean or its geometric mean), and whether
  "at σ′v0" is interpolated across increments or taken from the increment spanning it, as sheet 12 says for k.
- **c_v from readings:** log time, c_v = 0.026 H̄²/t50; root time, c_v = 0.111 H̄²/t90; H̄ = (H1 + H2)/2 in mm, t in
  minutes, c_v in m²/year (3.6.3.2.4, 3.6.3.3.3). The constructions are 3.6.3.2.1–3.6.3.2.3 (d0 from two pairs of
  times in the ratio 1:4, d100 from the tangents' intersection) and 3.6.3.3.1–3.6.3.3.2 (the line with abscissae
  1.15 times the early line's). 🟡 In the spec step: what "the early portion" and "the linear portions" are as numbers,
  so the same readings give the same c_v, and what a curve that has no straight line gives.
- **k = c_v·m_v·γw** per increment, γw from `settings.water_unit_weight`. 🟡 In the spec step: whose c_v (the lab's
  or the recomputed one, root or log time) and how the result names it, and a verified source for the relation, or it
  is stated as Terzaghi's definition of c_v with one.
- **E003** as M19 (a) decision 7 designed it, with its acceptance cases (the M19 (a) work file, AC 10).

**Constraints:**
- Recomputed and reported values are both kept and named apart (`reported_` columns), never merged.
- Nothing extrapolates: an increment that can't give a value (Δσ′ of 0, the first increment's unknown start stress,
  a time curve the construction can't fit) gets a reason, not an error.
- The constructions are fixed and stated so the same readings give the same c_v. A smoothing or a choice of range
  that would hide a judgment is either fixed in the spec or made a judgment input (SPEC §4).
- Golden values hand-calculated: m_v, Eoed, Eur,oed and k on the M19 (a) specimen BH1 U3; c_v by both methods on a
  readings set for at least one increment, with its points written out.
- US files: m_v in ft²/kip and c_v in ft²/yr convert through the existing `volume_compressibility` and
  `consolidation_coefficient` kinds; E003 takes its rounding from the file's own unit (TODO #73's build note).
- Published text cites the standard by clause ("BS 1377-5:1990, 3.6.2.2.4") and nothing about the copy read.

**SPEC and docs touched:**
- SPEC §4 (a bullet for the consolidation coefficients, as the oedometer fit has), §10.3 (new registry columns).
- `docs/analysis/compressibility.md` (new sections for m_v, the moduli, c_v and k); `docs/data/qc.md` §4.15 (E003);
  `docs/data/datasets.md` (the `oedometer_readings` template, which M19 (a)'s plan moved here).
- 🟡 A `time` quantity kind for the readings (M19 (a) decision 6 left it to this unit). The project's rule for a new
  kind applies: list the AGS headings in the time dimension and raise `db.SCHEMA_VERSION`.
- `docs/plots/P14-*.md` and `docs/plots/P15-*.md`, promoted from the README's idea rows in the spec step.
- Sheets 11 (§5.3) and 12 (§5.4) and their site pages; sheet 06 (§5.4's strain); the parameter index; `STATUS.md`'s
  M19 row.
- TODO #73 is deleted at close-out once E003 is built; #76 loses its link to #73 (decision 3).

### Evidence (read 2026-11-21)
BS 1377-5:1990 (incorporating Amendment 1), clauses 3.6.1–3.7, printed pp. 6–8:
- **3.6.2.2.4:** m_v (m²/MN) = ((H1 − H2)/H1)(1000/(p2 − p1)) "for each loading increment", H1 the height at the
  start of the increment, H2 at its end, p1 the previous stage's pressure, p2 this stage's (kPa). With 3.6.2.2.3,
  e = (H − Hs)/Hs, so (H1 − H2)/H1 = (e1 − e2)/(1 + e1): e at the increment's start, not e0.
- **3.6.2.1:** compression may be plotted as void ratio, as thickness, "or the strain expressed as a percentage
  reduction in thickness referred to the initial thickness": ε = (H0 − H)/H0 = (e0 − e)/(1 + e0). Report item (g)
  allows "the voids ratio or the vertical compression percentage" against log pressure.
- **3.6.3.2.4 and 3.6.3.3.3:** the c_v equations above. Checked by hand: with double drainage the drainage path is
  H̄/2, so c_v = T (H̄/2)²/t; T50 = 0.197 and T90 = 0.848 give 0.0493 and 0.212 mm²/min per H̄²/t, times 0.526 to
  m²/year (525 960 min/year, 10⁻⁶ m²/mm²): 0.0259 and 0.1115. The coefficients assume the standard's double-drained
  cell.
- **3.6.4:** c_v corrected to 20 °C when the lab's mean temperature is off by more than 2 °C; its note says this is
  for comparing tests, not for correlating with in situ conditions.
- **3.6.5:** C_sec = δH_s/H0 over one log cycle of time.
- **3.7, item (i):** m_v and c_v "to two significant figures, for each load increment", which E003's rounding interval
  assumes.
- **ISO 17892-5 wasn't seen.**

### Decisions (intent review, 2026-11-21)
1. **m_v takes e at the increment's start,** following BS 1377-5:1990, 3.6.2.2.4. This settles TODO #73. E003 and its
   message name the clause; `qc.md` records that ISO 17892-5 wasn't checked. Reason: the one standard at hand is
   explicit, and a lab dividing by 1 + e0 is what E003 should flag. Waiting for ISO would block E003 for a definition
   that is unlikely to differ.
2. **Unloading and reloading m_v use the same formula, as hangtu's extension.** BS defines m_v on loading increments
   only, so Eur,oed's definition is hangtu's, and the docs say so. E003 still skips any Δσ′ of 0 or less, so it never
   judges a lab's unload m_v.
3. **Strain for plots and the work method is ε = (H0 − H)/H0 = (e0 − e)/(1 + e0)** (3.6.2.1). The strain on H1 belongs
   to m_v only. This settles the strain for P13's ε axis (P13 §15) and removes #76's dependence on #73.
4. **(c) splits in two.** (c1), this branch: m_v, Eoed, Eur,oed and k from the increments, E003 and P14, all from
   `p.oedometer()`, with k from the lab's c_v. (c2), its own branch and work file: the `oedometer_readings` template,
   the `time` kind, c_v by both constructions and P15; its intent starts from this one's c_v parts. Reason: (c1)
   needs no new input and closes TODO #73; (c2) carries the graphical constructions and their golden values, and
   both together are more than one review.
5. **No temperature correction; `CONS_TEMP` stays unread.** 3.6.4's note says the correction is for comparing tests,
   not for in situ use, and the lab's c_v is taken as reported.
6. **C_sec (3.6.5, `CONS_INSC`) is left out.** No sheet asks for it; (c2)'s readings would allow it later.

### Out of scope
- Rock swelling (d); K0 from OCR, SHANSEP and the Soft Soil set (M20).
- Casagrande's σ′p and the work method (TODO #76).
- Settlement-against-time readings from AGS (wave 0); CRS and Rowe cell tests (`ESCG`, `ESCT`).
- Stage D for m_v, c_v and k (`representative()`, `select()`), and the field permeability tests (M24).

## Spec
(c1) only (intent decision 4): m_v, Eoed, Eur,oed and k per increment from `p.oedometer()`, with k from the lab's
c_v; QC E003; P14. The rules go to their topic docs at close-out (`compressibility.md` §8, `qc.md` §4.15); the
figure's spec is [`P14-consolidation-coefficients.md`](../plots/P14-consolidation-coefficients.md), promoted in this
commit. Its choices were agreed in review on 2026-11-21.

### Changes
- **`ht.analysis.oedometer_increments()`** (new, decisions 1–8), with its reference entry. Returns a copy of the frame
  with the columns of decision 6 added.
- **`ht.plot.consolidation_coefficients()`** (new, P14), with its spec, reference entry, site page and example.
  `docs/plots/README.md`: P14's row becomes `draft` in this commit. P00's `figure_sizes` gains a `stacked` kind
  (P14 §5).
- **QC E003** (decision 9) in `src/hangtu/qc/_oedometer.py`, on the raw `CONS` rows as E001–E005 are.
- **Registry** (decision 6; each name checked on 2026-11-21 against `columns.yaml`, `src/`, `docs/`, `tests/` and
  `SPEC.md`, outside `docs/work/`: none exists; `consolidation_coefficients` appears only in P14's README row):
  `applied_vertical_stress_at_increment_start`, `coefficient_of_volume_compressibility`, `constrained_modulus`,
  `unload_reload_constrained_modulus`, `hydraulic_conductivity_root_time`, `hydraulic_conductivity_log_time`,
  `spans_effective_vertical_stress`, and the four `…_reason` columns. `used_by: [plot.consolidation_coefficients]`
  on these and on the three `reported_` columns. No new quantity kind, so `db.SCHEMA_VERSION` doesn't change (the
  `time` kind is (c2)'s).
- **SPEC §4** (close-out): an "Oedometer increments" bullet after "Oedometer fit", linking `compressibility.md` §8:
  m_v per increment from the void ratio at its start (BS 1377-5:1990, 3.6.2.2.4), Eoed and Eur,oed as 1/m_v by
  branch, k = c_v·m_v·γw from the lab's c_v; each a value over its increment, never interpolated across increments;
  an increment that can't give a value gets a reason. §10.3 doesn't change: it lists no columns.
- **`docs/analysis/compressibility.md`** (close-out): the title and status widen to the oedometer analyses; new §8
  "Increments: m_v, the moduli and k" with decisions 1–8; the header's Related gains P14.
- **`docs/data/qc.md` §4.15** (close-out): E003's row and bullet replace "built in M19 (c)"; the status line drops
  "E003 isn't built yet".
- **Test files** (decision 10): `_make_files.py` writes `site_us.ags`'s `CONS_INMV` as a US lab would (2SF in
  ft²/kip); `qc_defects.ags` gains the E003 cases; `tests/data/ags/README.md` says both, and drops "but E003".
- **Example file:** none new. `site.ags`'s two oedometer specimens already carry m_v (2SF ft²/kip, written from
  their void ratios) and both c_v; they draw P14 and raise no E003.
- **Sheets** (close-out): 11 §5.3 and 12 §5.4 rewritten to what is built (decisions 4, 5, 7) with the k source
  (Sources); the parameter index: 11's stage B "part built (Eoed, Eur,oed: `oedometer_increments()`, M19 c1)", 12's
  "part built (k from the lab's c_v·m_v, M19 c1)". Their site pages wait for W5 (sheet 11) and W6 (sheet 12),
  when most of each sheet is built: promoting a sheet means verifying every [U] it publishes, nearly all for methods
  this unit doesn't touch. Until then the reference entry and `compressibility.md` carry the rules. The alternative,
  site pages now with only §5.3 and §5.4 and the rest marked later, is a smaller page per sheet.
- **`docs/TODO.md`** (close-out): #73 deleted; #76 loses its line on the strain (settled in the intent).
- **Docs site:** the P14 page and example, `reference/plot.md` and `reference/analysis.md` entries, the E003 line where
  the AGS and QC guide lists rules.

### Decisions
1. **m_v per increment** = (e1 − e2) / ((1 + e1)(σ′2 − σ′1)) (BS 1377-5:1990, 3.6.2.2.4, in void ratios; intent
   decision 1), per `specimen_id` in row order:
   - **σ′2** is the row's `applied_vertical_stress`; **σ′1** is the previous row's, in the same specimen, written to
     `applied_vertical_stress_at_increment_start`. The first increment's σ′1 is the seating load, which neither AGS
     nor the template gives: blank, with the reason.
   - **e1** is the row's `void_ratio_at_increment_start`, else the previous row's `void_ratio_at_increment_end`
     (with a note naming the rows); **e2** is the row's `void_ratio_at_increment_end`. The row's own start comes
     first: it is the lab's statement of this increment, and E001 reports where it differs from the previous end.
   - Computed in 1/kPa, written in the `volume_compressibility` kind (m²/MN; 1/kPa = 1000 m²/MN).
   - A blank σ′1, σ′2, e1 or e2, or σ′2 = σ′1, gives a blank m_v with the reason. **An m_v of 0 or less is kept** as
     computed (the void ratio moved against the stress change, which E002 flags on loading); the moduli of that row
     are blank with the reason. It is data, and dropping it would hide what E002 reports.
2. **Unloading and reloading use the same formula** (intent decision 2): Δe and Δσ′ are both negative on an
   unload, so m_v is positive. The docstring and `compressibility.md` say BS defines m_v on loading increments only,
   and that the unload and reload values are hangtu's extension.
3. **The branch** is read from `load_branch`, else added by `oedometer_load_branch()` with a note, as
   `oedometer_fit()` does.
4. **Eoed and Eur,oed** = 1/m_v, in the `modulus` kind:
   - `constrained_modulus` on `loading` rows only; `unload_reload_constrained_modulus` on `unloading` and
     `reloading` rows only; each is blank on the other's rows, and both on `constant_stress` rows. Two columns, not
     one with the branch beside it: sheet 11 treats them as two parameters, and stage D selects each on its own.
   - Each is the secant over its increment, the value BS 1377-5 gives m_v as. **No stress is chosen to report it
     at:** the row gives σ′1 and σ′2, and P14 draws the segment between them (P14 §7). A representative stress (the
     end, the mean, the geometric mean) would be a choice the value doesn't carry; a user who needs one computes it
     from the two columns.
   - Sheet 11's Cc and Cs forms (ln 10 (1 + e0) σ′v / Cc) aren't built: they are the tangent of a fitted line, a
     different value, and W5's HS reference moduli are where they belong.
5. **At σ′v0** (sheets 11 §5.3, 12 §5.4): **the increment spanning it, never an interpolation.**
   - `spans_effective_vertical_stress` (nullable boolean) is True on the first `loading` row with σ′1 < σ′v0 ≤ σ′2,
     and on the first `unloading` or `reloading` row in row order whose range (min, max] of σ′1 and σ′2 holds σ′v0;
     False on the others; blank on every row of a specimen with no σ′v0.
   - σ′v0 is `effective_vertical_stress`, one value per specimen (more than one is an error naming it), converted to
     the stress unit, as `oedometer_fit()` reads it. Without the column, the flag is blank and one note says to run
     `vertical_stress()`.
   - **No increment spans σ′v0** (below the first increment's end, above the last): all False, and one note per call
     naming the specimens. Nothing is extrapolated.
   - Reason: m_v, and so Eoed and k, are secants over an increment; interpolating between two increments' secants
     gives a value no increment had. Sheet 12 already says "the increment spanning σ′v0"; sheet 11's "interpolate
     between the two increments that bracket σ′v0" gives that same increment's secant when it is read as
     interpolating e, so the two agree. The docstring says that in an overconsolidated specimen the loading increment
     at σ′v0 is on recompression (sheet 11 §7).
6. **Names** (checked as under Changes):

   | Column | Kind | Rows | Label |
   |---|---|---|---|
   | `applied_vertical_stress_at_increment_start` | stress | all but each specimen's first | Applied vertical stress at increment start, σ′1 |
   | `coefficient_of_volume_compressibility` | volume_compressibility | decision 1 | Coefficient of volume compressibility, m_v |
   | `constrained_modulus` | modulus | loading | Constrained modulus on loading, Eoed |
   | `unload_reload_constrained_modulus` | modulus | unloading, reloading | Constrained modulus on unloading or reloading, Eur,oed |
   | `hydraulic_conductivity_root_time`, `hydraulic_conductivity_log_time` | hydraulic_conductivity | decision 7 | Hydraulic conductivity from c_v (root time), k |
   | `spans_effective_vertical_stress` | bool | decision 5 | |
   | `coefficient_of_volume_compressibility_reason`, `constrained_modulus_reason` (for whichever modulus the row's branch takes), `hydraulic_conductivity_root_time_reason`, `hydraulic_conductivity_log_time_reason` | text | blank values | |

   - `coefficient_of_volume_compressibility` is the recomputed value; the lab's stays
     `reported_coefficient_of_volume_compressibility` (M19 (a) decision 4). "Constrained modulus" is the standard
     term for the oedometer's M; the description says "Eoed, 1/m_v".
   - **Two k columns, not `hydraulic_conductivity`:** that name holds the permeameter and field values
     (`PTST_K`, `FGHG_IPRM`), and sheet 12 §7 says not to pool lab and field k. The two are named by the c_v they
     come from, as the `reported_` c_v columns are, so no choice between the methods is made.
7. **k = c_v·m_v·γw** per increment, for each reported c_v:
   - c_v the lab's (`reported_coefficient_of_consolidation_root_time`, `…_log_time`; intent decision 4), m_v the
     recomputed one (decision 1), γw `ht.settings.water_unit_weight` (SPEC §4: a setting, not a judgment), recorded
     in `attrs`. Computed in canonical units through pint: m²/yr × m²/MN × kN/m³ = 10⁻³ m/yr, a year of 365.25 days,
     as the registry's m²/yr and BS 1377-5's 0.026 and 0.111 coefficients use (525 960 min/year).
   - Blank, with the reason, where m_v is blank or 0 or less, or the c_v is blank or 0 or less. On every branch:
     the unload and reload values are hangtu's extension, as m_v's are.
   - The docstring states the relation's validity as the source gives it: one-dimensional, saturated, with the
     pore fluid's compressibility neglected. It says a lab k from an oedometer is a vertical k of a small specimen,
     usually below the field value (BS 1377-5:1990, 3.1.1, note 3, on fabric), and is a check, not a design
     value on its own.
8. **Units** resolve as SPEC §2.6; the stresses are read in `applied_vertical_stress`'s unit, or `display_units=`'s
   after conversion, as `oedometer_fit()`. m_v, the moduli and k are written in the display system's units (or
   canonical without it), with `attrs["units"]` naming each. Errors as `oedometer_fit()`: a missing
   `specimen_id`, `applied_vertical_stress` or `void_ratio_at_increment_end` names the column and the template.
9. **QC E003** (M19 (a) decision 7, as TODO #73's notes complete it):
   - **Rule:** `CONS_INMV` differs from (e1 − e2) / ((1 + e1)(σ′2 − σ′1)) by more than the rounding of the values
     allows. Warning. One finding per increment. The message gives both values in the file's unit, names BS
     1377-5:1990, 3.6.2.2.4, and says a lab dividing by 1 + e0 of the specimen gives values that grow apart at later
     increments.
   - **Skipped:** each specimen's first increment; any Δσ′ of 0 or less (so never an unload: intent decision 2); a
     blank or flagged `CONS_INMV`, stress or void ratio.
   - **e1** is `CONS_IVR`, else the previous `CONS_INCE` (as E002 reads it); **σ′1** the previous `CONS_INCF`.
   - **"Allows"** is interval arithmetic in the file's own units, from the raw text (`p.table("CONS", raw=True)` and
     each heading's unit): each e ± half a unit in its heading's last decimal place, by its `TYPE` (E001's rounding);
     the stresses as written; the reported m_v ± half a unit in the last place of its text, but never narrower than
     half a unit in its second significant figure. A finding means the intervals don't overlap. The recomputed
     interval is converted to `CONS_INMV`'s unit through pint before comparing.
   - **The 2SF floor** follows BS 1377-5:1990, 3.7, item (i) (m_v reported to two significant figures): a value
     written to more figures is usually a conversion, whose precision is its source's. `qc.md` records that a file
     converted from 2SF values in another unit can still be flagged where the two roundings fall apart, and that
     ISO 17892-5 wasn't checked.
10. **The US twin's m_v.** `site_us.ags` writes `CONS_INMV` as the SI value converted, to 10SF. That is the SI lab's
    2SF, not a US lab's, and E003 flags increments 5 and 6 on it (increment 5: the recomputed 0.0078088–0.0080782
    ft²/kip against 0.0081396 ± 0.00005). It becomes what a US lab reports: the recomputed m_v in ft²/kip to 2SF,
    `TYPE` `2SF` (table in AC 1). The twin test leaves `reported_coefficient_of_volume_compressibility` out of its
    1e-9 comparison and compares it to 2SF in ft²/kip instead; the recomputed m_v is compared with the rest. M19 (a)'s
    AC 4 reads `site_si.ags` and doesn't change.
11. **P14** as its spec: the recomputed m_v and the lab's c_v as segments from σ′1 to σ′2 on log axes, the lab's m_v
    as a mark, σ′v0 and the increments spanning it. It calls `oedometer_increments()` and returns `(fig, axs)`.

### Sources
- **BS 1377-5:1990** (incorporating Amendment 1): 3.6.2.2.4 (m_v), 3.7 item (i) (2SF), 3.1.1 note 3 (specimen
  fabric and the rate of settlement in situ). Read 2026-11-21 (the intent's Evidence; note 3 for k's
  caveat).
- **k = c_v·m_v·γw:** Freeze, R.A. & Cherry, J.A. (1979). *Groundwater*. Prentice-Hall. §8.3, Eq. (8.22),
  c_v = K′/(ρgα′), Terzaghi's coefficient of consolidation, α′ the aquitard's vertical compressibility (§2.9: "The
  parameter α is a vertical compressibility", Eq. 2.53 α = −de/(1 + e0)/dσe), with n′β neglected for clays
  ("for clays n′β ≪ α′"); after Terzaghi (1925). Verified 2026-11-21 in the free online edition (The Groundwater
  Project), chapters 2 and 8. α is m_v and ρg is γw; k = c_v·m_v·γw is the equation rearranged. Sheet 12's [6]
  is already this book, so §5.4's [U] becomes [V] via [6].
- **Unit factors:** exact by definition (1 ft = 0.3048 m, 1 lbf = 4.4482216152605 N): 1 m²/MN = 0.0478802590
  ft²/kip; 1 ksf = 47.8802590 kPa; 1 m²/yr = 10.7639104 ft²/yr; a year of 365.25 × 86 400 s.

### Acceptance criteria
Golden values hand-calculated from the M19 (a) specimen BH1-U3 (its table: the M19 (a) Spec's acceptance criteria),
σ in kPa, m_v = 1000 Δe / ((1 + e1) Δσ′) m²/MN, E = (1 + e1) Δσ′ / Δe kPa. Tolerance 1e-9 relative unless stated.

| # | Branch | σ′1 → σ′2 | e1 → e2 | m_v (m²/MN) | Eoed or Eur,oed (kPa) | US m_v, 2SF (ft²/kip) |
|---|---|---|---|---|---|---|
| 1 | loading | (blank) → 25 | 0.800 → 0.795 | blank: "first increment: its start stress isn't given" | blank | |
| 2 | loading | 25 → 50 | 0.795 → 0.788 | 0.007 / (1.795 × 25) = 0.155988858 | Eoed 44.875 / 0.007 = 6410.71429 | 0.0075 |
| 3 | loading | 50 → 100 | 0.788 → 0.776 | 0.012 / 89.4 = 0.134228188 | Eoed 7450 | 0.0064 |
| 4 | loading | 100 → 200 | 0.776 → 0.748 | 0.028 / 177.6 = 0.157657658 | Eoed 6342.85714 | 0.0075 |
| 5 | loading | 200 → 400 | 0.748 → 0.690 | 0.058 / 349.6 = 0.165903890 | Eoed 6027.58621 | 0.0079 |
| 6 | loading | 400 → 800 | 0.690 → 0.612 | 0.078 / 676 = 0.115384615 | Eoed 8666.66667 | 0.0055 |
| 7 | unloading | 800 → 200 | 0.612 → 0.625 | −0.013 / (1.612 × −600) = 0.0134408602 | Eur,oed 74 400 | |
| 8 | unloading | 200 → 50 | 0.625 → 0.638 | 0.013 / 243.75 = 0.0533333333 | Eur,oed 18 750 | |
| 9 | reloading | 50 → 200 | 0.638 → 0.630 | 0.008 / 245.7 = 0.0325600326 | Eur,oed 30 712.5 | |
| 10 | reloading | 200 → 800 | 0.630 → 0.608 | 0.022 / 978 = 0.0224948875 | Eur,oed 44 454.5455 | |
| 11 | loading | 800 → 1600 | 0.608 → 0.520 | 0.088 / 1286.4 = 0.0684079602 | Eoed 14 618.1818 | 0.0033 |
| 12 | unloading | 1600 → 400 | 0.520 → 0.538 | 0.018 / 1824 = 0.00986842105 | Eur,oed 101 333.333 | |

1. **Increments:** `oedometer_increments(p.oedometer())` on `site_si.ags` gives the table's σ′1, m_v and moduli for
   BH1-U3, each modulus only in its branch's column, and the reasons where blank.
2. **k:** increment 4 (c_v 2.1 root time, 1.8 log time; γw 9.81 kN/m³): k = 2.1 × 0.157657658 × 9.81 × 10⁻³ /
   31 557 600 = 1.02919912e-10 m/s (root time) and 8.82170672e-11 m/s (log time). Every other increment: blank,
   "no c_v reported". With `ht.settings.water_unit_weight` set to 10 kN/m³, root time gives 1.04913264e-10 m/s (the
   ratio 10 / 9.81).
3. **US display:** `display_units="US"` gives increment 4's m_v 0.00754868948 ft²/kip, Eoed 132.473326 ksf and
   k 1.02919912e-8 cm/s; σ′1 2088.54342 psf. To 1e-6 relative, the precision of the factors as written here.
4. **σ′v0:** with `effective_vertical_stress` 80 kPa, `spans_effective_vertical_stress` is True on increments 3
   (loading, 50 < 80 ≤ 100) and 8 (the first unload or reload holding 80: 50 < 80 ≤ 200), False elsewhere; with
   150 kPa, on 4 and 8; with 20 kPa, all False and the note naming BH1-U3; without the column, blank and the
   `vertical_stress()` note.
5. **Start void ratio:** a CSV frame with `void_ratio_at_increment_start` blank on increment 4 takes 0.776 from
   increment 3's end, with the note naming the row, and gives the table's m_v.
6. **Blank and odd rows** (hand-built frames, one specimen each): stresses 100, 100 gives the second row
   `constant_stress`, blank m_v, "no stress change"; 100, 200 with e 0.776 → 0.781 gives m_v −0.0281531532
   (−0.005 / 177.6 × 1000), kept, Eoed blank with "m_v is not positive"; a blank stress on increment 2 gives
   increments 2 and 3 a blank m_v with "no stress" and "the previous increment has no stress"; two specimens in one
   frame start each with a blank σ′1.
7. **Errors:** a frame without `void_ratio_at_increment_end` raises naming it and `ht.template("oedometer")`; two
   σ′v0 values in one specimen raise naming it.
8. **E003 cases** (`qc_defects.ags`):
   - increment 2 with `CONS_INMV` 0.32 raises one finding (recomputed 0.134–0.178 m²/MN; reported 0.315–0.325);
   - a specimen whose lab divided by 1 + e0 (e0 0.800) reports increment 6 as 0.11 and 11 as 0.061: only 11 raises
     (6: 0.1139–0.1168 against 0.105–0.115, overlapping; 11: 0.06765–0.06916 against 0.0605–0.0615);
   - an unload with `CONS_INMV` 9.9 raises nothing (skipped, Δσ′ < 0); a first increment with `CONS_INMV` 9.9 raises
     nothing.
   - Each E003 finding's message gives both values, the clause and the 1 + e0 hint.
9. **Good files stay clean:** `site_si.ags`, the rewritten `site_us.ags` (its intervals in ft²/kip, e.g. increment
   5: 0.0078088–0.0080782 against 0.00785–0.00795) and `site_v404.ags` (2DP void ratios: wider intervals) raise no
   E003; nor does the example `site.ags`.
10. **Twins:** `oedometer_increments(p.oedometer())` on `site_si.ags` and `site_us.ags` agree to 1e-9 for each
    `display_units`; `reported_coefficient_of_volume_compressibility` agrees to 2SF in ft²/kip (decision 10).
11. **Registry and reference:** the new columns are in `columns.yaml` with their kinds; `oedometer_increments` and
    `consolidation_coefficients` have reference entries (`tests/docs/test_site.py`); their docstrings give the
    equations, the BS clause, the k source, the validity and each reason's wording, and cite no internal file.
12. **P14:** its acceptance criteria (P14 §12).

## Plan
Draft, 2026-11-21. Seven commits, each green: the tests it touches, then the CI command with `-n 3`. Steps 1–4 on
Opus (a refactor that the calculation then builds on, the calculation, k's citation and validity, E003's interval
arithmetic), 5–6 on Sonnet (the plot and the docs site, with the spec's values and P14 §12 deciding correctness),
7 on Opus (the figure judged against P14, the sheets, close-out): two session boundaries, after 4 and after 6. A
step past about 300 changed lines without test data splits as noted. Reused, not rebuilt:
- **Oedometer:** `oedometer_load_branch()` and the branch constants (`analysis/_oedometer.py`); from
  `analysis/_oedometer_fit.py`, `_branches()`, `_stresses()`, `_one_value()`, `_in_situ()`, `_specimen_label()` and
  `_stress_text()`, which step 1 moves to `_oedometer.py` so both functions read the frame alike.
- **Units:** `resolve_units`, `parse_unit`, `check_dimension`, `convert`, `to_display` (`hangtu.units`), as
  `oedometer_fit()` uses them; `numeric_column`, `rows_text` (`_data`); `ColumnError`, `HangtuError`, `warn`
  (`errors`); `group_keys()` (`stats/_rows.py`).
- **QC:** `_number()`, `_rounding()`, `_specimens()`, `_void_ratio()`, `_at()` (`qc/_oedometer.py`), as E001 and E002
  read the raw `CONS` rows; `Finding`, `rule` (`qc/_registry.py`).
- **Plotting:** `style.context`/`style_axes`, `figure_size`, `axis_label`, `add_legend`, `Notes`, `figure_of`,
  `hint_missing`, `resolve_palette`, `format_number`, `_layers`, as `plot/_consolidation_curve.py` uses them.
- **Data:** `site_si.ags` (BH1-U3) as it is; `site_us.ags` and `qc_defects.ags` changed in step 4 only; the example
  project's `site.ags` as it is (spec, Changes).

Code cites `docs/analysis/compressibility.md` §8, which step 7 writes, as `oedometer_fit()` cites the earlier
sections; the registry's `ags` entries for the new columns say `"derived: docs/analysis/compressibility.md"`.

### 1. `M19: share the oedometer frame readers between the analyses` (Opus)
- Refactor only, no behavior change: `_branches()`, `_stresses()`, `_one_value()`, `_in_situ()`,
  `_specimen_label()` and `_stress_text()` move from `analysis/_oedometer_fit.py` to `analysis/_oedometer.py`
  and lose their leading underscore, since another module now imports them; `_in_situ()`'s docstring loses its
  reference to the fit's decision 11. `_stress_text()`'s lazy import of `format_number` moves with it.
- Tests: `tests/analysis/test_oedometer_fit.py`, `tests/analysis/test_oedometer_load_branch.py`,
  `tests/plot/test_consolidation_curve*.py` unchanged and green.

### 2. `M19: add oedometer_increments() with m_v and the moduli` (Opus)
- `columns.yaml`: all of decision 6's columns now, with their kinds and labels (text and bool columns without a
  label, as the registry allows), the `ags` entry above; no `used_by` yet (step 5 adds it, since
  `tests/test_registry.py` checks each `used_by` is callable; the M19 (b) build's note). The k columns too, so step 3
  adds no registry change. `tests/test_registry.py` stays green.
- `src/hangtu/analysis/_oedometer_increments.py` (new), exported in `analysis/__init__.py`:
  - inputs (decision 8): the required columns, each missing one an error naming it and `ht.template("oedometer")`;
    `load_branch` read or added with the note (decision 3); per `specimen_id` in `group_keys()` order, rows in frame
    order; a copy of the frame returned with the new columns appended, `attrs["units"]` naming each;
  - σ′1 from the previous row of the specimen; e1 from `void_ratio_at_increment_start`, else the previous end, with
    one note naming the rows (`rows_text`); m_v (decision 1) computed in 1/kPa, written in m²/MN or ft²/kip;
  - the reasons, worded as AC 1 and 6 give them: "first increment: its start stress isn't given", "no stress
    change", "no stress", "the previous increment has no stress", "no void ratio …", "m_v is not positive"; an m_v of
    0 or less kept;
  - Eoed and Eur,oed (decision 4) as 1/m_v in the branch's column, blank on the other's rows and on
    `constant_stress`; one `constrained_modulus_reason` for whichever the row takes;
  - `spans_effective_vertical_stress` (decision 5): σ′v0 through `in_situ()`, the first loading row and the first
    unload or reload row holding it, all False with one note naming the specimens when none does, blank with the
    `vertical_stress()` note without the column; two σ′v0 in a specimen an error naming it;
  - units (decision 8): stresses in `applied_vertical_stress`'s unit or `display_units=`'s; m_v and the moduli in
    the display system's units, else canonical;
  - docstring per the sheets' `TEMPLATE.md` checklist: the m_v equation and BS 1377-5:1990, 3.6.2.2.4; the unload
    and reload values as hangtu's extension (decision 2); the moduli as secants with no stress chosen; σ′v0's
    increment and the recompression remark; inputs and outputs with units; each reason's wording; an example on
    `p.oedometer()`. k's parts are left to step 3.
- `docs/site/reference/analysis.md`: `oedometer_increments`.
- Tests: `tests/analysis/test_oedometer_increments.py` (new), `site_si.ags` and `site_us.ags` through
  `Project.from_ags` as `test_oedometer_fit.py` does: AC 1, 3 (m_v, Eoed, σ′1), 4, 5, 6, 7; AC 10 for the columns
  built so far (both twins, each `display_units`, `reported_coefficient_of_volume_compressibility` left out until
  step 4); AC 11's docstring and reference checks (`tests/docs/test_site.py`, `tests/test_errors.py`).
- If past about 300 lines: (2a) inputs, σ′1, e1, m_v and its reasons (AC 1, 5, 6, 7), then (2b) the moduli, σ′v0 and
  units (AC 3, 4).

### 3. `M19: add k from the lab's c_v to oedometer_increments()` (Opus)
- `_oedometer_increments.py`: decision 7: `hydraulic_conductivity_root_time` and `…_log_time` from each reported
  c_v, the recomputed m_v and `ht.settings.water_unit_weight`, through pint in canonical units (m/s), written in
  the display system's unit (cm/s for US, as AC 3); γw recorded in `attrs`; the reasons "no c_v reported", "c_v is
  not positive" and m_v's own reason where m_v is blank or not positive.
- The docstring's k paragraph: the relation as Terzaghi's c_v rearranged, cited to Freeze & Cherry (1979), §8.3,
  Eq. (8.22) (Sources); validity (one-dimensional, saturated, pore fluid compressibility neglected); the vertical
  small-specimen caveat (BS 1377-5:1990, 3.1.1, note 3); the unload and reload values as hangtu's extension.
- Tests, same file: AC 2 (with the setting changed and restored in a fixture), AC 3's k, AC 10 for the k columns.

### 4. `M19: add QC E003, m_v against the lab's void ratios` (Opus)
- `src/hangtu/qc/_oedometer.py`: `@rule("E003")` (decision 9): each specimen's rows from `_specimens()`; e1 as E002
  reads it, σ′1 the previous `CONS_INCF`; the skips; the intervals from the raw text (each e ± half its last place
  by `TYPE`, the stresses as written, the reported m_v ± half its last place but never narrower than half a unit in
  its second significant figure); the recomputed interval converted to `CONS_INMV`'s unit through pint; one
  warning per increment whose intervals don't overlap, the message giving both values in the file's unit, BS
  1377-5:1990, 3.6.2.2.4, and the 1 + e0 hint. Interval ends of a quotient taken from the four corner values, so
  the sign of Δσ′ needn't be special-cased beyond the skip.
- `src/hangtu/qc/rules.yaml`: E003 between E002 and E004, warning, no thresholds (the comment says the bounds are the
  values' rounding).
- `tests/data/ags/_make_files.py`:
  - `site_us.ags`'s `CONS_INMV` (decision 10): the recomputed m_v in ft²/kip to 2SF with `TYPE` `2SF` (the AC
    table's US column), not `to_us()`'s 10SF conversion; the other converted headings unchanged;
  - `qc_defects.ags`: AC 8's cases on a new specimen (or two) appended after the existing `CONS` rows, so the lines
    of E001–E005's cases don't move; the file regenerated with `_make_files.py`, and every other file checked
    unchanged (`git diff --stat tests/data/ags`).
- `tests/data/ags/README.md`: `site_us.ags`'s m_v as a US lab writes it; `qc_defects.ags`'s E003 cases with their
  lines in the case table; "but E003, which isn't built" dropped.
- Tests: `tests/qc/test_oedometer.py`: AC 8 (each case, the interval ends quoted in the spec, the message's parts);
  `tests/qc/test_qc_acceptance.py`: E003's lines in the case list, and AC 9 on `site_si.ags`, `site_us.ags`,
  `site_v404.ags` and the example `site.ags`; `tests/datasets/test_oedometer.py`: the twin test compares
  `reported_coefficient_of_volume_compressibility` to 2SF in ft²/kip (decision 10, AC 10), and its US m_v at line
  128 to the new value; `tests/analysis/test_oedometer_increments.py`: AC 10's reported column.
- `docs/site/guides/ags-and-qc.md`: no per-rule list exists (it says "about 60 rules" and names the groups); the
  count is checked against `rules.yaml` and changed only if it no longer holds.

### 5. `M19: add ht.plot.consolidation_coefficients() (P14)` (Sonnet)
- `src/hangtu/_settings.py`: `figure_sizes` gains `"stacked": (6.5, 6.0)` in the default; `docs/plots/P00-framework.md`
  and `docs/plots/README.md`'s `figure_sizes` lines list it (P14 §5).
- `src/hangtu/plot/_consolidation_coefficients.py` (new), exported in `plot/__init__.py`, as P14 §10: calls
  `oedometer_increments()` with `units=` and `display_units=` and draws its columns, computing nothing of its own:
  two stacked panels sharing a log x; m_v segments from σ′1 to σ′2, loading solid, unload and reload thin dashed
  and lighter (§7); the lab's m_v as × at √(σ′1 σ′2); c_v root time solid and log time dotted, the first increment's
  c_v as × at its end stress; σ′v0's dotted line through both panels and the spanning increments thicker; §6's
  limits; §8's `reported=`, `branches=` and the footnote from the reasons; §11's edge cases; returns `(fig, axs)`.
- `columns.yaml`: `used_by: [plot.consolidation_coefficients]` on decision 6's columns and the three `reported_`
  columns.
- `docs/site/reference/plot.md`: `consolidation_coefficients`.
- Tests: `tests/plot/test_consolidation_coefficients.py` (new), P14 AC 1–4, 6, 8 and 9 read from the drawn artists
  (segment ends and y values, line styles and widths, axis scales and sharing);
  `tests/plot/test_consolidation_coefficients_acceptance.py` (new), AC 5 and 7 on the twin files and the example
  project; `tests/test_settings.py` for the `stacked` default.
- If past about 300 lines: (5a) the panels, segments, marks, limits and returns (AC 1–3, 6, 8), then (5b) σ′v0, the
  footnote, units and the edge cases (AC 4, 5, 7, 9).

### 6. `M19: draw the consolidation coefficients on the docs site` (Sonnet)
- `docs/site/examples/consolidation-coefficients.py` (new): the example project's oedometer specimens with
  `vertical_stress()` where the log allows it (B-5-U2-C1, as P13's page found), US units, and
  `oedometer_increments()`'s columns printed for one specimen. `docs/site/plots/consolidation-coefficients.md`
  (new): what it shows, segments rather than points, the branches, the lab's marks, σ′v0's increments, k as a check
  and not a design value, common options; linked in `zensical.toml`'s `nav` and `docs/site/plots/index.md`.
- `docs/site/guides/datasets.md`: `p.oedometer()`'s row points to P14 and `oedometer_increments()` beside P13.
- Run `docs/prepare_site.py` and `zensical build --clean --strict`.

### 7. `M19: close out (c1)` (Opus)
- **Visual check:** `docs/plots/img/P14-us.png` (the example's specimens, psf) and `P14-si.png` (BH1-U3, kPa, σ′v0
  = 80 kPa), 100 dpi, looked at against P14, committed (P14 AC 10).
- **Close-out:**
  - `docs/analysis/compressibility.md`: title and status widened to the oedometer analyses; §8 "Increments: m_v, the
    moduli and k" with decisions 1–8 and the k source, linking the API reference rather than restating the
    docstring; Related gains P14. `CLAUDE.md`'s `docs/analysis/` list: `compressibility.md` becomes "the oedometer
    fit and increments";
  - `docs/data/qc.md` §4.15: E003's row and bullet (decision 9, the 2SF floor, the converted-file caveat, ISO
    17892-5 not checked); the status line drops "E003 isn't built yet";
  - SPEC §4: the "Oedometer increments" bullet (spec, Changes);
  - `docs/plots/P14-consolidation-coefficients.md` status `built` with its images; `docs/plots/README.md` P14
    `built`;
  - sheets 11 §5.3 and 12 §5.4 (`docs/drafts/parameters/`) rewritten to what is built, 12's k source [V] via [6];
    sheet 06 §5.4's strain (intent decision 3); the parameter index's stage B entries for 11 and 12 (spec,
    Changes); no site pages (they wait for W5 and W6);
  - `docs/TODO.md`: #73 deleted; #76 loses its line on the strain; anything deferred here with its trigger;
  - `STATUS.md`: M19 "(a), (b), (c1) done; (c2) next", the Next line; `CHANGELOG.md` Unreleased:
    `oedometer_increments()`, `consolidation_coefficients()` and QC E003, in the user's words;
  - what a future session would get wrong without being told, written where it will be read.
- **Verification:** every AC of the Spec and of P14 §12 reported as met or not, with its test; the whole suite with
  `-n 3`; ruff; mypy; the lowest-versions run (then `git checkout uv.lock`); the strict docs build.
