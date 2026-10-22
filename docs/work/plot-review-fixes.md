# plot-review-fixes

## Intent
Two fixes from the P06 review (`docs/work/m8-index-plots.md`, "Plan: P06", Results).

- **Strata bands take the points' colors.** `draw_strata` resolved colors from `palette=` and the session only, while the points also use the data's palette (`df.attrs["palette"]`, from a project's geology map). Without `palette=`, a band and the points of the same unit could differ. The bands now go through the same chain: `palette=`, `ht.settings.palette`, the data's palette (the main data's first, then the strata table's own `attrs`), then the automatic colors. This matters more once M13 adds `p.stratigraphy()` through the geology map.
- **One count per row beyond an axis limit (P06).** A row whose water content point is drawn at the edge and whose limits bar is cut or hidden was counted twice under "beyond axis limit". A row now counts once, whether its point, its bar or both are at the edge. `Companion.draw` returns the rows it drew at the edge with its legend entries, and `_draw_profile` counts them with the points'.

Out of scope: `strata=` taking `p.stratigraphy()` (per hole, depth only); that is M13 (a)'s to decide.

SPEC: no change. P01 §8 (strata colors) and P06 §7 (the count) change.

## Plan
1. `plot: draw strata bands in the points' colors`: `draw_strata(..., data_palette=)`, passed `df.attrs["palette"]` by `_draw_profile`; P01 §8. Test: a frame with a data palette and strata, no `palette=`: band and point colors match; the strata table's own palette fills a unit the data lacks.
2. `P06: count a row beyond an axis limit once`: `Companion.draw` returns `(handles, edge)`; `_limits_bars` returns its edge rows instead of counting; P06 §7. Tests: w and bar both beyond `ylim=` → 1; w and LL both beyond `xlim=` → 1; bar alone beyond → 1 (as now).
