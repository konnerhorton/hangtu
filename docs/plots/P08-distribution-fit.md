# P08 — Distribution fit

| | |
|---|---|
| **ID / function** | P08 · `ht.plot.distribution_fit()` (+ `ht.stats.fit()`; also `FitResult.plot()`) |
| **Status** | built (M15 (c), 2026-10-30); image [`img/P08.png`](img/P08.png) |
| **Type** | plot + analysis (statistics) |
| **Milestone** | M15 (c) (SPEC §12.4), [`docs/work/m15c-fit.md`](../work/m15c-fit.md) |
| **Depends on** | P00; `ht.stats.fit()` (M15 (c) Spec) |
| **Related** | SPEC §5; TODO #8, #48; P24 and P27 (drafts) |

---

## 1. Purpose
Shows how well each candidate distribution fits one property's values in one group (e.g. N60 in the Alluvium),
so the AICc ranking of `ht.stats.fit()` can be checked by eye before a distribution is used in selection (M18).
The figure goes in a calculation package or an appendix of a ground investigation report, beside the result's
table.

## 2. Reference figure
```
  Probability density                          Value (kPa)
  ┌──────────────────────────────┐  ┌───────────────────────┐
  │      ▆▆                      │  │                    ●  │
  │   ▆▆ ██ ▆▆      ── lognormal │  │               ● ╱     │
  │   ██ ██ ██ ▆▆   -- normal    │  │           ●  ╱        │
  │ ▆▆██ ██ ██ ██▆▆ ·· gamma     │  │       ● ╱             │
  │ ██████████████  △ ≥100: 2    │  │    ●╱   lognormal     │
  └──────────────────────────────┘  └───────────────────────┘
        Value (kPa)                     Fitted quantile (kPa)
                                      Rank  Distribution  ΔAICc  AD p
                                      (text box, under the Q-Q panel)
```
A good version: the histogram and the curves share the density scale, so their areas agree; the Q-Q points sit
on the 1:1 line where the fit is good, and the eye goes to the tails, where fits differ.

## 3. Input data
**Row grain:** one row per value (per test, per specimen, per estimate), as `fit()` reads.

| Column | Description | Req.? | Notes |
|---|---|---|---|
| `value=` | the property fitted, any registry column | ✔ | units as SPEC §2.6 |
| `by=` columns | groups, as `fit()` | | one group drawn per figure |
| flag and source columns | `spt_refusal`, `qualifier`, `non_plastic`, … | | read by `fit()` (SPEC §5) |

**Value flags handled:** right-censored values (refusals, `>x`) and left-censored ones (`<x`) are not in the
histogram's bins: each is drawn as an open triangle at its bound on the value axis, pointing the way the true
value lies, with a count in the legend ("≥ 100: 2"). NP, assumed values and bands are left out by `fit()` and
counted in the footnote.

**Minimum data:** as `fit()`: a group with fewer than 4 uncensored values draws the histogram and the note "too
few values to fit (n = 3; 4 needed)", no curves and an empty Q-Q panel with the same note. *Changed in the
build:* `distribution_fit()` fits only the rows of the group drawn (faster, and the source check reads only
them), so for it such a group is `fit()`'s error; `FitResult.plot()` of a result with other groups draws it.

## 4. Analysis / calculations
`ht.stats.fit()` (M15 (c) Spec, Decisions 1–10). The plot draws the result; it computes nothing of its own apart
from the histogram's bins.
- **Histogram:** uncensored values in bins from `numpy.histogram_bin_edges(values, bins)`, `bins="auto"` by
  default (the larger of Sturges's and Freedman–Diaconis's counts), scaled so the bars' area is the share of
  values uncensored. The fitted PDFs integrate to 1 over all values, so the bars and the curves are on one
  scale when some values are censored.
- **Q-Q points:** for the chosen distribution, x = its fitted quantile F⁻¹(pᵢ) at each uncensored value's
  plotting position pᵢ (Decision 8), y = the value. A 1:1 line. Both axes in the value's units.

## 5. Figure layout
- **Panels:** two, side by side: histogram with the PDFs (left, wider, 3:2), Q-Q (right, equal aspect).
- **Default size:** the `default` kind (6.5 × 4.5 in), whole figure with the legend and footnote.
- **Orientation:** landscape.
- **Legend:** inside the histogram, in the first clear corner, else the least covered, never below the axes
  (*changed in the build* from README's fallback: a legend below is wider than the histogram and squeezes the
  Q-Q panel). The y axis has 40 % headroom over the tallest bar and the rank-1 curve, so the top corners are
  usually clear.

## 6. Axes
| | Histogram x | Histogram y | Q-Q x | Q-Q y |
|---|---|---|---|---|
| Quantity | the value | probability density | fitted quantile of the value | the value |
| Label (SI) | registry label + unit, e.g. "Undrained shear strength, s_u (kPa)" | "Probability density (1/kPa)" | "Fitted quantile, lognormal (kPa)" | registry label + unit |
| Scale | linear; `log=True` for a log axis (bins log-spaced) | linear | as the histogram's x | as the histogram's x |
| Limits | data and censored bounds, nice numbers; starts at 0 on a ratio scale | from 0 | equal to Q-Q y | data, nice numbers |

**Range constraints:** Q-Q is equal aspect, its two axes share limits.

## 7. Data marks
| Series | Mark | Color | Legend |
|---|---|---|---|
| Histogram | bars, light gray fill, thin edge | — | "Values (n = 23)" |
| Fitted PDFs | lines, one per distribution, ranked order | categorical palette, rank 1 solid and thicker, others dashed | "lognormal (rank 1)" |
| Censored values | open triangles at the bound on the x axis | dark gray | "≥ 100: 2" / "< 0.1: 1" |
| Q-Q points | filled circles | the distribution's color | — |
| 1:1 line | thin black | — | — |

**Draw order:** histogram → censored markers → PDFs; 1:1 line → Q-Q points.

## 8. Overlays and annotations
| Overlay | Argument | Default | Style |
|---|---|---|---|
| Fit table | `table=` | on | text box under the Q-Q panel's x label: rank, distribution, ΔAICc, AD p (or "—" with censored values). *Changed in the build* from the histogram's clear corner: the legend and the curves leave none reliably, and the Q-Q panel's equal aspect leaves room below it |
| Distributions drawn | `distributions=` | all fitted | names from the result |
| Q-Q distribution | `qq=` | the rank-1 fit | a name |
| Footnote | — | always when something is left out | counts left out, "no AD check: n censored", "no plotting positions: censored both ways", "values ≤ 0: lognormal, gamma, Weibull not fitted" |
| `reference_lines`, `note` | as README | off | as README |

## 9. Units behavior
The fit is made in the display units (`fit(display_units=...)`), so every axis, the table and the PDFs are in
them; the density's unit is the reciprocal of the value's. N and dimensionless values have no unit.

## 10. API
```python
def distribution_fit(
    df: pd.DataFrame,
    *,
    value: str,
    by: str | list[str] | None = None,
    group: str | tuple | None = None,
    distributions: list[str] | None = None,
    bounds: tuple[float | None, float | None] | Literal["auto"] = "auto",
    pool: str | list[str] | None = None,
    include_assumed: bool = False,
    qq: str | None = None,
    bins: int | str = "auto",
    log: bool = False,
    table: bool = True,
    reference_lines: list[tuple[float, str]] | None = None,
    note: str | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    **style_overrides,
) -> tuple[Figure, np.ndarray, FitResult]:
```
- Calls `ht.stats.fit()` with the shared arguments and draws one group: with `by=`, `group=` names it (a value,
  or a tuple for several columns); a missing or unknown `group` is an error listing the groups.
- `FitResult.plot(group=None, **kwargs)` draws the same figure from an existing result, without refitting.
- Returns `(fig, axs, result)` (README: a plot that runs an analysis also returns its result). No `ax=`: two
  panels need a figure; `ht.Sheet` composition of two-panel plots is P00's later work.
- **`log=`** is an axis setting here, not a statistic: `fit()` has none (M15 (c) intent 3).

**Example:**
```python
fig, axs, result = ht.plot.distribution_fit(p.spt(), value="spt_n60", by="geology_unit", group="Alluvium")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty group | Error from `fit()` naming the group |
| Fewer than 4 uncensored values | `FitResult.plot()`: histogram only, note, empty Q-Q with the note; `distribution_fit()`: `fit()`'s error (§3) |
| Censored both ways | Fits and table drawn; Q-Q panel empty with "no plotting positions: censored both ways" |
| Values ≤ 0 | Normal (and beta) drawn; footnote names the distributions not fitted |
| Missing units | `fit()`'s error naming the column and how to declare its units: the fit's parameters and table need the unit (*changed in the build* from "(units unknown)") |
| Sources mixed | `fit()`'s error, raised: one group of one source is what P08 is for, unlike P01's box |

## 12. Acceptance criteria and tests
1. **Areas:** the histogram's bar areas sum to the share uncensored (1e-9); each PDF line is `result.distribution()`'s
   `pdf` on the drawn x values.
2. **Q-Q:** with AC 5 of the Spec, the points' x are the fitted quantiles at 0.1 … 0.9, y the values; axes share
   limits.
3. **Censored:** two refusals draw two open triangles at 100 and "≥ 100: 2" in the legend; the table shows "—"
   for AD p.
4. **Arguments:** `distributions=`, `qq=`, `table=False`, `log=True` (log-spaced bins, log axes) each change only
   their part; `group=` missing with `by=` is an error listing groups.
5. **Same figure from the result:** `result.plot(group=...)` and `distribution_fit()` on the same rows give the
   same artists' data.
6. **Units:** US and SI differ only in labels and values scaled by the conversion.
7. **Visual check:** `docs/plots/img/P08.png` at 100 dpi, N60 in one unit of the example project with refusals,
   looked at and committed in the close-out.

## 13. References
As the M15 (c) Spec's sources (AICc, Anderson–Darling, Kaplan–Meier, Hazen positions).

## 14. Open questions
- None; the choices were agreed with the M15 (c) Spec (2026-10-30).

## 15. Future enhancements
- A probability plot (value against the standard-normal quantile) in place of the Q-Q.
- Several groups on one figure (P24, P27).
- Drawing bands as intervals (TODO #8).
