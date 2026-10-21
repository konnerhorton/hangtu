# P03 — SPT class histogram

| | |
|---|---|
| **ID / function** | P03 · `ht.plot.spt_histogram()` (uses `ht.analysis.spt()` and `ht.analysis.spt_class()`) |
| **Status** | built |
| **Type** | plot + classification |
| **Milestone** | M3 (0.1.0) |
| **Depends on** | P00, the SPT analysis (`docs/drafts/analysis.md` §1) |
| **Related** | SPEC §4 (refusals, N60). P02 (shown beside it), P07 (unit order). TODO #3 (`soil_class`, no longer needed here). M3 intent: `docs/work/m3-spt.md` |

---

## 1. Purpose
Shows what share of the SPT tests in each geology unit falls in each relative-density class (cohesionless soils) or consistency class (cohesive soils). It's how a GIR backs up "Unit B is predominantly dense to very dense". Reviewers read it next to the N profile (P02).

## 2. Reference figure
```
  Tests in unit (%)
  60 ┤            ▒▒
     │      ██    ▒▒                         █ Unit A (n = 84)
  40 ┤      ██ ▒▒ ▒▒ ██                      ▒ Unit B (n = 132)
     │   ██ ██ ▒▒ ▒▒ ██ ▒▒                   ╱ refusal
  20 ┤▒▒ ██ ██ ▒▒ ▒▒ ██ ▒▒ ██ ▒▒ ╱╱ ╱╱
     ├──────┬──────┬──────┬──────┬──────┬──────
     Very   Loose  Medium Dense  Very   Refusal
     loose  4–10   dense  30–50  dense
     < 4           10–30         ≥ 50
              SPT N class (cohesionless)
                  3 blank values not shown
```
**A good version:**
- grouped (side-by-side) bars, not overlaid translucent bars, which hide each other beyond two units;
- the class ranges are on the axis, so the reader doesn't need the table;
- the axis says which value was classified (N or N60) and which table was used;
- refusals are a class of their own, never folded into "very dense";
- every test is accounted for: in exactly one bar, or counted in the footnote.

## 3. Input data
**Row grain:** one row per SPT test. Columns are the `spt` template (`ht.template("spt")`), as P02.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `spt_n` | N as reported | count | ✔ | Required by `ht.analysis.spt()`, even when classifying N60 |
| `energy_ratio` | Hammer energy ratio (%) | percent | – | For N60 (analysis §1.3) |
| `spt_refusal` | Refusal flag | bool | – | Analysis §1.3 |
| `spt_penetration` | Seating + test penetration | small_length | – | Finds refusal where `spt_refusal` is blank; needs units |
| `spt_n60` | N60 | count | – | Kept where filled in |
| `geology_unit` | Geology unit | — | – | One bar per unit in each class |

No depth or elevation is needed. `soil_class` isn't read: the user picks the table and passes the rows it applies to (M3 intent, decision 6), for example by filtering on `geology_unit`.

**Hints** (one per call): "No 'geology_unit' column: all tests are drawn as one group." when the default `color_by` column is missing, and P02's refusal hint when both `spt_refusal` and `spt_penetration` are missing.

**Value flags handled:**
- refusal: its own hatched "Refusal" class, or left out and counted (§7);
- blank N (not a refusal): left out and counted;
- with `n="spt_n60"`, a test without an energy ratio: left out and counted. A refusal without N60 is still a refusal.

**Minimum data:** ≥ 1 test, else "No data".

## 4. Analysis / calculations
- **Classes:** `spt_histogram()` runs `ht.analysis.spt()` on the data (with `hammer_efficiency=` and `units=`), then `ht.analysis.spt_class()` on the result. The class tables, the lower-bound-inclusive boundaries and the refusal rule are therefore the analysis's (analysis §1.4, `config/spt_classes.yaml`), tested there once:

  | `cohesionless` (relative density) | N | `cohesive` (consistency) | N |
  |---|---|---|---|
  | Very loose | < 4 | Very soft | < 2 |
  | Loose | 4–10 | Soft | 2–4 |
  | Medium dense | 10–30 | Medium stiff | 4–8 |
  | Dense | 30–50 | Stiff | 8–15 |
  | Very dense | ≥ 50 | Very stiff | 15–30 |
  | | | Hard | ≥ 30 |

  "4–10" means 4 ≤ N < 10. A refusal is "Refusal" whatever its N.
- **Percent** of a bar = tests in the class in the unit / tests classified in the unit × 100. "Classified" means the tests in some bar: refusals are in the denominator when they are drawn (`refusal="separate"`) and not when they are excluded. Blank N and tests without N60 are in neither.
- Nothing else is computed. No value is converted.

## 5. Figure layout
- **Panels:** single, one class table per call. For both tables, two calls on a `Sheet`:
  ```python
  sand = spt[spt["geology_unit"].isin(["Fill", "Alluvial sand"])]
  clay = spt[spt["geology_unit"].isin(["Glacial till", "Residual soil"])]
  sheet = ht.Sheet(layout=(1, 2))
  ht.plot.spt_histogram(sand, table="cohesionless", ax=sheet[0])
  ht.plot.spt_histogram(clay, table="cohesive", ax=sheet[1])
  ```
- **Default size:** `default` (6.5 × 4.5 in).
- **Orientation:** landscape.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | class, categorical, in table order, then "Refusal" | percent of the unit's classified tests |
| Title | "SPT N class (cohesionless)" or "SPT N60 class (cohesive)": the registry label of `n` and the table | "Tests in unit (%)" |
| Tick labels | class name, one word per line, then the range, built from the table: "Very\nloose\n< 4", "Dense\n30–50", "Very\ndense\n≥ 50", "Refusal". One word per line keeps the labels apart on a half-page `Sheet` panel | numbers |
| Limits | one slot per class | 0 to a nice number at or above the tallest bar (never above 100) |
| Gridlines | none | horizontal, major |

The "Refusal" slot is there only with `refusal="separate"`. The ranges in the tick labels come from the table's lower bounds, so they always match the classification.

## 7. Data marks
| Series | Mark | Color by | Legend entry | Notes |
|---|---|---|---|---|
| Class share | grouped bars | `geology_unit` (palette, P00 §10) | ✔ "Unit A (n = 84)", n = tests classified in the unit | Units side by side within each class, in unit order |
| Refusal, `refusal="separate"` | bar in the "Refusal" slot, hatched | unit color | ✔ one shared entry, gray hatch, "refusal" | |
| Refusal, `refusal="exclude"` | none | — | — | Footnote "n refusals not shown"; percentages without them |
| `color_by=None` | one bar per class | neutral gray | ✔ "All tests (n = …)" | |

- **Unit order:** as P07: units in `order=` first, in that order, then the rest by name, then "(blank)" for a blank `geology_unit`.
- **Bar layout:** each class slot holds a group of width 0.8, split evenly between the units drawn. A unit with no tests in a class keeps its place (a gap), so a unit's bars line up across classes.
- There is no `refusal="cap"`: a refusal is a refusal, not a "very dense" test.

**Draw order (bottom → top):** gridlines → bars → bar labels → notes.

## 8. Overlays and annotations
| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Counts on bars | `bar_labels=` | off | The count (not the percent) above each non-zero bar. The y limit leaves room for the tallest label |
| Note | `note=` | off | Free text, added to the footnote. P01 writes its note inside the axes, where here it would cover the bars |
| Exclusion footnote | automatic | on | P02's reasons: "n blank values not shown", "n tests without an energy ratio not shown", "n refusals not shown" |
| No-tests note | automatic | on | "No classified tests: Unit C" for a unit in `order=` with no tests, or a unit whose tests are all left out |

P01's `ranges`, `reference_lines` and `stats_box` don't apply to a class histogram.

## 9. Units behavior
Nothing converts: N and N60 are counts and the y axis is a percent. `display_units` is accepted for the plot contract and changes nothing, so one figure serves US and SI. `spt_penetration` needs units only when it's used to find refusals (analysis §1.3), as P02.

## 10. API
```python
def spt_histogram(
    df: pd.DataFrame,
    *,
    n: Literal["spt_n", "spt_n60"] = "spt_n",
    table: Literal["cohesionless", "cohesive"] = "cohesionless",
    refusal: Literal["separate", "exclude"] = "separate",
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,          # stratigraphic order of geology units
    hammer_efficiency: float | None = None,  # passed to ht.analysis.spt()
    bar_labels: bool = False,
    note: str | None = None,
    # common
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,     # passed to ht.analysis.spt()
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```
`spt_n_capped` isn't offered: it gives the same classes as `spt_n` unless the cap is set below a class boundary, and then it misclassifies.

**Examples:**
```python
spt = ht.read_csv("spt.csv", units={"spt_penetration": "in"})
sand = spt[spt["geology_unit"].isin(["Fill", "Alluvial sand"])]
fig, ax = ht.plot.spt_histogram(sand, order=["Fill", "Alluvial sand"])
fig, ax = ht.plot.spt_histogram(sand, n="spt_n60", hammer_efficiency=80, bar_labels=True)
fig, ax = ht.plot.spt_histogram(clay, table="cohesive", refusal="exclude")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input | Empty axes with a "No data" note; no error |
| No `spt_n` column | The analysis's error, listing the columns |
| `n`, `table` or `refusal` not one of the allowed values | Error listing them, with an example (for `table`, the analysis's error) |
| Negative N | The analysis's error, naming the rows |
| N = 0 | Very loose / very soft |
| N exactly on a boundary | The upper class (lower bound inclusive): N = 4 is loose, N = 50 very dense |
| Refusal with a numeric N (e.g. 12) | "Refusal" only; never also in the class of its N |
| Refusal with a blank N | "Refusal" |
| Blank N, not a refusal | Left out of the bars and the percentages; "n blank values not shown" |
| `n="spt_n60"`, some tests without N60 | Left out (refusals still drawn) and counted: "n tests without an energy ratio not shown" |
| `n="spt_n60"`, no test has N60 | P02's error: set `ht.settings.hammer_efficiency`, pass `hammer_efficiency=`, fill in `energy_ratio`, or use `n="spt_n"` |
| `refusal="exclude"` | Refusals left out of the bars and the percentages; "n refusals not shown" |
| A unit in `order=` with no tests | No bars, no legend entry; listed in the no-tests note |
| A unit whose tests are all left out | No bars, no legend entry; listed in the no-tests note; its tests counted by reason |
| Blank `geology_unit` | A "(blank)" unit, last, in neutral gray |
| `color_by` column missing (default) | One group, as `color_by=None`, with the hint in §3 |
| Many units | Bars get narrower; legend as the README rules |
| `spt_penetration` without units, needed for a row | The analysis's `UnitsError`, with the `set_units` example |

## 12. Acceptance criteria and tests
- **Golden values** (worked by hand):
  - N = [0, 4, 10, 29, 30, 50, 51] in one unit, cohesionless → very loose 1 (0), loose 1 (4), medium dense 2 (10, 29), dense 1 (30), very dense 2 (50, 51) of 7: bar heights 14.3, 14.3, 28.6, 14.3, 28.6 %. `pd.cut` with its right-closed default gives a total of 6, so this catches it.
  - The same N with a refusal at N = 12 added → 8 classified; the refusal is in "Refusal" only, and medium dense stays at 2 (25.0 %). With `refusal="exclude"`, the heights are the 7-test ones above and the footnote says "1 refusal not shown".
- **Automated:**
  - tick labels and order for both tables, "Refusal" last, built from the table;
  - x-axis title for `spt_n` and `spt_n60` and both tables; y-axis title;
  - every test in exactly one bar: the bar counts sum to the unit's n;
  - two units with different n: heights per unit, legend "Unit A (n = 4)";
  - unit order with and without `order=`; "(blank)" last; `color_by=None` and its legend;
  - refusal bars hatched in the unit color, with one shared legend entry;
  - `bar_labels=True` labels non-zero bars only, with counts;
  - footnote counts for blank N, N60 partial, excluded refusals; the N60-none error text; the no-tests note;
  - the two hints, and no hint when the columns are there;
  - unknown `n`, `table` and `refusal` errors;
  - `display_units="US"` and `"SI"` give the same figure;
  - `assert_no_global_state`, also with `ax=` on a `Sheet` panel;
  - empty input gives "No data".
- **Acceptance against test data** `tests/data/spt.csv` (P02's): the test splits it on `geology_unit` into a cohesionless set (Fill, Alluvial sand) and a cohesive set (Glacial till, Residual soil), as a user would. The bar counts, n per unit, refusals and footnote counts are worked out by hand.
- **Visual check:** [`img/P03.png`](img/P03.png), a Letter `Sheet` with the cohesionless and cohesive histograms of the test data side by side, with bar labels. One image, since nothing converts between US and SI (§9).

## 13. References
- `docs/drafts/analysis.md` §1.4 and its references.
- Terzaghi, K. & Peck, R.B. (1948). *Soil Mechanics in Engineering Practice*. Wiley.
- Peck, R.B., Hanson, W.E. & Thornburn, T.H. (1974). *Foundation Engineering*, 2nd ed. Wiley.

## 14. Open questions
None.

**Pitfalls:**
- `pd.cut` bins are right-closed by default: `(0, 4], (4, 10], …` **drops N = 0** and puts N = 4 in "very loose". The golden test catches it.
- Applying the relative-density table to every soil, cohesive units included.
- Inferring refusal from a large N instead of the flag.
- Percentages over all tests instead of per unit, which makes a large unit swamp a small one.

## 15. Future enhancements
- Stacked 100% bars (one bar per unit), a compact alternative when there are many units.
- Picking the table from `soil_class` automatically (TODO #3).
- User-defined class bins.
