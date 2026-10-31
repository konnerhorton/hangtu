# Context trim: keep always-loaded files small and each rule in one place

## Intent

### Goal
Cut what Claude loads every session down to what it needs, and give each process rule a single home, so
instructions don't drift apart or go stale.

### Why
- `CLAUDE.md` is loaded in every session. Its first paragraph is 534 words (28% of the file) and mostly lists
  finished units. That history is already in `git log --first-parent main`, the `docs/work/` files and
  SPEC §12.4, and the paragraph grows with every close-out.
- The git and commit rules appear three times: in `CLAUDE.md` (~325 words), in the spec-driven-development
  skill and partly in `docs/reference/process.md`. If one copy changes and the others don't, the instructions
  contradict each other.
- `docs/TODO.md` says "when an item is resolved, move the decision into SPEC.md and delete it here", but it
  keeps a `## Done` section of 16 resolved items. Any read of the file pays for them.
- Lessons a unit teaches end up in its work file, which a later session doesn't read unless something
  points to it. The close-out step has no prompt to ask whether a lesson needs to be written down somewhere
  that will be read.

### Constraints
- Docs only. No code, tests or registry changes.
- Nothing is lost: each fact removed from `CLAUDE.md` or `TODO.md` is either already recorded somewhere else
  (checked, file named) or moved there in the same commit.
- `CLAUDE.md` keeps the git rules that must never be bent (staging, red commits, message format, approval),
  because they have to be in front of Claude every session.
- The spec-driven-development skill lives in `~/.claude/skills/` and isn't under version control. Back it up
  before editing it; its edits aren't part of any commit.

### Out of scope
- Moving step-specific rules (visual check, the wave spec step) out of `CLAUDE.md`. That can be a later pass.
- A hook that shows the branch before `git commit`.
- Trimming SPEC.md or the open TODO items.

### Decisions (intent review, 2026-10-31)
1. **Unit status lives in SPEC §12.4**, in a new `Status` column (`done`, `next`, blank), replacing the
   "(done)" notes in the M15 row. The parameter index (`docs/drafts/parameters/README.md`) stays the status
   of each parameter. 🟡 Proposed: a column rather than "(done)" notes, so the table can be scanned.
2. **Resolved TODO items are deleted, not archived.** This is the file's own rule, and git keeps the history.
3. **The close-out asks one question:** "What would a future session get wrong without being told?" The
   answer goes in `CLAUDE.md` Conventions (a recurring mistake), `SPEC.md` (a decision) or memory (a
   preference of the user's).
4. **Subagents (item 5 of the review):** `CLAUDE.md` gives standing permission to use an Explore subagent
   for broad read-only searches (step 6), instead of asking each time.

## Plan

Branch `context-trim` off `main`. The intent and this plan go in one commit (the middle path for a small
unit), then one commit for each step below. Each step is checked by reading it and by
`uv run ruff check . && uv run zensical build --clean --strict` where `docs/site/` is involved; nothing here
touches `docs/site/`.

### 1. `docs: keep unit status in SPEC §12.4, not CLAUDE.md`
- **Audit:** list each fact in the current status paragraph and name where it is already recorded.
  Expected: units (through M11 (a)) → SPEC §12.4 and `docs/work/`; `p.qc(accepted=...)` → SPEC §9 and `docs/data/qc.md`;
  SciPy ≥ 1.16.0 → SPEC §12.1 and `pyproject.toml`; the site follows `main` → `docs/work/docs-site.md`.
  Anything without a home moves to one in this commit.
- **`CLAUDE.md`:** replace the paragraph with:

  > Python library that derives the ground parameters a geotechnical design needs, from AGS4 or CSV test
  > data through to model parameter sets, for soil and rock, with plots, analyses, AGS4 ingest/QC and
  > statistics along the way (SPEC §1). Work is organized as stages A–D per parameter and waves 0–6
  > (SPEC §1.3). Done through M15 and M11 (a); 0.1.0 is on PyPI. Next: wave 2 (M11 (b), the fitting core and
  > P11–P12, then M17), then wave 0 (M16, waiting on TODO #31), selection (M18) and waves 3–6. Status: SPEC §12.4 for milestones,
  > `docs/drafts/parameters/README.md` for parameters.

  The `docs/site/` bullet in "Where things are" gains "built and follows `main`".
- **SPEC §12.4:** add the `Status` column (Decision 1). M0–M15 are `done`, M11 is `(a) done; (b) next`, the
  rest are blank. Remove the "(done)" notes from the M15 row.
- **`docs/reference/process.md`:** in loop step 6 (Close), "update `CLAUDE.md` status" becomes "mark the
  unit in SPEC §12.4"; the `CLAUDE.md` row of the documents table says it holds no status beyond the
  next step.

### 2. `docs: one home for the git rules`
- **`docs/reference/process.md`:** gains a `## Git and commits` section with the repo's full rules, moved
  from `CLAUDE.md`: branch per unit, `--no-ff` merges, one commit per loop step, committing at green
  points, the ~300-line split, not mixing kinds of change.
- **`CLAUDE.md`:** the `## Git and commits` section becomes:

  > The loop, branches and commit sizes: `docs/reference/process.md` (and the spec-driven-development
  > skill). These hold every time:
  > - **Stage files by name** (`git add <path> ...`), never `git add -A`, `git add .` or `git commit -a`.
  >   The working tree can hold local files that aren't ignored, and a broad add sweeps them into a public
  >   commit.
  > - **Never commit failing tests or lint errors.**
  > - **Message:** `<scope>: <imperative summary>`, at most 72 characters; the body says why and names any
  >   SPEC section or TODO item a decision touched. No attribution lines.
  > - **Approval:** Claude commits intermediate build steps of an approved plan without asking. Everything
  >   else needs the user's approval first: intent, spec and plan commits, docs-only commits, branch
  >   creation and merges, pushes, and anything that rewrites history. For a commit, show the message and
  >   wait.
- **The skill** (`~/.claude/skills/spec-driven-development/`; not committed, backed up to the scratchpad
  first):
  - `SKILL.md` step 6: "the one-paragraph status at the top of `CLAUDE.md`" becomes "the status of the unit
    in the project's roadmap table".
  - `references/templates.md`, `CLAUDE.md` template: the first paragraph keeps its placeholder and gains
    the hangtu paragraph above as an example, plus one line: "Keep it to what it is and what's next. Done
    work belongs in the roadmap table and git, not here."
  - The template's `## Git and commits`: "Point to the process doc for the loop; copy only the rules that
    must never be bent (staging, red commits, message, approval)."

### 3. `docs: drop resolved items from TODO`
- **Audit:** for each of the 16 `## Done` entries, name the file that records the decision (SPEC section,
  plot spec, data spec or `docs/work/` file). Expected to be all of them; #0c and the AGS heading check are
  history (git, `docs/data/ingest.md` §6).
- Move any decision that isn't recorded elsewhere into its home, then delete the `## Done` section.
- `grep -rn "TODO #<n>"` for each deleted number. A reference that reads as if the item were still open
  gets rewritten to point at where the decision is recorded.

### 4. `docs: ask what to write down at close-out`
- **`docs/reference/process.md`** step 6 gains: "Before merging, ask what a future session would get wrong
  without being told. Put a recurring mistake in `CLAUDE.md` Conventions, a decision in `SPEC.md`, and a
  preference of the user's in memory."
- **The skill**, `SKILL.md` step 6: the same sentence, in general terms (no hangtu paths).

### 5. Check
- `wc -w CLAUDE.md`: expect about 1,300 words, down from 1,883.
- Read `CLAUDE.md`, `process.md` and the skill side by side: each rule stated once, with pointers elsewhere.
- Start a fresh session and ask "what's next and how do I start it?" It should answer from the new
  paragraph and SPEC §12.4 without reading old work files.

### 6. `docs: standing permission for search subagents`
- **`CLAUDE.md`** "Workflow rules" gains: "For a broad read-only search (a name against the registry and
  every spec, every mention of a plot or TODO item), use an Explore subagent and keep only its conclusion."
  This gives standing permission, so it doesn't need asking each time.
- Run before step 5's check, so the word count and the fresh-session test include it.
