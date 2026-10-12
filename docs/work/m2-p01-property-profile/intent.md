# M2: P01 property profile — intent

## Goal
Build `ak.plot.profile()` from `docs/plots/P01-property-profile.md`: any property against depth or elevation, on a linear or log axis, colored by geology unit, with the four presets and all the overlays in P01 §8.

## Why
- It's the next milestone in SPEC §12.4, and the most-used plot in a report.
- P02 (SPT profile), P06 (water content profile) and P09 (characteristic profile) build on it. Getting the vertical axis, the overlays and the exclusion counts right once means those plots only add their own marks.

## Constraints
- **The feature spec is P01.** Build to it and to its acceptance criteria (P01 §12). If the build shows the spec is wrong, change P01 in the same commit as the code.
- Use the M1 framework (P00) for units, labels, limits, notes, edge markers, palette, legend, hints and errors. Don't reimplement any of it in the plot.
- SPEC §2.6: unit resolution order, and "(units unknown)" plus a warning, never a guess.
- SPEC §3: the plot contract, and no change to global matplotlib state.
- SPEC §8.1: elevation = ground level − depth.
- SPEC §10.3 and CLAUDE.md "Naming": column names come from the registry.
- SPEC §11: error messages say what is wrong, where, and what to do.
- SPEC §12.1: no new dependencies.
- **Done when** (SPEC §12.4): the P01 acceptance criteria pass, and `visual-check.png` (US and SI) is committed in the close-out.

## Decisions to confirm
- **No separate `spec.md`.** P01 is the spec. The spec step reviews it against this intent, fixes the points below and moves it from `draft` to `approved`.
- **Overlay column names follow the registry.** P01 §8 currently uses bare `unit, top, base`, which breaks the naming rule.
  - `strata`: `geology_unit` plus **either** `depth_top, depth_base` **or** `elevation_top, elevation_base`. Both pairs, or neither, is a clear error. When the pair matches `vs`, it is drawn as given. When it doesn't, it is converted using `ground_level`, which must then be a single value (the same rule as `secondary="depth"`, P01 §6); with several ground levels this is a clear error. Elevation strata are what make an idealized site profile over several holes possible, so depth-only isn't enough.
  - In elevation, top > base. A row with its top and base swapped is not drawn, and a warning names it (as for intervals, P01 §11).
  - `ranges`: `low, high, label, source`, plus an optional depth or elevation pair, handled the same way.
  - `elevation_top` and `elevation_base` are new registry columns (quantity length). They were checked against the whole registry and collide with nothing.
  - `design_lines`: `label, depth|elevation, value` (unchanged).
  - `low`, `high`, `label` and `source` are fields of an overlay table, not data columns, so they stay as they are.
- **Overlays are built for reuse.** Each overlay is a private function in a shared module (`plot/_overlays.py`). It takes the axes, the vertical reference and the display units, so P02, P06 and P09 can call it without going through `profile()`. P09 will produce `design_lines` tables in the same format.
- **Overlay templates.** Add `strata`, `ranges` and `design_lines` to the `templates:` section of `columns.yaml`, so `ak.template("strata")` gives users the exact columns. This is how we guide naming without adding classes (see "Out of scope").
- **Presets go in `config/defaults.yaml`**, as P00 planned: `hydraulic_conductivity`, `undrained_shear_strength`, `water_content` and `bulk_unit_weight`, with the values in P01 §6.
- **One unit of work.** The build commits are about 300 lines or less, in this order: presets → core scatter and axes (depth/elevation, linear/log, exclusions) → intervals and qualifiers → `marker_by` and `connect` → overlays (two or three commits) → secondary depth axis and stats box → test data and visual check.

## Out of scope
- `facet_by`, several properties side by side, trend lines, and strata built from GEOL data (P01 §15).
- P02, P06 and P09 themselves.
- **Typed overlay objects** (for example a `Strata` dataclass). Overlays stay plain DataFrames, checked against the registry with clear errors. We'll look at this again if overlays multiply in Batch 2.
- Examples, the README and the tutorial (M5).

## SPEC sections touched
- None expected. M2 implements §2.6, §3, §8.1 and §10.3 as written.
- P01 (§3, §8, §11, status) and `docs/plots/README.md` (P01 status) change in the spec and close-out commits.
- `columns.yaml` gains `elevation_top`, `elevation_base` and the three overlay templates.
