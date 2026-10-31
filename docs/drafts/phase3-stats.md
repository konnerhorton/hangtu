# Phase 3 (statistics) — draft notes

**Status:** working notes, not a spec. Input for the Phase 3 intents.
**Parent:** SPEC §5. The conventions shared by all statistics functions are there. Background for `characteristic` is in [`../reference/eurocode7-summary.md`](../reference/eurocode7-summary.md).

---

**Constraint from M13 b2, settled** (M15 (a), `docs/work/m15a-describe.md`, spec Decision 4): a band (`<target>_lower`/`_upper` with the value blank) is an interval. `describe()`, P01 and `fit()` (M15 (c)) leave it out and count it; fitting it as interval-censored stays an option in TODO #8. The input rules every function follows are in SPEC §5.

---

## Functions
| Function | Behavior |
|---|---|
| `describe` ✅ | Decided and built in M15 (a): `docs/work/m15a-describe.md` and SPEC §5 |
| `fit` ✅ | Decided and built in M15 (c): `docs/work/m15c-fit.md`, SPEC §5 and P08 |
| `compare` ✅ | Decided and built in M15 (d): `docs/work/m15d-compare.md` and SPEC §5 |
| `compare_groups` ✅ | Decided and built in M15 (d): `docs/work/m15d-compare.md` and SPEC §5 |
| `crosstab` ✅ | Decided and built in M15 (e): `docs/work/m15e-crosstab.md` and SPEC §5 |
| `characteristic` 🔬 | Moved to M18 (selection). EC7 characteristic value (see `docs/reference/eurocode7-summary.md` §7; TODO #13). Plot: P09 |
