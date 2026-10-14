# M9: examples, templates, README → v0.1.0

## Intent

### Goal
Release v0.1.0 on PyPI. An engineer who has never seen hangtu should be able to install it, follow the README, and do two things:
- run an example that goes from a CSV file to a plot;
- run an example that goes from an AGS file through QC to a plot.

From a CSV template they fill in, they should get the same plots an AGS file gives.

### Why
- v0.1 moved ahead of P04–P06 (SPEC §1.3, §12.4). With M7 done, the library can already go from a file to a plot. What's missing is a way for someone outside the repo to find that out. M10 (the feedback round) needs a release people can install.
- The README is out of date. It says AGS4 ingest "comes in a later release", and it shows none of `ht.Project`, `p.qc()` or the datasets.
- The CSV templates came before the datasets and no longer match them. For example, the `spt` template has no `depth_basis` and no `spt_n60`, and the `atterberg` template has no `sample_reference`. A CSV user and an AGS user should get frames of the same shape.

### Constraints
- **Done when** (SPEC §12.4): the examples run from a clean `pip install hangtu`, outside the repo, on all three operating systems.
- No new runtime dependency. The examples use only hangtu and what it already depends on.
- Example data is synthetic and small, and the repo is public (CLAUDE.md). The AGS example can reuse the generator behind `tests/data/ags/`.
- A template change is a registry change. Each column is checked against the whole registry (CLAUDE.md, Naming), and the M7 datasets stay the reference shape.
- The release itself goes through the existing `release.yml`: a TestPyPI rehearsal first, then a `v0.1.0` tag. Pushing and tagging need the user's approval each time.

### Decisions (settled in review)
1. **SPEC §13 #3 (a docs site?):** the README plus the examples only, for v0.1. A docs site waits until feedback shows what people look for, and will use Zensical when it comes. §13 #3 is removed.
2. **Examples are plain `.py` scripts** in `examples/`, each with a short header comment. Scripts are simpler than notebooks to run in CI and to read in a diff.
3. **Example data lives in the package**, reached through a call such as `ht.examples.path("site.ags")`, so the examples run after a plain `pip install` with no clone or download.
4. **Templates follow the datasets:** each of the `spt`, `atterberg`, `grain_size` and `permeability` templates lists the columns its `p.<dataset>()` returns that a person could fill in. Columns that hangtu calculates (`spt_n60`, `elevation`, `depth_basis`) are optional in the template. The CSV example shows that the plots accept the result.
5. **Clean-install check:** a CI job in `release.yml` (next to `test-wheel`) runs each example against the built wheel in an empty directory. It is part of the release, so it can't be skipped.
6. **TODO #18 is fixed in this unit:** when hangtu picks an axis limit from the data and a value lands exactly on it, the limit moves out one tick step. A lower limit of 0 stays at 0, so only the far end moves. Limits the user sets (`xlim=` and the like) stay exactly as given.
7. **Version:** `0.1.0` in `pyproject.toml` in the close-out commit. The tag and the push happen after merge, with approval.

### Out of scope
- P04–P06 and the analyses behind them (M8, v0.2).
- `to_yaml()` and stored QC overrides (the small unit planned after M7).
- A docs site (decision 1), a changelog beyond the GitHub release notes, and a logo.
- New plots, datasets or QC rules. Bugs the examples find are fixed in this unit, each as its own commit.

### SPEC sections touched
- §1.3, §12.4: M9 done at close-out.
- §2.6: the templates paragraph, if decision 4 changes what a template is.
- §11: the sketches checked against the examples.
- §12.1: the release check (decision 5) and the example data (decision 3).
- §13 #3: removed (decision 1).
- P00 §8 (axis limits): a data value never sits on a limit hangtu picks (decision 6).
- `columns.yaml` (templates), `README.md`, `release.yml`, `pyproject.toml`, TODO #18.

## Spec

The intent's decisions, made exact. M9 adds no analysis and no plot, so this section is the feature spec. SPEC.md and P00 change with it, as listed under "SPEC changes" below.

### 1. Example data: `ht.examples`
- **`ht.examples.path(name) -> pathlib.Path`** returns the path of a file that ships inside the package. An unknown name raises `HangtuError` listing the available names, for example: `No example file 'site.csv'. Files: atterberg.csv, permeability.csv, site.ags, spt.csv, strata.csv.`
- **`ht.examples.names() -> list[str]`** lists the files.
- The files are package data under `src/hangtu/examples/data/`. `uv_build` includes them in the wheel with no configuration, and a test checks them in the built wheel through `release.yml`'s `test-wheel` job.
- **Files** (all synthetic, US units, the audience v0.1 is aimed at, together under 200 KB):

| File | Content |
|---|---|
| `site.ags` | AGS 4.2 in US units (ft, in, cm/s), written in round values as a US consultant's file would be: 6 boreholes with ground levels, GEOL with three units (Fill, Alluvium, Terrace) using `GEOL_GEOL` codes, SPT every 2.5 ft to 10 ft and every 5 ft below, with increments, Atterberg limits with water contents, grading curves, lab and field permeability. Passes python-ags4, and has two planted QC warnings so the QC example shows a report with something in it: a gap in one hole's geology log (G002) and a plasticity index that doesn't match LL − PL (A002). Neither makes a dataset warn |
| `strata.csv` | The geology map for `site.ags` (`code`, `geology_unit`, `soil_class`, `order`, `color`) |
| `spt.csv`, `atterberg.csv`, `permeability.csv` | The same tests as `site.ags`, as a CSV user would type them: each file's columns follow its template (§2), depths and ground levels in ft, hydraulic conductivity in cm/s |

- **The CSV files are made from `site.ags`.** `tests/data/_make_examples.py` writes `site.ags` from fixed rules and a seeded `random.Random`, then ingests it and writes each dataset's template columns to CSV. The CSV and AGS examples then draw the same tests, which is what decision 4 promises. A test checks that the generator reproduces the shipped files.
- Values are realistic for a river valley site: N rising with depth in the Terrace, PI 10–35 in the Alluvium, hydraulic conductivity 1e-7 to 1e-3 cm/s. They are not taken from a real site.

### 2. Templates follow the datasets
- **Rule:** the `spt`, `atterberg`, `grain_size` and `permeability` templates are the columns of `p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()`, in the same order, without the columns only hangtu can produce:
  - `source_line` (a line in an AGS file);
  - `energy_source` (records which input hangtu used for N60);
  - `spt_n_capped`, `liquidity_index` and `consistency_index` (always calculated from columns the template has).
- So the templates gain:
  - `spt`: `depth_basis`, `spt_n60`, `remarks`, `geology_description`;
  - `atterberg`: `sample_reference`, `specimen_reference`, `depth_basis`, `depth_top`, `depth_base`, `geology_description`;
  - `grain_size`: `sample_reference`, `specimen_reference`, `ground_level`, `depth_basis`, `elevation`, `qualifier`, `soil_class`, `geology_description`;
  - `permeability`: `depth_basis`, `soil_class`, `geology_description`.
- **Every template column may be left blank.** The plots already work from what is filled in. Columns hangtu calculates for AGS data (`spt_n60`, `elevation`, `depth_basis`) are there for values the user has from a report, and are blank otherwise. A blank `depth_basis` means the depth is as given (SPEC §8.2, CSV row).
- `ht.columns(name)` lists the new columns with their descriptions. `profile`, `strength`, `index` and the overlay templates are unchanged.
- A test holds the rule: each of the four templates equals its dataset's columns minus the list above. The rule then can't drift when a dataset gains a column.

### 3. The examples
Two scripts in `examples/`, each a short header comment, then straight-line code with a comment per step and no functions. Each writes its output to the current directory and prints the file names it wrote.

**`examples/csv_to_plot.py`:**
1. Read `spt.csv`, `atterberg.csv` and `permeability.csv` with `ht.read_csv(ht.examples.path(...), units={...})`, declaring ft and cm/s.
2. Draw the SPT profile (P02, N60 from `hammer_efficiency=`), the SPT histogram (P03), hydraulic conductivity with depth (P01, log axis) and PI by geology unit (P07).
3. Put the four on a tabloid `ht.Sheet` and save `csv_example.pdf`.

**`examples/ags_qc_plot.py`:**
1. `ht.Project.from_ags(ht.examples.path("site.ags"), db="site.sqlite", display_units="US")`.
2. `p.set_geology_map(ht.examples.path("strata.csv"))`.
3. `p.qc()`: print the summary, save `qc_report.csv`.
4. Draw the same four plots from `p.spt()`, `p.atterberg()` and `p.permeability()`, and save `ags_example.pdf`.

- The two PDFs show the same tests at the same depths. The CSV files were written from the AGS datasets, so their depths are already mid-drive and their `depth_basis` says so.
- **No warnings in normal use:** each script runs with warnings shown and prints none, apart from what QC reports on purpose. A warning in an example would teach users to ignore warnings.
- The README links each script and shows the AGS one inline.

### 4. Clean-install check
- **CI, on every push:** `tests/test_examples.py` runs each script in a temporary directory, in a subprocess with `MPLBACKEND=Agg`, and checks it exits 0, prints no warning, and writes its files.
- **Release, before upload:** a new `release.yml` job, `examples`, runs after `build` on Windows, macOS and Linux with Python 3.12. It copies `examples/*.py` into an empty directory and runs each with `uv run --isolated --no-project --with dist/*.whl python <script>`. `publish-pypi` and `publish-testpypi` wait for it as well as for `test-wheel`. This is the SPEC §12.4 "done when".

### 5. Axis limits clear the data (TODO #18)
- **Rule, P00 §8:** when hangtu picks a limit from the data, no data value sits on it. If a value lands exactly on the limit, the limit moves out one step. On a linear axis that's one tick step, and on a log axis one decade.
- **What it covers:**
  - the upper limit of a ratio-scale linear axis;
  - the depth axis's deepest limit;
  - both ends of a log axis.
- **What it doesn't cover:**
  - **A lower limit of 0 stays at 0.** A value of 0 sits on that axis, as engineers expect.
  - **Limits the user sets** (`xlim=`, `ylim=`) and **preset fixed limits** are used as given. A value on one of those is drawn there, as now.
  - **Padded limits** (elevation, and linear axes with negative values) need nothing, since the 5% padding already keeps values inside.
- **Examples:**
  - PI with a maximum of 30 gives 0–35, not 0–30;
  - the deepest test at 6.0 m gives a depth axis to 7 m;
  - a maximum of 7.8 gives 0–8, as now;
  - k from 1e-5 to 3e-4 cm/s gives 1e-6 to 1e-3, not 1e-5 to 1e-3.
- **Where:** `nice_limits` and `log_limits` in `plot/_limits.py`. Every plot gets the change through them. A single value with no preset range (± one step) is unchanged, since the value sits in the middle.

### 6. README
Rewritten for v0.1. In order:
1. one paragraph on what hangtu is;
2. install;
3. **from an AGS file**, with the AGS example inline and its figure;
4. **from your own CSV**, with templates and `read_csv`;
5. what v0.1 does, as a short list;
6. what it doesn't do yet (P04–P06, statistics), with the roadmap table;
7. who it's for;
8. license.

- The status line changes from "pre-alpha" to "early release: names and arguments may change before 1.0".
- The figure is a PNG of the AGS example's SPT profile, at `docs/img/readme-spt.png`, linked by its full GitHub URL so it shows on PyPI too.
- Every code block in the README runs. A test extracts the Python blocks and runs them against the example data.

### 7. Release
- Close-out: `version = "0.1.0"` in `pyproject.toml`.
- After merge, with approval for each step:
  1. push `main`;
  2. run `release.yml` by hand, which publishes to TestPyPI, and install from there once;
  3. tag `v0.1.0` and push the tag, which publishes to PyPI;
  4. write the GitHub release notes from the README's "what v0.1 does" list.

### 8. SPEC changes
Made in the spec commit, except the two marked close-out.
- §2.6: templates are their dataset's columns, minus those only hangtu produces (§2 here).
- §12.1:
  - the `examples` job in the release checks;
  - "0.1.0" replaces the 0.0.1 line as the current release, with the 0.0.1 line kept as history.
- §12.2: `ht.examples` among the top-level names, and `examples/data/` among the shipped data files.
- §12.4: M9 done (close-out).
- §13 #3 removed, settled as "README and examples for v0.1; a docs site later, with Zensical".
- P00 §8: the rule in §5 here. TODO #18 is closed (close-out).

### 9. Acceptance criteria
1. `ht.examples.path()` returns an existing file for every name in `ht.examples.names()`, from the installed wheel. An unknown name gives the error in §1.
2. `site.ags` passes python-ags4, and its QC report has no errors and exactly the two planted warnings. Info findings are allowed: blank increments after a refusal, and GRAG without a silt/clay split, are what real files have.
3. The generator reproduces every shipped example file byte for byte.
4. Each of the four templates equals its dataset's columns minus the §2 list. A template saved, filled from the dataset, and read back with `ht.read_csv` feeds its plots with no warning.
5. Both example scripts exit 0, print no warning and write their files: in CI from the source tree, and in `release.yml` from the wheel on all three operating systems.
6. The CSV and AGS examples give the same `spt_n` and `plasticity_index` values per hole and depth.
7. Axis limits follow §5, with table-driven tests covering each listed example and each exclusion.
8. Every Python block in the README runs.

## Plan

Spec: the `## Spec` section above.

Each build step below is one commit with ruff and pytest passing. A step that goes past about 300 changed lines (not counting test data and the shipped example files) is split.

### Layout
```
src/hangtu/
  plot/_limits.py             nice_limits/log_limits move a limit off the data (§5)
  columns.yaml                spt, atterberg, grain_size, permeability templates (§2)
  examples/__init__.py        path(), names() (§1)
  examples/data/              site.ags, strata.csv, spt.csv, atterberg.csv, permeability.csv
  __init__.py                 + examples
tests/data/_make_examples.py  writes examples/data/ (reuses tests/data/ags/_make_files.py helpers)
tests/test_examples.py        ht.examples, generator check, both scripts run clean
tests/test_readme.py          every Python block in README.md runs
examples/csv_to_plot.py  examples/ags_qc_plot.py
.github/workflows/release.yml + examples job; publish jobs wait for it
README.md, docs/img/readme-spt.png
```

### Decisions the build makes
1. **The limit rule sits at the end of `nice_limits` and `log_limits`.** Every plot already gets its limits through them. A `clear=False` keyword turns it off where the range isn't data: the typical range with no data, the empty vertical axis, and P01's room beyond `clear_of`. A single value inside a preset's typical range is kept off the limits by `clear_of_data`, so only the value moves a limit, not the typical range.
   - **Linear:** if the upper limit equals the largest value, extend it by one step and recompute the nice limits for the wider range. The extra tick can change the step (0–140 in steps of 20 gives 9 ticks), so the limits are re-snapped to the new step, and the 4–8 ticks rule still holds.
   - **The lower end** only moves when it isn't 0 and equals the smallest value. That only happens on the depth axis with negative depths, or with a typical range.
   - **Log:** a decade equal to `vmin` or `vmax` moves out one decade, and `min_decades` applies after that.
2. **Golden limits that change** are updated in the same commit, each with a comment giving the reason: `(0, 100) → (0, 120)`, the exact-decade log case and the single-value typical-range case. Plot tests that assert limits on whole-step data are updated the same way. Any other change shows up as a failure, and I list it in the commit body.
3. **`ht.examples` is a module, not data on `Project`:** `importlib.resources.files("hangtu.examples") / "data" / name`, returned as a `Path`. The wheel is installed unzipped, so a real path works for `from_ags` and `read_csv`.
4. **The example site** is its own set of values in `_make_examples.py`, not the test files: 6 holes, 77 SPT, 14 Atterberg, 8 gradings and 10 permeability results, enough to draw realistic figures. It reuses `group`, `write_group`, `tran` and the UNIT/TYPE descriptions from `_make_files.py` (loaded with `importlib`, as the test conftests do). It is written directly in round US values, not converted from SI, so the file reads like a real US one. The planted QC findings are a geology gap (G002) and a PI slip (A002). A missing `LOCA_GL`, the first idea, would also raise C001 and blank that hole's elevations, so the example would print warnings.
5. **CSV files are written** by ingesting `site.ags` into a temporary database, taking each dataset with `display_units="US"`, keeping the template's columns, and writing them with `to_csv(index=False)`, with floats to 6 significant figures so the files read cleanly. Writing depends on pandas' CSV output, so the check against the generator (acceptance criterion 3) compares parsed frames for the CSV files and bytes for `site.ags`.
6. **The scripts run as subprocesses in the tests,** with Python's default warning filters, as a user would run them. The test fails if anything is written to stderr. QC findings go to stdout as part of the printed summary, so they don't count.

### Build 1: `M9: keep axis limits off the data`
- `plot/_limits.py` (decision 1); golden tables in `tests/plot/test_limits.py` (decision 2), plus the §5 cases:
  - PI 30 → 0–35;
  - depth 6.0 → 7;
  - k 1e-5 to 3e-4 → 1e-6 to 1e-3;
  - 0 stays at 0;
  - `xlim=` used as given;
  - a single value unchanged.
- The property test gets stricter: `lo < vmin` unless `lo == 0`, and `hi > vmax`.
- Update any P01/P02/P03/P07 test whose limits move.

### Build 2: `M9: make the dataset templates follow the datasets`
- `columns.yaml`: the four templates (spec §2).
- `tests/test_registry.py`:
  - each template equals its dataset's columns minus the excluded list, using `tests/data/ags/site_si.ags`;
  - a filled template read back with `ht.read_csv` feeds P01/P02/P03/P07 with no warning.
- Fix `read_csv` dtype handling if blank `spt_refusal`/`non_plastic` columns trip it (likely `boolean` with NA).

### Build 3: `M9: add the example site generator and site.ags`
- `tests/data/_make_examples.py` (decision 4), `src/hangtu/examples/data/site.ags` and `strata.csv`.
- Tests in `tests/test_examples.py`:
  - python-ags4 passes;
  - `p.qc()` gives exactly the two planted findings;
  - the generator reproduces the files.

### Build 4: `M9: add ht.examples and the example CSV files`
- `examples/__init__.py`, the `ht.examples` export, and the three CSV files (decision 5).
- Tests:
  - `path()` for every name;
  - the unknown-name error text;
  - CSV and AGS give the same `spt_n` and `plasticity_index` per hole and depth (criterion 6).

### Build 5: `M9: add the CSV and AGS examples`
- `examples/csv_to_plot.py`, `examples/ags_qc_plot.py` (spec §3).
- `tests/test_examples.py`: both run in `tmp_path`, exit 0, write their files and print no warning (decision 6).
- Look at both PDFs.

### Build 6: `M9: run the examples against the wheel before release`
- `release.yml`: an `examples` job (3 operating systems × Python 3.12), with `publish-pypi` and `publish-testpypi` needing both `test-wheel` and `examples`.
- It can't be checked locally beyond `uv build`, then running each script with `uv run --isolated --no-project --with dist/*.whl` in an empty directory. I do that by hand and record it in Results.

### Build 7: `M9: rewrite the README for v0.1`
- `README.md` (spec §6), `docs/img/readme-spt.png` (100 dpi, from the AGS example, looked at before committing).
- `tests/test_readme.py`: extracts the ```` ```python ```` blocks and runs them in `tmp_path`.

### Build 8 (close-out): `M9: close out examples, templates and v0.1.0`
- `pyproject.toml` `version = "0.1.0"` (and `uv.lock`).
- SPEC §12.1: 0.1.0 is the current release, with the 0.0.1 line kept as history. SPEC §12.4: M9 done.
- TODO #18: closed. CLAUDE.md state line: M9 done, M10 next. Plan Results.
- The release itself (push, TestPyPI, tag) follows the merge, with approval at each step (spec §7).

### Verification
- At every commit: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- Before the close-out:
  - the lowest-version run, then `git checkout uv.lock`;
  - `uv build`, then both scripts run against the wheel from an empty directory outside the repo;
  - look at both example PDFs and the README figure.
- After merge, with approval: a TestPyPI rehearsal, then `pip install hangtu` in a fresh environment and run one example.
