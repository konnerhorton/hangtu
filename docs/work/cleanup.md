# Cleanup: published text, living specs, a shorter SPEC and one home for status

## Intent

### Goal
Pause between waves and tidy what has built up over M0–M18. This covers four things:
- what users read (docstrings and messages) shouldn't point to files they can't see;
- decisions should live in living specs, not in finished units' work files;
- SPEC.md should hold current decisions only;
- status should have one home.

### Why
- **Published text points at internal files.** The API reference is built from docstrings, and about 55
  lines in public docstrings cite `SPEC §…`, `docs/…`, `TODO #…` or a milestone. 24 error, warning and
  result messages do the same ("a judgment with no default (SPEC §4)", "See docs/data/qc.md §3.4",
  "derived values come with wave 5 (M23)"). None of those files is published or shipped in the wheel.
- **Decisions live in history.** `CLAUDE.md` calls `docs/work/` history, yet SPEC cites work files 38 times
  as the place a decision is recorded. The code does too: `_judgments.py` says its spec is "m13a, Spec
  Decision 1". A session that follows those pointers reads work files of 400–600 lines.
- **Drafts that aren't drafts.** `docs/drafts/analysis.md` is a built, decided feature spec.
  `docs/drafts/phase2-data.md` and `phase3-stats.md` are mostly "moved to" pointers.
- **SPEC.md is at the top of its healthy size (451 lines),** and is growing in §4 and §5, where one-feature
  detail repeats `docs/analysis/statistics.md`. It carries 46 "decided …" stamps, which are history that git
  already holds.
- **Status is in five places:** SPEC §12.4 (milestones), SPEC §12.1 (releases), the first paragraph of
  `CLAUDE.md`, the plot list and the parameter index. Every close-out edits SPEC even when no decision
  changed.

### Constraints
- Behavior doesn't change. Step 1 changes message text and docstrings only; steps 2–4 are docs.
- Nothing is lost. A fact taken out of SPEC, a draft or a TODO item is already in a living doc (named in the
  commit) or moves to one in the same commit.
- SPEC sections keep their numbers (`CLAUDE.md`, Workflow rules).
- The repo is public: no private sources named.

### Out of scope
- Splitting large modules, or sharing the stats modules' notes and count code. Revisit before M19.
- Private module docstrings and code comments, which are for developers. Step 2 repoints only those that cite
  a work file as the spec of a decision.
- The spec-driven-development skill (in `~/.claude/skills/`, not versioned).
- `docs/work/` files themselves: they stay as history, unedited.

### Decisions (review, 2026-11-08)
1. **The "decided" stamps go entirely:** "(decided)", "(decided 2026-…, `docs/work/…`)" and the same
   provenance in parentheses. SPEC states the current decision; git and the work files hold when and why.
   The Conventions block (Decided / Proposed / Open / Research) goes too: nothing in SPEC is proposed or
   open any more.
2. **`STATUS.md` at the root holds status:** what's next, the milestone tables and the releases, with links to
   the plot list and the parameter index (which stay where they are). This reverses `context-trim`'s
   Decision 1, which put unit status in SPEC §12.4. The reason: SPEC should change only when a decision
   does.
3. **The local test command is `uv run pytest -n 3 --dist loadfile`.** `CLAUDE.md` says to use it, with no
   reason given. The command labeled "what CI runs" keeps `-n auto`, as `ci.yml` does.
4. **Commands stay `uv run`**: it syncs `.venv` to `uv.lock` before each run, so an environment can't go
   stale after a branch switch.

### SPEC sections touched
§1.2 (table fix), §1.3, §3, §4, §5, §8.3, §12.1, §12.4 and §13 (step 3). Everything else only loses stamps.

## Spec

The unit is done in steps 1, 1b, 2, 3 and 4, in that order. Each step's plan is written after the step before it is merged
into this branch.

### Step 1: published text cites no internal file
**What counts as published:**
- the docstrings of everything in the API reference (every `::: name` in `docs/site/reference/*.md`), and
  of its public members (methods and properties of a documented class, members of a documented module);
- every string literal in `src/hangtu` that isn't a docstring: error, warning and note text, and result
  reasons.

**What counts as an internal reference:** `SPEC §`, `docs/`, `TODO #`, a milestone (`M` and a number) or a
wave (`wave` and a number).

**How each kind is rewritten:**
| Reference | Rewrite |
|---|---|
| A rule's source, `(SPEC §4)` and the like | Drop the parenthesis. The sentence already states the rule ("a judgment with no default") |
| A data-layer spec (`docs/data/datasets.md §6.x`, `qc.md §3.x`) | Say what the user needs in the docstring or message. Where a docs-site page covers it, name the page by its title ("the AGS and QC guide") |
| A derivation in a work file (`mohr_coulomb_fit`, `shear_box_fit`, `hoek_brown_fit`) | State the derivation in a few lines in the docstring's Notes, taken from the work file's "Derivation(s)" section |
| Sources in a work file (`undrained_shear_strength_from_tests`) | Name the sources |
| `TODO #48`, `TODO #53` | Keep the fact ("not yet checked against the original papers"), drop the number |
| A milestone or wave | Plain words: "planned, not built yet"; name the function where one exists (`friction_angle_from_shear_box()`) |

**Tests:** two tests fail on any internal reference. One walks the documented objects; the other scans
string literals with `ast` and leaves docstrings out. The two `pytest.raises` matches that expect `SPEC §4`
(`test_shear_box_conversion.py:438`, `test_add_judgment.py:105`) match the rest of the message instead.

### Step 1b: site pages and column descriptions cite no internal file
Step 1 covered docstrings and messages. Two more kinds of text are published, with the same definition of an
internal reference:
- the hand-written pages under `docs/site/` (15 lines on 8 pages). One is wrong, not just internal:
  `guides/selection.md:134` quotes the `NO_STIFFNESS` message as it was before step 1;
- the registry's column `description`s, which `ht.columns()` prints and `docs/prepare_site.py` writes to
  `reference/columns.md` (4 entries).

The README links to SPEC and `docs/plots` on GitHub on purpose, and stays as it is.

**Rewrites**, using the step 1 table plus these:
| Reference | Rewrite |
|---|---|
| "Choosing a design value is stage D (M18)" | Name the function and the guide: "…is selection: `ht.stats.select()` (the selection guide)" |
| A wave in a "when" column or sentence (page 15, page 22) | "planned" |
| `docs/data/datasets.md` §6.11/§6.12 (pages 05, 22) | Say the rule in the sentence, or name the datasets guide where it covers it |
| A milestone in a column description ("M14 b", "in M13", "until wave 5", "TODO #3") | Drop it, keeping the fact ("selected; derived values aren't built yet") |

**Tests:** `test_site_pages_cite_no_internal_files` scans `docs/site/**/*.md`, leaving out generated files.
`test_column_descriptions_cite_no_internal_files` scans the loaded registry's descriptions.

### Step 2: decisions in living specs
- **`docs/analysis/judgments.md`** (new, living): the file format, how a value resolves, keys and the
  project-wide value with its `reason`, what a result records, and one entry per judgment (keys, whether a
  project-wide value is allowed, its checks, and what absence does). Taken from the Spec of
  `m13a-judgments.md` and the later decisions in `m13b2`, `m14b`, `m15d`, `m17c`, `m18a`, `m18d` and `m18e`,
  checked against `src/hangtu/_judgments.py`. The public guide `docs/site/guides/judgments.md` is unchanged.
- **`docs/analysis/strength.md`** (new, living): triaxial stresses at failure, failure from readings, the
  line-fit core and the three envelope fits with their derivations, undrained strength from tests, and the
  shear box φ′ conversion. Taken from `m11a`–`m11c`, `m17a`–`m17c` and `m18d`. Step 1 has already put each
  derivation in its docstring; this doc keeps the reasons and the rules that span the fits.
- **`docs/drafts/analysis.md` → `docs/analysis/index-and-spt.md`**, with its status set to living spec. Its §4
  (SPT correlation candidates, settled in M13) is dropped: the built set is `config/correlations.yaml`, and
  the contract is `correlations.md`.
- **`docs/drafts/phase2-data.md` and `phase3-stats.md` are deleted.** Their two open research items (pcf in
  AGS density headings; how US files fill `ISPT_PEN*`) become TODO items.
- **Pointers are repointed** to the living docs: SPEC, `CLAUDE.md` ("Where things are"), `process.md` (the
  documents table), module docstrings and comments that cite a work file as a decision's spec, and the 42
  `derived: docs/work/…` entries in `columns.yaml`, which become the living doc or a short formula.

### Step 3: SPEC, STATUS.md, CLAUDE.md, process.md
- **`STATUS.md`** (new, root):
  - Next: one to three lines, as `CLAUDE.md` gives it now;
  - Open milestones, with Done when and Status;
  - Done milestones, one line each;
  - Releases: 0.0.1 and 0.1.0 with what each holds, moved from §12.1;
  - links to the plot list (`docs/plots/README.md`) and the parameter index.
- **SPEC.md:**
  - Remove the stamps and the Conventions block (Decision 1). Milestone names stay only where they point at
    future work ("until wave 5").
  - Remove `Status: Draft.`; add `STATUS.md` to the document map.
  - Fix §1.2's AGSi row, which is missing a cell separator.
  - Cut §1.3 "Order of work" to the order itself, without the history of why wave 2 moved.
  - §3: drop the batch status line.
  - §4 and §5: each bullet keeps its cross-cutting rule and points to its living doc
    (`docs/analysis/judgments.md`, `strength.md`, `statistics.md`, `correlations.md`). One-feature detail
    goes, after checking that the living doc holds it. Examples: the ψ rules of `mohr_coulomb_set()`, the
    mechanics of `select()` and `compare_sources()`, `hoek_brown_fit()`'s σci handling.
  - §12.1: keep the release process; the release history goes to `STATUS.md`.
  - §12.4: a one-line pointer to `STATUS.md`, keeping the section number.
  - §13: a one-line pointer to `docs/TODO.md`.
  - Target: about 330 lines.
- **`CLAUDE.md`:**
  - The first paragraph: what hangtu is, then "Status and what's next: `STATUS.md`".
  - Commands: the whole suite as `uv run pytest -n 3 --dist loadfile` (Decision 3).
  - "Where things are": `STATUS.md`, the new `docs/analysis/` files, and `docs/drafts/` reduced to the
    parameter sheets.
- **`docs/reference/process.md`:**
  - The documents table gains `STATUS.md`.
  - The close-out updates `STATUS.md` (not SPEC §12.4 and the "Next" sentence).
  - "Starting from zero" step 4 loses the `phase2-data.md` instruction, which is long past.

### Step 4: TODO sweep
- Check each item against the code and the specs. Delete those already resolved; #5 (the M8 standards check)
  and #21 (P17's source, for M12) look resolved and are checked first.
- Remove the "built in …" and "settled in …" history inside the open items, keeping only what is still open.
- Repoint references to the moved docs.
- Item numbers don't change, because other files cite them.

## Plan

### Step 1: published text cites no internal file
Two build commits, each with ruff, mypy and the tests it touches passing, and the whole suite
(`uv run pytest -n 3 --dist loadfile`) before the second.

**Commit 1: `cleanup: keep internal references out of public docstrings`**
1. **Test first:** `tests/docs/test_site.py::test_public_docstrings_cite_no_internal_files`.
   - Resolve each name from `_documented()` with `importlib` plus `getattr`.
   - Collect its docstring (`inspect.getdoc`). For a class, add the docstrings of public methods and
     properties from `vars(cls)`; for a module, add those of its `__all__` members.
   - Fail with a list of `name: line` for each line matching
     `SPEC §|docs/|TODO #|\bM\d{1,2}\b|\bwave \d\b`.
   - Run it to confirm it fails with the expected list (about 55 lines).
2. **Rewrite**, by the table in the Spec, in:
   - `stats/`: `_compare.py`, `_compare_sources.py`, `_crosstab.py`, `_fit.py`, `_representative.py`,
     `_select.py` and `_mohr_coulomb_set.py`;
   - `analysis/`: `_add_judgment.py`, `_shear_box_conversion.py`, `_hoek_brown_fit.py`, `_mohr_coulomb.py`,
     `_phase_relations.py`, `_shear_box_fit.py`, `_triaxial_readings.py`, `_undrained.py`,
     `_vertical_stress.py`, the package docstring of `correlations/`, and the 11 correlation functions'
     "(SPEC §4)" sentence (in `correlations/_framework.py`, if it is shared, otherwise in each module);
   - `plot/`: `_representative_profile.py`, `_shear_box_envelope.py` and `style.py`;
   - `project.py`: the 12 dataset methods' `docs/data/datasets.md` pointers, and `set_judgments`;
   - `_judgments.py`: the docstring of `ht.judgments`.
   - The derivations for `mohr_coulomb_fit`, `shear_box_fit` and `hoek_brown_fit` come from the "Derivation(s)"
     sections of `m11b`, `m17b` and `m17c`, shortened to the equations and steps a user needs.
   - The sources for `undrained_shear_strength_from_tests` come from `m17a`'s Sources.
   - For `project.py`, check each `datasets.md` section the pointer named, and add the sentence a user needs
     (usually the depth basis or the row rule) where the docstring doesn't already give it.
3. **Check:** `uv run zensical build --clean --strict` after `docs/prepare_site.py`, and read the rendered
   reference pages for the three fits.

**Commit 2: `cleanup: keep internal references out of messages`**
1. **Test first:** `tests/test_errors.py::test_messages_cite_no_internal_files`. Parse each `src/hangtu/**/*.py`
   with `ast`, skip module, class and function docstrings, and fail on any other `str` constant matching the
   same pattern, listing `file:line`. Run it to confirm the 24 hits.
2. **Rewrite** each message by the table:
   - `_judgments.py` (4), `analysis/_vertical_stress.py` (2), `_phase_relations.py` (2), `_add_judgment.py`,
     `_hoek_brown_fit.py`, `_shear_box_conversion.py` (2), `stats/_select.py`, `_significance.py`,
     `_representative.py` (3), `_compare_sources.py`, `_mohr_coulomb_set.py` (3): drop the reference.
     `NO_STIFFNESS` becomes "no selection; derived values aren't built yet"; the rock message names the
     generalized Hoek–Brown set as planned.
   - `qc/_accepted.py:84` and `qc/_settings.py:206`: name the AGS and QC guide's "Accepting reviewed
     findings" (check that it covers the format), or say the expected shape in the message.
   - `qc/_settings.py:215`: the `where` argument passed to `read_yaml` becomes a plain description of the
     file.
3. Update the two `pytest.raises(match=…)` patterns that expect `SPEC §4`, and grep `tests/` for other
   matches on the changed text.
4. Full suite, ruff, mypy.

Commit messages are shown for approval before the intent/spec/plan commit; the two build commits follow the
approved plan.

### Step 1b: site pages and column descriptions cite no internal file
**Commit: `cleanup: keep internal references out of site pages and columns`** (Sonnet)
1. **Test first,** both in `tests/docs/test_site.py`. Run them to confirm the 15 and 4 hits:
   - `test_site_pages_cite_no_internal_files`: every `docs/site/**/*.md` that git tracks (`git ls-files`),
     which leaves out the generated pages. It fails with `file:line` on the step 1 pattern.
   - `test_column_descriptions_cite_no_internal_files`: every column's `description` in the loaded registry.
2. **Rewrite** by the Spec's tables:
   - `guides/selection.md:134`: the message as it is now. Grep the guides for other quoted messages that
     step 1 changed.
   - Parameter pages 06, 07, 08, 10, 15 and 22: "stage D (M18)" and "selection (M18)";
   - Page 15, lines 71, 88 and 89, and page 22's table: waves;
   - Pages 05 and 22: the `datasets.md` pointers;
   - `columns.yaml` lines 268, 418, 494 and 666.
3. **Check:** `uv run python docs/prepare_site.py && uv run zensical build --clean --strict`. Run
   `tests/docs/test_site.py` and the registry tests, ruff and mypy.

### Step 2: decisions in living specs
Five build commits. Each one runs ruff, mypy and the tests it touches, and the whole suite
(`uv run pytest -n 3 --dist loadfile`) runs before the last. Commits 1–3 are (Opus), because they check specs
against the code; 4–5 are (Sonnet), because they are mechanical once the living docs exist.

**How a pointer is rewritten** (commits 1–4):
- If the decision is in a living doc after this step, cite that doc and section. The living docs are
  `judgments.md`, `strength.md`, `index-and-spt.md`, `statistics.md` and `correlations.md` in `docs/analysis/`,
  `docs/data/*.md`, and a plot spec.
- If it is only in the module's own public docstring (`vertical_stress()`, `spt_n1_60()`,
  `phase_relations()`, `clay_activity()`), drop the citation. The module comment keeps the rule, in a line
  where it doesn't already say it.
- Every repointed citation is checked against its target. A fact the target doesn't hold is added to it in
  the same commit.
- SPEC: inside a "decided …" stamp, only the work-file path changes to the living doc. Step 3 removes the
  stamp and keeps the link as the bullet's pointer. Stamps that cite only provenance (`parameter-roadmap.md`,
  `docs-site.md`, `type-check.md`) are left for step 3 to remove.
- `docs/work/` files, plot specs and `docs/data/*.md` keep their work-file citations, which are history or
  "Related" links (Out of scope). The only exception is the path of the moved draft (commit 3).

**Commit 1: `cleanup: write the judgments living spec`** (Opus)
1. `docs/analysis/judgments.md`, with a header table in the shape of `statistics.md` (Status, Parent: SPEC §4,
   Related: the work files below):
   - §1 The file: `judgments.yaml`, where it is found, `p.set_judgments()`, units blocks and `unitless`.
   - §2 How a value resolves: explicit argument → file → error naming it, plus the two exceptions.
   - §3 Keys and the project-wide value: `by:`, the optional project-wide value with its `reason`,
     `project_only`, and `none_allowed` with `none`.
   - §4 What a result records.
   - §5 One entry per judgment: `unit_weight`, `water_level`, `plasticity_index`, `specific_gravity`,
     `significance_level`, `spt_refusal_upper_limit`, `fixed_intact_compressive_strength`,
     `critical_state_friction_angle` and `selection`. Each entry gives its keys, whether a project-wide value
     is allowed, its checks, what absence does, and its readers.
   - Sources: the Spec of `m13a`, then `m13b2` D11, `m14b` D4, `m15d` D8, `m17c` D8, `m18a` D1–3, `m18d` D5
     and `m18e` D6–10, each checked against `KINDS` and the selection section of `_judgments.py`. Where a work
     file and the code disagree, the code wins and the disagreement is listed in the commit body.
2. Repoint to it: `_judgments.py` (module docstring and the 12 comments), `analysis/_add_judgment.py`,
   `analysis/_judgment_values.py:71`, `stats/_representative.py:44,500`, the 3 `m13a` entries in
   `columns.yaml`, and SPEC §4's judgment bullets (lines 182, 187, 192–193).
3. Check: `uv run pytest tests/test_judgments*.py tests/analysis/test_add_judgment.py`, ruff and mypy. (A
   comment-only change, but the yaml loads in tests.)

**Commit 2: `cleanup: write the strength living spec`** (Opus)
1. `docs/analysis/strength.md`, with the same header (Parent: SPEC §4, Related: `m11a`–`m11c`, `m17a`–`m17c`,
   `m18d`, and `docs/data/datasets.md` §6.10–6.12 for the datasets):
   - §1 Triaxial stresses at failure (`triaxial_failure_stresses()`), the one place σ1, σ3 and σ′ are computed.
   - §2 Failure from readings (`m11c`).
   - §3 The line-fit core (`_line_fit`): transform, free or fixed intercept, back-transform, and the derived
     result base (`m11b` D3, D12).
   - §4–§6 The three fits, `mohr_coulomb_fit()`, `shear_box_fit()` and `hoek_brown_fit()`: the rules that span
     them (groups, reported pairs, validity, what a result records) and each fit's reasons. Derivations
     aren't repeated, because the docstrings hold them since step 1. A one-line pointer names the
     docstring.
   - §7 Undrained strength from tests: the basis and the factors.
   - §8 The shear box φ′ conversion (`m18d`), including the `critical_state_friction_angle` link to
     `judgments.md` §5.
2. Repoint to it: `analysis/_line_fit.py`, `_mohr_coulomb.py`, `_shear_box_fit.py`, `_hoek_brown_fit.py`
   ("decisions cited by number" becomes section numbers), `_derived.py` (3), `_fit_groups.py` (2),
   `_undrained.py:13`, `_shear_box_conversion.py`, the `m11b`, `m17b`, `m17c` and `m18d` entries in
   `columns.yaml` (16, as a short formula where one fits, e.g. `derived: arctan(b) of the line fit`, otherwise
   `derived: docs/analysis/strength.md §n`), and SPEC §4 lines 183–185 and §5 line 203.
3. Check: the strength tests (`tests/analysis/test_*fit*.py`, `test_triaxial*.py`, `test_undrained*.py`,
   `test_shear_box_conversion.py`) and `tests/test_registry*.py`, ruff and mypy.

**Commit 3: `cleanup: move the analyses draft to docs/analysis/index-and-spt.md`** (Opus)
1. `git mv docs/drafts/analysis.md docs/analysis/index-and-spt.md`. The title becomes "Index tests and SPT",
   with a header table: Status: living spec, §1 built in M3, §2–3 in M8, 🔬 values marked; Parent: SPEC §4.
2. Drop §4. Its facts are already in the `vertical_stress()` docstring (assumptions, γw), the `spt_n1_60()`
   docstring (C_N methods, cap 1.7, blank above 300 kPa), `correlations.md` (naming, explicit N, out of range,
   bounds) and `config/correlations.yaml` (the built set). Before deleting, check each bullet against those;
   any that is missing goes into `correlations.md`.
3. Repoint the path (sections keep their numbers): SPEC line 171 and the §4 document map row (line 19),
   `columns.yaml`, `analysis/__init__.py`, `_fractions.py`, `_gradation.py`, `_plasticity.py`,
   `_classification.py`, `_spt.py`, the three `config/*.yaml`, the 7 test files, P00, P02–P06,
   `docs/data/datasets.md` and the 3 `TODO.md` headings (#5, #22, #24). Step 4 then only checks TODO, so no
   link is left broken between steps.
4. Check: `grep -rn "drafts/analysis" . --exclude-dir=docs/work` is empty. Run the touched tests, ruff and mypy.

**Commit 4: `cleanup: point the remaining work-file citations at living docs`** (Sonnet)
1. **`ht.stats` → `statistics.md`:** `_rows.py` (3), `_result.py`, `_note.py`, `_significance.py`,
   `_compare.py`, `_crosstab.py`, `_representative.py:3`, `_compare_sources.py`, `_refusal_limit.py`,
   `_model_set.py` and `_mohr_coulomb_set.py`. Remove the `phase3-stats.md` link from the header.
2. **Correlations → `correlations.md`:** `correlations/_friction_angle.py`, `_undrained_shear_strength.py`,
   `_stress_history.py` and `_stiffness.py`, and the `m13b*`, `m15b` and `m18a` entries in `columns.yaml`.
3. **Plots → their spec:** `plot/_geology_units.py` (P07), `_profile.py` (P01), `stats/_positions.py` and
   `plot/_distribution_fit.py` (P08), `plot/_values.py:206` (`correlations.md` §3).
4. **Datasets → `docs/data/datasets.md`:** `datasets/_shear_box.py` (§6.12), `_undrained.py` (§6.11), and the
   `columns.yaml` comments (lines 13, 38, 319, 1101, 1256 and 1427) and the `m18f` entries.
5. **Public docstrings → none:** `_vertical_stress.py`, `_overburden.py`, `_phase_relations.py`,
   `_clay_activity.py`, under the rule above.
6. **SPEC:** the remaining work-file paths in §4–§5 (lines 186, 206–207).
7. **Regression test:** `tests/test_errors.py::test_source_cites_no_work_file`, which fails on
   `docs/work/` in any `src/hangtu/**/*.py` or `*.yaml`, so a new module points at a living doc from the
   start.
8. Check: `grep -rn "docs/work/" src/hangtu` is empty, and `grep -n "docs/work/" SPEC.md` leaves only the
   provenance stamps. Run the whole suite, ruff and mypy.

**Commit 5: `cleanup: retire the phase drafts and list the living specs`** (Sonnet)
1. Delete `docs/drafts/phase2-data.md` and `phase3-stats.md`. Their two research items become TODO #57 (pcf in
   AGS density headings, with its references) and #58 (how US files fill `ISPT_PEN*`). The rest is already
   in `ingest.md`, `qc.md`, `datasets.md`, SPEC §5 and §7, `statistics.md`, and TODO #8, which loses its
   `phase3-stats.md` pointer. SPEC §7's metadata table list is checked against the draft's.
2. `CLAUDE.md`, "Where things are": `docs/analysis/` lists all five living specs; the `docs/drafts/` bullet
   names only the parameter sheets; the `docs/data/` bullet loses its milestone tags.
3. `docs/reference/process.md`: the documents table names `docs/analysis/` as the feature spec for an
   analysis that spans units (line 18). "Starting from zero" step 4 is left for step 3.
4. Check: `grep -rn "phase[23]-\|drafts/analysis" . --exclude-dir=docs/work` is empty.

The build commits of steps 1b and 2 follow the approved plan without separate approval, docs-only ones included
(review, 2026-11-08).

### Step 3: SPEC, STATUS.md, CLAUDE.md, process.md
Three docs-only commits, no code or tests touched (no test reads SPEC, `CLAUDE.md` or `process.md`). Each one
is checked by grep and a read of the changed sections. 1–2 are (Sonnet), because they move text; 3 is (Opus),
because it checks SPEC against the living docs before cutting.

**The size target is in words, not lines** (review, 2026-11-08). SPEC's bullets are one line each, however long, so trimming §4
and §5 hardly changes the line count: moving §12.4 out and dropping the stamps gives about 400 lines. The
target "about 330 lines" becomes about 6,000 words (from 7,996), a cut of a quarter, and the final count is
given in both.

**Commit 1: `cleanup: give status one home in STATUS.md`** (Sonnet)
1. **`STATUS.md`** (new, root), in the shape of the skill's template, under 50 lines:
   - **Next:** the `CLAUDE.md` sentence (wave 0, M16, once TODO #31 is settled; else wave 3, M19, with M20 on
     M18's model-set base; then waves 4–6).
   - **Last checkpoint:** this unit, 2026-11-08; its merge commit is filled in at the merge.
   - **Open:** SPEC §12.4's table (M16, M19–M24) with Done when and Status.
   - **Done:** one line per milestone in build order, from §12.4's Done table, then the rule for numbers (kept
     when the order changes; M10 dropped, not reused).
   - **Elsewhere:** the plot list (`docs/plots/README.md`) and the parameter index
     (`docs/drafts/parameters/README.md`).
   - **Releases:** 0.0.1 (the M2b state: P00, P01, P07) and 0.1.0 (M9: P00–P03 and P07, the SPT analysis,
     AGS4 ingest, QC, the four datasets, `examples/` and `ht.examples`), from §12.1 and §1.3.
2. **SPEC:**
   - §12.4 becomes one line: "Milestones and their status: [`STATUS.md`](STATUS.md)." Its intro's rules
     (rows in build order, each milestone names its wave, numbers kept) move to `STATUS.md`.
   - §12.1: the 0.0.1 and 0.1.0 bullets go; §1.1's "claimed by the 0.0.1 placeholder release (§12.1)" stays as
     a fact, pointing to `STATUS.md`.
   - §1.3 Releases keeps the rule (cut when a milestone leaves something usable, not tied to waves or planned
     ahead); "0.1.0 … is the first, on PyPI" goes. "§12.4 has the milestones" points to `STATUS.md`.
   - §3: the "Batch 1 (P00–P07): all built" line goes; "the milestone of every other plot is in §12.4" points
     to `STATUS.md`.
   - The document map gains `STATUS.md`; `Status: Draft.` goes.
3. **`CLAUDE.md`:**
   - The first paragraph ends at the waves sentence, then "Status and what's next: `STATUS.md`."
   - Commands: the whole suite is `uv run pytest -n 3 --dist loadfile`; the CI line keeps `-n auto`
     (Decision 3).
   - "Where things are" gains `STATUS.md` (status, what's next, releases) as its second bullet.
4. **`docs/reference/process.md`:** the documents table gains `STATUS.md`, and `CLAUDE.md`'s row loses "What's
   next? Done work is in SPEC §12.4"; "Stages and waves" and "Starting from zero" step 3 say `STATUS.md` for
   §12.4; the close-out updates `STATUS.md` (the unit's status, and Next when it changes) instead of §12.4 and
   `CLAUDE.md`'s "Next" sentence; "Starting from zero" step 4 loses the `phase2-data.md` instruction and keeps
   the rule (a phase boundary is where the spec is redesigned).
5. **Other pointers to §12.4:** `docs/plots/README.md:115`, `docs/plots/TEMPLATE.md:16`,
   `docs/drafts/parameters/README.md:6`.
6. **Check:** `grep -rn "§12\.4\|SPEC §12\.1" . --exclude-dir=docs/work --exclude-dir=sandbox` leaves only
   SPEC's pointer and `CLAUDE.md`'s dependency rule (§12.1 keeps the dependencies).

**Commit 2: `cleanup: drop SPEC's decided stamps and Conventions block`** (Sonnet)
1. Every "(decided)", "(decided <date>)", "(decided <date>, `docs/work/…`)", "(agreed for now)", "(naming
   decided)", "(was TODO 0b)", and the heading "Framework (decided)" go (Decision 1). Where a stamp holds the
   bullet's only link to a living doc, the link stays as the pointer ("…, [`strength.md`](…) §1"). §8.2's
   "Depth used (decided)" header becomes "Depth used".
2. The milestone tags that are only provenance ("(M18 (a))", "(M15 (c), …)", "M11 c", "(M14 (a))") go; those
   that point at future work ("until wave 5", "for GSI and D in M22", "M16's user-defined groups") stay.
3. The Conventions block goes; 🔬 marks become plain "TODO #n".
4. §1.2: the AGSi row gets its missing separator (`… later also input | Later (export, then import) |`).
5. §1.3 "Order of work": the order and its one reason each (statistics before waves 2 and 0, wave 0 waits on
   TODO #31); the history of why wave 2 moved goes.
6. §8.2's CSV row cites `index-and-spt.md` §1.2 (not "analysis.md").
7. §13: "None open. Pending decisions and research: [`docs/TODO.md`](docs/TODO.md)." The history of #1 and #2
   goes (it is in `datasets.md`).
8. **Check:** `grep -n "decided\|🟡\|❓\|🔬\|docs/work/" SPEC.md` is empty.

**Commit 3: `cleanup: keep SPEC §4 and §5 to the cross-cutting rules`** (Opus)
1. For each bullet in §4 and §5, keep the rule another feature could get wrong, one sentence where it can, and
   its living doc as the pointer. Before cutting a detail, check that the doc holds it; one it doesn't is added
   there in this commit. The cuts the Spec names:
   - **Envelope fits** keep the shared core, "a reason, not an error", nothing through the origin unless asked,
     and σci never picked by a rule; each fit's mechanics (four lines per group, Hoek's axes, 0.5 σci) go to
     `strength.md` §4–§6, which holds them.
   - **Derived results** keep `kind = "derived"`, the naming rule (the parameter's name, a test's name where it
     would pool unlike tests, `reported_`, `correlation_name`, `conversion_name`); the conversion's equation and
     tables go (`strength.md` §8).
   - **`compare_sources()`, `select()`**: "never pooled, a position, never a test" and "the selection is a
     judgment that names a method or gives a value with a reason"; the method list, the error for an unlisted
     unit and the no-source case go (`statistics.md` §5–§6).
   - **Model sets** keep the published model as the definition, the four origins, and that a set reads
     `select()` and never re-implements it; `mohr_coulomb_set()`'s ψ rules, E′/ν′ and the views go
     (`statistics.md` §7).
   - **Judgments**: resolution, keys, the file, recording and "absence is an error, with two exceptions" stay,
     each in a line; the selection bullet keeps its keys and points to `judgments.md` §5.9.
   - **Undrained strength, phase relations, triaxial stresses**: one or two lines each, the rule and the doc.
2. §5's opening list of functions drops the milestone tags.
3. **Check:** each cut detail found in its living doc (listed in the commit body as "checked: …"); every link
   resolves; `wc -l -w SPEC.md` against the target above.
