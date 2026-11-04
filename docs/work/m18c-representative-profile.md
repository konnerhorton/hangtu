# M18 (c): representative value profile (P09)

## Intent
M18 is selection, stage D (SPEC §1.3, §12.4), in four units (`docs/work/m18a-refusals.md`): (a) SPT refusals
(done), (b) representative values (done), **(c) this unit, P09**, (d) sources compared, the selection as a
judgment, and the Mohr–Coulomb set.

### Goal
- One plot shows a parameter's values against depth or elevation with the representative value that
  `ht.stats.representative()` computed for each geology unit, constant or as a line with depth, beside the mean
  it came from, so a reviewer can see in one figure what was selected, from which values, and how cautious it is.
- The figure states the view and its judgments (method, side, distribution, the V_X case, θ and L, k or the
  percentile) and n per unit, so it can go in a design report or a calculation package without a separate table
  to explain it.

### Why
- **Today it takes two calls and the figure doesn't explain itself.** `representative(...).design_lines()` passed
  to `ht.plot.profile(design_lines=)` draws the lines (M18 (b), decision 10), but the figure doesn't say which
  view a line is or which judgments made it, shows no spread between the mean and the cautious line, and shows
  nothing of the values the trend left out (censored values, M18 (b) spec decision 8) or of the units that got no
  line (too few values). A reviewer reading a design report needs all four.
- **The figure is where a representative value gets checked.** Whether a depth trend is believable, whether a
  constant is too low at depth, whether one unit is really two: engineers judge these by eye on a profile (the
  M18 (b) intent: "depth trends are common and done by eye"). M18 (d) compares sources the same way.
- **P08 is the precedent.** `ht.plot.distribution_fit()` runs `fit()` and draws its result, returning
  `(fig, axs, result)`, with `FitResult.plot()` as the shortcut (P08 spec). P09 does the same for
  `representative()`.
- **What depends on it:** M18 (d) draws the sources it compares and the selection on this figure or on its parts.

### Scope
- **The function:** 🟡 `ht.plot.representative_profile(df, *, value=, by=, <representative()'s arguments>,
  <P01's arguments>) -> (fig, ax, result)`, and `RepresentativeResult.plot()` as the shortcut that draws an
  existing result. 🟡 The name follows M18 (b)'s intent decision 1 (`representative`, not `characteristic`), so
  P09's working title "characteristic value profile" changes too.
- **Built on P01:** the values are drawn by `ht.plot.profile()` with its conventions (colors by geology unit,
  flags, out-of-range values at the edge, strata, water level, US and SI). P09 adds what P01 doesn't have:
  - the representative line per unit and, 🟡 on by default, the mean (or median) line it came from;
  - 🟡 a shaded band between them, so the size of the reduction is visible;
  - values left out of a trend (censored) drawn distinctly and counted, and units without a line named with
    their reason, in the footnote;
  - a note giving the view and its judgments, and n per unit (in the legend label or a small table, 🟡 for the
    spec).
- **One view per call**, as `representative()` (M18 (b), spec decision 1). Every judgment is a required argument
  passed through; the plot adds none (SPEC §4).
- **Visual check:** `docs/plots/img/P09-us.png` and `P09-si.png` from realistic data, a constant view and a
  depth trend.
- Docs: the plot spec `docs/plots/P09-representative-profile.md`, the site page and example, and the
  `docs/site/reference/plot.md` entry.

### Constraints
- Plot contract (`docs/plots/README.md`, CLAUDE.md): styling in a context manager, `ax=` draws into the axes,
  units resolved as in SPEC §2.6, `display_units=` converts the data and the lines together.
- SPEC §5: the plot reads the result and computes nothing of its own ("one calculation, many views"), so the
  lines on the figure and `result.to_frame()` can't disagree. Sources mixed in a group: the plot says "mixes
  sources" instead of raising, unless `representative()` raises first (🟡 the spec says which governs).
- Never drop data silently: values left out of the calculation (bands, non-plastic, assumed, censored in a trend)
  are still drawn by P01, or counted in the footnote when they can't be.
- No new dependencies.

### Out of scope
- **Several views on one figure** (a characteristic line beside a percentile). A second call with `ax=` can add
  one; 🟡 whether that redraws the values is for the spec. A comparison of views as a feature waits for M18 (d).
- **Sources compared by depth or unit, and the selection as a judgment:** M18 (d).
- **Confidence or prediction bands as their own overlay** (the full interval around a trend, both sides). The
  shaded band is between the mean and the representative line only; the interval curves are already in the
  result if a later unit wants them.
- **Moving-window statistics** (P01's "later" list): not a representative value.
- **New statistics:** anything the figure needs that `RepresentativeResult` doesn't keep is added to the result
  in this unit's build, with a test, not computed in the plot.

### SPEC sections touched
- SPEC §12.4: M18 (c)'s status.
- `docs/plots/README.md`: the P09 row (name, function, status) and the "Overlays" list, whose `characteristic`
  entry still names `ht.stats.characteristic`, which M18 (b) built as `representative()`.
- `docs/plots/P01-property-profile.md`: the "Related" row and the design lines row name P09 by its new name.
- `docs/analysis/statistics.md`: `representative()` points to its plot.
- `CLAUDE.md`: the "Next" sentence at close-out.

## Spec
The feature spec is the plot spec, [`docs/plots/P09-representative-profile.md`](../plots/P09-representative-profile.md)
(draft, 2026-11-04). Its 🟡 items are this step's proposals:
1. **`by=` is one column or none**, and is P01's `color_by`, so a line and its values share a color.
2. **The table** replaces P01's stats box: the view in full (`result._view()`), then n and the value (or top →
   base) per unit, or "—" and the reason. `stats_box`, `design_lines` and `color_by` aren't offered.
3. **Band under the values**, in the unit's color, so no value is hidden; `mean=` and `band=` are independent.
4. **`values=False`** draws a second view into an existing `ax=` without redrawing the values (intent, "Out of
   scope").
5. **`RepresentativeResult.plot(df, ...)` takes the data again**, because the result keeps statistics, not rows,
   and P01 draws every row; it checks the rows give the result's groups and counts, else raises.
6. **Mixed sources:** `representative()` raises, and that governs, as in P08.
7. **Units:** `display_units=` goes to both calls; `result.plot()` draws in the result's units and raises for
   another.
8. **No new fields on the result**: the lines, view and counts are already kept.
9. **Visual check data:** lab data, a seeded synthetic s_u set made in the image script, a constant (US) and a
   depth trend (SI); the example project's s_u is too thin for a trend (decided in review, 2026-11-04).

Also changed in this step: `docs/plots/README.md` (the P09 row and the overlays entry for representative values)
and `docs/plots/P01-property-profile.md` (P09's new name in "Related" and the design lines row).
