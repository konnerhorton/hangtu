# M12: P17 clogging diagram

## Intent

### Goal
`ht.plot.clogging_diagram()` places fine-grained specimens on the Thewes & Burger (2004) chart of clay clogging potential for TBM drives, with plasticity index across and consistency index up, and returns each specimen's zone so a GBR or TBM specification can quote the counts ("High: 14 of 52").

### Why
- M12 is the last unit of wave 1 (SPEC §1.3, §12.4). The rest of the wave is done: vertical stress and the SPT correlations (M13), phase relations and activity (M14).
- Clogging potential is a routine input to tunnel GBRs, and the chart is drawn by hand today from the same Atterberg and water content results hangtu already joins.
- The data is in place: `p.atterberg()` gives one row per specimen with `water_content`, `liquid_limit`, `plastic_limit`, `plasticity_index`, `non_plastic` and `consistency_index`, and `ht.analysis.plasticity()` adds PI and Ic to a CSV table. M12 adds no data and no new analysis of Ic.

### Constraints
- **Axes (TODO #21, settled):** x is `plasticity_index`, y is `consistency_index`, as in the paper. The draft's working layout (LL against Ic) was wrong and its zone polygons are not used.
- **Zones come from the paper, not from memory.** Each zone's coordinates are checked against the published figure in the spec step and kept in a config file with the citation (as `config/plasticity_systems.yaml` does for P04). Only the boundary values and the citation are published, not the figure.
- Plot contract (SPEC §3, `docs/plots/README.md`): a plot that runs an analysis returns `(fig, ax, result)`; styling in a context manager; legend and sizes per P00.
- Never drop data silently (SPEC §3): Ic < 0 (wetter than the liquid limit, common in soft clays), Ic or PI beyond the axes, NP specimens, and specimens missing w or a limit are drawn at the edge or counted in the footnote, each distinct.
- Zones are labeled with text, not told apart by color alone (`docs/plots/README.md`).
- Nothing converts: PI is a percentage and Ic is dimensionless.

### Out of scope
- The Hollmann & Thewes (2013) diagram (P18), which adds a gradation screen first. Not yet placed (SPEC §1.3).
- Any change to how Ic is computed or how w is paired with LL and PL (M7, M8).
- Clogging from mineralogy, cutterhead design or conditioning agents: the chart is a screen on index properties only, and the docstring says so.

### SPEC sections touched
- §12.4: M12 marked done at close-out; §1.3's wave 1 row is then complete.
- `docs/plots/drafts/P17-clogging.md` is promoted to `docs/plots/P17-clogging.md` in the spec step, with the corrected axes and verified zones.
- `docs/TODO.md` #21 is resolved in the spec step, once the zone coordinates are checked.
- New config file for the zones; registry `used_by` for `plasticity_index` gains P17.

### Proposed (for review)
1. 🟡 **The input is `p.atterberg()` or any table with w, LL and PL (or PI).** Ic is computed by `ht.analysis.plasticity()` when the column is absent, never by a second formula.
2. 🟡 **`result` is a DataFrame**, one row per input row, with `clogging_zone` (the zone's name, or blank with the reason it couldn't be placed). A new registry name, checked against the registry in the spec step.
3. 🟡 **`zones=` takes a user table** in the same shape as the config, so a variant from another source (such as the draft's LL-based layout) can be drawn without being built in.
4. 🟡 **Color by `geology_unit`** by default, like P04.

## Spec
The feature spec is [`docs/plots/P17-clogging-diagram.md`](../plots/P17-clogging-diagram.md), promoted from the draft. What changed from the intent, and why:

1. **The zone is an analysis, `ht.analysis.clogging_potential()`, and the plot returns `(fig, ax)`.** This replaces intent proposal 2's `(fig, ax, result)`. P04 set the pattern: `plasticity()` adds the classes and `plasticity_chart()` draws them. It also keeps "every analysis is a plain function on a DataFrame" (CLAUDE.md), so a CSV user gets the zones without a figure. The column is `clogging_potential` (the paper's term), checked against the registry: no collision.
2. **Zones live in `config/clogging_methods.yaml`**, read by both the analysis and the chart, keyed by `method=`, so a second source (P18) is a new key, not a new function.
3. **A point on a shared boundary takes the higher potential** 🟡, so a borderline specimen is never reported as the safer one.
4. **Specimens beyond the axes are classified by their true (PI, Ic)** and drawn at the edge. Ic < 0 is common in soft clays, so the bottom edge will often carry points.
5. **`zones=` has the shape of P04's `regions=`** (`label, plasticity_index, consistency_index`), with the zones listed from low to high potential. No new column for the ranking.
6. **The rest of the diagram is "low"; beyond the axes is "outside the diagram"** (review, 2026-10-29). The paper's chart covers PI 0–70 and Ic 0.3–1.5 only, so a specimen beyond it gets a blank `clogging_potential` rather than a zone the figure doesn't show. 🟡 The extension past the axes is hangtu's call, not the paper's.

### Names (registry)
- New column `clogging_potential`: text, the zone name. `used_by: [P17]`.
- New template `clogging_zones: [label, plasticity_index, consistency_index]`.
- `plasticity_index` and `consistency_index` gain P17 in `used_by` (`consistency_index` has it already).

### Golden values
Ic = (LL − w) / (LL − PL), from `plasticity()`:

| # | w | LL | PL | PI | Ic | `clogging_potential` | Why |
|---|---|---|---|---|---|---|---|
| 1 | 30 | 60 | 25 | 35 | 30 / 35 = 0.857 | high | inside PI 20–70, Ic 0.75–1.3 |
| 2 | 8 | 50 | 20 | 30 | 42 / 30 = 1.400 | medium-high | inside PI 20–70, Ic 1.3–1.5 |
| 3 | 20 | 35 | 20 | 15 | 15 / 15 = 1.000 | medium | left strip, PI 10–20 |
| 4 | 32 | 60 | 20 | 40 | 28 / 40 = 0.700 | medium | bottom strip, Ic 0.6–0.75 |
| 5 | 20 | 40 | 20 | 20 | 20 / 20 = 1.000 | high | on PI = 20, medium against high: the higher |
| 6 | 8 | 60 | 20 | 40 | 52 / 40 = 1.300 | high | on Ic = 1.3, medium-high against high: the higher |
| 7 | 30 | 60 | 20 | 40 | 30 / 40 = 0.750 | high | on Ic = 0.75, medium against high: the higher |
| 8 | 36 | 60 | 20 | 40 | 24 / 40 = 0.600 | medium | on medium's outer edge |
| 9 | 20 | 28 | 20 | 8 | 8 / 8 = 1.000 | low | left of medium, PI < 10 |
| 10 | 8 | 40 | 20 | 20 | 32 / 20 = 1.600 | blank | Ic > 1.5: outside the diagram; drawn at the top edge |
| 11 | 50 | 40 | 20 | 20 | −10 / 20 = −0.500 | blank | Ic < 0.3: outside the diagram; drawn at the bottom edge |
| 12 | 25 | 100 | 25 | 75 | 75 / 75 = 1.000 | blank | PI > 70: outside the diagram; drawn at the right edge |
| 13 | 30 | 30 | 30 | 0 | blank | blank | PI = 0: not drawn; counted |
| 14 | 25 | NP | NP | blank | blank | blank | NP: not drawn; counted |
| 15 | 31 | 40 | 20 | 20 | 9 / 20 = 0.450 | low | below medium, Ic < 0.6 |
| 16 | 34 | 40 | 20 | 20 | 6 / 20 = 0.300 | low | on low's outer edge (the bottom axis) |

Rows 1–16 together: zone counts "High: 4 · Medium-high: 1 · Medium: 3 · Low: 3 · outside the diagram: 3 of 14 specimens", plus the PI = 0 and NP lines (rows 13–14 can't be placed). Row 8 also checks the low–medium boundary: medium, the higher. Tolerance 1e-9: the values are exact quotients.

### Acceptance criteria
1. `clogging_potential()` returns every input row in order, with `plasticity_index` and `consistency_index` as `plasticity()` gives them and `clogging_potential` per the golden table.
2. Each zone's polygon, read back from the drawn patches, matches `config/clogging_methods.yaml` vertex by vertex, and the config matches P17 §4's table (checked against the paper, 2026-10-29). The axes are 0–70 and 0.3–1.5.
3. A grid of points over the axes: the zone each is drawn in matches its `clogging_potential`.
4. A point on a shared boundary is given the higher of the two zones (rows 5–8), and a point on the diagram's edge is in the zone (row 16).
5. Ic below 0.3, Ic above 1.5 and PI above 70 are drawn at the edge with an arrow, counted in the footnote, and classified by their true values: outside the diagram (rows 10–12).
6. NP, PI = 0, and blank w, LL or PL are each counted on their own footnote line and not drawn.
7. The zone counts line matches `clogging_potential().value_counts()`, including "outside the diagram".
8. Every zone has a text label inside its polygon.
9. `zones=` from a DataFrame and from a CSV path replaces the built-in zones in both functions; a zone with fewer than three vertices is an error naming it.
10. No `water_content` column is an error naming it and `p.atterberg()`.
11. Renders with `ax=` into a `Sheet` panel, leaves `rcParams` unchanged, and is the same figure for US and SI.
12. Docstrings follow the checklist in `docs/drafts/parameters/TEMPLATE.md` (equation, inputs, validity, source); reference entries in `docs/site/reference/plot.md` and `analysis.md`; a page at `docs/site/plots/clogging-diagram.md` with an example; `docs/plots/img/P17.png` from the example project, looked at.

## Plan
P04's pattern: the classification is an analysis, the zones are one config file both functions read, and the plot returns `(fig, ax)`. Each step is one commit, with ruff and pytest green.

1. **`refactor: move polygon tables out of P04's regions module`.** The analysis can't import from `hangtu.plot`, so the vertex-table reading moves to `src/hangtu/_polygons.py`:
   - `Polygon` (label, vertices, `centroid()`), moved from `_regions.Region`;
   - `read_polygons(table, fields, what, start)`, the reader, with the axis columns and error wording as arguments;
   - `contains(vertices, points, tolerance)`: even-odd ray casting, with a point within 1e-9 of an edge counted as inside.

   `plot/_regions.py` keeps `draw_regions` and P04's wording, so `tests/plot/test_plasticity_regions.py` passes unchanged. New `tests/test_polygons.py`: inside, outside, on an edge, on a vertex, an L-shape, and the centroid of an L.
2. **`M12: clogging_potential(), the zones and their registry names`.**
   - `config/clogging_methods.yaml`: `thewes_burger_2004`, with its source, the `axes` box (0–70, 0.3–1.5), and the zones low → high (`name`, `vertices`, optional `label_at`).
   - `analysis/_clogging.py`:
     - runs `plasticity()` for PI and Ic;
     - raises an error when `water_content` is missing;
     - places rows by testing zones from highest to lowest, so a boundary goes to the higher zone (decision 3);
     - leaves rows beyond the box blank (decision 6);
     - warns once with the blank rows counted by reason, as `clay_activity()` does. The plot uses an internal `_place()` that doesn't warn, since its footnote counts them. Spec §4 gets a sentence on the warning.
   - Docstring per the checklist in `docs/drafts/parameters/TEMPLATE.md`.
   - Registry: the `clogging_potential` column, the `clogging_zones` template, and P17 in `plasticity_index.used_by`.
   - The export and the entry in `docs/site/reference/analysis.md`.
   - Tests in `tests/analysis/test_clogging_potential.py`: the 16 golden rows (criteria 1, 4); rows unchanged; `zones=` from a DataFrame and from a CSV, and a two-vertex error (9); no `water_content` (10); the warning; the config against spec §4 (2).
3. **`M12: draw the clogging diagram's zones`.**
   - `plot/_clogging_diagram.py` with the spec §10 signature, drawing the empty chart: the axes and ticks, the zone fills (green → yellow → orange → red in table order), the outlines, and the labels on a white bbox.
   - Low and medium are L-shapes, so the config's `label_at` places their labels (low (35, 0.45), medium (45, 0.675)). A user zone's label goes at its centroid when that is inside the polygon, else at its vertex mean. Spec §8 changes to match.
   - The export and the entry in `docs/site/reference/plot.md`.
   - Tests in `tests/plot/test_clogging_diagram.py`: the patches against the config (2); each label inside its zone (8); `zones=`; no `rcParams` change; `ax=` into a `Sheet` panel; US and SI identical (11).
4. **`M12: specimens, edge markers and zone counts on P17`.**
   - Scatter by `color_by` and the legend, as P04 does; `edge_markers()` for points beyond the box.
   - New footnote reasons `zero_plasticity` and `no_water_content`. NP, blank values and points beyond the box reuse the existing reasons.
   - The zone counts line, from `_place()`.
   - `labels=`, `note=`, "No data" and the `geology_unit` hint.
   - Tests: the edge markers and footnote counts (5, 6); the zone line against `value_counts()` (7); a 50 × 50 grid where each point's drawn zone equals its `clogging_potential` (3). Split if past about 300 lines.
5. **`M12: close out`.**
   - `docs/site/examples/clogging-diagram.py`, `docs/site/plots/clogging-diagram.md` and the `nav` entry.
   - `docs/plots/img/P17.png` at 100 dpi, looked at.
   - Statuses: P17 → built in its spec and `docs/plots/README.md`; SPEC §12.4 M12 done; the CLAUDE.md status paragraph; TODO #21 closed or reduced to what's still missing.
   - Before committing: `prepare_site.py` and `zensical build --clean --strict`.
   - Each acceptance criterion reported as met or not.
