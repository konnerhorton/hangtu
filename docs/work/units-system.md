# Units system: declare a file's units in one step

## Intent

### Goal
A user can declare every unit in a CSV or DataFrame in one step by naming the system it was recorded in
(`"US"` or `"SI"`), and declare exceptions column by column. Resolves the open item in TODO #66.

### Why
- In the agent trials (TODO #66), the lab agent declared about 24 units by hand from `ht.columns()` before it could
  run the strength analyses. A real lab sheet has as many unit columns, all in one system.
- The planned tutorial and its marimo copy (the next unit) start from a file and walk to a parameter set. One
  declaration keeps unit bookkeeping out of every step of them.
- The units each system means are already set: each quantity kind in `config/defaults.yaml` has a `US` and an `SI`
  unit (`length`: ft or m, `small_length`: in or mm, `stress`: psf or kPa, `modulus`: ksf or MPa).

### Constraints
- **A declaration, not a guess** (SPEC §2.6). The user states the system, and hangtu reads the units from it. Columns
  hangtu can't place stay undeclared and still fail or warn as today.
- **It covers columns the user never looked at**, so what it declares is easy to see: the published table of units
  per system, and `ht.units_of(df)` afterwards.
- **The same code reads the same units in every session.** `ht.settings.display_overrides` and `display_units`
  change what a plot shows, not what a file holds.
- Plain-function API (CLAUDE.md conventions): an argument to `ht.read_csv()` and `ht.set_units()`, not a new object.

### Out of scope
- The rest of TODO #66 (`stratigraphy.csv`, a CSV example per analysis family, renaming `strata.csv` to
  `geology_map.csv`). It goes in the tutorial unit, whose CSV examples will use this.
- Units in a header row or a second header line in the file.
- AGS data, which takes its units from the file.

### SPEC sections touched
- SPEC §2.6: the one-step declaration, which units it gives, and how it combines with per-column units.
- `docs/site/guides/units.md`: the declaration, and a table of each quantity's US and SI unit.
- `docs/TODO.md` #66: its open item is resolved and leaves the item.
- `CHANGELOG.md`: Unreleased entry.

### Decisions (intent review, 2026-11-27)
1. **A `system=` keyword**, as in `ht.read_csv(path, system="US", units={"cell_pressure": "ksf"})` and
   `ht.set_units(df, system="SI")`. `units="US"` was rejected because it can't also carry the exceptions.
2. **Which columns:** every registered number column whose quantity kind has a unit (length, stress and so on) gets
   that kind's unit in the system. Percent, count, dimensionless and text columns are unaffected, and so are columns
   not in the registry, which stay undeclared.
3. **Precedence:** a unit in `units=` wins over `system=`, and so does a unit already declared on the frame.
   `system=` only fills columns without a unit.
4. **No message when it runs.** A notice on every read would be ignored, and warnings are errors in the suite.
5. **US stress stays psf,** accepting that a lab sheet in ksf or tsf read as `system="US"` is 1000 or 2000 times
   too small. The guard is decision 6, and the docs name stress and modulus as the columns to check.
6. **The default unit of each of a file's columns is easy to see before declaring.** The user asked for this to
   counter decision 5's risk. The column reference already lists each registered column's US and SI unit; this unit
   adds a view of the user's own file (see the spec).

## Spec

The rules live in P00 §4.4 and SPEC §2.6, both updated in this commit. This section adds the reasons and the
acceptance criteria.

### Behavior
- **`ht.read_csv(path, units=None, *, system=None, **pandas_kwargs)`** and **`ht.set_units(df, units=None, *,
  system=None)`**. `system` is `"US"` or `"SI"`. `set_units` needs `units` or `system` or both; with neither it raises
  `UnitsError` showing both forms.
- **What `system=` declares:** for each of the frame's columns that is registered, a number, and of a quantity kind
  with a unit, the kind's unit in that system, written as `ht.columns()` shows it (`"ft"`, `"psf"`, `"kN/m³"`). The
  string declared is the one the user saw in the column reference, so what they checked is what they get.
- **Precedence:** `units=` → a unit already in `df.attrs["units"]` → `system=`. The first two are as today.
- **Independent of display settings:** `ht.settings.display_units` and `display_overrides` don't change what
  `system=` declares. With `display_overrides={"stress": "ksf"}`, `system="US"` still declares psf.
- **A frame with none of its columns in the registry** raises `UnitsError` when `system=` is given: it names the
  columns, says `system=` declares units only for registered column names, and points to `ht.columns()`. This
  catches headers such as `Depth (ft)`, where `system=` would otherwise declare nothing and say nothing. A frame
  with some registered columns isn't an error; its other columns stay undeclared and show in `ht.columns(df)`.
- **A bad `system`** (`"us"`, `"metric"`) raises `UnitsError` naming the two values.

### Seeing the defaults first (decision 6)
- **`ht.columns(df)`** takes a DataFrame as well as a template name. It returns one row per column of the frame, in
  the frame's order, with the usual columns (`name`, `description`, `quantity`, `us_unit`, `si_unit`, `used_by`) and
  one more, `declared_unit`: the unit in `df.attrs["units"]`, blank if none. A column not in the registry has the
  description "Not a registered column" and the rest blank. So before declaring, the user reads the file with
  `ht.read_csv(path)`, runs `ht.columns(df)`, and checks the `us_unit` or `si_unit` column against the lab sheet; after
  declaring, `declared_unit` shows the result.
- 🟡 **Proposed:** `ht.columns(template)` and `ht.columns()` keep their columns, without `declared_unit`. A template
  has no units to show, and the column reference page is built from `ht.columns()`.
- **The units guide** gains a section, "Declaring a whole file at once", with an example that reads a CSV, prints
  `ht.columns(df)` (its output generated on the page), declares `system="US"` with one exception, and prints
  `ht.units_of(df)`. It says plainly that a US lab sheet in ksf or tsf needs those columns given in `units=`, and
  names the stress and modulus columns as the ones to check.
- **The column reference page's intro** says the listed US and SI units are also what `system=` declares.

### Unit strings
- The superscript texts that `ht.columns()` shows and pint reads only with a warning (`kN/m³`, `Mg/m³`, `ft²/kip`,
  `m²/MN`, `ft²/yr`, `m²/yr`) become aliases in `src/hangtu/units/aliases.yaml`, so `system=` declares them
  silently, and a user who copies one from the column reference gets no warning either.

### Acceptance criteria
1. `ht.read_csv` of a file with `depth`, `spt_penetration`, `cell_pressure`, `bulk_unit_weight`,
   `hydraulic_conductivity`, `water_content` and `spt_n`, with `system="US"`, gives `units_of` = ft, in, psf, pcf,
   cm/s for the first five and nothing for `water_content` and `spt_n`. With `system="SI"`: m, mm, kPa, kN/m³, m/s.
2. `system="US", units={"cell_pressure": "ksf"}` declares `cell_pressure` in ksf and the rest as in 1.
3. `set_units(df, system="SI")` on a frame that already declares `depth` in ft keeps ft and fills the rest.
4. Under `ht.settings.override(display_units="SI", display_overrides={"stress": "ksf"})`, `system="US"` gives the
   same units as 1.
5. A column not in the registry, and text, percent, count and dimensionless columns, get no unit from `system=`.
6. `system=` on a frame whose columns are all unregistered raises `UnitsError` naming them and `ht.columns()`.
7. `system="us"` raises `UnitsError` naming `"US"` and `"SI"`; `set_units(df)` with neither argument raises
   `UnitsError` showing both forms.
8. No warning is raised by `system=` for any quantity kind, in either system (the suite runs with warnings as
   errors); each of the six superscript strings in "Unit strings" parses without a warning.
9. End to end: values read with `system="US"` and drawn with `display_units="SI"` match a hand conversion: depth
   10.0 ft → 3.048 m; `cell_pressure` 2,000 psf → 95.76 kPa (P00 §14's golden values).
10. `ht.columns(df)` lists the frame's columns in order, gives the registered ones' US and SI units, the
    unregistered one "Not a registered column", and `declared_unit` before (blank) and after `set_units(df,
    system="US")` (ft, psf, …).
11. `ht.columns()` and `ht.columns("spt")` are unchanged (no `declared_unit` column).
12. The units guide example runs in `prepare_site.py`, and the docs site builds with `--strict`.

## Plan

Four build commits, each green (`uv run ruff check . && uv run ruff format --check . && uv run mypy` and the tests the
step touches; the whole suite with `-n 2` before step 4's commit). Steps 1–3 on Sonnet in one session, step 4 on Opus
in a new one: it writes the published text and closes the unit.

### 1. `units: alias the superscript unit texts that ht.columns() shows` (Sonnet)
- `src/hangtu/units/aliases.yaml`: add `kN/m³`, `Mg/m³`, `ft²/kip`, `m²/MN`, `ft²/yr`, `m²/yr`, each beside its
  ASCII form, with the same pint expression.
- `tests/units/test_parse.py`: each of the six parses without a warning to the same unit as its ASCII form, and every
  quantity kind's `US` and `SI` `text` in `config/defaults.yaml` parses without a warning (AC 8, second half). The
  second test guards a kind added later.

### 2. `units-system: declare a file's units with system=` (Sonnet)
- `src/hangtu/units/__init__.py`:
  - a private `_system_units(df, system) -> dict[str, str]`: for each column with `column_info` of type number and a
    quantity kind whose `canonical` isn't null, the kind's `[system]["text"]`. It reads `quantity_kinds()` directly,
    never `_display_target`, so `display_overrides` can't reach it (AC 4).
  - `set_units(df, units=None, *, system=None)`: validate `system` (`"US"` or `"SI"`, else `UnitsError` naming both;
    a message of its own, not `_settings._display_units`, whose text names `settings.display_units`); neither argument
    raises `UnitsError` showing both forms; no registered column in the frame raises `UnitsError` naming the columns
    and `ht.columns()`. Merge as `{**system_units, **units_of(df), **units}`, then check each declared unit as today.
  - `read_csv(path, units=None, *, system=None, **pandas_kwargs)`: pass both through when either is given.
  - Docstrings: `system` in Parameters, the precedence, and that `ht.columns(df)` shows what it would declare; an
    example with an exception (`system="US", units={"cell_pressure": "ksf"}`) and a sentence that US stress is psf.
- `tests/units/test_dataframes.py`: AC 1–7 and AC 9 (round trip through `to_display` with `display_units="SI"`:
  10.0 ft → 3.048 m, 2,000 psf → 95.76 kPa, to 4 significant figures, the precision the golden values are given to).
  Build AC 1's file in `tmp_path` and AC 5's frame with a text column (`loca_id`), a percent (`water_content`), a
  count (`spt_n`), a dimensionless (`plasticity_index`) and an unregistered column (`my_note`). AC 8, first half:
  `system=` on a frame of every registered number column, in both systems, under `warnings.simplefilter("error")`.
- `tests/test_errors.py` picks up the new messages; check it passes, and fix the text rather than the test if not.

### 3. `units-system: ht.columns(df) shows each column's units` (Sonnet)
- `src/hangtu/registry.py`, `columns(template: str | pd.DataFrame | None = None)`: for a DataFrame, rows in the frame's
  order with `declared_unit` from `df.attrs.get("units", {})` (read directly; importing `hangtu.units` here would be
  circular), and "Not a registered column" with blanks for unknown names. Template and no-argument output unchanged.
  Docstring: the DataFrame form, `declared_unit`, and the check-before-declaring use, with an example.
- `tests/test_registry.py`: AC 10 and 11 (11 compares the columns of `ht.columns()` and `ht.columns("spt")` to the
  current list).

### 4. `units-system: guide section, column reference intro, close-out` (Opus)
- `docs/site/examples/units-system.py`: read `ht.examples.path("triaxial.csv")` (US units: ft, psf, pcf) without
  units; print `ht.columns(df)` for a few columns (depth, a stress, a unit weight, water content); declare
  `system="US"`; print `ht.units_of()` for the same columns. No figure; its `.txt` output shows on the page.
- `docs/site/guides/units.md`: section "Declaring a whole file at once" after "Declaring units": the example, the
  precedence in one sentence, and a warning admonition that US stress is psf, so a lab sheet in ksf or tsf names its
  stress and modulus columns in `units=`, and how to find them in `ht.columns(df)`.
- `docs/prepare_site.py`: the column reference intro says these US and SI units are also what `system=` declares.
- Close-out: `CHANGELOG.md` Unreleased (Added: `system=` on `read_csv()` and `set_units()`; `ht.columns()` takes a
  DataFrame); `docs/TODO.md` #66 drops its "Open (You)" line, the rest of #66 staying for the tutorial unit;
  `STATUS.md` (In progress cleared, a Done line); a TODO or CLAUDE.md note only if the build turns up something a
  future session would get wrong.
- Check: AC 12 (`uv run python docs/prepare_site.py && uv run zensical build --clean --strict`), read the generated
  output on the page, and report each acceptance criterion as met or not.

### Notes from the build
- All four steps were built in one Opus session rather than steps 1–3 on Sonnet.
- The superscript aliases sit after their ASCII forms in `aliases.yaml`: ingest's `_alias_for()` writes the first
  alias that matches a canonical unit, so ingested frames keep `kN/m3` and `m2/yr`.
- The guide's example declares `system="US"` with no exception, because `triaxial.csv` is in psf throughout; the
  exception (`units={"cell_pressure": "ksf"}`) is shown in the warning admonition instead of being run against data
  it would misread.
