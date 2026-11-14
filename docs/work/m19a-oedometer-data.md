# M19 (a): oedometer data

## Intent
M19 is wave 3's first milestone (SPEC §1.3): the oedometer, one engine for sheets 06 (σ′p, Cc, Cs), 11 (Eoed,
Eur,oed), 12 B (k from cv·mv) and 21 (rock swelling), drawn as P13–P15. M19 splits in four, data first
(decision 1). This unit, (a), is stage A for those sheets: the oedometer tests read from the file into a
dataset.

**Goal:** from an AGS file or a CSV, an engineer gets each oedometer specimen's load increments. Each one has the
stress and void ratio at its start and end, and the lab's mv and cv. The specimen's initial state (void ratio,
height, water content, densities, condition) and any swelling values come with them. The values are in registry
columns with units, and loading, unloading and reloading are marked on each increment. They feed P01 and P07 as they
are, are what (b)–(d) derive from, and are checked by QC rules that catch records that can't give a valid result.

**Why:**
- **Nothing reads consolidation tests today.** `preconsolidation_stress` and `overconsolidation_ratio` exist only as
  SPT correlation outputs (M13 b2), so sheet 06 has nothing measured to compare them with on P01. The datasets
  spec puts consolidation out of scope (`docs/data/datasets.md` §1), and `site.ags` has no `CONG` or `CONS`.
- **The values are in standard groups** (checked against python-ags4 1.2.0's 4.2 dictionary, 2026-11-14):
  - `CONG`, one row per specimen: `CONG_TYPE` (a pick list: Oedometer, Hydraulic cell, Settlement on saturation,
    Measurement of swelling, Measurement of swelling pressure, Expandability), `CONG_COND` (Undisturbed,
    Remoulded), `CONG_IVR`, `CONG_HIGT`, `CONG_SDIA`, `CONG_MCI`, `CONG_MCF`, `CONG_BDEN`, `CONG_DDEN`,
    `CONG_PDEN` (# prefix when assumed), `CONG_SATR`, `CONG_SPRS` (swelling pressure, kPa), `CONG_SATH` (height
    change on saturation, %), `CONG_CORR` (corrected for equipment deformation);
  - `CONS`, one row per increment (`CONS_INCN`): `CONS_INCF` (stress at end, kPa), `CONS_IVR` and `CONS_INCE`
    (void ratio at start and end), `CONS_INMV` (the lab's mv, m²/MN), `CONS_CVRT` and `CONS_CVLG` (cv by root time
    and log time, m²/yr), `CONS_INSC` (secondary compression), `CONS_TEMP`.

  No group holds settlement against time, so P15's readings come from a CSV template (decision 3).
- **Sheet 06's and 11's pitfalls that belong to the data:**
  - σ′p and Cc come from the loading branch, Cs and Eur,oed from an unload–reload loop, so each increment says which
    branch it is on;
  - a curve with too few increments past the expected σ′p (maximum stress under 2–3 σ′p) can't give Cc;
  - void ratios that don't chain (one increment's end isn't the next one's start) or that rise under loading;
  - the lab's mv to recompute from the void ratios and compare.

  Each becomes a column, a QC finding, or a blank that is counted, never dropped.

**Scope:** the `CONG` and `CONS` groups (decision 4), joined to their sample like the other datasets (depth,
elevation, geology unit); `p.oedometer()`; an `oedometer` CSV template and an `oedometer_readings` template
(time against settlement per increment, for P15 in (c)); QC rules for the data pitfalls above; oedometer tests
added to `site.ags` through `_make_examples.py`, with the CSVs written from it.

**SPEC and TODO touched:**
- SPEC §8.2 (test depth), §10.2–10.3 (a new dataset and registry columns). The split into units goes in
  `STATUS.md`.
- `docs/data/datasets.md` §1 (consolidation moves in scope) and a new §6 subsection; `docs/data/qc.md` for the new
  rules.
- TODO #59 is left for later (decision 2). TODO #67's physical check (a consolidation stress far above the
  overburden) is the same kind of check as this unit's QC; the spec step decides whether to take it.

### Decisions (intent review, 2026-11-14)
1. **M19 is four units:** (a) oedometer data; (b) compressibility: σ′p (a bilinear fit, with Casagrande, Pacheco
   Silva and the work method as checks), Cc, Cs, OCR, Eoed and Eur,oed, sample quality by Δe/e0, P13; (c) mv, cv,
   k = cv·mv·γw, P14 and P15; (d) rock swelling, Huder–Amberg and Grob, from `CONS` increments and `CONG_SPRS`.
   M20 (K0 from OCR, SHANSEP, the Soft Soil set) follows. Reason: data first, and each fits one review.
2. **TODO #59 (shared result code in `ht.stats`, module size) waits** until the unit that puts σ′p and Cc into
   `representative()` and `select()`. Reason: M19 (a)–(d) add a dataset and analyses, not `ht.stats` results.
3. **P15's time–settlement readings come from a CSV template now,** as wave 2 did for triaxial readings; wave 0
   adds the AGS route. Reason: AGS 4.2 has no group for them, and cv fitting is P15's whole purpose.
4. **`CONG` and `CONS` only.** The CRS and Rowe cell groups (`ESCG`, `ESCT`, which carry the lab's σ′p, Cc and Cs)
   come later, marked as rate-dependent so they aren't mixed with incremental tests. Reason: incremental-load tests
   are the common case, and CRS σ′p differs from them by method.
5. **One row per increment,** with the specimen's values repeated. Reason: it matches `p.triaxial()`'s one row per
   stage, and it is what P13 and the fits read.
6. **The branch is marked from the stress sequence:** a stress below the previous one is unloading, and a stress
   rising again before it passes the previous maximum is reloading. The column is `load_branch`, checked against
   the registry in the spec step.

### Open (for the spec step)
- **Names** for the new columns (stress and void ratio at an increment's end, mv, cv by two methods, swelling
  pressure, height change on saturation), checked against the whole registry. Existing ones are reused:
  `void_ratio`, `water_content`, `bulk_unit_weight`, `dry_unit_weight`, `sample_condition`, `test_type`.
- **The swelling `CONG_TYPE`s** (Measurement of swelling, swelling pressure, Expandability): read here and left for
  (d), or read in (d).
- **Assumed particle density** (`CONG_PDEN` with #): kept as a flag, as `p.particle_density()` does.
- **Which QC rules,** and whether TODO #67's physical check is one of them.

### Out of scope
- Every derivation: σ′p, Cc, Cs, Eoed, k and swelling (M19 b–d).
- `ESCG` and `ESCT` (decision 4); settlement-against-time readings from AGS (wave 0).
- Stage D for sheet 06 (`representative()`, `select()`) and TODO #59.
