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
