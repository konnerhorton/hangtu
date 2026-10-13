# M3 SPT analysis — plan

Intent: [m3-spt/intent.md](../m3-spt/intent.md). Spec: [`docs/drafts/analysis.md`](../../drafts/analysis.md) §1, finished in the spec step (intent decision 1).

Each build step is one commit, with ruff and pytest passing. A step that grows past about 300 changed lines is split.

## Spec
`analysis.md` §1 was finished in the spec commit: the API (§1.3–1.4), the refusal, N60, cap and class rules, the errors (§1.5) and the golden values (§1.6). SPEC §4, §8.2 and §13.1 were updated with it.

## Package layout
```
src/hangtu/
  __init__.py                   exports analysis
  analysis/__init__.py          exports spt, spt_class
  analysis/_spt.py              spt(), spt_class()
  config/spt_classes.yaml       the two class tables, with sources
  columns.yaml                  + spt_class; used_by gains "analysis" where it applies
tests/analysis/
  test_spt.py                   N60, refusal, cap, units, errors
  test_spt_class.py             class tables and boundaries
```
- The module is `_spt.py`, not `spt.py`, so `ht.analysis.spt` is the function and not a submodule (the same reason as `plot/_profile.py`).

## Decisions the build makes
These are implementation choices §1 leaves open. Any that changes what a user sees goes into §1 in the commit that builds it.
1. **Penetration units are resolved only when a row needs them** (a blank `spt_refusal` with a filled-in `spt_penetration`), through `units.resolve_units(..., analysis=True)`, so a table with every refusal filled in needs no penetration units (§1.3).
2. **`spt_refusal` is parsed by one helper** that maps the accepted values (§1.3) to booleans and lists the rows holding anything else. A column of strings or objects read from CSV with blanks is handled without a pandas FutureWarning.
3. **Classes use `numpy.searchsorted(lowers, n, side="right") - 1`**, not `pd.cut` (§1.4 pitfall).
4. **`config/spt_classes.yaml`** holds each table as `{source, classes: [{name, lower}, ...]}`, read with `_config.load`. Each class's upper bound is the next lower bound, so a later `bins=` argument is just another list.
5. **`spt_class` is a registry column** (text, `used_by: [P03]`): the class name. Checked against the registry, with no collision with `soil_class`.
6. **Row lists in errors** use `plot._data.rows_text`, moved to a shared module if importing it from `plot` would make `analysis` depend on `plot`. Any move is a refactor commit of its own.

## Build 1: `analysis: add ht.analysis.spt for N60, refusal and the cap`
- `analysis/_spt.py`: `spt()` (§1.3; decisions 1, 2 and 6). Errors: no `spt_n` column, non-numeric N, negative N, a bad `energy_ratio`, unknown `spt_penetration` units.
- `ht.analysis` namespace, exported from `hangtu`.
- Tests, with the §1.6 golden values:
  - N60: N = 30, ER = 80 → 40.0; N = 25, ER = 55 → 22.917 (to 3 decimals); ER from the argument, from the settings, and from the row in preference to both; no ER anywhere → blank; an existing N60 kept.
  - Refusal: given True/False kept; blank with penetration 300 mm → True, 450 mm → False; penetration 12 in → True (304.8 mm), 18 in → False; both blank → False.
  - Cap: N = 120 → 100; refusal with N = 38 → 100; refusal with blank N → 100; `cap=50` and `ht.settings.spt_cap = 50`.
  - Rows and order unchanged; `df` not modified; `attrs["units"]` kept.
  - Each error's text says what, where and what to do.

## Build 2: `analysis: add SPT class tables and ht.analysis.spt_class`
- `config/spt_classes.yaml` (decision 4); `columns.yaml`: `spt_class` (decision 5).
- `spt_class()` (§1.4; decision 3). An unknown `table` is an error listing the two tables.
- Tests:
  - Cohesionless golden (§1.6): N = [0, 4, 10, 29, 30, 50, 51] → very loose, loose, medium dense, medium dense, dense, very dense, very dense.
  - Cohesive golden: N = [0, 1, 2, 4, 8, 15, 30, 31] → very soft, very soft, soft, medium stiff, stiff, very stiff, hard, hard.
  - Every non-blank row lands in exactly one category; the counts sum to n.
  - A refusal with N = 12 → "Refusal" only; blank N → blank; the categories keep table order with "Refusal" last.
  - `n="spt_n60"`; a missing `n` column lists the columns available.
  - The registry naming test covers `spt_class`.

## Build 3 (close-out): `analysis: close out the SPT analysis`
- `docs/drafts/analysis.md` §1: any detail the build changed, and decisions that change what a user sees.
- `TODO.md`: #4 closed (the tables and convention are decided, in `config/spt_classes.yaml`); #3 no longer lists the SPT histograms as depending on it.
- `CLAUDE.md`: the status line says the SPT analysis is done and P02 is next.
- This plan: a Results section.

## Verification
- After each build: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- At close-out: Python 3.13 and 3.14 (`uv run --isolated --python 3.1x pytest`); the lowest dependency versions, as in CLAUDE.md; `uv build`, and check that the wheel has `config/spt_classes.yaml` and `spt_class` in `columns.yaml`.
