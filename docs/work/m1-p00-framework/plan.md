# M1: P00 framework — plan

Intent: [intent.md](intent.md). Spec: [`docs/plots/P00-framework.md`](../../plots/P00-framework.md) (section numbers below are P00's unless marked SPEC).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Order
The intent listed units before the registry. The registry goes first instead, because the units dimension check (§4.3 #5) needs each column's quantity kind.

## Package layout
```
src/ags_kit/
  __init__.py          re-exports the public API (§2)
  errors.py            AgsKitError, UnitsError, ColumnError, AgsKitHint; warn() with the user's stacklevel
  _settings.py         ak.settings
  config/defaults.yaml default settings; quantity kinds with canonical, US and SI display units (§4.1)
  registry.py          loads columns.yaml; columns(), template(), column_info()
  columns.yaml         (promoted in the spec step)
  units/__init__.py    pint registry, parse_unit, aliases, set_units, read_csv, units_of, resolve_units, to_display
  units/aliases.yaml   (promoted in the spec step)
  plot/__init__.py     palette_cmap, legend_handles, reset_palette; exposes style and common
  plot/ags_kit.mplstyle
  plot/style.py        context(**style_overrides)
  plot/common.py       private helpers for plots, re-exported from the modules below
  plot/_labels.py, _limits.py, _notes.py, _palette.py, _legend.py, _hints.py
  sheet.py             Sheet
```
- The registry module is `registry.py`, not `columns.py`, and the settings module is `_settings.py`, not `settings.py`. Otherwise `ak.columns` and `ak.settings` would each be both a submodule and an object, and the object would hide the module.
- Tests mirror the package: `tests/test_settings.py`, `tests/test_registry.py`, `tests/units/`, `tests/plot/`, `tests/test_sheet.py`. SPEC §12.2 says `tests/plots/`, but the package is `ak.plot`, so the Build 11 commit changes that example to `tests/plot/`.
- `tests/conftest.py` has an autouse fixture that resets settings after each test. Later builds add aliases and palette assignments to it, and closing all figures.
- Tests run with `--import-mode=importlib`, so shared helpers can't be imported from `tests/`. They are fixtures in `tests/plot/conftest.py`.

## Build 1: `M1: add errors and settings`
- `errors.py`:
  - `AgsKitError(Exception)`; `UnitsError(AgsKitError, ValueError)`; `ColumnError(AgsKitError, ValueError)`; `AgsKitHint(UserWarning)` (§12).
  - `warn(message, category)` walks the stack to the first frame outside `ags_kit`, so warnings point at the user's line (§11).
- `config/defaults.yaml`: the default settings from §3.
- `_settings.py`: a `Settings` object with attribute access. Assigning a value validates it and raises `AgsKitError` naming the allowed values. An unknown key raises too. Also `reset()` and an `override(**values)` context manager that restores the old values even if the block raises.
  - Validation: `display_units` must be `"US"` or `"SI"`. `figure_sizes` values must be pairs of positive numbers. `palette` colors must pass `matplotlib.colors.is_color_like`. `hammer_efficiency` must be in (0, 100] or None. `spt_cap` must be a positive int. `display_overrides` keys must be quantity kinds; their units are checked in Build 3.
- Tests (§14 Settings): defaults; each validation error; `override()` restores values when the block raises; `reset()`.

## Build 2: `M1: load the column registry and build templates`
- The quantity-kind table goes into `config/defaults.yaml`: canonical unit, US and SI display unit, and the label text for each (§4.1). Density in US is `pound / foot**3` (mass) with the text `pcf`. It lands here, not in Build 3, because `ak.columns()` shows each column's display units. `_config.py` loads and caches the package's YAML files.
- `registry.py`: loads `columns.yaml` once. `column_info(name)` returns the entry or None.
  - `ak.columns(template=None)` returns one row per column: name, description, quantity, US unit, SI unit, used by. The display units come from the quantity-kind table.
  - `ak.template(name)` returns an empty DataFrame in template order, with dtypes `float64` for number, `object` for text and `bool` for bool. An unknown name raises `ColumnError` listing the templates.
- Tests (§14 Registry): the file loads; every number column has quantity, scale and label; every quantity is a kind in §4.1; every template column exists; names are unique `snake_case`; no name is a bare symbol from the CLAUDE.md "Naming" list (`su`, `cu`, `k`, `ll`, `unit`, …). Plus `columns("spt")` rows and `template()` columns, and the error for an unknown template.

## Build 3: `M1: parse unit strings and check their dimensions`, then `M1: convert values to display units`
This step is two commits, because together they come to about 470 lines: parsing, aliases and the dimension check first, then `to_display`. The tests are split the same way (`tests/units/test_parse.py`, `tests/units/test_display.py`).
- `units/__init__.py`: one `pint.UnitRegistry`.
  - `parse_unit(text, column=None)` runs the lookup order in §4.2: the alias table; then pint with a `UserWarning` saying what the string was read as; then `UnitsError` showing `ak.add_unit_alias(...)`.
  - `add_unit_alias(text, pint_expr)` checks that the expression parses. `define_unit(definition)` calls `ureg.define`.
- `to_display(values, unit, quantity, display_units=None)` returns `(magnitudes, display_text)`. It uses `display_units`, else `settings.display_units`, then `settings.display_overrides`. `percent`, `dimensionless` and `count` are returned unchanged. A column with no quantity kind (an unregistered value) is drawn in its declared unit. Its kind is never guessed.
- §4.3 #1: a force-per-volume unit on a `density` column is divided by standard gravity before conversion. `pcf` is the case that matters.
- `settings.display_overrides` now checks each unit's dimension against its kind.
- Tests (§14 Units): the golden values (10 ft, 2,000 psf, 1e-5 m/s, 120 pcf as unit weight and as density, 6 in); a US value shown in SI and converted back by hand matches; "ft" passes silently, "feet" warns, "Ft" raises; `add_unit_alias` and `define_unit`; every alias in `aliases.yaml` parses; overrides (`{"stress": "ksf"}`).

## Build 4: `M1: declare units on DataFrames`
- `set_units(df, units)` checks each string with `parse_unit`. An unknown column raises `ColumnError`. A registered column whose unit has the wrong dimension raises `UnitsError` (§4.3 #5). The units are merged into `attrs["units"]` on a shallow copy, so the input frame is never changed.
- `read_csv(path, units=None, **pandas_kwargs)` is `pd.read_csv` followed by `set_units`. `units_of(df)` returns a copy of the dict.
- `resolve_units(df, columns, units=None, *, quantities=None, analysis=False)` runs the order in §4.4. `quantities` gives the kind of an unregistered column (from a plot preset). `needs_units(column, quantity=None)` tells plots whether a None unit means "unknown" or "not needed". For a plot, unknown units give `None` plus one `UserWarning` per column showing the `ak.set_units` call that fixes it. With `analysis=True` it raises `UnitsError`.
- §4.3 #3 and #4: `parse_quantity("3 m")` parses overlay strings through the same alias table. There is no elevation helper yet; P01 adds one when it needs it.
- Tests: `depth: "kPa"` raises; the input frame isn't changed; attrs survive filtering, column selection, `.copy()` and sorting; after `merge`, `resolve_units` warns. The plot-level part of that criterion is covered in Build 11.

## Build 5: `M1: add house style and axis labels`
- `plot/ags_kit.mplstyle` (§6) and `style.context(**style_overrides)`, which nests `matplotlib.style.context` and `rc_context`.
- `_labels.axis_label(text, unit=None, datum=None, unknown=False)` (§7).
- Tests: rcParams are unchanged after the context exits, including when the block raises; overrides apply inside it; label cases from §7 (`"Elevation (ft, NAVD88)"`, `"SPT N60"`, `"... (units unknown)"`, `kN/m³`).

## Build 6: `M1: compute nice axis limits and log ticks`
- `_limits.nice_limits(vmin, vmax, *, start_at_zero, typical=None)`: steps of 1, 2 or 5 × 10ⁿ, picking the smallest step that gives 4–8 major ticks. If `start_at_zero` is set and all values are ≥ 0, the lower limit is 0; otherwise both ends are padded by 5%. A zero range gets ± one step around the value, or `typical` if given.
- `log_limits(vmin, vmax, min_decades=2)` (≤ 0 raises `ValueError`; callers count those values first). `nice_step(lo, hi)`, `set_linear_axis(ax, axis, limits)` and `set_log_axis(ax, axis, limits)` set limits together with matching ticks, so matplotlib's own tick choice can't disagree with the limits. `apply_vertical_axis(ax, vs, vmin, vmax)` for depth and elevation (§8).
- Tests (§14 Limits): a table with the three cases in §14 and more. Hypothesis properties: the limits enclose the data, and there are 4–8 ticks.

## Build 7: `M1: count excluded values and mark values beyond limits`
- `_notes.Notes`: `add(reason, n)` and `count(mask, reason)` for the reasons in §9, with singular and plural wording. `render(ax)` writes one 7 pt gray footnote in axes coordinates below the legend, listing only non-zero counts, and sets `ax.ags_notes`. `add_text()` is for the legend's "see legend_handles()" note.
- `edge_markers(ax, x, y, limits, color)` draws values beyond the limits at the limit, as open markers with outward arrows. Arrow length is in points, so it doesn't depend on the data scale. It returns the count.
- Tests (§14 Notes): a synthetic frame with NaN, ≤ 0 and beyond-limit values gives the right counts in `ax.ags_notes` and the footnote text; marker positions sit at the limit.

## Build 8: `M1: assign stable geology unit colors`
- `_palette.resolve_palette(units, palette=None, order=None)` resolves `palette=`, then `settings.palette`, then automatic colors (§10). Automatic colors are `tab20`, darker shades first, assigned in `order` or else sorted names, and remembered for the session. More than 20 units repeat colors with a warning.
- `palette_cmap(units=None)`, `legend_handles(units=None)` and `reset_palette()` are public in `ak.plot`.
- Tests (§14 Palette): the same color across two calls; `order` is respected; `reset_palette()` clears assignments; explicit and settings palettes win; 21 units warn.

## Build 9: `M1: add legend layout and missing-column hints`
- `_legend.add_legend(ax, sections, notes)`: sections go in the order units → marker groups → special markers. The legend sits outside on the right, has no frame and uses 8 pt text. Columns hold up to 12 entries. With more than 30 entries there is no legend, and a note goes through `notes.add_text`.
- `_hints.hint_missing(df, optional)`: one `AgsKitHint` per call, sent through `errors.warn`, and none when `settings.hints` is False.
- Tests (§14 Legend, Hints): 12, 13 and 31 entries give 1 column, 2 columns, and no legend plus a note; one hint per call that points at the test file; no hint when hints are off.

## Build 10: `M1: add Sheet for multi-panel pages`
- `sheet.py` (§13): `Sheet(size, layout, title, orientation)` uses `plt.figure` with constrained layout. The 0.5 in margins come from the engine's `rect`, and the title from `suptitle` at the top left (12 pt bold). Panels are created on first access through int, `(r, c)` or slice keys, and the same Axes comes back for the same cells. An overlapping span raises `AgsKitError`. `save(path, dpi=300)` accepts `.pdf`, `.png` and `.svg` and raises `AgsKitError` naming them otherwise. An unknown size or orientation raises an error that lists the valid ones.
- Tests (§14 Sheet): figure size for each size and orientation; spans; the same Axes returned twice; overlap errors; `save` writes all three formats to `tmp_path`.

## Build 11 (close-out): `M1: add shared plot test helpers and close out P00`
- `tests/plot/conftest.py` fixtures (§14):
  - `dummy_plot`: a minimal plot following the contract. It uses `resolve_units`, `to_display`, the style context, labels, limits, notes, edge markers, palette, legend and hints, and returns `(fig, ax)`.
  - `assert_no_global_state(plot_fn, ...)`: rcParams are unchanged; with `ax=` no figure is added; the input frame and its attrs are unchanged.
  - `assert_us_si_equivalent(plot_fn, df, quantities, **kwargs)`: point positions match after converting US back to SI, and `ax.ags_notes` is equal.
- Tests: the M1 "done when": `dummy_plot(ax=sheet[0])` leaves `plt.get_fignums()` unchanged; both helpers pass on the dummy plot; after `merge` the dummy plot's label says "(units unknown)" and it warns.
- `__init__.py` exports the §2 API. A test checks that each name in §2 exists.
- Close-out:
  - `docs/plots/README.md`: P00 status set to done.
  - `CLAUDE.md`: status line says M1 is done and M2 (P01) is next.
  - SPEC §12.2: change the test path example.
  - P00: change any spec details the build changed.
  - `TODO.md`: no change expected.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out:
  - Run the tests on Python 3.13 and 3.14: `uv run --isolated --python 3.1x pytest`.
  - Run the lowest dependency versions as described in CLAUDE.md. matplotlib 3.8 must support `ConstrainedLayoutEngine(rect=...)`. If it doesn't, use `fig.subplots_adjust`-style margins, and update this plan in that commit.
  - `uv build`, then check that the wheel contains `columns.yaml`, `config/defaults.yaml`, `units/aliases.yaml` and `ags_kit.mplstyle`.
- Look at a saved Tabloid `Sheet` PNG with the dummy plot in two panels, as a visual check of the style, legend placement and footnote.
