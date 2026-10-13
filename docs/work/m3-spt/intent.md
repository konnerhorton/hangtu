# M3: P02–P03 and the SPT analysis — intent

Shared intent for three units of work, each on its own branch and merged on its own:

| Unit | Branch | Plan | Builds |
|---|---|---|---|
| SPT analysis | `m3-spt-analysis` | [plan](../m3-spt-analysis/plan.md) | `ht.analysis.spt()`, `ht.analysis.spt_class()` |
| P02 | `m3-p02` | [plan](../m3-p02/plan.md) | `ht.plot.spt_profile()` |
| P03 | `m3-p03` | [plan](../m3-p03/plan.md) | `ht.plot.spt_histogram()` |

The analysis is merged first. P02 and P03 branch off `main` after it, in that order.

## Goal
Build the SPT analysis (from `docs/drafts/analysis.md` §1), P02 SPT N profile and P03 SPT class histogram.

## Why
- M3 is the next milestone in SPEC §12.4.
- SPT is the most common test in US practice. P02 and P03 are both on almost every report.
- P02 builds on P01, so it shows whether the P01 overlays can really be reused.
- The analysis stands on its own: an engineer can compute N60, refusals and classes without drawing anything.

## Constraints
- Use the P00 framework and the P01 overlays (`plot/_overlays.py`). Don't reimplement them.
- SPEC §2.6 (units), §3 (plot contract), §4 (refusals at the cap with a note, N60 NULL until an energy ratio is given), §10.3 and CLAUDE.md "Naming" (registry column names), §11 (error messages), §12.1 (no new dependencies).
- Never drop data silently: refusals, blank N, rows with no energy ratio and excluded refusals all show up as counts.
- Golden values for the analysis are calculated by hand (CLAUDE.md "Workflow rules").
- **Done when** (SPEC §12.4): the P02 and P03 acceptance criteria and the SPT golden tests pass, and each plot's `visual-check.png` (US and SI) is committed in its close-out.

## Decisions
1. **Where the analysis spec lives.** `docs/drafts/analysis.md` §1 is finished in place as the SPT spec and marked decided. Analyses stay in one file of their own, apart from the plot specs, so they can be used without a plot; Atterberg and grain size follow in M4. This may be revisited when the file grows.
2. **Three units of work**, as in the table above.
3. **Mid-drive depth** from increments is deferred to Phase 2 (SPEC §8.2, §13.1). For CSV input, `depth` is what the user gives. The P02 spec says so.
4. **Refusal** comes from `spt_refusal` where it is filled in, else is inferred from `spt_penetration` < 450 mm. Report-string parsing and `refusal="extrapolate"` are deferred to Phase 2.
5. **SPT class tables** (TODO #4): the boundaries in `analysis.md` §1 are confirmed, with the lower bound inclusive, so N = 0 is "very loose" and N = 10 is "medium dense". Classes are computed from whichever N column the user names; the default is `spt_n`. User-defined bins come later.
6. **Cohesive or cohesionless** is the user's call. They pick the table (`table="cohesionless"` or `"cohesive"`) and pass the rows it applies to. `soil_class` isn't read, and there is no two-panel `spt_histograms()`: two calls on a `Sheet` do that.
7. **N or N60.** P02 and P03 plot `spt_n` by default. With `n="spt_n60"`, rows without N60 are left out and counted, and if no row has it, the error says to set `ht.settings.hammer_efficiency` or fill in `energy_ratio`. N and N60 are never mixed in one plot, and the axis label names the column.

## Out of scope
- AGS ingest, increments, mid-drive depth and report-string parsing (Phase 2).
- `refusal="extrapolate"`, and user-defined class bins.
- Statistics on censored refusals (TODO #8, Phase 3).
- Correlations from N (friction angle, modulus, s_u).
- Examples, the README and the tutorial (M5).

## SPEC sections touched
- §4: the pointer to `analysis.md` §1 says it is decided.
- §11: `spt_histograms(spt)` in the API sketch becomes `spt_histogram(spt, table="cohesionless")`.
- §13.1: deferred to Phase 2 (decision 3).
- `docs/drafts/analysis.md` §1, `docs/plots/README.md` (P02 and P03 status), `TODO.md` (#3 no longer blocks P03; #4 closed).
- `columns.yaml` (`spt_class`) and `config/spt_classes.yaml` (new).
