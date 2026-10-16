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
- **Short examples near the top:** each getting-started, guide and plot page opens with an example of a few lines that a user can copy (with the copy button) and run right after `pip install hangtu`, on the data in `ht.examples`. No clone, download or setup.
- **Docs don't rot:** code shown on the site runs in CI, either because it is pulled in from `examples/` or because a test runs it. Reference pages (API, columns) are generated from the code and `columns.yaml`, not copied.
- **The internal docs stay internal.** `SPEC.md`, `docs/work/`, `docs/plots/`, `docs/data/` and `docs/drafts/` are specs for building hangtu and are not published as user docs. Their paths don't move, since SPEC, TODO and CLAUDE.md link to them.
- **Dependencies:** Zensical and `mkdocstrings-python` go in a `docs` dependency group, never in the runtime dependencies (approved in review).
- American spelling; nothing private (the repo is public).

### Decisions (settled in review)
1. **Where the site source lives.** `docs/` already holds the internal specs, and `/site` is gitignored as the build output. `docs/site/` is Zensical's `docs_dir`, and `zensical.toml` is at the repo root. Moving the internal docs out of `docs/` instead would break many links.
2. **Pages for the first version**, all short:
   - Home (what hangtu is, who it's for, a figure);
   - Install;
   - Getting started: CSV → plot and AGS → QC → plot, from `examples/`;
   - Guides: units, CSV templates and the column registry, AGS ingest and QC, datasets;
   - Plots: one page per shipped plot (P01–P03, P07, and P04–P06 as they land), each with its figure and the options an engineer is likely to change;
   - Reference: API from the numpy docstrings, and the column registry from `columns.yaml`.
3. **API reference.** Generated from the numpy docstrings with mkdocstrings and `mkdocstrings-python`. Checked 2026-10-16 with Zensical 0.0.70, mkdocstrings 1.0.7 and mkdocstrings-python 2.0.9 on a test site built from `hangtu.analysis`: the API pages render, cross-references (`[text][hangtu.analysis.plasticity]`) resolve from guide pages, and `objects.inv` is written. Zensical is still alpha, so its version is pinned in the `docs` group and raised deliberately.
4. **Math.** Pages and docstrings need equations (N60, consistency index, correlations). MathJax through `pymdownx.arithmatex` (`generic = true`), with `$...$` inline and `$$...$$` on their own lines for blocks, and the MathJax script pinned to an exact version. The same test site showed math in both Markdown pages and docstrings reaching the HTML ready for MathJax. A docstring that contains math needs a raw string (`r"""`). KaTeX is faster but covers less LaTeX, and only MathJax produces MathML for screen readers.
5. **Figures.** The build draws them from `ht.examples` data with the same code the page shows, so they always match the code. The committed `docs/plots/img/PXX.png` were drawn for spec review and can go stale, so the site doesn't use them.
6. **Hosting and which version the site shows.** GitHub Pages, built by a new workflow and deployed on each `v*` tag, so the site matches what `pip install hangtu` gives. A build (without deploy) runs in CI on every push so broken links fail early. Versioned docs (one site per release) wait until there is more than one release worth reading.
7. **Unit id and branch.** This file is `docs-site.md`. The worktree's branch is `docs`, which is ambiguous with the `docs/` folder in git commands, so the branch is renamed to `docs-site`.
8. **Logo.** The ASCII logo designed on 2026-10-15 is used as it is: a 20-column wordmark (compacted lifts of `=` and `:` rows, with the name in the middle lift) and a 10-column small mark (an `h` cut from the same lifts). Both are pure 7-bit ASCII, with no frame. In this unit:
   - `logo.txt` moves into the repo as `docs/img/logo.txt`, the single source for both marks;
   - the wordmark goes at the top of `README.md` in a plain code block, checked on GitHub and in PyPI's rendering of the long description;
   - the wordmark heads the site's home page, also as text;
   - the small mark is rendered to SVG for the site's header logo and the favicon. A script generates the SVG from `logo.txt`, drawing each `=` and `:` as shapes rather than font glyphs so it looks the same everywhere, and it is rerun whenever `logo.txt` changes.
9. **The name, next to the logo.** The home page and the README explain the name in two lines, under the wordmark:

   > *Hangtu* is Chinese for rammed earth, one of the oldest ways of building with soil: it raised city walls in China more than 4,500 years ago. `hangtu` respects the long tradition of humans building with earth materials, while automating the mundane and leaving judgment to the engineer.

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
