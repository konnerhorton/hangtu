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
   depth trend (SI), with realistic scatter (CoV about 0.3, skewed, uneven depths, an outlier or two), not points
   close to a line; the example project's s_u is too thin for a trend (decided in review, 2026-11-04).

Also changed in this step: `docs/plots/README.md` (the P09 row and the overlays entry for representative values)
and `docs/plots/P01-property-profile.md` (P09's new name in "Related" and the design lines row).

## Plan
Draft, 2026-11-04. Five commits, each green: the tests it touches, then the CI command with `-n 3`. All on Opus:
steps 2–4 hold the plot's rules and edge cases, step 5 judges the figure against the spec, and step 1 is too
small for a session of its own. Suggest a new session after step 3.

### 1. `P01: let a plot built on profile() draw before its legend` (Opus)
A refactor, no behavior change.
- `src/hangtu/plot/_profile.py`: `_draw_profile()` gains `overlay=`, a callable
  `(ax, vertical, scale, colors, notes) -> list of legend handles`, called after the values are drawn and before
  the legend and footnote, so P09's lines, its footnote lines and its legend entries join P01's. The band's
  place under the values (spec §7) is by `zorder`, not draw order. 🟡 It also records the axes' vertical and
  value scale as `ax.ags_profile`, so a later call with `values=False` (step 4) draws in the same coordinates.
- Tests: the existing `tests/plot/test_profile*.py` pass unchanged; one test that `overlay=` is called once with
  P01's `Vertical` and `ValueScale` and its handles reach the legend.

### 2. `P09: draw representative and mean lines on a profile` (Opus)
- `src/hangtu/plot/_representative_profile.py` (new): `representative_profile()` with spec §10's signature. It
  checks `by=` (one column or None; a list is an error saying to filter or make one column), calls
  `representative()` with the judgments unchanged and `display_units=`, then `_draw_profile(color_by=by,
  stats_box=False)` with an overlay that draws, per unit with a line, from `result.design_lines(mean=True)`:
  the band (`fill_betweenx`, alpha 0.15, under the values), the mean (median) line dashed 0.8 pt and the
  representative line solid 1.5 pt, all in the unit's P01 color; and the gray style entries of §7 ("percentile
  10", "mean − 1.5 std", "mean to …").
  - `vs`: a trend defaults to `result.trend` and the other is an error naming both; a constant defaults to
    `result.vertical`, the other converted by P01's design-line rule (one ground level).
  - Edge cases (§11): a line ≤ 0 on a log axis cut and counted, a line beyond `xlim=` clipped and counted; two new
    `REASONS` in `_notes.py` (names checked against the existing ones).
  - Added in the build: `_draw_profile()` takes `cover_x=`, values its automatic x limits also cover, so a line
    beyond the values (a characteristic value below the lowest) isn't clipped unless `xlim=` is given.
  - `plot/__init__.py` exports it; `docs/site/reference/plot.md` entry (the site test requires one), and the page's
    opening sentence names it among the plots that return a result.
- Tests: `tests/plot/test_representative_profile.py` (new): criterion 1 (constant and trend, normal and
  lognormal, 1e-12 against `design_lines(mean=True)`), criterion 2, criterion 6, criterion 7 for `mean=`,
  `band=`, `by=[...]` and `vs`, criterion 9, criterion 10's US/SI call pair; the log and `xlim` rows of §11; no unit
  with a line draws values with no line entries and no error.

### 3. `P09: add the view table and the left-out footnote` (Opus)
- `_representative_profile.py`: the table at P01's stats-box place with its room rule (reusing `draw_stats_box`
  and `_room_below_data`): `result._view()` wrapped, then per unit in legend order n (with "k censored" for a
  constant), the value or top → base to 3 significant figures in the display unit, or "—" and the reason;
  `table=False` removes it. The footnote's text lines through `notes.add_text()`: "Left out of the lines: …" (a
  trend's censored and no-depth counts), "Not in the lines: …" (assumed and range counts, the kinds P01 draws
  as values), "No line: <unit> (<reason>)".
- Any field the table or footnote needs that the result lacks is added to `RepresentativeResult` with a test
  (spec decision 8 expects none).
- Tests: criteria 3, 4, 5 and 7 for `table=`.

### 4. `P09: draw a second view and draw from a result` (Opus)
- `_representative_profile.py`: `values=False` draws only the lines, band and table into `ax=`, reading
  `ax.ags_profile`; without `ax=`, or into an axes P01 didn't draw, an error. 🟡 Its footnote lines are added to
  the existing footnote, not drawn a second time.
- `src/hangtu/stats/_result.py`: `RepresentativeResult.plot(df, **kwargs)` draws the same figure through a
  shared `draw(result, df, ...)` and returns `(fig, ax)`. 🟡 The check that `df` is the result's rows reruns
  `representative()` with the result's recorded inputs and compares each group's `count` and `count_*`,
  raising for the first that differs; a `display_units=` other than the result's is an error naming both.
- Tests: criterion 7 for `values=`; criterion 8 (same artists' data from both routes; a row removed raises
  naming its group); criterion 10's `result.plot()` units error.

### 5. `P09: document the representative value profile; close out (c)` (Opus)
- `docs/site/plots/representative-profile.md` (new) with `docs/site/examples/representative-profile.py`, in the
  `nav` of `zensical.toml`; `docs/site/guides/representative-values.md` points to it.
- Visual check (criterion 11): the seeded synthetic s_u set of spec decision 9, made in the site example so it is
  reproducible; a scratch script draws `docs/plots/img/P09-us.png` (constant per unit) and `P09-si.png` (depth
  trend) from it at 100 dpi. Looked at against §2's "a good version" and the scatter rule, and fixed before the
  commit if not.
- `docs/plots/P09-representative-profile.md`: status built, the images, 🟡 marks settled or carried to §14.
- Close-out: `docs/plots/README.md` P09 row "built"; `docs/analysis/statistics.md` §2 points to P09; SPEC §12.4
  M18 "(c) done; (d) next"; the "Next" sentence in `CLAUDE.md`; the lesson check (CLAUDE.md conventions, SPEC,
  memory).

## Verification
- Each acceptance criterion mapped to a test above; line coordinates at 1e-12 against the result's own frame.
- Full CI command locally with `-n 3`; `uv sync --group docs && uv run python docs/prepare_site.py && uv run
  zensical build --clean --strict`.
- Both PNGs looked at once steps 2–4 are green, not after each change.
