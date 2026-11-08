# Correlations: the contract every correlation follows

| | |
|---|---|
| **Status** | Living spec. Built for the SPT correlations (M13 b1–b3), with statistics (M15 b) and refusal bounds (M18 a) |
| **Parent** | SPEC §4 (correlations are stage C of every parameter, §1.3) |
| **Related** | [`docs/work/m13b1-spt-framework.md`](../work/m13b1-spt-framework.md) (framework, (N1)60), [`m13b2-spt-strength-history.md`](../work/m13b2-spt-strength-history.md) (bands, chaining, USCS map), [`m13b3-spt-stiffness.md`](../work/m13b3-spt-stiffness.md) (`soil=`), [`m15b-correlation-statistics.md`](../work/m15b-correlation-statistics.md), [`m18a-refusals.md`](../work/m18a-refusals.md). The built set: `src/hangtu/config/correlations.yaml` |

Update this file in the same commit as any change to the contract, and SPEC §4 if the change alters its summary.

## 1. Scope and naming
Correlations (decided 2026-10-15; widened 2026-10-21) are stage C of every parameter (SPEC §1.3), from any input property (SPT N, PI, CPT qt, Is50, index properties). SPT correlations are the first set (M13). They live in `ht.analysis.correlations`, one function per published correlation, named target first: `<target>_<authors>_<year>`, with `<first>_et_al_<year>` for three or more authors (`undrained_shear_strength_stroud_1974`; decided 2026-10-23, `docs/work/m13b2-spt-strength-history.md`).

## 2. What each correlation does
- **States its equation and cites its source**, with constants kept in the source's units.
- **Has one entry in `config/correlations.yaml`** holding its facts (source, range, input, applies to), so the result's metadata and a plot's footnote read one place; the docstring is written by hand, and a test checks it against the entry.
- **Says when it applies and when it doesn't:** soil types, input range, the input it was derived with (for SPT, field N, N60 or (N1)60), the data and region behind it, and known biases. The input is explicit: a column that doesn't match is an error, never a silent correction. This is in the docstring and in metadata attached to the result, so a plot or report can show it.
- **Returns NaN with a count outside its range**, and never clips or extrapolates the input. The one exception is an SPT correlation's N input (§3).
- **Its out-of-range warning gives the range only when some rows are outside it**, in the docstring's terms and units (`N pa/σ′v0`, `σ′v0 > 0 kPa`).
- **Returns rows that name the correlation** (`correlation_name`), so several estimates of one property compare on P01 (`color_by=`) or P07.
- **Reads the one column its correlation was derived with**, by its registry name, with no argument to point it at another. A correlation published at another hammer energy is used in its 60 % form, from a cited source (decided 2026-10-22, `docs/work/m13b1-spt-framework.md`). One derived on field N reads `spt_n`, and says so.
- **Gives a band, where its source does,** as `<target>_lower` and `<target>_upper` beside `<target>`, which holds the central value or NaN; nothing is interpolated between the source's values.
- **Carries its source's statistics and advice on use on every row** (`correlation_data_count`, `correlation_r_squared`, `correlation_scatter`, `correlation_advice`, and `<target>_correlation_standard_deviation` where the source gives an arithmetic standard deviation), so they survive a merge or a file round trip. The advice is in the source's words where it has them, else marked as hangtu's. Other databases' checks of a correlation (bias, COV) are in its metadata, not on the rows; applying them is selection (decided 2026-10-30, `docs/work/m15b-correlation-statistics.md`).
- **Takes test data or values derived directly from them as inputs.** Chaining one correlation into another is discouraged, not prevented: it warns and is recorded on the rows (`correlation_input`).
- **Reads soil type only when asked:** an opt-in USCS map (`uscs=`) gives NaN with a reason for rows outside hangtu's proposed groups, which the user can override, from a `uscs_symbol` column the user supplies (decided 2026-10-23, `docs/work/m13b2-spt-strength-history.md`).
- **Takes a coefficient the source gives by soil type from a required argument** naming the source's row (`soil=`, one row or one per geology unit), never inferred; `uscs=` checks the row and doesn't choose it, since a USCS symbol can't split the sources' rows (decided 2026-10-26, `docs/work/m13b3-spt-stiffness.md`).
- **Names its target as the source describes the estimate** (`drained_youngs_modulus`, with the strain level in its notes), so estimates at different strain levels or drainage can't be confused (decided 2026-10-26).

## 3. SPT refusals and the N range
Decided 2026-11-02 (TODO #54); widened in `docs/work/m18a-refusals.md`, decision 1; built in M18 (a); to revisit once it has been used on real projects.

- A correlation that rises with N gives a refusal "at least" the estimate at its N, a row with N above the correlation's range "at least" the estimate at the upper limit, and one below it "at most" the estimate at the lower limit. Each is marked as a bound in `correlation_qualifier`, never as a value, so `fit()` and selection keep the rows as censored instead of losing the densest and loosest tests.
- This is for the N input only; a row outside another input's range keeps NaN with a count.
- Only an inclusive range end bounds, and a lower end only above 0: a strict limit or a lower end of 0 says where the equation stops, not where the data did.
- Each of the eleven SPT correlations rises with its N input (a property test checks it).
