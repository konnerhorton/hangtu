# Docs site

## Intent

### Goal
A public docs site for hangtu, built with Zensical, with a simple layout. An engineer who finds hangtu on PyPI or GitHub should be able to, without reading the source:
- install it and get to a first plot, from a CSV file or from an AGS file;
- find how to do a task (fill in a template, set units, run QC, pick a dataset, draw a plot);
- look up what a function takes and returns, and what a column means and which units it expects.

### Why
- The README is the only user documentation, and it can't hold much more than install and two examples. The plots, datasets, QC rules and column registry have no user-facing description outside the docstrings and the internal specs.
- v0.2 adds four plots, triaxial, clogging and the SPT correlations. Each correlation must say when it applies (SPEC §4), and a docs page is where an engineer will read that before trusting a number.
- SPEC §12.1 already picks Zensical. M9 decision 1 put the site off until feedback showed what people look for. This unit starts it now, ahead of v0.2, because a site is where potential users will find out what hangtu does, and it is easier to grow page by page as features land than to write all at once later.

### Constraints
- **Simple layout:** Zensical's default theme with minimal configuration: the ASCII logo (decision 8), but no custom CSS, no theme changes and no custom templates.
- **Written for engineers, not developers** (CLAUDE.md). Pages lead with the task and the result.
- **Short examples near the top:** each getting-started, guide and plot page opens with an example of a few lines that a user can copy (with the copy button) and run right after installing hangtu, on the data in `ht.examples`. No clone, download or setup.
- **Docs don't rot:** code shown on the site runs in CI, either because it is pulled in from `examples/` or because a test runs it. Reference pages (API, columns) are generated from the code and `columns.yaml`, not copied.
- **The internal docs stay internal.** `SPEC.md`, `docs/work/`, `docs/plots/`, `docs/data/` and `docs/drafts/` are specs for building hangtu and are not published as user docs. Their paths don't move, since SPEC, TODO and CLAUDE.md link to them.
- **Dependencies:** Zensical and `mkdocstrings-python` go in a `docs` dependency group, never in the runtime dependencies (approved in review).
- American spelling; nothing private (the repo is public).

### Decisions (settled in review)
1. **Where the site source lives.** `docs/` already holds the internal specs, and `/site` is gitignored as the build output. `docs/site/` is Zensical's `docs_dir`, and `zensical.toml` is at the repo root. Moving the internal docs out of `docs/` instead would break many links. The built site goes to `build/site/` (already gitignored), not `/site`, so `site` names only the source.
2. **Pages for the first version**, all short:
   - Home (what hangtu is, who it's for, a figure);
   - Install;
   - Getting started: CSV → plot and AGS → QC → plot, from `examples/`;
   - Guides: units, CSV templates and the column registry, AGS ingest and QC, datasets, SPT analysis;
   - Plots: one page per shipped plot (P01–P03, P07, and P04–P06 as they land), each with its figure and the options an engineer is likely to change;
   - Reference: API from the numpy docstrings, and the column registry from `columns.yaml`.
3. **API reference.** Generated from the numpy docstrings with mkdocstrings and `mkdocstrings-python`. Checked 2026-10-16 with Zensical 0.0.70, mkdocstrings 1.0.7 and mkdocstrings-python 2.0.9 on a test site built from `hangtu.analysis`: the API pages render, cross-references (`[text][hangtu.analysis.plasticity]`) resolve from guide pages, and `objects.inv` is written. Zensical is still alpha, so its version is pinned in the `docs` group and raised deliberately.
4. **Math.** Pages and docstrings need equations (N60, consistency index, correlations). MathJax through `pymdownx.arithmatex` (`generic = true`), with `$...$` inline and `$$...$$` on their own lines for blocks, and the MathJax script pinned to an exact version. The same test site showed math in both Markdown pages and docstrings reaching the HTML ready for MathJax. A docstring that contains math needs a raw string (`r"""`). KaTeX is faster but covers less LaTeX, and only MathJax produces MathML for screen readers.
5. **Figures.** The build draws them from `ht.examples` data with the same code the page shows, so they always match the code. The committed `docs/plots/img/PXX.png` were drawn for spec review and can go stale, so the site doesn't use them.
6. **Hosting and which version the site shows.** GitHub Pages, built by a new workflow and deployed from `main` whenever a push changes what the site is built from, or by hand. Deploying is cheap, so the site follows `main` rather than the last release, and the Install page points users who want the latest features to installing from GitHub. A build (without deploy) runs in CI on every push so broken links fail early. Versioned docs (one site per release) wait until there is more than one release worth reading.
7. **Unit id and branch.** This file is `docs-site.md`. The worktree's branch is `docs`, which is ambiguous with the `docs/` folder in git commands, so the branch is renamed to `docs-site`.
8. **Logo.** The ASCII logo designed on 2026-10-15 is used as it is: a 20-column wordmark (compacted lifts of `=` and `:` rows, with the name in the middle lift) and a 10-column small mark (an `h` cut from the same lifts). Both are pure 7-bit ASCII, with no frame. In this unit:
   - `logo.txt` moves into the repo as `docs/img/logo.txt`, the single source for both marks;
   - both marks are rendered to SVG by a script, from `logo.txt`: each `=` and `:` as shapes and each letter as an outline, rather than font glyphs, so they look the same everywhere. It is rerun whenever `logo.txt` changes;
   - the wordmark SVG goes at the top of `README.md` as an image, checked on GitHub and in PyPI's rendering of the long description, and heads the site's home page (changed in the build from a code block: an image reads as a logo);
   - the small mark is the site's header logo and the favicon.
9. **The name, next to the logo.** The home page and the README explain the name in two lines, under the wordmark:

   > *Hangtu* is Chinese for rammed earth, one of the oldest ways of building with soil: it raised city walls in China more than 4,500 years ago. `hangtu` respects the long tradition of humans building with earth materials while automating the mundane and leaving judgment to the engineer.

   Checked 2026-10-16: rammed-earth (hangtu) city walls date to the Longshan period, for example Chengziya, around 2600 BCE. Mudbrick is older (Jericho, around 9000 BCE), so the text says "one of the oldest", not "the oldest".

### Out of scope
- New features, plots or analyses. A docstring that is wrong or missing is fixed in this unit, each fix its own commit.
- Tutorials beyond the two getting-started paths, notebooks, and a gallery beyond the plot pages.
- Versioned docs, a custom domain, theme work, search tuning.
- Other logo work: a social or PyPI card image, other designs (wavy lifts were set aside for later).
- Publishing the internal specs.
- Moving `SPEC.md` content into user docs. That shrinking happens per section as the user docs cover it (process.md, "Does SPEC.md eventually go away?").

### SPEC sections touched
- §12.1: the docs line. The intent commit records that the site is built now, ahead of v0.2; the close-out records where it lives, how it is built and deployed, and the `docs` dependency group.
- §12.4: a row for this unit, if it is counted as a milestone.
- `README.md` (the wordmark, the name and a link to the site), `pyproject.toml` (the `docs` group and a `Documentation` URL), `.github/workflows/` (the build and deploy), `CLAUDE.md` (the docs commands and where the site source lives).

## Spec

The intent's decisions, made exact. The site has no other feature spec, so this section is it. Zensical behavior marked "checked" was tried on a scratch site with Zensical 0.0.70 on 2026-10-16.

### 1. Layout of the files
| Path | Content | In git |
|---|---|---|
| `zensical.toml` | The site configuration (§2) | yes |
| `docs/site/` | The site source: Markdown pages, by section (§3) | yes |
| `docs/site/examples/<name>.py` | The example shown on each page (§4) | yes |
| `docs/site/img/generated/` | Figures, printed output, header logo and favicon written by `docs/prepare_site.py` | no (gitignored) |
| `docs/site/img/wordmark.svg` | The wordmark, written by `docs/prepare_site.py` | yes, because the README links to it |
| `docs/site/reference/columns.md` | The column registry page, written by `docs/prepare_site.py` (§5) | no (gitignored) |
| `docs/prepare_site.py` | Writes everything generated, before a build (§5) | yes |
| `docs/img/logo.txt` | The wordmark and the small mark, the one source for both (§6) | yes |
| `build/site/` | The built site (`site_dir`) | no (`build/` is already gitignored) |

Building, locally and in CI:
```
uv sync --group docs
uv run python docs/prepare_site.py
uv run zensical build --clean --strict      # or: uv run zensical serve
```
`--strict` stops the build on any warning, including a link to a page that doesn't exist (checked), and a missing snippet file stops it in any mode (checked).

### 2. Configuration (`zensical.toml`)
- **Project:** `site_name = "hangtu"`, `site_url = "https://konnerhorton.github.io/hangtu/"`, `site_description` (the PyPI description), `repo_url` to the GitHub repo, `docs_dir = "docs/site"`, `site_dir = "build/site"` (checked), and an explicit `nav` (§3). The build output stays out of `/site`, so `docs/site/` is the only thing called `site`. The existing `/site` line in `.gitignore` is removed.
- **Theme:** the default theme. Features: `content.code.copy`, `navigation.instant`, `navigation.sections`, `navigation.footer`, `navigation.top`, `search.highlight`. The light/dark toggle that follows the system setting, as `zensical new` writes it. `logo` and `favicon` point to the generated SVGs (§6; an SVG works for both, checked). No other theme settings.
- **Markdown extensions:** the set `zensical new` writes (admonitions, details, tabs, highlighting, superfences, attribute lists), plus:
  - `pymdownx.arithmatex` with `generic = true`;
  - `pymdownx.snippets` with `base_path = ["docs/site/examples", "examples"]` and `check_paths = true`, so pages include the example files instead of copying them.
- **Math:** `extra_javascript` lists `docs/site/javascripts/mathjax.js` (Zensical's documented config, which retypesets after instant navigation) and `https://unpkg.com/mathjax@3.2.2/es5/tex-mml-chtml.js`, pinned. MathJax 3 because it's what Zensical's config is written for.
- **API reference:** the mkdocstrings plugin with the Python handler: `paths = ["src"]`, `docstring_style = "numpy"`, `show_source = false`, `show_root_heading = true`, `show_signature_annotations = true`, `separate_signature = true`, `members_order = "source"`, `filters = ["!^_"]`. No external inventories, so a build needs no network beyond package install.
- **Dependencies:** a `docs` group in `pyproject.toml` with `zensical==0.0.70` (exact, since it's alpha) and `mkdocstrings-python>=2.0.9`. `uv.lock` holds the rest. The group isn't installed by default, so the existing CI jobs don't change.

### 3. Pages and navigation
Every page in Getting started, Guides and Plots follows one shape: a title, one sentence on what the page is for, the example (§4) with its output, then the explanation, and last a "See also" list linking to the reference.

| Nav | File | Content |
|---|---|---|
| Home | `index.md` | The wordmark and the name (§6), what hangtu does in a few bullets (from the README's "What it does"), a figure, one short example, and links to Install and Getting started |
| Install | `install.md` | Two ways, in tabs. **Latest** (what this site describes), first: `pip install git+https://github.com/konnerhorton/hangtu` (and the `uv add` equivalent). **Released**: `pip install hangtu`, which may lag the site. Then the Python and OS support, and checking the version |
| Getting started | `getting-started/csv.md` | CSV → plot: a template, filling it in, reading it with units, a plot. The full `examples/csv_to_plot.py` in a collapsed block |
| | `getting-started/ags.md` | AGS → QC → plot: a project, the geology map, QC, a dataset, a plot. The full `examples/ags_qc_plot.py` in a collapsed block |
| Guides | `guides/units.md` | Declaring units, display units (US and SI), what happens when a unit is missing |
| | `guides/templates.md` | CSV templates, `ht.columns()`, the registry, flagged values (NP, refusal, `<x`) |
| | `guides/ags-and-qc.md` | Ingest, the project database, `p.qc()` and its report, `p.diff()` |
| | `guides/datasets.md` | `p.spt()`, `p.atterberg()`, `p.grain_size()`, `p.permeability()`, their filters, and the depth, elevation and geology joins |
| | `guides/spt.md` | SPT analysis with `ht.analysis.spt()` and `ht.analysis.spt_class()`: refusal, N60 from the energy ratio (with the formula), the cap, and the classes, including that choosing the table is the engineer's call |
| Plots | `plots/index.md` | What every plot shares: `(fig, ax)`, `ax=`, `display_units=`, out-of-range counts, the palette, and `ht.Sheet` for printable sheets |
| | `plots/profile.md` | P01, property profile |
| | `plots/spt-profile.md` | P02, SPT profile |
| | `plots/spt-histogram.md` | P03, SPT class histogram |
| | `plots/geology-unit-comparison.md` | P07, property by geology unit |
| Reference | `reference/project.md` | `ht.Project` |
| | `reference/plot.md` | `ht.plot` |
| | `reference/analysis.md` | `ht.analysis` |
| | `reference/data.md` | `ht.read_csv`, units (`set_units`, `units_of`, `define_unit`, `add_unit_alias`), `ht.template`, `ht.columns`, `ht.examples`, `ht.settings`, `ht.Sheet` |
| | `reference/errors.md` | The error and hint classes, and what each means for the user |
| | `reference/columns.md` | Generated (§5) |

Plot pages are added in the same unit as their plot (P04–P06 in M8), and the plot's close-out adds them. Each plot page has a "Common options" table of the few arguments an engineer is most likely to change, linking to the full signature in the reference.

### 4. Examples on the pages
- **One file per example** in `docs/site/examples/`, named after what it shows (`spt-profile.py`). A page includes it with a snippet (`--8<-- "spt-profile.py"`), so the code on the page is the code that runs.
- **Short and self-contained:** about 10 lines or fewer. It starts with `import hangtu as ht`, reads only `ht.examples` data, and needs nothing but hangtu installed (from `main`, §7). A plot example ends by saving its figure as `<name>.png`, which shows the user how to save one too. Other examples end by printing the result.
- **The figure is the example's output.** `docs/prepare_site.py` runs each example in a fresh temporary folder and copies `<name>.png` to `docs/site/img/generated/`. The page shows that image right under the code.
- **Near the top:** on Getting started, Guides and Plots pages, the first example comes before the first `##` heading.

### 5. `docs/prepare_site.py`
Run before every build. It:
1. runs each `docs/site/examples/*.py` (§4) and collects the figures. An example that fails stops the script with the example's name and error;
2. writes `reference/columns.md` from the registry: one table of every column, then each template's columns in order, with each column's name, description, quantity and US and SI units, as `ht.columns()` reports them. The `used_by` field is left out, since plot IDs (P01) mean nothing to a user;
3. writes `img/generated/logo.svg` and `img/generated/favicon.svg` from `docs/img/logo.txt` (§6).

It uses only hangtu and its runtime dependencies, so the `docs` group adds nothing to it.

### 6. Logo and name
- **`docs/img/logo.txt`** holds the two marks from `sandbox/logo/logo.txt`, unchanged: the 20-column wordmark, a blank line, then the 10-column small mark. Every line in each block has the same width.
- **README:** the wordmark SVG replaces the `# hangtu` heading at the top, linked by its raw GitHub URL so PyPI shows it too, and the two lines on the name (intent, decision 9) follow it.
- **Home page:** the same SVG, then the same two lines.
- **Wordmark SVG:** drawn like the small mark, with the letters as outlines of DejaVu Sans Mono Bold (shipped with matplotlib), in an earth tone (`#8a6a4a`) that reads on light and dark backgrounds. A test checks the committed file matches `logo.txt`.
- **SVG:** the small mark is drawn on a grid of character cells. Each `=` is two horizontal bars across its cell, each `:` is two small squares stacked in the middle of its cell, and spaces are empty. There is no text and no font, so it looks the same in every browser. `logo.svg` is white, for the colored header. `favicon.svg` is dark gray on transparent, for a browser tab.

### 7. Build and deploy
- **CI (`ci.yml`):** a new `docs` job on Ubuntu runs the three build commands in §1 on every push to `main` and every pull request.
- **Deploy (`docs.yml`, new):** on a push to `main` that changes any of `docs/site/**`, `docs/prepare_site.py`, `docs/img/logo.txt`, `zensical.toml`, `src/**` (docstrings and the registry feed the reference pages) or `examples/**`, and by hand (`workflow_dispatch`). It installs hangtu from the checkout, builds as in §1 and publishes `build/site/` with `actions/upload-pages-artifact` and `actions/deploy-pages`, as Zensical's own workflow does. It needs `pages: write` and `id-token: write`, and only for that job.
- **One-time setup by the user:** in the repo settings, set Pages to deploy from GitHub Actions. `main` may deploy to the `github-pages` environment by default.
- **Links:** `pyproject.toml` gets `Documentation = "https://konnerhorton.github.io/hangtu/"` under `[project.urls]`, and the README links to the site under the name. The README's Install section adds the install from GitHub for the latest features, next to `pip install hangtu`.

### 8. Acceptance criteria
1. The build in §1 passes with `--strict` on a clean checkout.
2. Every public name (`ht.__all__`, `ht.plot.__all__`, `ht.analysis.__all__`, and the public methods of `ht.Project`) appears on a reference page. A test checks the `:::` directives against those lists.
3. Every file in `docs/site/examples/` runs in an empty folder, and every plot example writes `<name>.png`. A test runs them, so the CI matrix covers them on all three operating systems.
4. Every Getting started, Guides and Plots page includes an example before its first `##` heading. A test checks the Markdown.
5. `reference/columns.md` lists every column in the registry. A test checks it.
6. The SVGs have one shape pair per `=` or `:` and one outline per letter, with no text, and the committed wordmark SVG that the README shows matches `docs/img/logo.txt`. Tests check both.
7. Math renders in a browser on a page and in a docstring: checked by eye with `zensical serve` at the close-out.
8. The wordmark renders monospaced on GitHub, and in PyPI's rendering of the README (checked on TestPyPI at the next release rehearsal).
9. The first deploy from `main` serves the site at the `site_url`.

### SPEC and other changes at the close-out
- SPEC §12.1: the docs line says where the site lives, how it is built, when it is deployed, and the `docs` group.
- `CLAUDE.md`: the docs commands under Commands, `docs/site/` under Where things are, and the status line.
- `.gitignore`: the two generated paths in §1, and `/site` removed (§2).
- `docs/plots/README.md`: a plot's close-out adds its page to the site (§3).

## Plan

Each step is one commit (two where noted), green under ruff and pytest and under about 300 changed lines. Section numbers refer to the Spec above.


### 1. Scaffold the site (`docs: scaffold the Zensical site`)
- `pyproject.toml`: `[dependency-groups] docs = ["zensical==0.0.70", "mkdocstrings-python>=2.0.9"]`; `uv lock`.
- `zensical.toml` at the root, per spec §2: project keys (`docs_dir = "docs/site"`, `site_dir = "build/site"`, `site_url`, `repo_url`), the theme features and light/dark palette (copied from `zensical new` output), the markdown extensions from `zensical new` plus `pymdownx.arithmatex` and `pymdownx.snippets` (`base_path = ["docs/site/examples", "examples"]`, `check_paths = true`), MathJax `extra_javascript` (pinned 3.2.2), the mkdocstrings Python handler options, and `nav` with only Home for now.
- `docs/site/index.md` (placeholder), `docs/site/javascripts/mathjax.js` (Zensical's documented config).
- `.gitignore`: drop `/site`; add `docs/site/img/generated/` and `docs/site/reference/columns.md`.
- Check: `uv sync --group docs && uv run zensical build --clean --strict`.

### 2. Examples runner (`docs: run the page examples before a build`)
- `docs/prepare_site.py` with `main()` and one function per job (spec §5). This step: `run_examples()` runs each `docs/site/examples/*.py` in a fresh temp folder with `MPLBACKEND=Agg` (same subprocess pattern as `tests/test_examples.py::test_example_runs_clean`), stops with the example's name and stderr on failure, and copies `<name>.png` to `docs/site/img/generated/`.
- First example: `docs/site/examples/spt-profile.py` (≤10 lines: `ht.read_csv(ht.examples.path("spt.csv"), units=...)`, `ht.plot.spt_profile(...)`, `fig.savefig("spt-profile.png")`), shown on the placeholder home page.
- `tests/docs/test_site.py`: parametrized over `docs/site/examples/*.py`, runs each in `tmp_path` like `test_example_runs_clean` (returncode 0, empty stderr, `<name>.png` written for files that call `savefig`). Criterion 3.

### 3. Logo and name (`docs: add the ASCII logo to the README and site`)
- Move `sandbox/logo/logo.txt` → `docs/img/logo.txt` (copy; the sandbox is the user's to clean up).
- `prepare_site.py`: `write_logo()` parses the small mark (second block) and writes `img/generated/logo.svg` (white) and `favicon.svg` (dark gray): `=` → two bars, `:` → two stacked squares, per cell; no text. `zensical.toml`: `theme.logo`, `theme.favicon`.
- `README.md`: wordmark in a plain fence replacing `# hangtu`, then the two lines on the name (intent decision 9). Home page: same, fence with `{ .text .no-copy }`. *Changed after review: both use the wordmark as an SVG image, `docs/site/img/wordmark.svg`.*
- Tests: SVG has 2 shapes per `=`/`:` in the small mark; README's first fence equals the wordmark block in `logo.txt`; `tests/test_readme.py` still finds two `python` blocks. Criterion 6.

### 4. Reference pages (`docs: generate the API and column reference`)
- `docs/site/reference/{project,plot,analysis,data,errors}.md` with `:::` directives (spec §3). `ht.settings` is documented through its class (`hangtu._settings.Settings`), titled `ht.settings`.
- `prepare_site.py`: `write_columns_page()` from `ht.columns()`: one table of every column (a table per template would repeat most rows), then each template's column list; table columns name, description, quantity, US unit, SI unit (no `used_by`).
- Tests: every name in `ht.__all__`, `ht.plot.__all__`, `ht.analysis.__all__`, `ht.examples.__all__` has a `:::` directive (criterion 2); `columns.md` has every registry column (criterion 5).
- Docstrings that render badly or warn under `--strict` are fixed in their own commits (`docs: fix the <name> docstring`), before this step's commit.

*Built in the order 6 and 7, then 5, in two commits: the guides and plot pages link to each other, and the home and getting-started pages link to both, so each commit builds with `--strict`. Pages that print a result show the output the examples print, which `docs/prepare_site.py` saves as `<name>.txt` next to the figures.*

### 6. Guides (with step 7: `docs: write the guides and plot pages`)
- `guides/units.md`, `templates.md`, `ags-and-qc.md`, `datasets.md`, `spt.md` (N60 formula in MathJax, refusal, cap, classes, the table is the engineer's call), each with its example file.

### 7. Plot pages (with step 6)
- `plots/index.md` (shared behavior, `ht.Sheet`), `profile.md`, `spt-profile.md`, `spt-histogram.md`, `geology-unit-comparison.md`, each with an example, its figure and a "Common options" table.

### 5. Home, Install, Getting started (`docs: write the home, install and getting-started pages`)
- `index.md` (wordmark, name, what it does, figure, one example, links), `install.md` (tabs: latest from GitHub first, then PyPI), `getting-started/csv.md` and `ags.md` with short examples from `docs/site/examples/` and the full `examples/*.py` in a collapsed `???` block via snippets.
- Test: each page under Getting started, Guides and Plots in the `nav` (read with `tomllib`) has a `--8<--` include before its first `## ` (criterion 4).

### 8. CI and deploy (`docs: build the site in CI and deploy it from main`)
- `ci.yml`: `docs` job (Ubuntu, Python 3.12): `uv sync --locked --group docs`, `uv run python docs/prepare_site.py`, `uv run zensical build --clean --strict`.
- `.github/workflows/docs.yml`: on push to `main` with the `paths` in spec §7, and `workflow_dispatch`; same build, then `actions/configure-pages`, `upload-pages-artifact` (`path: build/site`), `deploy-pages`; `pages: write` and `id-token: write` on that job only.
- `pyproject.toml`: `Documentation` URL. `README.md`: install from GitHub for the latest features, and a link to the site.

### 9. Close-out (last build commit)
- SPEC §12.1 docs line; `CLAUDE.md` commands (`uv sync --group docs`, prepare, build/serve), `docs/site/` under Where things are, status line; `docs/plots/README.md`: a plot's close-out adds its page.
- By eye with `zensical serve`: math on the SPT guide and in a docstring, the header logo and favicon, light and dark (criterion 7).
- After merge and push (with approval): the user sets Pages to deploy from GitHub Actions; check the site at the `site_url` (criterion 9). README on PyPI is checked at the next TestPyPI rehearsal (criterion 8).

### Verification
- Every step: `uv run ruff check . && uv run ruff format --check . && uv run pytest`, and from step 1 on `uv run python docs/prepare_site.py && uv run zensical build --clean --strict`.
- Criteria 1–6 are tests or the strict build; 7 by eye at step 9; 8 and 9 after merge.
