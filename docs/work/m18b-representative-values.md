# M18 (b): representative values

## Intent
M18 is selection, stage D (SPEC §1.3, §5, §12.4), in four units (`docs/work/m18a-refusals.md`): (a) SPT
refusals (done), **(b) this unit**, (c) P09, (d) sources compared, the selection as a judgment, and the
Mohr–Coulomb set.

### Goal
- One statistics function computes, per geology unit, the representative value of a parameter from its values,
  constant or as a line with depth, and offers it in the views engineers use: Eurocode 7's characteristic value
  and the cautious estimates US practice uses (a lower percentile, the mean less a multiple of the standard
  deviation).
- Its result gives each view as a number per unit and as the `design_lines` frame P01 already draws, so a
  selection (M18 (d)) and P09 (M18 (c)) read one calculation.

### Why
- **Stage D needs a value per unit, and hangtu stops at the distribution.** `describe()` and `fit()` summarize;
  nothing turns the values into the cautious estimate a design report states. Engineers do it by hand in a
  spreadsheet today, and the report can't show how.
- **EC7's characteristic value is one view, not the frame** (decided 2026-11-02, TODO #13). Most users are in the
  US and want a design line with depth or a cautious estimate per unit in their own terms. "One calculation, many
  views" (SPEC §5): the result keeps n, the mean, the standard deviation and the trend fit, and each view reads
  them, so two views of one set can't disagree on the data.
- **Depth trends are common and done by eye.** s_u and N60 rise with depth in most units; a constant value per
  unit is then too low at depth and too high near the top. EC7's depth-dependent procedure (a regression with
  its confidence or prediction interval, the EC7 summary §3.5) gives a defensible line.
- **The choices are judgments, and today they are invisible.** Which estimate (mean or fractile), which side
  (low or high), what V_X (computed or assumed), the scale of fluctuation and the failure length: only the
  engineer knows them (EC7 summary §3.2), and a result that hides them can be off by a factor of two.
- **What depends on it:** P09 (M18 (c)) draws it; selection (M18 (d)) records which view each unit and parameter
  uses.

### Scope
- **The function:** `ht.stats.representative(df, value=, by=, ...)` (decision 1), returning a
  `RepresentativeResult` of kind *parameter* (SPEC §5).
- **Constant per unit, or a line with depth** (`trend=None | "depth" | "elevation"`): a least-squares line, its
  confidence interval for a mean estimate and its prediction interval for a fractile.
- **The views**, each named by the user, none by default:
  - EC7 characteristic value, Formula 4.5 and Annex A as the JRC report (2025) restates them: Type A (mean) and
    Type B (fractile); V_X computed (Case 2) or assumed (Case 3); normal or lognormal; low or high side.
  - Type C, from Γ² computed by the variance function from θ and L (both arguments, in length units), with
    `gamma2=` as an override (decision 3).
  - A percentile of a fitted normal or lognormal distribution, the one the user names (decision 4).
  - Mean − k·s, k given by the user (Schneider's 0.5 and the simplified fractile's 1.75 are then just values
    of k, named in the docs, not methods).
- **Flagged values follow SPEC §5's input rules.** With censored values in a group, the mean and s come from
  `fit()`'s censored maximum-likelihood normal (or lognormal) fit, with a note that the k_n factors assume
  complete data (decision 2). Bounds from the correlations, and refusals with the M18 (a) limit, enter the same
  way. 🟡 How a depth trend takes censored values (a censored regression, or leaving them out and counting them)
  is for the spec.
- **Warnings the JRC guidance gives:** n below its guidance for the case (EC7 summary §3.7), a negative
  characteristic value from a normal fit (a sign the data are lognormal), a trend whose residuals aren't
  constant.
- **Golden values** from the JRC report's worked examples (Annexes I–III), and hand calculations for the US views.
- Docs: a "Representative values" guide, the API reference, and the statistics guide's pointer.

### Constraints
- SPEC §4: judgments have no defaults, are recorded on the result, and resolve argument → `judgments=` →
  the project's file. 🟡 In (b) the view's inputs (estimate, side, V_X, θ, L, k, p) are required arguments;
  the judgments file names them per unit and parameter in (d), when the selection becomes a judgment.
- SPEC §5: input rules (counts add up, flags from the registry, sources not pooled unawares, H&F 7 percentiles,
  units); one calculation, many views; a result object with `.to_frame()`, `.to_dict()` and a summary.
- SPEC §5, "statistics are designed for lab data": SPT N and its correlations get the simple treatment. 🟡 Type C
  on SPT is not worth offering (TODO #13).
- Never cite from memory: every formula and k_n is checked against the JRC report (public, CC BY 4.0), which
  quotes EN 1997-1:2024. The lognormal Annex A formulae and Angus (1988) are checked in the spec step, or left
  out (TODO #13).
- No new dependencies: SciPy has Student's t and the normal quantiles.

### Out of scope
- **P09**, the figure (M18 (c)). (b) gives the `design_lines` frame; P01 draws it as it does today.
- **The selection as a judgment**, sources compared by depth or unit, and model sets (M18 (d)).
- **Estimating θ from data** (detrending a CPT, fitting a correlation model). θ is an input; a helper is later.
- **Nominal values** (EC7's cautious estimate without statistics): a value with a reason, which (d)'s judgment
  file records.
- **Partial factors, η and design values**: hangtu stops at the representative value (EC7 summary §5).
- **Bivariate c′–φ′ characteristic values**: they come with the Mohr–Coulomb set in (d), if at all.
- **Non-linear trends.** A line on depth only; 🟡 whether `log=True` (a line through ln values) is in (b) is
  for the spec.

### SPEC sections touched
- SPEC §5: the function list (`characteristic` becomes `representative`, decision 1), the views and their
  defaults (none), how censored values enter.
- SPEC §12.4: M18 (b)'s status.
- `docs/TODO.md` #13: resolved into SPEC §5 and deleted, or narrowed to what stays open (Type C, lognormal).
- `docs/drafts/phase3-stats.md`: its `characteristic` row points to the built function.
- `docs/reference/eurocode7-summary.md` §7: the proposed API is superseded by the spec.

### Decisions (intent review, 2026-11-03)
1. **The function is `ht.stats.representative()`, not `characteristic()`.** EC7's 2nd-generation term covers a
   statistical and a cautious estimate (EC7 summary §2), and it reads plainly to US users; `characteristic` would
   frame the US views as variants of an EC7 method. The EC7 view keeps the name "characteristic value".
2. **Censored values enter through the censored maximum-likelihood fit.** The mean and s come from `fit()`'s
   normal or lognormal fit, so refusals (with or without the M18 (a) limit), `<x`/`>x` and bounded correlation
   estimates are treated as in `fit()`, not biased low at their value as in `describe()`. The note says EC7's
   k_n factors assume complete data.
3. **Type C is in, from θ and L.** It is most real cases (JRC), and it adds one term to k_n; Γ² comes from the
   variance function, with `gamma2=` to give it directly. θ and L are inputs, never defaults; estimating θ is
   out of scope.
4. **The percentile view is of the fitted distribution**, normal or lognormal as the user names, so it handles
   censored values and a small n, and matches P08. The empirical percentile stays `describe()`'s.
