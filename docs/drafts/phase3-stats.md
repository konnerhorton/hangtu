# Phase 3 (statistics) — draft notes

**Status:** working notes, not a spec. Input for the Phase 3 intents.
**Parent:** SPEC §5. The conventions shared by all statistics functions are there. Background for `characteristic` is in [`../reference/eurocode7-summary.md`](../reference/eurocode7-summary.md).

---

## Functions
| Function | Behavior |
|---|---|
| `describe` 🔬 | n, mean, median, std, CoV, min, max, P25/P75, P5/P95. Proposed floors: std only if n ≥ 2; P25/P75 only if n ≥ 4; P5/P95 only if n ≥ 20. No CoV for interval-scale columns (TODO #9) |
| `fit` 🔬 | MLE; AICc; Anderson-Darling / Lilliefors. Reports P(X outside bounds). `bounds=` enables truncnorm/beta. Censored data (refusals, `<x`) via `scipy.stats.CensoredData`. `.plot()` = P08 (TODO #8, #12) |
| `compare` 🔬 | Welch's t-test plus a rank-based test side by side; effect size with CI; plain-English summary; low-power warning (TODO #10) |
| `compare_groups` 🔬 | Welch's ANOVA + Games-Howell, alongside Kruskal-Wallis + Dunn (Holm) (TODO #11) |
| `crosstab` | Contingency table between classification columns (e.g. lab USCS vs logged unit), with mismatch listing |
| `characteristic` 🔬 | EC7 characteristic value (see `docs/reference/eurocode7-summary.md` §7; TODO #13). Plot: P09 |
