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
