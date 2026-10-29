# Test speed: cache the AGS4 check, run in parallel

## Intent

### Goal
Bring the full test suite from about 7.5 minutes to about a minute locally, so a build step can run it before every commit.

### Why
- Baseline (one core, 2,784 tests): 459 s.
- `ht.Project.from_ags` runs 292 times in the suite and takes 209 s of that. One ingest of `site_si.ags` takes about 1 s, and about 90% of it is `python_ags4`'s `AGS4.check_file` (`src/hangtu/ags/_read.py`), which gives the same answer for the same text every time.
- Fixtures such as `fresh` (`tests/datasets/conftest.py`) and `project` (`tests/test_project.py`) ingest the same few files once per test, so each test gets a database it can change.
- The suite runs on one core, and the machine has 8.
- At 7.5 minutes, "never commit failing tests" makes each commit wait on a long run, or tempts running only part of the suite.

### Constraints
- **Library code doesn't change.** This is test infrastructure only.
- **Every test still exercises hangtu's own ingest code:** decoding, parsing, findings, units and `database.write`, with the session and project settings in force at that moment. Only the third-party validator's result is reused.
- **Findings are identical with and without the cache,** including those that come from `python_ags4`'s log messages.
- **Tests stay independent:** no test can change a cached result another test sees, and no test depends on the order or process it runs in.
- `pytest-xdist` is a new dev dependency (approved for this unit). It isn't a runtime dependency, so SPEC §12.1 doesn't change.
- A single-file run (`uv run pytest tests/x.py`) stays as fast as now, with no worker startup unless asked for.

### Out of scope
- Making the library's ingest faster for users (for example, caching `check_file` in hangtu itself, or skipping the check). That would be a SPEC §6 decision.
- Speeding up individual slow tests (docs examples, plots) beyond what parallel runs give.
- Coverage or CI matrix changes.

### SPEC sections touched
None. CLAUDE.md's Commands and Git sections change (step 3).

## Plan

### Step 1: cache the AGS4 rule check across the run
- `tests/conftest.py`: a session-scoped wrapper around `python_ags4.AGS4.check_file`, installed for the whole run.
  - Key: the file text and `standard_AGS4_dictionary`. Value: the result and the log records `check_file` emitted.
  - A hit returns a deep copy of the result and re-emits the stored log records through their original loggers, so `_Capture` in `_read.py` turns them into the same findings.
- Only calls with a text buffer are cached, which is how `_read.py` calls it. A call with a path goes to the real check, so `tests/ags/test_files.py` and `tests/test_examples.py`, which check files directly, need no opt-out. `cache.disabled()` turns it off where a test needs the real check.
- Tests:
  - `tests/test_check_cache.py`: for `site_si`, `defects`, `qc_defects` and a file with a duplicate heading, the findings are equal with the cache on and off. A hit logs the same records as the real check. A changed copy of a file misses the cache. Changing a returned result doesn't change the next hit. A path isn't cached.
  - The full suite passes, and the pass/fail/xfail counts match the baseline.
- Time the suite again and record it here. Result: 2,819 passed in 256 s, from 459 s (2,811 tests before this step).
- Fallback, if replaying the logs is fragile: ingest each test file once per session and `shutil.copy` the SQLite into each test's `tmp_path` in `fresh`, `project` and `tests/stats/conftest.py`, only where the session settings are at their defaults when the fixture runs.

### Step 2: run in parallel with pytest-xdist
- First, audit for parallel safety, and fix anything found in its own commit before this step:
  - tests that write outside `tmp_path` (into `tests/data/`, `docs/`, or the working directory)
  - tests that depend on order or shared state the autouse `_restore_session_state` fixture doesn't reset
  - the Hypothesis example database
- `pyproject.toml`: add `pytest-xdist` to the `dev` group at the lowest version that supports `pytest>=8.0`. Update `uv.lock`.
- Use `--dist loadfile`, so module-scoped fixtures are built once. Don't add `-n` to `addopts`.
- `.github/workflows/ci.yml`: run `uv run pytest -n auto --dist loadfile`.
- Check:
  - several `-n auto` runs, and one `--dist load` run to shake out hidden coupling
  - the oldest-versions check (`UV_RESOLUTION=lowest-direct`), then `git checkout uv.lock`
  - record the timings here
- Result: no test wrote outside `tmp_path` or depended on order, so there were no fixes. 2,819 passed in 93 s with `-n auto --dist loadfile`; `load`, `loadscope` and `worksteal` took 90–98 s. The machine has 4 cores with 2 threads each, and `-n 4` also takes 93 s, so about 90 s is the floor here. pytest 8.0.0 with pytest-xdist 3.6.0 passes too, but 3.6.0 is yanked, so the floor is 3.6.1.

### Step 3: focused runs during a build
- CLAUDE.md, Commands: add the full-suite command with `-n auto --dist loadfile`, and the focused form (`uv run pytest <files>`, `--lf` for failures).
- CLAUDE.md, Git and commits: while iterating on a step, run the tests it touches. Run the full suite once, in parallel, before the commit.
- Close-out: final timings in this file.

### Commits
1. `tests: cache the AGS4 rule check across the run`
2. any parallel-safety fixes, one commit each
3. `tests: run in parallel with pytest-xdist`
4. `docs: focused test runs during a build`, with the close-out timings
