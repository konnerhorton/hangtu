# Agent-review fixes: the mechanical items from TODO #60–69

## Plan

Six small units, taken from the agent-use review (TODO #60–69). None of them needs an intent or a spec. Each unit:
- gets its own branch off `main`, named below, and is merged with `git merge --no-ff`;
- has one or two build commits;
- removes its TODO entry, or the part of the entry it settles, in its last commit;
- adds a CHANGELOG "Unreleased" line when users will see the change.

Branch creation and merges need the user's OK, as usual; build commits don't.

Order: 3 → 2 → 1 → 4 → 5 → 6, smallest first. Units 1 and 2 both touch message text, so they go one after the other.

Left out because each needs a decision: `fit(group_by=...)` count-0 groups (empty units may be kept on purpose, to match `describe()` and the categorical unit order), the long `note=` axes collapse, and `failure_envelope()` crowding (all TODO #69).

### Unit 1: `docstring-refs` (TODO #68)
**Problem:** `test_public_docstrings_cite_no_internal_files` (`tests/docs/test_site.py`) has two gaps:
- It never checks the docstrings of the `ht.stats`, `ht.plot` and `ht.analysis` modules themselves, so "SPEC §5" (stats) and "docs/plots/README.md" (plot) got through.
- `INTERNAL_REFERENCE` doesn't catch `analysis.md §x` or `(P01)`.

**Steps:**
1. Extend the test to the module docstrings, and widen the pattern to `\w+\.md\b` and `\(P\d\d\)`. Run it to see it fail and list the hits.
2. Fix the hits:
   - the three module docstrings;
   - the first lines of six `ht.analysis` functions (`spt`, `spt_class`, `plasticity`, `uscs`, `aashto`, `gradation`): `analysis.md §…` becomes the site page's title, or is dropped;
   - the first lines of fifteen plot functions: drop the "(Pxx)" suffix.
3. **Decided:** `used_by` in `ht.columns()` names plot functions (`plot.profile`), not plot IDs. Extend the test to check `used_by` for plot IDs.

**Commit:** `docs: remove internal references from public docstrings`

### Unit 2: `text-value-messages` (TODO #64, Claude's part)
- **Change:** in `src/hangtu/stats/_rows.py` (the "Replace it with a number" message) and `src/hangtu/plot/_text_values.py` (the "clean the column" message), a `<x` or `>x` text value now gets "put `<` or `>` in `qualifier` (or the column's own qualifier) and the number in the value column". `NP` and other text keep the current wording.
- **Tests:** `pytest.warns(match=...)` for each of the two messages.
- **Left in TODO #64:** the `read_csv` question (whether `ht.read_csv` splits `<x` into the qualifier column).

**Commit:** `stats: point text-value messages to the qualifier column`

### Unit 3: `unit-name-warning` (TODO #69, first bullet)
- **Cause:** `parse_unit()` (`src/hangtu/units/__init__.py`) warns whenever pint, not the alias table, reads a string. That includes `"inch"`, which pint reads as itself, so the warning suggests the alias `inch → inch`.
- **Fix:** skip the warning when pint's canonical name is the text exactly. That reading isn't a guess, so the "never guess a unit" rule still holds. Strings pint has to interpret, like `"feet"`, still warn.
- **Tests:** `"inch"` and `"foot"` give no warning; `"feet"` still does.

**Commit:** `units: don't warn when a unit string is pint's own name`

### Unit 4: `spt-attrs` (TODO #65)
- **Change:** `spt()` writes `result.attrs["spt"]`, following the pattern of `attrs["spt_n1_60"]` (`src/hangtu/analysis/_overburden.py`). It holds:
  - `cap`: `ht.settings.spt_cap`;
  - `energy_ratio` per hole: `{loca_id: {"value": ..., "source": "data" | "argument" | "setting" | None}}`.
- **Source of the data:** `_energy_ratio()` (`src/hangtu/analysis/_spt.py`) already knows which source each row used. It just needs to return that.
- **Tests:** one each for data, argument and setting, plus a hole that mixes data and argument.
- **Docs:** a line on the record in the docstring, and an update to `docs/analysis/index-and-spt.md` §1.3.

**Commit:** `analysis: record the SPT energy ratio and cap in attrs`

### Unit 5: `spt-profile-n1-60` (TODO #69, third bullet)
- **Change:** add `"spt_n1_60"` to `N_COLUMNS`, `AXIS_SYMBOL` (shown as "(N1)60") and the `n` `Literal` in `src/hangtu/plot/_spt_profile.py`. Refusal markers work the same way as for N60.
- **Tests:** a profile from `spt_n1_60()` output draws its refusals.
- **Docs:** update the list of allowed `n` values in the P02 spec and on the site page.

**Commit:** `P02: accept (N1)60 in spt_profile`

### Unit 6: `example-csvs` (TODO #62)
- **Cause:** `strength.csv` is the output of `p.undrained_strength()` (`tests/data/_make_examples.py`), so the UU rows have both `undrained_shear_strength` and `deviator_stress_at_failure` filled in. `undrained_shear_strength_from_tests()` then refuses them as two inputs to s_u.
- **Step 1, a finding first:** is this a dataset problem (the template should leave derived s_u blank) or a problem in the CSV generator? If it's the dataset, it touches the AGS route too: stop and check with the user before going further.
- **Step 2:** put the hand penetrometer values in `hand_penetrometer_reading`, regenerate with `_make_examples.py`, and add a parametrized test in `tests/test_examples.py` that runs each example CSV through the analysis its template feeds. Example data stays AGS-first: change `site.ags` through the generator, not the CSVs by hand.

**Commit:** `examples: make each example CSV pass its own analysis`
