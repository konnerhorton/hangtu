# Rename the package to hangtu — intent

## Goal
Rename the package from `ags-kit` / `ags_kit` to **`hangtu`**, imported as `import hangtu as ht`. The change is mechanical only: the distribution name, the import package, the package-named error classes, the `ak` alias, and the prose that names the package.

## Why
- `ags-kit` is a working name (SPEC §1.1, TODO #0), and it has to be settled before the first PyPI release.
- It ties the package to one file format, while DIGGS support is on the roadmap.
- US engineers, the target audience, mostly don't know AGS.
- "AGS" is a trade body's acronym, and that body's official library is `python-ags4`, so `ags-kit` could look endorsed.
- Renaming now, after M2 and before M3, means fewer references to change than waiting until M5.

## Constraints
- **No behavior changes.** The same tests pass before and after, and only names change. Every build commit leaves ruff and pytest green.
- **Leave other uses of "AGS" alone:** AGS4, AGSi, `python-ags4`, the `ags:` registry field, and future `read_ags` / `from_ags`.
- **Frozen history stays as written.** `docs/work/m0-*`, `m1-*` and `m2-*` and git history aren't rewritten.
- **One unit, easy to undo.** It is merged into `main` with `git merge --no-ff`, so `git revert -m 1 <merge>` undoes the whole rename.
- **Commits by kind** (CLAUDE.md "Git and commits"), each a pure substitution:
  - the package move and import name;
  - the error class names;
  - the `ht` alias;
  - the docs.
- If a change alters a recorded decision, the spec that records it changes in the same commit. That applies to the error class names in P00.
- No new dependencies (SPEC §12.1).
- **Done when:**
  - a leftover search for `ags_kit|ags-kit|AgsKit|\bak\b` (outside frozen history) finds nothing;
  - `uv build` produces a `hangtu` wheel containing all the package data;
  - CI is green.

## Decisions to confirm
- **Error classes:** `AgsKitError` → `HangtuError` and `AgsKitHint` → `HangtuHint`. Users will see these names in tracebacks and `warnings` filters.
- **The style file:** `plot/ags_kit.mplstyle` → `plot/hangtu.mplstyle`.
- **No separate `spec.md`.** The spec commit records the name in SPEC §1.1, removes "rename settled (TODO 0)" from the M5 row in §12.4, and deletes TODO #0. Two items from TODO #0 move into §1.1:
  - "AGS and DIGGS stay in the description, keywords and README";
  - "check PyPI availability again just before the first release".

## Out of scope
- **Branding:** what the name means, the README pitch, and the PyPI description and keywords. The pyproject `description` stays as it is for now.
- Publishing a placeholder release to claim the name on PyPI.
- **Renaming the repo folder.** You'll do this after the merge, and move Claude's memory folder to match.
- The version stays at `0.1.0.dev0`.

## SPEC sections touched
- §1.1 (name decided), §12.2 (package layout) and §12.4 (M5 row).
- Every other mention of the name and every `ak.` sample changes mechanically in the close-out: §2.6, §3, §4, §10.3, §11 and the title.
- Docs: `docs/plots/P00-framework.md` (error class names), the other plot specs, `docs/plots/README.md`, `docs/reference/`, `README.md`, `CLAUDE.md` and `TODO.md`.
