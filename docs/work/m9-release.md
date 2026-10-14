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
