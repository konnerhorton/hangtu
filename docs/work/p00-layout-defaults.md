# P00: layout defaults, with the legend inside, citation names and shorter charts

## Intent
**Goal:** the default plots give the data most of the figure. The legend doesn't take width from the axes, legend
entries are short enough to read, and each kind of plot has a size that suits its shape.

**Why:** the published figures show the plotting area squeezed (evidence, `docs/site/img/generated/`, 2026-10-26):
- `correlations.png`, `correlations-clay.png`: the profile is `4.0 + 1.5` in wide (`LEGEND_WIDTH`,
  `src/hangtu/plot/_profile.py:57`), and the legend entries `effective_friction_angle_hatanaka_uchida_1996` and
  `undrained_shear_strength_terzaghi_peck_1967` fill all of the extra 1.5 in. The axes are about 2 in wide and 6 in
  tall, with most of their area empty. The plot reads as "too tall" mostly because it is so narrow.
- The legend entry is the raw `correlation_name`. It repeats the quantity the x label already gives, and the part
  a reader needs, the authors and year, is at the end.
- `spt-histogram.png`: P03 uses `default` (6.5 × 4.5 in). Six bars don't need 4.5 in of height.
- The same holds for any long group name, such as a geology unit name from user data: on the right, each character
  of the longest entry is width taken from the axes.

**SPEC and docs touched:** SPEC §3 (house style: "legend outside right"); P00 §3 (`figure_sizes` default), §9 (the
footnote "in the narrow column beside the axes"), §11 (legend), §14 (legend tests); plots README ("Color and
markers" legend bullet, "Output" sizes); P01 §5 (default size); P03 §5 (default size); P04 §5 (the note on white
space with the legend on the right); P07 (single-panel legend placement). P05 keeps its bottom legend, so its spec
is unchanged.

### Decisions (discussion, 2026-10-26)
1. **The legend goes inside the axes when a corner is clear, else below the x label.** It is never on the right by
   default. The choice is deterministic: a fixed corner order, and the first corner with nothing in the way wins.
   matplotlib's `loc="best"` was rejected because it can still cover data and its choice is hard to predict or
   test. "Always below" was rejected because it costs height on every plot, including the many with an empty
   corner.
2. **Correlations are named by their citation in legends**, e.g. "Hatanaka & Uchida (1996)": the first source's
   `cite` in `config/correlations.yaml`, overridable by an optional `label:` per entry. Sentence case of the name
   was rejected because it is still long and repeats the axis label. A required hand-written label for every entry
   was rejected as upkeep with no gain while the citation is unique.
3. **New size kinds, with fixed totals.** `profile` becomes the size of the whole figure, legend included, and a
   new `chart` kind is shorter for bar charts. The height doesn't follow the data, because figures that sit side by
   side in a report, hole by hole, should be the same size.

### Out of scope
- Subscripts in labels (`s_u` → s<sub>u</sub>, TODO #43).
- A general `legend_labels=` argument for renaming any group. Users can still edit the returned legend.
- The P07 grid's shared figure legend, which already sits below the panels.
- Axis label wrapping. With the legend out of the way, an x label as long as "Undrained shear strength, s_u (psf)"
  fits a 4.5 in profile. 🟡 Revisit if a registry label doesn't fit.
- Changing depth limits for sparse data (P00 §8 keeps 0 at the top).

## Spec
The feature specs are P00 and the plot specs. This section lists what changes in each, then the acceptance
criteria.

### Changes
**P00 §11, Legend** (replaces the first bullet's placement sentence):
- `add_legend(..., where=)` takes `"auto"` (the default), `"inside"`, `"bottom"` or `"right"`.
- **`"auto"`:** the legend goes inside the axes, in the first clear corner in the order upper right, upper left,
  lower right, lower left. If no corner is clear, it goes below the x label, as `"bottom"`. 🟡 One order for every
  plot. Trying the deeper corners first on an inverted depth axis was considered and dropped, since the first test
  is often near the surface and the deepest one at the bottom, so neither end is reliably empty.
- **Clear** means the legend's box, padded by 4 pt, overlaps none of:
  - a marker (scatter offsets, padded by the marker radius);
  - a line (any segment crossing the box, not just its vertices);
  - a data patch;
  - a text, an annotation or a text box (the stats box, notes, strata, water level and range labels, P04 zone
    labels).

  **Background fills don't count:** artists below `_layers.LINES` (strata bands, user regions, range bands, P05
  envelopes), plus the axes background. A legend over a shaded band is readable. A legend over a point is not.
- The test runs after the figure's layout engine has run, so the axes have their final size.
- **`"inside"`:** the same corners, with no fallback. If no corner is clear, the corner with the fewest obstacles
  wins, ties going to the earlier corner.
- **`"right"`:** today's placement, unchanged, including `offset=` for a secondary axis.
- **`"bottom"`:** unchanged (P05).
- **Frame:** an inside legend gets a white frame at 0.85 alpha with no edge, so gridlines don't run through the
  text. 🟡 The frame values are proposed.
- `add_legend` returns the legend and the placement it chose, and `Notes.render` takes that placement:
  - legend on the right: the footnote goes below it, as now;
  - legend inside, or no legend: the footnote goes below the x label;
  - legend below: the footnote goes below the legend.
- **Long entries:** an entry longer than 28 characters wraps at word boundaries, onto as many lines as it needs,
  with `textwrap`. It is never shortened, so the legend never hides a name. 🟡 28 characters is proposed: about
  1.6 in at 8 pt, which fits an inside legend on a 4.5 in profile.
- The 12-row columns and the 30-entry note are unchanged.
- **Public argument:** every plot with a legend takes `legend="auto" | "inside" | "bottom" | "right" | False`. `False`
  draws no legend, while the footnote still renders below the x label (no data is hidden). `True` is `"auto"`.
  - Plots: `profile`, `spt_profile`, `water_content_profile`, `spt_histogram`, `plasticity_chart`,
    `geology_unit_comparison`, and `grain_size` (which defaults to `"bottom"`, as P05 §5).
  - `geology_unit_comparisons` (the grid) has no `legend=`. Its shared legend stays below the grid.
- **With `ax=`:** the corner is chosen against the axes at plot time. A figure resized afterwards can move data
  under the legend. The docstring says to pass `legend="bottom"` or `"right"` in that case.

**P00 §9:** the footnote "sits below the legend, or below the x label when the legend is inside". The "narrow
column" wording changes: lines are still one per count.

**P00 §3 and the plots README, "Output":** `figure_sizes` defaults to `{"default": (6.5, 4.5), "profile": (4.5, 6.0),
"chart": (6.5, 3.5)}`.
- Each size is the **whole figure**, including any legend and footnote.
- A kind missing from a user's dict falls back to `default`, as `grid` already does in P07. `default` stays
  required.
- 🟡 The numbers are proposed, to be checked against the regenerated figures in the close-out.

**Plots README, "Color and markers":** "The legend sits inside the axes in a clear corner, else below the x label
(P00 §11). P05 puts it below. With more than 12 entries …" (the rest as now).

**SPEC §3, house style:** "legend inside the axes when a corner is clear, else below" in place of "legend outside
right".

**Per plot:**
- **P01 §5:** default size is `profile`, 4.5 × 6.0 in in total. Remove "plus legend width". The legend and footnote
  move right to clear a secondary depth axis only when `legend="right"` (P01 §6, secondary axis).
- **P03 §5:** default size is `chart` (6.5 × 3.5 in).
- **P04 §5:** drop the note on white space from the right-hand legend. With equal aspect and the legend inside or
  below, the box fills more of the figure. The zone labels and A-line usually block every corner, so the legend
  usually goes below. That is expected.
- **P07, single panel:** `"auto"` like the others. The count labels outside the right spine no longer push the
  legend, and `offset=` applies only with `legend="right"`.
- **P02, P06:** inherit P01.

**Correlation display names** (`docs/work/m13b1-spt-framework.md` Decision 6 holds; this adds to the entry format):
- `config/correlations.yaml` entries may have `label:`. The header comment documents it.
- `ht.analysis.correlations.describe(name)` returns `label`: the entry's `label:`, else `sources[0].cite`. The
  docstring says it is the legend text.
- In P01, P02 and P06, a group value of `color_by` or `marker_by` that is a correlation name in the catalog is
  shown by its label, in the legend only. The data, the color assignment, the session palette and the legend
  order are unchanged. Other values show as they are.
- Within one target column, labels are unique. Today's seven entries already are, so none needs `label:`.

### Acceptance criteria
1. A profile whose points all lie in the lower half of the axes puts the legend inside at the upper right, and the
   footnote below the x label.
2. With a point in each corner region, `"auto"` puts the legend below the x label, and `"inside"` puts it in the
   corner with the fewest obstacles.
3. A line whose two vertices lie outside the upper-right corner, but which crosses it (the P04 A-line shape), blocks
   that corner.
4. A strata band behind the upper-right corner doesn't block it, while the strata label in that corner does.
5. The P01 stats box at the lower left blocks that corner.
6. P03 bars are data: a bar reaching into a corner blocks it. (The bars must be drawn at a data layer: see the
   plan.)
7. `legend="right"` gives today's legend position, within 1 pt, including with `secondary="depth"`.
8. `legend=False` draws no legend, the footnote still renders, and `ax.ags_notes` is unchanged.
9. An invalid `legend=` raises `HangtuError` naming the allowed values.
10. `profile()` without `figsize` returns a 4.5 × 6.0 in figure with any legend, and `spt_histogram()` a 6.5 × 3.5
    in one.
11. `ht.settings.figure_sizes = {"default": (6, 4)}` (no `profile` or `chart`) gives a 6 × 4 in profile and
    histogram, with no error.
12. The legend texts of a profile colored by `correlation_name` from the two φ′ correlations are
    "Hatanaka & Uchida (1996)" and "Kulhawy & Mayne (1990)", and its colors match those of a call before this
    change.
13. `describe("undrained_shear_strength_stroud_1974")["label"] == "Stroud (1974)"`. A `label:` in the entry wins.
14. A catalog test checks that labels are unique within each target column.
15. A 40-character geology unit name, "Weathered sandstone and siltstone residuum", gives a two-line legend entry
    containing every word, and nothing is truncated.
16. No plot changes `rcParams` (P00 §14), including during the corner search.
17. **Visual check:** the regenerated `docs/plots/img/P01*.png`, `P02.png`, `P03.png`, `P04.png`, `P06-*.png`,
    `P07-*.png` and the site's `correlations*.png` and `spt-histogram.png` are looked at. Each legend is readable,
    covers no data, and the axes are visibly wider in the profiles. P05 is unchanged.
