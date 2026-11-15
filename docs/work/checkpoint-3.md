# Checkpoint 3: living specs hold rules, not the history of the units that built them

## Intent

### Goal
The third checkpoint, after M19 (a). It covers 11 merges since checkpoint 2 (`1e39bac..4f03bfd`). It grew into a
unit because the data specs need restructuring, which takes decisions. Two parts on one branch:
- **Checkpoint fixes:** drift found by the checkpoint checks (pointers into history, status outside `STATUS.md`, a
  shipped 🟡, a stale TODO trigger, the README roadmap, SPEC §10.2's dataset list).
- **Data specs:** `docs/data/datasets.md`, `qc.md` and `ingest.md` hold rules, with each fact in one place.

### Why
- **Each data unit adds to the data specs and never takes anything away.** `datasets.md` (630 lines) has:
  - a Status row listing each milestone;
  - "(Mxx)" heading tags;
  - §10, "Ingest change (TODO #17)";
  - §11, a registry change log by milestone that repeats `columns.yaml`;
  - §12, test files by milestone, which repeats `tests/data/ags/README.md`;
  - §14, "Decisions in review".

  `qc.md` (§4.11–4.15 tags, §8 test files) and `ingest.md` (§11 test files) follow the same pattern. M19 (a)
  added to all of them again.
- **Living specs cite work files as the basis of their rules** in 19 places, although the rule is stated inline.
- **Status lives outside `STATUS.md`:** the Status rows of all eight living specs in `docs/data/` and
  `docs/analysis/` list milestones.
- **SPEC §10.2's dataset list** (`SPEC.md:310`, 790 characters) repeats `datasets.md` §6 and grows with every
  data unit.

### Constraints
- Docs only, plus one code comment (`columns.yaml:634`). No behavior changes.
- Nothing is lost. Each fact taken out is already in a living doc (named in the commit body) or moves to one in
  the same commit.
- Section numbers stay the same in SPEC and in the data specs, because other docs and tests cite them by number.
  §14 of `datasets.md` is the last section, so deleting it renumbers nothing.
- **Acceptance criteria stay as they are** (`datasets.md` §13, `qc.md` §9, `ingest.md` §12): about 20 test files
  cite them by number. Only milestone wording comes out of their text.

### Out of scope
- TODO #59 (shared result code in `ht.stats`, module size): only its trigger changes.
- Work files of merged units: they are history and stay as they are.
- `docs/plots/` specs' own Status rows, which the checkpoint checks didn't flag.
- For M19 (b)'s intent, not this unit:
  - The measured σ′p reuses `preconsolidation_stress` and `overconsolidation_ratio` (`columns.yaml:635–650`),
    with `correlation_name` telling estimates apart; their `ags:` sources gain the oedometer route.
  - The σ′p fit would be the fourth module that imports 6–7 private names from `analysis/_fit_groups`; the plan
    either gives it a small in-package interface or accepts the pattern.

### Decisions (review, 2026-11-15)
1. **`qc.md` §8's rule-to-case table moves to `tests/data/ags/README.md`** as the `qc_defects.ags` entry. It
   replaces the run-on cell of cases by line, keeping each line number. Reason: one home for what a test file
   holds, next to the script that writes it.
2. **Acceptance criteria stay in the specs, unchanged in number.** Reason: tests cite them; moving them changes
   every one of those tests for no reader's gain.
3. **SPEC §10.2 points to `datasets.md` §6** instead of listing each dataset.
4. **From now on, a unit changes a living spec's rules in place.** Its acceptance criteria, decisions in review
   and notes on test files stay in its work file, and test files are described in `tests/data/ags/README.md`.
   This goes in `docs/reference/process.md`.

### SPEC sections touched
§10.2 (the dataset list becomes a pointer). No decision changes.

## Plan

Each step is one commit, scope `checkpoint-3`. Every step is docs-only apart from the comment in step 1, so
each commit runs `uv run pytest tests/docs/test_site.py tests/test_errors.py` and `uv run ruff check .`. Step 1
and the last step also run the whole suite (`uv run pytest -n 2 --dist loadfile`). Steps 1–8 are mechanical
edits to decided homes (Sonnet). Step 9 is the close-out (Opus). Show each message before committing (CLAUDE.md).

### Step 1: `checkpoint-3: drop work-file pointers from living-spec rules` (Sonnet)
Remove the `docs/work/…` citation (and the parentheses or clause it sits in), keeping the rule's text whole, at:
- `docs/data/datasets.md`: lines 274, 293, 315, 343, 385, 434, 469, 506. At 315 keep "a heading map is TODO
  #72".
- `docs/data/qc.md`: lines 259, 274, 293, 306, 319. Each "From `docs/work/…`." opening sentence goes.
- `docs/data/ingest.md:130`.
- `docs/plots/P00-framework.md:118` and `:174`, `P01-property-profile.md:144` and
  `P07-geology-unit-comparison.md:72`. In each, "(M15 (a), `docs/work/m15a-describe.md`…)" goes too. In P07 also
  "(changed in M15 (a) from `(10, 50, 90)`: …)". Keep that clause's reason: "a p10–p90 bar on fewer than 10
  values only interpolates between the extremes".
- Keep `P17-clogging-diagram.md:181` and `datasets.md:599`, whose golden values live in the work files they
  cite.
- `src/hangtu/columns.yaml:634`: the comment becomes `# --- Stress history (correlations from M13; oedometer
  values from M19) ---`, padded to the same width.

Find them again with `git grep -n 'docs/work/' -- docs/data docs/plots docs/analysis`. Line numbers move as
earlier lines change, so work from the bottom of each file up.

### Step 2: `checkpoint-3: keep milestone status out of living specs` (Sonnet)
- **Status rows** (line 5) of `docs/data/{datasets,qc,ingest}.md` and
  `docs/analysis/{correlations,index-and-spt,judgments,statistics,strength}.md`: "Living spec." plus what it
  covers, with no milestone. For `qc.md`, keep that E003 is not built yet, citing TODO #73.
  `index-and-spt.md` keeps its 🔬 / TODO #5 sentence.
- **Intent rows** of the three data specs become **Related** rows, with the work files linked as history, as
  the analysis specs do. Merge each into the existing Related row.
- **Heading tags:** remove "(M8)", "(M13)", "(M14)", "(M11 a)", "(M17 a)", "(M19 a)" from `datasets.md`
  §6.5–6.14 and `qc.md` §4.11–4.15. Section numbers don't change.
- Check: `grep -nE '^#.*\(M[0-9]+' docs/data docs/analysis -r` is empty.

### Step 3: `checkpoint-3: promote shipped hints; point SPEC §10.2 to datasets.md` (Sonnet)
- `docs/plots/README.md:28`: remove "🟡 ". `ht.HangtuHint` and `settings.hints` have shipped
  (`tests/test_errors.py:17`).
- `SPEC.md:310`: first check that every fact on the line is in `datasets.md` §2 or §6, and move anything missing
  there. Then replace the line with a one-line rule and a pointer: each dataset is one test's rows as one frame,
  with the registry's columns, and what each holds is in [`docs/data/datasets.md`](docs/data/datasets.md) §6.
  Keep the section's other lines.

### Step 4: `checkpoint-3: move TODO #59's trigger to the stage-D unit` (Sonnet)
`docs/TODO.md:268`: the trigger "for M19's intent" becomes "for the unit that puts σ′p and Cc into
`representative()` and `select()`". The Open line's "before M19 adds the oedometer results" becomes "before that
unit". Source: `docs/work/m19a-oedometer-data.md`, decision 2.

### Step 5: `checkpoint-3: add the oedometer data to the README roadmap` (Sonnet)
`README.md:87`: the Built row adds "oedometer data" after the shear box data. `:88`'s Planned row keeps "oedometer
and swelling" analyses, worded as the analyses ("compressibility and consolidation from the oedometer, rock
swelling, with the Soft Soil set"). Published text: no milestones.

### Step 6: `checkpoint-3: fold datasets.md §10, §11 and §14 into their homes` (Sonnet)
- **§10:** the body becomes one line saying the `particle_size` kind and the schema version are in `ingest.md`
  §7 and §2 (`ingest.md:107` and `:35` already hold them). Repoint `ingest.md:107`'s "`datasets.md` §10" to
  nothing, since it states the rule itself.
- **§11:** delete the M7 new-column list and the six per-milestone bullets (M13, M14, M11 a, M17 a, M19 a,
  M17 c); `columns.yaml` holds every column and source. Keep two rules: new names are checked against the whole
  registry, and a template is a subset of its dataset. Keep §11.1, removing its milestone and work-file
  references (`:579–582`).
- **§14:** move its one decision (`SPEC_REF`/`SPEC_DPTH` are `recommended`, and why: required, they left out every
  lab result without a specimen depth, so the lab depth fallback never ran) into §7's first bullet, in place of
  "(… recommended, §14)". Delete §14. Repoint `qc.md:220`'s "`datasets.md` §14" to §7, and drop its "(M7, …)".
- **§13's text:** milestone wording only, for example #14 "M8 datasets feed the plots" becomes "Classification
  datasets feed the plots". Numbers unchanged.

### Step 7: `checkpoint-3: describe test files in one place` (Sonnet)
- **`tests/data/ags/README.md`:**
  - `qc_defects.ags` entry: replace the run-on cell with `qc.md` §8's rule-to-case table, a column of each case's
    line(s) taken from the current cell. Keep the cell's opening facts (five holes on a 50 m grid, BH5 without
    coordinates, cascades in `tests/qc/test_qc_acceptance.py`). The table may sit below the file table, under a
    `## qc_defects.ags` heading, with the cell pointing to it.
  - Move in anything else from `datasets.md` §12, `qc.md` §8 and `ingest.md` §11 that the README lacks: check
    each sentence. Known: "all but `defects.ags` pass python-ags4"; the good files stay QC-clean.
  - Line 3's pointers to the spec sections stay. Line 23's "`datasets.md` §13 #16" stays.
- **`datasets.md` §12, `qc.md` §8, `ingest.md` §11:** keep the heading. The body is one or two lines of principle
  plus a pointer to `tests/data/ags/README.md`: synthetic, written by `_make_files.py`; one case per rule in
  `qc_defects.ags`; the good files are QC-clean (§9 #2). Keep `datasets.md:599`'s golden-value pointer to
  `docs/work/grag-fractions.md` in the README's `grag.ags` row, which already has it.
- Check: `uv run pytest tests/ags/test_files.py tests/qc/test_qc_acceptance.py`, which read the files, not the
  README. The README has no test.

### Step 8: `checkpoint-3: living specs change in place` (Sonnet)
`docs/reference/process.md`, loop step 2 (Spec): add decision 4 in one or two sentences. Check `CLAUDE.md`'s
`docs/data/` line ("data-layer specs that outlive a unit of work") still reads right, and leave it unless it
doesn't.

### Step 9: `checkpoint-3: close out` (Opus)
- `STATUS.md`: `Last checkpoint: 3, after M19 (a), 2026-11-15, 4f03bfd.` Next is unchanged.
- No CHANGELOG entry (nothing user-visible).
- Rerun the checkpoint checks for decision states, pointers into history and status outside `STATUS.md`, and
  confirm that only the kept hits remain.
- Whole suite, ruff, mypy, `docs/prepare_site.py` and `zensical build --clean --strict`.
- Merge to `main` with `--no-ff` after approval. The message is one line: checkpoint 3 after M19 (a), with the
  kinds of change made.

### Notes from the build
- Step 2 also took milestone tags off `qc.md` §4.10's field-list comments and `datasets.md` §2's API comments, and
  folded `datasets.md` §1's "Added in M8 / M19 (a)" notes into §1's list, which had named only four datasets.
- Step 6 also repointed the code and test comments that cited `datasets.md` §10 (to `ingest.md` §7) and §14 (to
  `datasets.md` §7), and dropped the references to TODO #17, which no longer exists.
- Step 7's `qc_defects.ags` table was checked against the file's lines and gained BH4-U1's clean `LDEN` row (131)
  and the L006/L007 lines (17–20). The README also gained M19 (a)'s oedometer cases, which only `datasets.md` §12 had.
- The close-out's checks found about 30 more milestone references in the specs' prose, which steps 1–2 hadn't
  listed. They went in an extra commit before the close-out (`checkpoint-3: drop the remaining milestone references
  from living specs`), with the user's approval.
