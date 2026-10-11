# P00 — Plot framework

| | |
|---|---|
| **ID / module** | P00 · `ak.settings`, units functions, column registry, `ak.plot` helpers, `ak.Sheet` |
| **Status** | approved |
| **Type** | infrastructure (no user-facing plot) |
| **Target version** | v0.1, milestone M1 |
| **Depends on** | M0 scaffolding |
| **Related** | SPEC §2 (units), §3 (plotting), §10.3 (registry); plots README (shared conventions); registry [`src/ags_kit/columns.yaml`](../../src/ags_kit/columns.yaml); aliases [`src/ags_kit/units/aliases.yaml`](../../src/ags_kit/units/aliases.yaml) |

This spec defines the *implementation* of the shared conventions in the plots README. Where the two overlap, the README states the rule and this spec says how it is built and tested.

---

## 1. Purpose and scope
Everything P01–P07 need, so that each plot spec only describes its own drawing. M1 is done when the acceptance criteria in §14 pass and a dummy plot composes on a `Sheet`.

**In scope:** settings · units for DataFrames · column registry and CSV templates · house style · labels · axis limits and ticks · out-of-range markers and exclusion notes · palette · legend rules · hints · errors · `Sheet`.
**Not in scope:** any real plot (P01 is M2), AGS ingest, unit rules that only matter on ingest (in `docs/drafts/phase2-data.md`).

## 2. Public API added in M1
```python
import ags_kit as ak

ak.settings                     # session settings (§3)
ak.read_csv(path, units=None, **pandas_kwargs) -> pd.DataFrame
ak.set_units(df, units: dict[str, str]) -> pd.DataFrame     # returns a new frame, never modifies df (decided)
ak.units_of(df) -> dict[str, str]
ak.add_unit_alias(text: str, pint_expr: str) -> None
ak.define_unit(pint_definition: str) -> None
ak.columns(template: str | None = None) -> pd.DataFrame       # registry as a readable table
ak.template(name: str) -> pd.DataFrame                        # empty frame with the template's columns
ak.Sheet(size="tabloid", layout=(1, 1), title=None, orientation="landscape")
ak.plot.palette_cmap(units=None) -> ListedColormap
ak.plot.legend_handles(units=None) -> list[Artist]
ak.plot.reset_palette() -> None
ak.AgsKitError, ak.UnitsError, ak.ColumnError, ak.AgsKitHint
```
Internal helpers used by every plot live in `ak.plot.common` (§6–§9). They are private API: tested, but free to change.

## 3. Settings
`ak.settings` is a single object with attribute access. Values are validated on assignment (a bad value raises `AgsKitError` naming the allowed values).

| Key | Type | Default | Used by |
|---|---|---|---|
| `display_units` | `"US"` \| `"SI"` | `"US"` (decided) | every plot and analysis without `display_units=` |
| `display_overrides` | `dict[quantity, unit]` | `{}` | e.g. `{"stress": "ksf"}` |
| `vertical_datum` | `str \| None` | `None` | elevation labels |
| `palette` | `dict[unit, color]` | `{}` | §10 |
| `figure_sizes` | `dict[kind, (w, h)]` inches | `{"default": (6.5, 4.5), "profile": (4.0, 6.5)}` | §5 of each plot spec |
| `hints` | `bool` | `True` | §11 |
| `hammer_efficiency` | `float \| None` (%) | `None` | SPT analysis (M3) |
| `spt_cap` | `int` | `100` | SPT analysis (M3) |

- `ak.settings.reset()` restores defaults.
- `with ak.settings.override(display_units="SI"): ...` changes values temporarily (used heavily in tests).
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
| `percent` | % | % | % | % | water content, LL, PL, % passing, ER |
| `dimensionless` | — | — | — | (none) | PI, LI, Ic, Cu, Cc |
| `count` | — | — | — | (none) | SPT N; never converted |
| `angle` | deg | deg | deg | ° | |

`percent`, `dimensionless` and `count` columns never need declared units.

### 4.2 Unit strings and aliases
- **Lookup order** (decided), all case-sensitive:
  1. the alias table, [`src/ags_kit/units/aliases.yaml`](../../src/ags_kit/units/aliases.yaml);
  2. pint's own parser. If pint understands the string, it is accepted with a `UserWarning` saying what it was read as and how to make that explicit, e.g. `Unit "feet" for column 'depth' was read as foot. Add it with ak.add_unit_alias("feet", "foot") to silence this.`;
  3. otherwise `UnitsError`, showing `ak.add_unit_alias(...)`.
- The dimension check (§4.3 #5) runs after either lookup, so a string pint reads as something unexpected is still caught for registered columns.
- `add_unit_alias` validates the pint expression; `define_unit` adds a genuinely new pint unit first.
- One pint `UnitRegistry` per process, owned by `ags_kit.units`.

### 4.3 Phase 1 unit rules
1. **pcf** converts by quantity kind: unit weight → kN/m³, density → Mg/m³. The column's quantity kind decides, so the same string is safe for both. 🔬 TODO #1.
2. **SPT N** is a count and never converted. Penetrations are `small_length` and are. 🔬 TODO #2.
3. **Elevation** = ground level − depth, after both are converted to the same unit.
4. **Overlay definitions and thresholds** given as strings (`"3 m"`, `"10 ft"`) are parsed through the same alias table.
5. **Dimension check:** when a registered column is declared with a unit of the wrong dimension (e.g. `depth: "kPa"`), `set_units`/`read_csv` raise `UnitsError`.

### 4.4 Units on DataFrames (SPEC §2.6)
- `read_csv` and `set_units` validate every unit string, then store `{column: unit string}` in `df.attrs["units"]`. `set_units` merges with existing units and returns a shallow copy.
- `units_of(df)` returns that dict (empty if none).
- **Resolution in a plot** (helper `resolve_units(df, columns, units=)`): `units=` argument → `df.attrs["units"]` → registry quantity kind (for unitless kinds) → unknown. Unknown means "(units unknown)" in the label plus a `UserWarning` naming the column and showing the `ak.set_units` call that fixes it. Analyses raise `UnitsError` instead.
- **Conversion helper** `to_display(values, unit, quantity, display_units)` returns `(magnitudes, display_unit)`. Plots draw magnitudes only; pint never reaches matplotlib.

## 5. Column registry and templates
- Source: [`src/ags_kit/columns.yaml`](../../src/ags_kit/columns.yaml). Its header comment lists the fields: `description, type, quantity, scale, label, ags, used_by` (later `agsi`).
- **Rules:**
  - lowercase `snake_case`, one meaning per name across the whole package;
  - number columns must have `quantity`, `scale` and `label`;
  - a plot spec that needs a new column adds it here in the same change;
  - any unregistered numeric column can still be plotted as a `value`, with units from `units=`/`df.attrs` and a label from the column name or `label=`.
- `ak.columns()` returns one row per column (name, description, quantity, US unit, SI unit, used by). `ak.columns("spt")` limits it to a template.
- `ak.template(name)` returns an empty DataFrame with the template's columns. Unknown names raise `ColumnError` listing the available templates.
- **Template CSVs are plain** (decided): one header row, no units row. Units are declared in `read_csv(..., units={...})`, which matches how engineers keep units: in their head or in a note, not in the file.
- **Names are written out** (CLAUDE.md, "Naming"): `undrained_shear_strength`, `uniformity_coefficient`, `curvature_coefficient`, `liquid_limit`, `spt_n60`, not `su`, `cu`, `cc`, `ll`, `n60`. Symbols belong in axis labels (`label`), never in column names. Units never appear in names (`particle_size`, not `size_mm`).
- A registry test loads the file and checks the rules above (§14).
- `loca_id` keeps the AGS name (decided): it is the most widely adopted convention.

## 6. House style
- `plot/ags_kit.mplstyle` plus a context manager `ak.plot.style.context()`; every plot body runs inside it. rcParams are identical before and after a call.
- Font: sans-serif (`Arial`, `Helvetica`, `DejaVu Sans` fallback), 8 pt ticks and legend, 9 pt axis labels, 10 pt titles.
- Light major gridlines (0.5 pt, gray 85%), minor gridlines on log axes only (0.3 pt).
- Spines: all four, 0.6 pt. Ticks inward.
- Savefig: 300 dpi, `bbox_inches="tight"` is left to the user (examples show it).
- `**style_overrides` on any plot are passed as rcParams inside the context, so users can change one thing without touching global state.

## 7. Labels
- `axis_label(text, unit=None, datum=None, unknown=False)` → `"Elevation (ft, NAVD88)"`, `"Depth (m)"`, `"Liquid limit, LL (%)"`, `"SPT N60"` (no unit for counts and dimensionless), `"k (units unknown)"`.
- Unit text uses display forms: `kN/m³`, `Mg/m³`, `cm/s`, `psf`, `°`, with Unicode superscripts.
- Label text comes from the registry `label`, a preset, or `label=`; only the unit part is generated.
- The datum is added only to elevation labels and only when `settings.vertical_datum` is set.

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

Helpers: `nice_limits(vmin, vmax, *, start_at_zero)`, `log_limits(vmin, vmax, min_decades=2)`, `apply_vertical_axis(ax, vs)`.

## 9. Out-of-range markers and exclusion notes
- **Edge markers:** a value beyond a fixed limit is drawn at the limit as an **open** marker in the series color, with a short arrow pointing outward (`edge_markers(ax, x, y, limits, color)`).
- **Notes collector:** every plot creates a `Notes` object that counts exclusions and edge-clipped values by reason ("NaN", "≤ 0 on log axis", "beyond axis limit", "less than", "greater than", "refusal", "NP"). At the end of the plot it renders one footnote below the legend (7 pt, gray), listing only non-zero counts, e.g. "3 values beyond axis limit · 2 values ≤ 0 not shown on log axis".
- The counts are also attached to the axes as `ax.ags_notes` (a dict) so tests and users can read them (decided).

## 10. Palette
- Resolution: `palette=` argument → `settings.palette` → automatic.
- **Automatic:** colors from `tab20`, reordered to use the 10 darker shades first, then the 10 lighter ones. Units are assigned in stratigraphic `order` if known, else sorted by name. Assignments are remembered for the session (`reset_palette()` clears them), so a unit keeps its color in every plot.
- More than 20 units: colors repeat, with a warning.
- `palette_cmap(units)` returns a `ListedColormap` in unit order; `legend_handles(units)` returns patches for a stand-alone legend.

## 11. Legends and hints
- **Legend:** outside the axes on the right, no frame, 8 pt. Sections in order: units (colors), then marker groups, then special markers (qualifiers, edge markers) with counts. More than 12 entries → columns of up to 12; more than 30 → no legend, and a note saying "n units: see ak.plot.legend_handles()".
- **Hints** (plots README, "Input data"): `hint_missing(df, optional)` collects missing optional columns with a short reason each and issues **one** `AgsKitHint` per call, unless `settings.hints` is `False`. The warning's `stacklevel` points at the user's line.

## 12. Errors
- `AgsKitError` is the base class. `UnitsError(AgsKitError, ValueError)` for unit problems; `ColumnError(AgsKitError, ValueError)` for missing or unknown columns and templates.
- Messages follow SPEC §11: what is wrong, where (column, row count), and what to do, with a runnable example where possible:
  `Column 'depth' has no units. Declare them with ak.set_units(df, {"depth": "ft"}) or read_csv(..., units={...}).`

## 13. Sheet
- `ak.Sheet(size="tabloid", layout=(rows, cols), title=None, orientation="landscape")` creates one figure with a GridSpec, using constrained layout so outside legends fit.
- **Sizes (portrait, inches):** Letter 8.5 × 11 · Tabloid 11 × 17 · ANSI D 22 × 34 · A4 8.27 × 11.69 · A3 11.69 × 16.54. Landscape swaps them. Margins 0.5 in.
- **Panels:** `sheet[i]` (row-major index), `sheet[r, c]`, and slices for spanning panels (`sheet[0, :]`). Each panel's Axes is created on first access and the same object is returned after that. Overlapping spans raise `AgsKitError`.
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
- **Legend:** 12 / 13 / 31 entries give 1 column / 2 columns / no legend + note.
- **Hints:** one `AgsKitHint` per call; none when `settings.hints = False`.
- **Sheet:** each size and orientation has the right figure size; spans work; `save` writes PDF, PNG and SVG; a dummy plot drawn with `ax=sheet[0]` adds no figure (`plt.get_fignums()` unchanged).
- **Shared test helpers** for later plots: `assert_us_si_equivalent(plot_fn, df, **kwargs)` (same point positions after conversion and same note counts; only labels and ticks differ) and `assert_no_global_state(plot_fn, ...)`.

## 15. Open questions
None open.

## 16. Future enhancements
- Title block and drafting templates for `Sheet`.
- Inch display for coarse particle sizes.
- Per-project settings stored with the Phase 2 database (`to_yaml()` / `load_yaml()`).
