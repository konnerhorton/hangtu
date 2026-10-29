# P00 — Plot framework

| | |
|---|---|
| **ID / module** | P00 · `ht.settings`, units functions, column registry, `ht.plot` helpers, `ht.Sheet` |
| **Status** | built |
| **Type** | infrastructure (no user-facing plot) |
| **Milestone** | M1 (0.1.0) |
| **Depends on** | M0 scaffolding |
| **Related** | SPEC §2 (units), §3 (plotting), §10.3 (registry); plots README (shared conventions); registry [`src/hangtu/columns.yaml`](../../src/hangtu/columns.yaml); aliases [`src/hangtu/units/aliases.yaml`](../../src/hangtu/units/aliases.yaml) |

This spec defines the *implementation* of the shared conventions in the plots README. Where the two overlap, the README states the rule and this spec says how it is built and tested.

---

## 1. Purpose and scope
Everything P01–P07 need, so that each plot spec only describes its own drawing. M1 is done when the acceptance criteria in §14 pass and a dummy plot composes on a `Sheet`.

**In scope:** settings · units for DataFrames · column registry and CSV templates · house style · labels · axis limits and ticks · out-of-range markers and exclusion notes · palette · legend rules · hints · errors · `Sheet`.
**Not in scope:** any real plot (P01 is M2), AGS ingest, unit rules that only matter on ingest (in `docs/drafts/phase2-data.md`).

## 2. Public API added in M1
```python
import hangtu as ht

ht.settings                     # session settings (§3)
ht.read_csv(path, units=None, **pandas_kwargs) -> pd.DataFrame
ht.set_units(df, units: dict[str, str]) -> pd.DataFrame     # returns a new frame, never modifies df (decided)
ht.units_of(df) -> dict[str, str]
ht.add_unit_alias(text: str, pint_expr: str) -> None
ht.define_unit(pint_definition: str) -> None
ht.columns(template: str | None = None) -> pd.DataFrame       # registry as a readable table
ht.template(name: str) -> pd.DataFrame                        # empty frame with the template's columns
ht.Sheet(size="tabloid", layout=(1, 1), title=None, orientation="landscape")
ht.plot.palette_cmap(units=None) -> ListedColormap
ht.plot.legend_handles(units=None) -> list[Artist]
ht.plot.reset_palette() -> None
ht.HangtuError, ht.UnitsError, ht.ColumnError, ht.HangtuHint
```
Internal helpers used by every plot live in `ht.plot.common` (§6–§9). They are private API: tested, but free to change.

## 3. Settings
`ht.settings` is a single object with attribute access. Values are validated on assignment (a bad value raises `HangtuError` naming the allowed values).

| Key | Type | Default | Used by |
|---|---|---|---|
| `display_units` | `"US"` \| `"SI"` | `"US"` (decided) | every plot and analysis without `display_units=` |
| `display_overrides` | `dict[quantity, unit]` | `{}` | e.g. `{"stress": "ksf"}` |
| `vertical_datum` | `str \| None` | `None` | elevation labels. A name in the datum table (`vertical_datums.yaml`, `ht.add_vertical_datum()`) is stored as its short name (`navd 88` → `NAVD88`); another is kept as written, with a hint |
| `palette` | `dict[unit, color]` | `{}` | §10 |
| `figure_sizes` | `dict[kind, (w, h)]` inches | `{"default": (6.5, 4.5), "profile": (4.5, 6.0), "chart": (6.5, 3.5)}` | §5 of each plot spec. Each size is the whole figure, legend and footnote included. A kind missing from the dict falls back to `default`, which is required |
| `hints` | `bool` | `True` | §11 |
| `hammer_efficiency` | `float \| None` (%) | `None` | SPT analysis (M3) |
| `spt_cap` | `int` | `100` | SPT analysis (M3) |
| `geology_key` | `"GEOL_GEOL"` \| `"GEOL_GEO2"` \| `"GEOL_LEG"` \| `"GEOL_FORM"` \| `"GEOL_BGS"` | `"GEOL_GEOL"` | datasets (M7, `docs/data/datasets.md` §5.1) |
| `water_unit_weight` | `str`, a unit weight with its unit | `"9.81 kN/m3"` | pore pressure in `ht.analysis.vertical_stress()` (M13), converted to the units in use (62.45 pcf); set `"62.4 pcf"` or a seawater value where the design uses one |

- `ht.settings.reset()` restores defaults.
- `with ht.settings.override(display_units="SI"): ...` changes values temporarily (used heavily in tests).
- Defaults for the *values* (display maps, presets, classification tables) live in `config/defaults.yaml`. Settings only hold the session's choices.

## 4. Units

### 4.1 Quantity kinds and display units
The quantity kind of a column comes from the registry, or from a plot preset for unregistered value columns. Display units come from this table, then `display_overrides`.

| Quantity kind | Canonical | US display | SI display | Label text | Notes |
|---|---|---|---|---|---|
| `length` | m | ft | m | ft / m | depth, elevation |
| `small_length` | mm | in | mm | in / mm | penetrations, increments |
| `particle_size` | mm | mm | mm | mm | always mm (decided); inch display for coarse sizes is Later |
| `stress` | kPa | **psf** (decided) | kPa | psf / kPa | override e.g. `ksf` |
| `unit_weight` | kN/m³ | pcf (lbf/ft³) | kN/m³ | pcf / kN/m³ | §4.3 #1 |
| `density` | Mg/m³ | pcf (lb/ft³) | Mg/m³ | pcf / Mg/m³ | §4.3 #1 |
| `hydraulic_conductivity` | m/s | **cm/s** (decided) | m/s | cm/s / m/s | |
| `modulus` | kPa | ksf | MPa | ksf / MPa | Young's and other moduli (M13 b3); kept after `stress`, which a kPa unit matches first |
| `velocity` | m/s | ft/s | m/s | ft/s / m/s | wave velocities (M13 b3); kept after `hydraulic_conductivity`, which an m/s unit matches first |
| `percent` | % | % | % | % | water content, LL, PL, % passing, ER |
| `dimensionless` | — | — | — | (none) | PI, LI, Ic, Cu, Cc |
| `count` | — | — | — | (none) | SPT N; never converted |
| `angle` | deg | deg | deg | ° | |

`percent`, `dimensionless` and `count` columns never need declared units.

### 4.2 Unit strings and aliases
- **Lookup order** (decided), all case-sensitive:
  1. the alias table, [`src/hangtu/units/aliases.yaml`](../../src/hangtu/units/aliases.yaml);
  2. pint's own parser. If pint understands the string, it is accepted with a `UserWarning` saying what it was read as and how to make that explicit, e.g. `Unit "feet" for column 'depth' was read as foot. Add it with ht.add_unit_alias("feet", "foot") to silence this.`;
  3. otherwise `UnitsError`, showing `ht.add_unit_alias(...)`.
- The dimension check (§4.3 #5) runs after either lookup, so a string pint reads as something unexpected is still caught for registered columns.
- `add_unit_alias` validates the pint expression; `define_unit` adds a genuinely new pint unit first.
- One pint `UnitRegistry` per process, owned by `hangtu.units`.

### 4.3 Phase 1 unit rules
1. **pcf** (decided) converts by quantity kind: unit weight → kN/m³, density → Mg/m³. The column's quantity kind decides, so the same string is safe for both, and both display as "pcf" in US mode. In US practice pcf usually means lbm/ft³, but some reports use it for lbf/ft³; under standard gravity the two are numerically identical, so whichever the author meant, the number is the same.
2. **SPT N** (decided) is a count and never converted. ASTM D1586 counts blows per 12 in (304.8 mm) and ISO 22476-3 per 300 mm; the 1.6% difference is far below SPT repeatability. Penetrations are `small_length` and are converted.
3. **Elevation** = ground level − depth, after both are converted to the same unit.
4. **Overlay definitions and thresholds** given as strings (`"3 m"`, `"10 ft"`) are parsed through the same alias table.
5. **Dimension check:** when a registered column is declared with a unit of the wrong dimension (e.g. `depth: "kPa"`), `set_units`/`read_csv` raise `UnitsError`.

### 4.4 Units on DataFrames (SPEC §2.6)
- `read_csv` and `set_units` validate every unit string, then store `{column: unit string}` in `df.attrs["units"]`. `set_units` merges with existing units and returns a shallow copy.
- `units_of(df)` returns that dict (empty if none).
- **Resolution in a plot** (helper `resolve_units(df, columns, units=)`): `units=` argument → `df.attrs["units"]` → registry quantity kind (for unitless kinds) → unknown. Unknown means "(units unknown)" in the label plus a `UserWarning` naming the column and showing the `ht.set_units` call that fixes it. Analyses raise `UnitsError` instead.
- **Conversion helper** `to_display(values, unit, quantity, display_units)` returns `(magnitudes, display_unit)`. Plots draw magnitudes only; pint never reaches matplotlib.

## 5. Column registry and templates
- Source: [`src/hangtu/columns.yaml`](../../src/hangtu/columns.yaml). Its header comment lists the fields: `description, type, quantity, scale, label, ags, used_by, statistics` (later `agsi`).
- **Rules:**
  - lowercase `snake_case`, one meaning per name across the whole package;
  - number columns must have `quantity`, `scale` and `label`;
  - a plot spec that needs a new column adds it here in the same change;
  - any unregistered numeric column can still be plotted as a `value`, with units from `units=`/`df.attrs` and a label from the column name or `label=`.
- **`statistics:`** (M15 (a), `docs/work/m15a-describe.md`) marks a flag or source column for the statistics functions, so `describe()`, `fit()` and `compare()` read one list and a new one is added here, not in code:
  - `role`: `at_least` (the value is a lower bound), `qualifier` (`<` or `>` on the row's value), `non_plastic`, `assumed`, or `source` (rows with different values come from different sources);
  - `values`: the value columns a flag applies to (all, if omitted; never on `qualifier` or `source`);
  - `when`: on a text flag, the values that set it (`specific_gravity_source`: `assumed`, `judgment`). A bool flag is set by True.
- `ht.columns()` returns one row per column (name, description, quantity, US unit, SI unit, used by). `ht.columns("spt")` limits it to a template.
- **Overlay fields:** names used only in overlay tables (P01 §8: `low`, `high`, `label`, `value`) go in a separate `fields:` section, with a description and type. They share the column namespace and naming rules, and templates may use them, but they aren't data columns: `ht.columns()` leaves them out, and `ht.columns("ranges")` lists them with blank units.
- `ht.template(name)` returns an empty DataFrame with the template's columns. Unknown names raise `ColumnError` listing the available templates.
- **Template CSVs are plain** (decided): one header row, no units row. Units are declared in `read_csv(..., units={...})`, which matches how engineers keep units: in their head or in a note, not in the file.
- **Names are written out** (CLAUDE.md, "Naming"): `undrained_shear_strength`, `uniformity_coefficient`, `curvature_coefficient`, `liquid_limit`, `spt_n60`, not `su`, `cu`, `cc`, `ll`, `n60`. Symbols belong in axis labels (`label`), never in column names. Units never appear in names (`particle_size`, not `size_mm`).
- A registry test loads the file and checks the rules above (§14).
- `loca_id` keeps the AGS name (decided): it is the most widely adopted convention.

## 6. House style
- `plot/hangtu.mplstyle` plus a context manager `ht.plot.style.context()`; every plot body runs inside it. rcParams are identical before and after a call.
- rcParams only reach axes created inside the context, so every plot also calls `style.style_axes(ax)` inside it. This gives `Sheet` panels and a user's own `ax=` the house grid, ticks and spines.
- Font: sans-serif (`Arial`, `Helvetica`, `DejaVu Sans` fallback), 8 pt ticks and legend, 9 pt axis labels, 10 pt titles.
- Light major gridlines (0.5 pt, gray 85%), minor gridlines on log axes only (0.3 pt).
- Spines: all four, 0.6 pt. Ticks inward.
- Savefig: 300 dpi, `bbox_inches="tight"` is left to the user (examples show it).
- `**style_overrides` on any plot are passed as rcParams inside the context, so users can change one thing without touching global state. Names can be written with dots (`**{"font.size": 10}`) or with underscores (`font_size=10`), because keyword arguments can't contain dots. An unknown name raises `HangtuError` suggesting the closest one.

## 7. Labels
- `axis_label(text, unit=None, datum=None, unknown=False)` → `"Elevation (ft, NAVD88)"`, `"Depth (m)"`, `"Liquid limit, LL (%)"`, `"SPT N60"` (no unit for counts and dimensionless), `"k (units unknown)"`.
- Unit text uses display forms: `kN/m³`, `Mg/m³`, `cm/s`, `psf`, `°`, with Unicode superscripts.
- Label text comes from the registry `label`, a preset, or `label=`; only the unit part is generated.
- The datum is added only to elevation labels, from the data's `df.attrs["vertical_datum"]` (a project dataset carries its project's), else `settings.vertical_datum`. The data's wins because a datum is a fact about the data, not a preference (decided 2026-10-14, M9). A project's datum may come from the file's `LOCA_DATM` (`docs/data/ingest.md` §7).

## 8. Axis limits and ticks
| Case | Rule |
|---|---|
| Linear, ratio scale, all values ≥ 0 | lower limit 0; upper = next "nice" value above the max |
| Linear, otherwise | nice floor/ceiling with 5% padding |
| "Nice" values | steps of 1, 2 or 5 × 10ⁿ, chosen to give 4–8 major ticks |
| Log | whole decades enclosing the data, **at least 2** (extend the upper end); majors labeled `10ⁿ`, minors 2–9 unlabeled |
| Depth axis | 0 at the top, inverted, to the nice ceiling of the deepest value |
| Elevation axis | normal direction, nice floor/ceiling with 5% padding |
| Single point / zero range | ± one nice step around the value, or the preset's typical range if there is one |
| Fixed limits (`xlim=`, presets with fixed limits) | used as given; data beyond them handled by §9 |
| A value exactly on a limit hangtu picks | the limit moves out one step (a tick step, or a decade on a log axis), so no point sits on the frame. A lower limit of 0 stays at 0, and fixed limits are used as given (decided 2026-10-14, TODO #18) |

Helpers: `nice_limits(vmin, vmax, *, start_at_zero)`, `log_limits(vmin, vmax, min_decades=2)`, `apply_vertical_axis(ax, vs)`.

## 9. Out-of-range markers and exclusion notes
- **Edge markers:** a value beyond a fixed limit is drawn at the limit as an **open** marker in the series color, with a short arrow pointing outward (`edge_markers(ax, x, y, limits, color)`). It returns a mask of the values drawn at the edge, so the plot draws the rest normally and counts these.
- **Notes collector:** every plot creates a `Notes` object that counts exclusions and edge-clipped values by reason ("NaN", "≤ 0 on log axis", "beyond axis limit", "less than", "greater than", "refusal", "NP"). At the end of the plot it renders one footnote (7 pt, gray), listing only non-zero counts, one per line. It sits below the legend, or below the x label when the legend is inside the axes or there is none, e.g. "3 values beyond axis limit, shown at the edge" / "2 values ≤ 0 not shown on log axis".
- The counts are also attached to the axes as `ax.ags_notes` (a dict) so tests and users can read them (decided).

## 10. Palette
- Resolution: `palette=` argument → `settings.palette` → `df.attrs["palette"]` (a project's geology map, `docs/data/datasets.md` §5.2) → automatic.
- A categorical `geology_unit` gives the units' order, where a plot lists them.
- **Automatic:** colors from `tab20`, reordered to use the 10 darker shades first, then the 10 lighter ones. Units are assigned in stratigraphic `order` if known, else sorted by name. Assignments are remembered for the session (`reset_palette()` clears them), so a unit keeps its color in every plot.
- More than 20 units: colors repeat, with a warning.
- `palette_cmap(units)` returns a `ListedColormap` in unit order; `legend_handles(units)` returns patches for a stand-alone legend.

## 11. Legends and hints
- **Legend:** 8 pt. Sections in order: units (colors), then marker groups, then special markers (qualifiers, edge markers) with counts. More than 12 entries → columns of up to 12; more than 30 → no legend, and a note saying "n units: see ht.plot.legend_handles()".
- **Placement** (`docs/work/p00-layout-defaults.md`): `add_legend(..., where=)` takes `"auto"` (the default), `"inside"`, `"bottom"` or `"right"`, and returns the legend and the placement it chose.
  - `"auto"`: inside the axes, in the first clear corner in the order upper right, upper left, lower right, lower left; if none is clear, below the x label, as `"bottom"`. One order for every plot.
  - **Clear** means the legend's box, padded by 4 pt, overlaps no marker (padded by its radius), no line segment (one crossing the box counts, not just its vertices), no data patch, and no text, annotation or text box. Artists below `_layers.LINES` (strata bands, user regions, range bands, P05 envelopes) and the axes background don't count. The test runs after the layout engine, so the axes have their final size.
  - `"inside"`: the same corners with no fallback; if none is clear, the corner with the fewest obstacles, ties to the earlier corner.
  - `"right"`: outside on the right, no frame. `offset=` moves it further right, in points, to clear a secondary axis.
  - `"bottom"`: centered under the x label in up to four columns, no frame (P05).
  - An inside legend has a white frame at 0.85 alpha with no edge, so gridlines don't run through the text.
  - `Notes.render` takes the placement: below a right legend, below a bottom legend, and below the x label for an inside legend or none.
  - An entry longer than 28 characters wraps at word boundaries onto as many lines as it needs. It is never shortened.
- **Public argument:** every plot with a legend takes `legend="auto" | "inside" | "bottom" | "right" | False` (`True` is `"auto"`; `grain_size` defaults to `"bottom"`). `False` draws no legend, and the footnote still renders below the x label. The P07 grid has no `legend=`; its shared legend stays below the panels. With `ax=`, the corner is chosen at plot time, so pass `"bottom"` or `"right"` if the figure is resized afterwards.
- **Correlation names:** in P01, P02 and P06, a `color_by` or `marker_by` group that is a correlation name in the catalog is shown in the legend by its citation, `ht.analysis.correlations.describe(name)["label"]` (an entry's `label:`, else its first source's `cite`), e.g. "Hatanaka & Uchida (1996)". Data, colors and legend order are unchanged.
- **Hints** (plots README, "Input data"): `hint_missing(df, optional)` collects missing optional columns with a short reason each and issues **one** `HangtuHint` per call, unless `settings.hints` is `False`. The warning's `stacklevel` points at the user's line.

## 12. Errors
- `HangtuError` is the base class. `UnitsError(HangtuError, ValueError)` for unit problems; `ColumnError(HangtuError, ValueError)` for missing or unknown columns and templates.
- Messages follow SPEC §11: what is wrong, where (column, row count), and what to do, with a runnable example where possible:
  `Column 'depth' has no units. Declare them with ht.set_units(df, {"depth": "ft"}) or read_csv(..., units={...}).`

## 13. Sheet
- `ht.Sheet(size="tabloid", layout=(rows, cols), title=None, orientation="landscape")` creates one figure with a GridSpec, using constrained layout so outside legends fit.
- **Sizes (portrait, inches):** Letter 8.5 × 11 · Tabloid 11 × 17 · ANSI D 22 × 34 · A4 8.27 × 11.69 · A3 11.69 × 16.54. Landscape swaps them. Margins 0.5 in.
- **Panels:** `sheet[i]` (row-major index), `sheet[r, c]`, and slices for spanning panels (`sheet[0, :]`). Each panel's Axes is created on first access and the same object is returned after that. Overlapping spans raise `HangtuError`.
- **Title:** simple text at the top left, 12 pt bold. No title block (Later).
- `sheet.save(path, dpi=300)`: the format comes from the extension (`.pdf`, `.png`, `.svg`); others raise an error.
- Plots given `ax=` draw into the panel, never create a figure, and ignore `figsize`.

## 14. Acceptance criteria and tests
- **Units golden values:** 10.0 ft = 3.048 m · 2,000 psf = 95.76 kPa · 1.0e-5 m/s = 1.0e-3 cm/s · 120 pcf unit weight = 18.85 kN/m³ · 120 pcf density = 1.922 Mg/m³ · 6.0 in = 152.4 mm.
- **Units behavior:**
  - a value declared in US units, displayed in SI and converted back by hand, matches;
  - an alias-table string ("ft") is accepted silently; a string only pint knows ("feet") is accepted with a warning naming the interpretation; a string neither knows ("Ft") raises `UnitsError` naming the column and showing `add_unit_alias`;
  - `depth: "kPa"` raises a dimension error;
  - `df.attrs["units"]` survives filtering, column selection, `.copy()` and sorting; after `merge` a plot shows "(units unknown)" and warns.
- **Settings:** validation errors; `override()` restores values even when the block raises; `reset()`.
- **Registry:** the file loads; every number column has quantity, scale and label; every quantity kind is in §4.1; every template column exists; names are unique snake_case.
- **Style:** `rcParams` unchanged after a plot call, including when the plot raises.
- **Limits:** table-driven tests for `nice_limits` and `log_limits`, e.g. (0.3, 7.8, zero) → (0, 8); (2e-7, 3e-4) → (1e-7, 1e-3); (5e-6, 8e-6) → (1e-6, 1e-4).
- **Notes and edge markers:** counts match for a synthetic frame with NaN, ≤ 0 and beyond-limit values.
- **Palette:** the same unit gets the same color in two separate plots; `order` is respected; `reset_palette()` clears it.
- **Legend:** 12 / 13 / 31 entries give 1 column / 2 columns / no legend + note. Placement: points only in the lower half put the legend at the upper right and the footnote below the x label; a point in each corner sends `"auto"` below and `"inside"` to the corner with the fewest obstacles; a line crossing a corner with both vertices outside it blocks the corner; a strata band doesn't block a corner while its label does; the P01 stats box blocks the lower left; P03 bars block a corner they reach into; `"right"` matches the old position within 1 pt; `legend=False` draws none and keeps the footnote and `ax.ags_notes`; a bad `legend=` raises naming the values; a 40-character entry wraps with every word kept; rcParams are unchanged through the corner search.
- **Hints:** one `HangtuHint` per call; none when `settings.hints = False`.
- **Sheet:** each size and orientation has the right figure size; spans work; `save` writes PDF, PNG and SVG; a dummy plot drawn with `ax=sheet[0]` adds no figure (`plt.get_fignums()` unchanged).
- **Shared test helpers** for later plots, as fixtures in `tests/plot/conftest.py`: `assert_us_si_equivalent(plot_fn, df, quantities, **kwargs)` (same point positions after conversion and same note counts; only labels and ticks differ; `quantities` names the x and y quantity kinds) and `assert_no_global_state(plot_fn, df, **kwargs)`. A `dummy_plot` fixture shows how a plot uses every helper.

## 15. Open questions
None open.

## 16. Future enhancements
- Title block and drafting templates for `Sheet`.
- Inch display for coarse particle sizes.
- Per-project settings stored with the Phase 2 database (`to_yaml()` / `load_yaml()`).
