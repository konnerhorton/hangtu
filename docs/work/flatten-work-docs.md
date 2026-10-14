# Flatten docs/work to one file per unit

Branch `flatten-work-docs`, off `main` after M6 merges. A docs-only unit with no feature spec: the layout is recorded in `docs/reference/process.md` and `CLAUDE.md`, which this unit updates.

## Intent

### Goal
Each unit of work gets a single file, `docs/work/<id>.md`, with `## Intent`, `## Plan` and, when there is no other feature spec, `## Spec` sections. Plot visual checks go next to the plot specs, in `docs/plots/img/`.

### Why
- Most `docs/work/` folders hold two short files (40 to 125 lines each). One unit is easier to read when it's one file, and the folder level adds nothing.
- M3 is spread over four folders (`m3-spt`, `m3-spt-analysis`, `m3-p02`, `m3-p03`): the intent in one and the plans in the other three. Someone looking for M3 later can't easily find it.
- The visual checks outlive their unit, and the plot specs already link to them (P02, P03, P07). They belong with the plot specs.

### Constraints
- **Frozen docs keep their content.** Intents and plans are frozen once merged (process.md). Only these change: headings get demoted one level, the "— intent" / "— plan" title suffixes go, and links get repaired. No wording is rewritten.
- **IDs are the branch names**, so `git log --first-parent main` still matches the file names. The exception is M3, which shared one intent across three branches and becomes `m3-spt.md`.
- Each step gets one commit, and every docs link resolves after each one.
- Docs only: no code changes and no new dependencies.

### Out of scope
- Renaming units or giving them new IDs (for example, `p07` → `m2b-p07`).
- Rewording old intents and plans, including prose mentions of `intent.md`, `plan.md` or `visual-check.png` inside them.
- Adding images to the P00 and P01 specs. They move to `docs/plots/img/` but nothing new links to them.

## Plan

### Target layout
```
docs/work/
  m0-scaffolding.md
  m1-p00-framework.md
  m2-p01-property-profile.md
  m3-spt.md                     intent + plans for spt-analysis, P02, P03
  m5-ingest.md
  m6-qc.md
  p07-geology-unit-comparison.md
  rename-hangtu.md
  flatten-work-docs.md          this file
docs/plots/img/
  P00.png                       from m1-p00-framework/visual-check.png
  P01.png                       from m2-p01-property-profile/visual-check.png
  P02.png                       from m3-p02/visual-check.png
  P03.png                       from m3-p03/visual-check.png
  P07-si.png                    from p07-geology-unit-comparison/visual-check.png
  P07-us.png                    from p07-geology-unit-comparison/visual-check-us.png
```

### File shape
```markdown
# M5: AGS4 ingest

## Intent
### Goal
...

## Spec            (only when the unit has no feature spec elsewhere)

## Plan
Spec: [`docs/data/ingest.md`](../data/ingest.md).
### Package layout
...
```
- The H1 is the shared part of the old titles, without "— intent" / "— plan".
- Inside each section, every heading moves down one level (`##` → `###`). Headings inside code fences are left alone.
- The plan's opening line `Intent: [intent.md](intent.md). Spec: …` becomes `Spec: …`, because the intent is now in the same file.
- Relative links lose one `../`: `../../plots/X.md` becomes `../plots/X.md`, and `../m3-p02/plan.md` becomes `#plan-p02`.

For the merges I use a throwaway script in the scratchpad that concatenates, demotes headings outside fences and rewrites links. It isn't committed. I read each output diff before staging it.

### Build steps
1. **`docs: move plot visual checks to docs/plots/img`**
   - `git mv` the six PNGs as listed in the target layout.
   - Repoint the image links in `docs/plots/P02-spt-profile.md`, `P03-spt-histogram.md` and `P07-geology-unit-comparison.md`.
   - `CLAUDE.md` "Visual check": save to `docs/plots/img/PXX.png`, or to `PXX-si.png` and `PXX-us.png` when US and SI need separate figures, and commit it in the close-out.
2. **`docs: merge the M3 units into docs/work/m3-spt.md`**
   - `git mv docs/work/m3-spt/intent.md docs/work/m3-spt.md`, then add `## Plan: SPT analysis`, `## Plan: P02` and `## Plan: P03` from the three plan files, each demoted one level. Delete the three folders.
   - The intent's unit table links to `#plan-spt-analysis`, `#plan-p02` and `#plan-p03`.
   - Repoint the "M3 intent" pointer in the P02 and P03 specs to `docs/work/m3-spt.md`.
   - This step is separate because it's the one merge that isn't mechanical.
3. **`docs: merge each unit's intent and plan into one file`**
   - For `m0-scaffolding`, `m1-p00-framework`, `m2-p01-property-profile`, `m5-ingest`, `m6-qc`, `p07-geology-unit-comparison` and `rename-hangtu`: `git mv <id>/plan.md <id>.md`, since the plan is the larger file and `--follow` tracks it, then put the intent above it in the file shape above. Delete the folder.
   - Repoint the "Intent" pointers in `docs/data/ingest.md`, `docs/data/qc.md` and `docs/plots/P07-geology-unit-comparison.md`, and the frozen path mentions in `rename-hangtu.md`'s intent and plan (`docs/work/m0-*` and so on). Those are commands, so they have to stay runnable.
   - `docs/reference/process.md`: the table rows become one row for `docs/work/<id>.md` (Intent, Spec, Plan sections; intent frozen once done, plan frozen once merged). Loop steps 1 to 3 say "add the `## Intent` / `## Spec` / `## Plan` section" in place of "write `intent.md`" and "commit `plan.md`". The feature spec alternative `docs/work/<id>/spec.md` becomes the `## Spec` section. New units are written in this shape from the start: the intent commit creates the file, and each later loop step's commit adds its section. Nothing is merged at the close-out.
   - `CLAUDE.md` "Where things are": `docs/work/<id>.md`. Add: "`docs/work/` files for merged units are history. Read one only when the task or a spec points to it." Splitting the file wouldn't help context use much (a merged file adds 30 to 80 lines to a lookup), but pulling old units in "for context" does cost a lot.
   - This step is mostly moves and is about 400 lines once the intents are folded in. If the diff reads poorly, split it into M0 to M2, then M5, M6, P07 and the rename.

This file already uses the new shape, so it's committed as is by the loop's intent and plan commits, before step 1.

### Verification
After every step:
- `uv run ruff check . && uv run ruff format --check . && uv run pytest` passes. Nothing should change, but it's what CI runs.
- Every relative link and image in `*.md` resolves, including `#anchors` against GitHub's slug rules. I check this with a scratchpad script that isn't committed.

At the close-out:
- `find docs/work -mindepth 1 -type d` prints nothing.
- `git grep -n -E "docs/work/[a-z0-9-]+/|\.\./work/[a-z0-9-]+/"` finds nothing.
- `git grep -n "visual-check" -- ':!docs/work'` finds only the CLAUDE.md rule and the prose in `sandbox/plotting-library-decision.md`.
- Each `docs/work/*.md` has exactly one H1 outside code fences.
- `git log --follow --oneline docs/work/m5-ingest.md` reaches back to the M5 plan commit.
- I read the merged files rendered on GitHub (the branch pushed, with your approval) to check the headings and links.

### Open question
**When to run it.** The plan assumes it runs after M6 merges, so `m6-qc` is converted along with the rest. Running it before the M6 build would mean merging `main` into `m6-qc` partway through.
