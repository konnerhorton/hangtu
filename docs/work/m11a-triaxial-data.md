# M11 (a): triaxial data

## Intent
M11 is wave 2's first milestone (SPEC §1.3, §12.4). Wave 2 is "one fitting core" for soil strength (sheets 04 and
05), joint strength (22) and the intact Hoek–Brown fit (15). M11 builds that core and its first use, c′ and φ′
from triaxial tests, drawn as P11 (failure envelope) and P12 (shearing curves and stress paths). M17 then reuses
the core for undrained strength, the shear box and the Hoek–Brown fit.

M11 splits in two, data first (decision 2): this unit, (a), is stage A of sheet 04 for triaxial tests, the
stresses at failure read from the file into a dataset. (b) is stage B: the fitting core, `mohr_coulomb_fit()`,
P11 and P12.

**Goal:** from an AGS file or a CSV, an engineer gets each triaxial specimen's or stage's state at failure: the
test type, cell pressure, deviator stress and pore pressure, and from them σ′3 and σ′1 (σ3 and σ1 for total-stress
tests). The values are in registry columns with units, multistage stages and the lab's failure criterion are marked
on each row, and the lab's own c′ and φ′ come with them. They feed P01 and P07 as they are, are what (b) fits, and
are checked by QC rules that catch records that can't give a valid result.

**Why:**
- **Nothing reads strength tests today.** `effective_friction_angle` exists only as an SPT correlation output
  (M13 b1). Sheet 04 is part built at stage C, but stages A and B are empty. So the correlations have nothing
  measured to be compared with on P01 or P07, and selection (M18, starting with the Mohr–Coulomb set) has no
  measured c′ and φ′ to work from. None of the test files or the example file has a triaxial group.
- **The values at failure are in standard groups** (checked against python-ags4 1.2.0's 4.2 dictionary,
  2026-10-31):
  - `TREG`: `TREG_TYPE` (a pick list, CD to CAUE, with multistage CDM and CUM), `TREG_FCR` (the failure
    criterion, free text, example "Maximum deviator stress"), and `TREG_PHI` and `TREG_COH` (the lab's fit);
  - `TRET`, one row per test or stage (`TRET_TESN`): `TRET_CELL`, `TRET_DEVF`, `TRET_PWPF`, `TRET_CONP`,
    `TRET_BACK`, `TRET_BVAL`, `TRET_STV`, `TRET_DRN`;
  - `TRIG` and `TRIT` for total stress (UU: `TRIT_CELL`, `TRIT_DEVF`).

  None of them has readings during shearing. P12's come from a CSV the user shapes (TODO #19), in (b).
- **Sheet 04's pitfalls that belong to the data:**
  - failure criteria and multistage stages mixed in one fit, so each row says which it is;
  - CU without pore pressure can't give φ′;
  - saturation (`TRET_BVAL`) below what the test standard requires;
  - the lab's `TREG_PHI`/`TREG_COH` to recompute and compare.

  Each becomes a column, a QC finding, or a blank that is counted, never dropped.

**Scope:**
- **One dataset** (SPEC §10.2), `p.triaxial()`, from `TREG`/`TRET` and `TRIG`/`TRIT`. It has one row per stage at
  failure, effective-stress and total-stress rows together, told apart by `test_type` (decision 3), and the common
  filters. σ′3 = σ3 − u_f and σ′1 = σ′3 + q_f are computed by the dataset and never stored (SPEC §7), as N60 is.
- **A CSV template** in the dataset's shape (SPEC §2.6), so CSV and AGS data reach (b) in the same shape.
- **Registry names** for the new columns, checked against the whole registry.
- **The groups in the SI/US twin test files**, and a defects case for each new QC rule.
- **Level 1 QC rules** from the pitfalls, among them saturation against the test standard (decision 7).

**SPEC and TODO touched:**
- SPEC:
  - §1.3 and §12.4, the order of work (committed in `eeba488`);
  - §12.4, M11 in two units and the shear box in M17 (decisions 2 and 6, in this commit);
  - §10.2, §10.3 and §2.6 (the dataset, registry names, template);
  - §9 via `docs/data/qc.md` (new rules).
- Other docs: `docs/data/datasets.md`, `docs/data/qc.md`, and the parameter index (04 A).
- TODO: #31 (wave 0's sample dataset, unchanged but now later); #19 (decided, stays).

### Decisions (intent review, 2026-10-31)
1. **Wave 2 comes before wave 0, and M16 moves after M17** (SPEC §1.3, §12.4, `README.md`, `CLAUDE.md`, the
   parameter index; committed separately). Wave 0 is built against a sample dataset of real files (TODO #31) that
   isn't ready. Wave 2 doesn't need it: its values at failure are standard groups, and its readings come from a
   CSV (TODO #19). Once M16 lands, the readings and rock triaxial results can also come from the AGS file.
2. **M11 splits into data (a) and analysis (b)**, following `docs/reference/process.md` ("Stages and waves").
   Splitting off P12 alone was rejected: its input is a CSV, so it doesn't wait on M16, and it shares the fit with
   P11.
3. **One dataset**, with effective-stress and total-stress rows together, told apart by `test_type`.
4. **`TREG_FCR` is read as written and compared exactly** (SPEC §8.3). No mapping to a short list for now; that
   may change once it has been used on real files.
5. **The lab's `TREG_PHI` and `TREG_COH` come back in the dataset**, so (b) can compare them with hangtu's fit.
6. **The shear box (`SHBG`/`SHBT`) goes to M17**, soil and rock joints together, since both are in one group.
7. **Saturation is a QC rule, not a filter or a judgment.** It checks a record against its test standard, not a
   plausible range, so it is level 1. The threshold comes from the standard, verified in the spec step (D4767 is
   thought to require B ≥ 0.95; unverified). The dataset carries the B-value and leaves the choice of specimens
   to (b).
8. **Multistage stages are marked on each row**, from `TREG_TYPE` (CDM, CUM) and `TRET_TESN`. The dataset keeps
   every stage, and (b) decides whether a fit leaves them out.

### Open (for the spec step)
- **Columns:** which `TREG`/`TRET`/`TRIG`/`TRIT` headings come back (initial state such as `TRET_BDEN` and
  `TRET_IVR`, strain at failure, `TRET_CU`, `TRET_E50`), and the names, checked against the whole registry. P11
  and P12 propose `effective_minor_principal_stress`, `deviator_stress` and others.
- **Pore pressure:** σ′3 at failure from `TRET_CELL` − `TRET_PWPF`, or from `TRET_CONP` and the excess pore
  pressure, and what happens when they disagree or one is blank. For CD tests, whether a blank `TRET_PWPF` means
  the back pressure (sheet 04 §5.1) or stays blank. Never guessed: a blank that can't be derived stays blank,
  and is counted.
- **The multistage marker:** a flag, a stage number, or both; how `TRET_TESN` is read when `TREG_TYPE` is blank.
- **The QC rules:** which of the pitfalls are level 1, and their thresholds as quantity strings. Candidates:
  saturation below the standard's B-value; a CU stage without `TRET_PWPF`; σ′3 ≤ 0 at failure; a `TREG` with no
  `TRET` rows, or the reverse.
- **The example file:** whether `ht.examples`' `site.ags` gains triaxial groups here or in (b), with the plot
  pages.
- **Sources:** the B-value threshold and the failure-criterion definitions in ASTM D4767, D7181 and D2850 (and the
  ISO 17892-8/-9 counterparts), checked against the standards.

### Outline of (b), for context
The fitting core (input rules for failure points, a fit result object, grouping, points left out and counted),
`mohr_coulomb_fit()`, P11 `failure_envelope()` and P12 `triaxial_shearing()` with its readings template, the plot
specs promoted from `docs/plots/drafts/`, and sheet 04's site page. Settled for (b) in this review:
- **The fit result is its own object**, not on the statistics base (`_Result`, SPEC §5). Results of derivations
  may need a family of their own, apart from statistics results.
- **A fitted c′ and φ′ is a derived value** (Eurocode 7's measured → derived → representative → design), as an SPT
  correlation estimate is. The result records that, with its method and points. SPEC §5's *property* and
  *parameter* keep their meanings: *parameter* stays for values selected in M18.
- **P12 puts pore pressure (or volumetric strain) on a second y axis, off by default.**

Left for (b)'s intent: what a fit refuses to pool unawares, what M17's fits need from the core, what P11 returns
with several groups, P11's default `space=`, how P12 picks the failure reading, and the sources for the s′–t and
p′–q constructions.

### Out of scope
- Everything in (b) (above).
- **M17:** undrained strength as a parameter (s_u from UU, UCS, vane, pocket penetrometer; `TRET_CU` and
  `TRIT_CU` as s_u), the shear box (decision 6), the intact Hoek–Brown fit.
- **M16:** readings and rock triaxial results from user-defined AGS groups.
- **Later:** anisotropic consolidation and extension tests (`TRET_CVP`, `TRET_CRP`, carried if the spec keeps
  them, but not interpreted); E50 from the curves (wave 5); a reader for lab software exports (TODO #19: none).
