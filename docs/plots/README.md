# Plot specifications

Each figure is a separate feature with its own spec file in this folder, written from [TEMPLATE.md](TEMPLATE.md). Some figures are analyses in their own right (triaxial, consolidation). Their spec covers the calculations as well as the drawing.

**Why plots come first:** plots are what users will use first, so building them first gets feedback soonest. Plot functions take ordinary pandas DataFrames with documented columns. They don't depend on the AGS ingest or the database, so they can be built, tested and tried out with data from a CSV file before the ingest exists. When the ingest lands, the ready-made datasets (`p.spt()`, etc.) simply produce DataFrames in the same shape.

---

## Shared conventions (apply to every plot unless its spec says otherwise)

### Function contract
- Signature: `ht.plot.<name>(df, *, <plot-specific args>, units=None, display_units=None, figsize=None, ax=None, **style_overrides) -> (fig, ax)`.
  - Multi-panel figures return `(fig, axs)`.
  - Plots that run an analysis also return a result object: `(fig, ax, result)`.
- With `ax=` given, the plot draws into that axes and never creates a figure. This is what makes `ht.Sheet` composition work.
- Analysis code lives in `ht.analysis.*` as plain functions, which can be called without plotting. The plot calls the analysis and draws its result.
- Every plot returns standard matplotlib objects that the user can edit afterwards.
- No global state: the house style is applied inside a context manager.

### Input data
- Input is a "tidy" DataFrame: one row per observation, using the **friendly column names** from the column registry (`depth`, `elevation`, `spt_n60`, `liquid_limit`, …). The column names a plot needs are listed in its spec.
- **Input units** are resolved as in SPEC §2.6:
  1. the `units=` argument;
  2. `df.attrs["units"]`;
  3. the column registry plus the session or project display system (Phase 2 datasets);
  4. otherwise "(units unknown)" in the label, with a warning.
- **Display units** come from `display_units=`, else `ht.settings.display_units`. Plots never convert silently without labeling.
- **Required vs optional columns:** each spec keeps the required set to the minimum needed to draw something useful. When optional columns that unlock features (`geology_unit`, `loca_id`, `ground_level`, …) are missing, the plot emits **one hint** per call listing them and what each would add. 🟡 Hints are a `UserWarning` subclass, `ht.HangtuHint`, so they can be filtered, and `ht.settings.hints = False` turns them off.
- Standard optional grouping columns: `loca_id` (exploratory hole), `geology_unit` (geology unit), `specimen_id`.

### Axes and labels
- **Label format:** `Quantity (unit)`, e.g. `Elevation (ft, NAVD88)`, `SPT N60` (counts and dimensionless values get no unit), `Liquid limit, LL (%)`. Sentence case, with the symbol after a comma where useful.
- **Depth axes** point downward (inverted), starting at 0 at the top. **Elevation axes** point upward.
- **Log axes** use decade major ticks with labeled powers (`10⁻⁶`), plus minor ticks at 2–9 without labels.
- **Limits:** extend to the next "nice" number beyond the data. Ratio quantities (N, %, k) start at zero unless the scale is log. The spec says when limits are fixed (e.g. the plasticity chart).
- **Presets** (named settings for a common quantity, e.g. `preset="hydraulic_conductivity"`) live in `config/defaults.yaml`. They set the label, quantity, scale, start-at-zero and a typical range, and any of these can be overridden per call. The typical range only sets *default axis limits* when data are sparse; real data always set the limits. Typical ranges are never used for QC (QC level 2, not yet placed, uses its own user-defined ranges).
- **Equal aspect** when both axes are the same quantity (stress–stress, e.g. Mohr circles; length–length). The spec flags this explicitly.

### Out-of-range data
- **Never drop data silently.** A point beyond a fixed axis limit is drawn **at the edge as an open marker with an arrow**, with a count noted in the legend or a footnote (e.g. "3 values > 100 shown at limit").
- **Flagged values** (refusal, NP, `<x`, `>x`) get a distinct marker, and are counted in a note when they can't be plotted at all.
- **Text in a value column** (`NP`, `dry`) has no position on the value axis: it is drawn at the axis edge at its depth, one marker shape per distinct text, with a legend entry and a count (P01 §3, §7). Unrecognized text is also warned about.

### Color and markers
- Color encodes the **geology unit** by default (the session or project palette, SPEC §3; stable across all plots). Marker shape encodes a secondary grouping (e.g. `loca_id` or test type) when requested.
- The legend sits inside the axes in a clear corner, else below the x label (P00 §11). P05 puts it below. With more than 12 entries it splits into columns, and with more than 30 it is replaced by a note.
- Color is never the only carrier of meaning that matters. Zones and lines are also labeled.

### Overlays and annotations
- Every overlay is **named, optional, and toggled by an argument** (e.g. `a_line=True`, `ranges=df`, `stats_box=True`).
- **Standard overlays available everywhere they make sense:**
  - `ranges`: user-supplied published ranges (bands);
  - `reference_lines`: user-supplied lines, as a DataFrame or a list of `(value, label)`;
  - `stats_box`: `True` shows the plot's default statistics (set in its spec); a list chooses them, e.g. `["count", "mean", "cov"]`;
  - `characteristic`: a result from `ht.stats.characteristic`;
  - `note`: free text.
- Overlays come from data and are never hard-coded: published zones (A-line, classification bands, etc.) live in `config/defaults.yaml` or in the plot module, with their source cited.

### Output
- **Default sizes are global settings**, by plot kind: `ht.settings.figure_sizes = {"default": (6.5, 4.5), "profile": (4.5, 6.0), "chart": (6.5, 3.5)}` (inches; `default` fits a Letter or A4 page with margins, `profile` is portrait, `chart` is a shorter one for bar charts). Each size is the whole figure, including any legend and footnote. A kind missing from the dict falls back to `default`. Each spec says which kind it uses. `figsize=` overrides the size for one call. With `ax=`, the size comes from the axes.
- `fig.savefig` is left to the user. The examples show PDF and PNG at 300 dpi.

---

## Draft plot list

**Status:** `idea` → `draft` (spec written) → `review` → `approved` → `built`.

A plot's close-out also adds its page to the docs site: `docs/site/plots/<name>.md`, opening with an example from `docs/site/examples/`, plus its entry in `docs/site/reference/plot.md` and the `nav` in `zensical.toml`.

Draft notes for plots that are still at `idea`, and seven proposed new plots (P24–P30), are in [`drafts/`](drafts/README.md). The proposed IDs aren't in the tables below until each one is picked up.

### Batch 1: index and in-situ plots (start here)
Data for all of these already exists in the MVP scope. P00 is the foundation the others build on.

| ID | Plot | Function | Type | Notes / dependencies | Status |
|---|---|---|---|---|---|
| P00 | **Plot framework**: house style, palette, unit-aware labels, out-of-range markers, legend rules, `Sheet` | `ht.plot.style`, `ht.Sheet` | infrastructure | Everything depends on this. Includes units for DataFrames and the column registry | [built](P00-framework.md) |
| P01 | **Property profile**: any property against depth or elevation, linear or log axis. Presets for permeability (log), undrained shear strength, moisture content, unit weight | `profile` | plot | Foundation for P02, P06 and P09 | [built](P01-property-profile.md) |
| P02 | **SPT N profile**: N or N60 against elevation or depth, refusal markers, optional per-hole lines | `spt_profile` | plot + light analysis (`ht.analysis.spt`) | P01 | [built](P02-spt-profile.md) |
| P03 | **SPT class histogram**: share of tests per class and unit, cohesionless (relative density) or cohesive (consistency) | `spt_histogram` | plot + classification (`ht.analysis.spt_class`) | P00 | [built](P03-spt-histogram.md) |
| P04 | **Plasticity chart**: USCS or BS 5930, A/U lines, zones, NP count | `plasticity_chart` | plot + classification | P00 | [built](P04-plasticity-chart.md) |
| P05 | **Grain size distribution**: curves, envelope per unit, sieve axis, D-value markers | `grain_size` | plot + analysis (Dx, Cu, Cc, gradation) | P00 | [built](P05-grain-size.md) |
| P06 | **Water content profile with Atterberg limits**: w against depth, with a PL–LL bar for each specimen | `water_content_profile` | plot | P01 | [built](P06-water-content-profile.md) |
| P07 | **Property by geology unit**: values per unit with percentile bars (or boxes), against a report's baseline range per unit; one panel or a grid of properties | `geology_unit_comparison`, `geology_unit_comparisons` | plot | P00, P01 presets | [built](P07-geology-unit-comparison.md) |

### Batch 2: laboratory analysis plots (each is a substantial analysis)
| ID | Plot | Function | Notes | Status |
|---|---|---|---|---|
| P08 | **Distribution fit**: histogram + fitted PDFs + Q-Q plot (2 panels) | `distribution_fit` (also `FitResult.plot()`) | plot + analysis (statistics) | P00; `ht.stats.fit()` (M15 (c)) | [built](P08-distribution-fit.md) |
| P09 | **Characteristic value profile**: data, mean and characteristic lines (constant or depth trend) against depth | `characteristic_profile` | plot + analysis (EC7) | P01; TODO #13 | idea |
| P10 | *Merged into P12* (stress–strain curves draw the same readings as measured stress paths) | — | ID not reused | — |
| P11 | Triaxial: **failure envelope** with Mohr-Coulomb fit, drawn as Mohr circles, s′–t or p′–q (`space=`); optional idealized drained paths | `failure_envelope` | **Equal aspect required** in all spaces; total vs effective; M11 (b) | [built](P11-failure-envelope.md) |
| P12 | Triaxial shearing: stress–strain curves and measured stress paths (s′–t, p′–q) with P11's envelope (`space=`) | `triaxial_shearing` | Needs readings during shearing, which AGS doesn't carry: a user CSV | idea |
| P13 | Consolidation: e (or strain) against log σ′v, with σ′p by Casagrande and/or other methods, Cc/Cr | `consolidation_curve` | | idea |
| P14 | Consolidation: c_v and m_v against log σ′v | `consolidation_coefficients` | | idea |
| P15 | Consolidation: settlement against √t and log t per load increment (Taylor / Casagrande fitting) | `time_settlement` | | idea |
| P16 | Compaction curve: dry density against moisture content, zero-air-voids lines | `compaction_curve` | Common in US practice; AGS CMPG/CMPT | idea |

### Batch 3: roadmap plots
| ID | Plot | Notes |
|---|---|---|
| P19 | Pressuremeter curve with moduli (E_M, unload/reload) → Hardening Soil parameters | |
| P20 | Modulus against depth from multiple sources (SPT correlation, PMT, triaxial, oedometer) | Builds on P01 |
| P21 | Simple location plan (hole positions and labels, colored by type) | Not GIS: plain x/y scatter |
| P17 | [Clogging: Thewes & Burger (2004) diagram](P17-clogging-diagram.md) | M12; built |
| P18 | Clogging: Hollmann & Thewes (2013) diagram | Not yet placed |
| P22 | CPT profiles (qc, fs, Rf, u2; SBT chart) | CPT is on the Later roadmap |
| P23 | Lateral earth pressure with depth (coefficient K and/or σ′h profile) | Probably builds on P01; scope to define |

### Suggested order
**P00 → P01 → P07 → P02 → P03 → P04 → P05 → P06**: the core index and SPT set, enough for a first release. Then P17 (M12), P08 (M15, statistics), P09 (M18, selection), P11–P12 (M11), and the rest in the milestone order of SPEC §12.4.
