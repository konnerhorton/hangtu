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
