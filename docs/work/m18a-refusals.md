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
