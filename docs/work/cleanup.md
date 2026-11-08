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

The unit is done in four steps, in order. Each step's plan is written after the step before it is merged
into this branch (step 1's is below).

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
