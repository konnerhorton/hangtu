# M1: P00 framework — intent

## Goal
Build the shared plot framework from `docs/plots/P00-framework.md`: settings, units on DataFrames, the column registry and CSV templates, house style, labels, axis limits, out-of-range markers and notes, palette, legends, hints, errors and `Sheet`. Then P01–P07 only have to describe their own drawing.

## Why
- It's the next milestone in SPEC §12.4. M2 (P01) can't start without it.
- Every plot depends on the cross-cutting rules: unit resolution (SPEC §2.6), registry names (§10.3), and "never drop data silently" (§3). If each plot reimplements them, they will drift apart. Building them once, with tests, keeps the plots consistent.

## Constraints
- **The feature spec is P00**, which is already approved. Build to it and to its acceptance criteria (P00 §14). If the build shows the spec is wrong, change P00 in the same commit as the code.
- SPEC §2.6: the order units are resolved in, never guessing a unit, an error for analyses and "(units unknown)" plus a warning for plots.
- SPEC §3: the plot contract. Never change global matplotlib state.
- SPEC §10.3 and CLAUDE.md "Naming": the registry is the only source of column names, and names are written out in full.
- SPEC §11: error messages say what is wrong, where, and what to do.
- SPEC §12.1: only the Phase 1 dependencies. `pytest-mpl` is optional and isn't needed for M1.
- SPEC §12.2: data files ship inside the package (`columns.yaml`, `config/defaults.yaml`, `units/aliases.yaml`), and tests mirror the package.
- **Done when** (SPEC §12.4): the framework tests pass and a dummy plot composes on a `Sheet` without creating another figure.

## Decisions to confirm
- **No separate `spec.md`.** P00 is the spec, so the spec step is a review of P00 against this intent. That step promotes the two drafts:
  - `docs/drafts/columns.yaml` becomes `src/ags_kit/columns.yaml`, including the Batch 1 entries beyond P01, which stay provisional (the file's header says so). Shipping them now means the registry test covers them and `ak.template()` works for every template. Each later plot spec may still change its own entries.
  - `docs/drafts/units-aliases.yaml` becomes `src/ags_kit/units/aliases.yaml`. Its comments that refer to Phase 2 (U002, "SPEC 2.5 #2") are rewritten to point at P00 §4.3.

  Both drafts are deleted from `docs/drafts/` when they are promoted, so there is only one copy of each.
- **`config/defaults.yaml` holds only what M1 uses:** the display unit for each quantity kind (P00 §4.1) and the default settings. Presets and classification tables arrive with the plots that use them (M2–M4).
- **The settings for later milestones** (`hammer_efficiency`, `spt_cap`) are added and validated now, because P00 §3 lists them, but nothing reads them until M3.
- **TODO #1 (pcf) and #2 (SPT N)** stay open. M1 implements what P00 §4.3 says now (pcf converts according to the column's quantity kind, and N is never converted). Both are covered by tests, so if either decision changes, the change is small and visible.
- **One unit of work, not two.** M1 is big, but the parts depend on each other: plots need units, units need the registry, and `Sheet` needs style. The plan splits it into build commits of about 300 lines or less, in dependency order: errors and settings → units → registry and templates → style and labels → limits → notes and edge markers → palette and legend → hints → `Sheet` and shared test helpers.

## Out of scope
- Any real plot (P01 is M2), plot presets, and analyses (M3–M4).
- AGS ingest and the unit rules that apply only on ingest (`docs/drafts/phase2-data.md`).
- `Sheet` title blocks, inch display for particle sizes, and per-project settings files (P00 §16).
- Examples, the README and the tutorial (M5).
- Publishing the repo and the CI matrix (TODO #0c).

## SPEC sections touched
- None expected. M1 implements §2.6, §3 and §10.3 as written.
- §10.3 links to `docs/drafts/columns.yaml`. When the drafts are promoted, that link is pointed at the shipped file. The same goes for the links in P00 (§4.2, §5) and the drafts line in CLAUDE.md.
