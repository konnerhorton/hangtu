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
