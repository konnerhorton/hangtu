# Phase 3 (statistics) — draft notes

**Status:** working notes, not a spec. Input for the Phase 3 intents.
**Parent:** SPEC §5. The conventions shared by all statistics functions are there. Background for `characteristic` is in [`../reference/eurocode7-summary.md`](../reference/eurocode7-summary.md).

---

**Constraint from M13 b2, settled** (M15 (a), `docs/work/m15a-describe.md`, spec Decision 4): a band (`<target>_lower`/`_upper` with the value blank) is an interval. `describe()` and P01 leave it out and count it; `fit()` (M15 (c)) may take it as an interval-censored value. The input rules every function follows are in SPEC §5.

---

## Functions
| Function | Behavior |
|---|---|
| `describe` ✅ | Decided and built in M15 (a): `docs/work/m15a-describe.md` and SPEC §5 |
| `fit` ✅ | Decided in M15 (c): `docs/work/m15c-fit.md` (Spec) and P08 |
| `compare` 🔬 | Welch's t-test plus a rank-based test side by side; effect size with CI; plain-English summary; low-power warning (TODO #10) |
| `compare_groups` 🔬 | Welch's ANOVA + Games-Howell, alongside Kruskal-Wallis + Dunn (Holm) (TODO #11) |
| `crosstab` | Contingency table between classification columns (e.g. lab USCS vs logged unit), with mismatch listing |
| `characteristic` 🔬 | Moved to M18 (selection). EC7 characteristic value (see `docs/reference/eurocode7-summary.md` §7; TODO #13). Plot: P09 |
