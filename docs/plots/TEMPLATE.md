# PXX — <Plot name>

<!--
How to use this template:
- Copy it to docs/plots/PXX-short-name.md and fill in each section.
- Delete guidance comments as you go. Write "n/a" rather than deleting a section, so it's clear it was considered.
- Shared conventions (function contract, label format, out-of-range policy, colors, legends) are in docs/plots/README.md.
  Only record *deviations* from them here.
-->

| | |
|---|---|
| **ID / function** | PXX · `ak.plot.<name>()` (+ `ak.analysis.<name>()` if it includes an analysis) |
| **Status** | idea / draft / review / approved / built |
| **Type** | plot · plot + light analysis · analysis |
| **Target version** | v0.1 / v0.2 / … |
| **Depends on** | e.g. P00, P01 |
| **Related** | other plot specs, SPEC sections, TODO items |

---

## 1. Purpose
<!-- What engineering question does this figure answer? Who looks at it, and where does it end up (GIR, design report, internal check)? One or two short paragraphs. -->

## 2. Reference figure
<!-- A sketch (ASCII is fine) or an image in docs/plots/img/PXX-*.png, or a citation to a published example
     ("as Fig. 4 in Hollmann & Thewes 2013"). Describe what makes a *good* version of this plot. -->

```
  (ASCII sketch)
```

## 3. Input data
<!-- One row per what? (per test, per specimen, per curve point, per stage). Use friendly column names from the column registry.
     "Typical range" = what most real data falls in (drives default axis limits).
     "Valid range" = physical or hard bounds (outside → QC flag / out-of-range marker). -->

**Row grain:** one row per …

| Column | Description | Quantity kind | Canonical unit | US display | SI display | Req.? | Typical range | Valid range | AGS source | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `depth` | Test depth | length | m | ft | m | ✔ | 0–50 m | ≥ 0 | derived (SPEC §8.2) | |
| | | | | | | | | | | |

**Grouping columns used:** `geology_unit` (color) · `loca_id` (marker / lines) · `specimen_id` · …

**Value flags handled:** refusal / NP / `<x` / `>x` / none. Say how each is shown.

**Minimum data:** e.g. "≥ 1 point" or "≥ 3 points per curve; otherwise the curve is skipped and noted".

## 4. Analysis / calculations
<!-- n/a for pure plots. Otherwise this is the core of the spec: formulas, methods with references, assumptions, options, and what the result object contains.
     Every number drawn on the plot that isn't raw data must be defined here. -->

- **Function:** `ak.analysis.<name>(df, ...) -> <Result>`
- **Method(s):**
  1. … (formula, reference)
- **Options:** e.g. `method="casagrande" | "becker"`
- **Result object fields:** name · description · unit
- **Assumptions and limitations:**
- **Edge cases:** e.g. too few points, non-monotonic data, division by zero

## 5. Figure layout
- **Panels:** single / n panels (arrangement, shared axes)
- **Default size:** W × H in (see the README default; justify any deviation)
- **Orientation:** landscape / portrait

## 6. Axes
<!-- One block per axis, including secondary axes. -->

| | X axis | Y axis | Secondary (if any) |
|---|---|---|---|
| Quantity / column | | | |
| Label (US) | | | |
| Label (SI) | | | |
| Scale | linear / log | | |
| Direction | normal / inverted | | |
| Limits rule | auto-nice / fixed [a, b] / starts at 0 / symmetric / from config | | |
| Default limits (typical data) | | | |
| Major / minor ticks | | | |
| Gridlines | major / minor / none | | |

**Range constraints:**
- [ ] Equal aspect (1:1 data scale), e.g. Mohr circles, s′–t paths
- [ ] Axes share limits with another panel
- [ ] Fixed limits regardless of data (e.g. plasticity chart 0–100 / 0–60, extendable)
- [ ] Other: …

## 7. Data marks
<!-- How the data are drawn. -->

| Series | Mark | Color by | Marker by | Size / width | Legend entry | Notes |
|---|---|---|---|---|---|---|
| Main data | scatter / line / step / bar / curve | `geology_unit` | `loca_id` (optional) | | ✔ | |
| Flagged values | open marker / arrow at edge | | | | ✔ with count | |

**Draw order (bottom → top):** zones → reference lines → data → fitted lines → annotations.

## 8. Overlays and annotations
<!-- Everything drawn that isn't the raw data: reference lines, zones, fitted results, labels, text boxes, user overlays.
     Each one is named, has an argument to toggle it, a default, a data source, and a style. -->

| Overlay | Argument | Default | Source of definition | Style | Notes |
|---|---|---|---|---|---|
| e.g. A-line | `a_line=` | on | Casagrande (1948); config | solid black 0.8 pt | labeled on the line |
| Published ranges | `ranges=` | off | user DataFrame or CSV | translucent band | |
| Stats box | `stats_box=` | off | `ak.stats.describe` | text box, upper right | |
| Analysis result | | | §4 result object | | e.g. σ′p construction lines |

**User-supplied overlay format:** columns and units expected for any user data (e.g. `ranges`: `group, low, high, source`).

## 9. Units behavior
- What changes between US and SI display (axes, tick values, secondary axes, overlay definitions)?
- Are any overlays defined in a particular unit system (e.g. a zone published in kPa)? Convert them, and keep the source unit in the citation.
- Quantities that are never converted (e.g. N, particle size in mm):

## 10. API
```python
def <name>(
    df: pd.DataFrame,
    *,
    # data selection / mapping
    value: str = "...",
    vs: Literal["depth", "elevation"] = "elevation",
    color_by: str | None = "geology_unit",
    # overlays
    ...,
    # common
    ax: Axes | None = None,
    display_units: Literal["US", "SI"] | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```

**Example:**
```python
fig, ax = ak.plot.<name>(df, ...)
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input | Empty axes with a "No data" note; no error |
| Single point / single specimen | |
| Missing required column | Clear error naming the column and its expected unit |
| Values outside the valid range | Out-of-range marker + note (README policy) |
| Too many groups for the legend | README legend rules |
| Mixed units / missing units | |
| Duplicates | |

## 12. Acceptance criteria and tests
- **Golden values:** calculations checked against hand calculations or published worked examples (cite them).
- **Visual checks** (manual review list): e.g. "A-line passes through (20, 0) and (50, 21.9)".
- **Automated:** it renders; labels include units; overlay toggles work; `ax=` composition works; US and SI give the same figure apart from labels and ticks.
- **Test data:** which synthetic or public dataset is used.

## 13. References
<!-- Standards, papers and textbooks for every method, zone and classification used. -->
-

## 14. Open questions
-

## 15. Future enhancements
<!-- Things deliberately left out of this version. -->
-
