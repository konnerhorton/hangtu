# M3: P02–P03 and the SPT analysis — intent (draft for discussion)

**Status:** draft. Comment, edit or answer inline. The questions are marked **Q1–Q7** and each has Claude's recommendation. Once they're answered, this becomes the real intent.

## Goal
Build the SPT analysis (`ht.analysis.*`, from `docs/drafts/analysis.md` §1), P02 SPT N profile (`ht.plot.spt_profile`) and P03 SPT histograms (`ht.plot.spt_histogram`, `ht.plot.spt_histograms`).

## Why
- M3 is the next milestone in SPEC §12.4.
- SPT is the most common test in US practice. P02 and P03 are both on almost every report.
- P02 builds on P01, so it shows whether the P01 overlays can really be reused.

## Constraints
- Use the P00 framework and the P01 overlays (`plot/_overlays.py`). Don't reimplement them.
- SPEC §2.6 (units), §3 (plot contract), §4 (refusals at the cap with a note, N60 NULL until an energy ratio is given), §10.3 and CLAUDE.md "Naming" (registry column names), §11 (error messages), §12.1 (no new dependencies).
- Never drop data silently: refusals, blank N and rows left out of a histogram all show up as counts.
- Golden values for the analysis are calculated by hand (CLAUDE.md "Workflow rules").
- **Done when** (SPEC §12.4): the P02 and P03 acceptance criteria and the SPT golden tests pass, and `visual-check.png` (US and SI) is committed in the close-out.

## Scope and structure

### Q1. Where does the SPT analysis spec live?
`docs/drafts/analysis.md` §1 has to become a feature spec before we build from it (CLAUDE.md).
- **Recommendation:** a new `docs/analyses/spt.md`, because it outlives this unit. M4 adds `atterberg.md` and `grain-size.md` next to it. §1 is then removed from the draft and replaced by a pointer.
- **Other option:** `docs/work/m3-spt/spec.md`.

> Answer:

### Q2. One unit of work or several?
- **Recommendation:** one branch (`m3-spt`) with three specs: the SPT analysis, P02 and P03. The build commits go in this order, at about 300 lines or less each: analysis → P02 → P03 → test data and visual check.
- **Other option:** three units (`m3-spt-analysis`, `m3-p02`, `m3-p03`), each merged on its own.

> Answer:

## What M3 builds and what waits for Phase 2

The CSV template (`columns.yaml`, `spt`) has no increment columns and no report string. So these items only matter on AGS ingest:

### Q3. Mid-drive depth from increments
SPEC §8.2, and open question SPEC §13.1.
- **Recommendation:** defer to Phase 2. For CSV input, `depth` is whatever the user gives us. The P02 spec says so.

> Answer:

### Q4. Refusal detection
- **Recommendation for M3:** refusal comes from `spt_refusal` when the column is there. Otherwise it is inferred when `spt_penetration` < 450 mm.
- Parsing report strings such as `25/75 50/30` is deferred to Phase 2.
- `refusal="extrapolate"` (N = blows × 300 / penetration) needs the blow count for the partial drive. That isn't in the CSV template, so it is deferred as well, unless we add a column for it now.

> Answer:

## Decisions only you can make

### Q5. SPT class tables (TODO #4)
TODO #4 says the tables are already in `config/spt_classes.yaml`, but that file doesn't exist. The values in `analysis.md` §1 are:
- **Cohesionless** (Terzaghi & Peck 1948 / Peck, Hanson & Thornburn 1974): very loose 0–4, loose 4–10, medium dense 10–30, dense 30–50, very dense > 50.
- **Cohesive** (Terzaghi & Peck 1948): very soft < 2, soft 2–4, medium stiff 4–8, stiff 8–15, very stiff 15–30, hard > 30.

Please confirm:
- (a) the boundaries;
- (b) the boundary convention. With lower bound inclusive, N = 10 is "medium dense", not "loose";
- (c) whether to classify on N or N60 by default.

> Answer:

### Q6. Which rows are cohesive and which cohesionless (TODO #3)
P03 needs a rule. The current `soil_class` draft is `coarse | fine | organic | fill | rock`.
- **Recommendation:**
  - `coarse` → cohesionless histogram;
  - `fine` → cohesive histogram;
  - `organic`, `fill`, `rock` and blank → in neither, but counted in the note so nothing is dropped silently.
- Users can always pass their own filtered data to `spt_histogram()` instead.
- This needs TODO #3 settled, or at least settled enough for P03.

> Answer:

### Q7. No energy ratio
N60 has no default (SPEC §4), so with most CSVs it will be empty.
- **Recommendation:** P02 and P03 fall back to N, with a hint that says how to set `hammer_efficiency` or the `energy_ratio` column.
- The labels always say "SPT N" or "SPT N60", so the two are never mixed up.
- A dataset where some rows have an energy ratio and some don't: plot N60 where it exists, and leave the rest out with a count? Or plot N for everything?

> Answer:

## Out of scope
- AGS ingest, increments, mid-drive depth and report-string parsing (Phase 2).
- Statistics on censored refusals (TODO #8, Phase 3).
- Correlations from N (friction angle, modulus, s_u).
- Examples, the README and the tutorial (M5).

## SPEC sections touched
- §4 (pointer to the new analysis spec) and §13.1 (if Q3 is deferred).
- `docs/drafts/analysis.md` (§1 moves out), `docs/plots/README.md` (P02 and P03 status), `TODO.md` (#3, #4).
- `columns.yaml` (any new SPT columns) and `config/spt_classes.yaml` (new).
