# P02 — SPT N profile

| | |
|---|---|
| **ID / function** | P02 · `ht.plot.spt_profile()` (uses `ht.analysis.spt()`) |
| **Status** | built |
| **Type** | plot + light analysis |
| **Target version** | v0.1 (milestone M3) |
| **Depends on** | P00, P01, the SPT analysis (`docs/drafts/analysis.md` §1) |
| **Related** | SPEC §4 (refusals, N60), §8.2 (test depth). P03 (shown beside it). M3 intent: `docs/work/m3-spt/intent.md` |

---

P02 is P01 with SPT conventions. Everything not stated here is as P01: axes, overlays, units, legend, notes, edge cases. This spec records only what differs.

## 1. Purpose
Shows SPT N (or N60) against elevation or depth for many holes at once, colored by geology unit. It answers: how dense or stiff is each unit, does N trend with depth, and are there holes or zones that stand out. It's the most common figure in a GIR's in-situ testing section, usually shown next to the SPT class histogram (P03).

## 2. Reference figure
```
                    SPT N
           0    20    40    60    80   100  120
     150 ┼─────┼─────┼─────┼─────┼─────┼────┤
         │  ●     ●                         │   ● Fill
 Elev    │     ●  ●   ●                     │   ● Unit A
 (ft)    │        ●     ●      ●            │   ● Unit B
     130 ┤           ●    ●       ●      ▶  │   ▶ refusal (2)
         │                ●    ●         ▶  │
     110 ┼──────────────────────────────────┘
                     2 refusals, shown at N = 100
```
**A good version** is P01 with SPT conventions:
- refusals are visible as a distinct marker at the cap, clear of the frame;
- the axis names the column plotted: "SPT N", "SPT N60" or "SPT N (capped)";
- nothing is mixed: one plot shows N or N60, never both.

## 3. Input data
**Row grain:** one row per SPT test. Columns are the `spt` template (`ht.template("spt")`).

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `spt_n` | N as reported | count | ✔ | Required by `ht.analysis.spt()`, even when plotting N60 |
| `depth` / `elevation` | Test depth or elevation | length | ✔ one | As P01. See "Test depth" below |
| `ground_level` | Ground level | length | – | As P01 |
| `energy_ratio` | Hammer energy ratio (%) | percent | – | For N60 (analysis §1.3) |
| `spt_refusal` | Refusal flag | bool | – | Analysis §1.3 |
| `spt_penetration` | Seating + test penetration | small_length | – | Finds refusal where `spt_refusal` is blank; needs units |
| `spt_n60` | N60 | count | – | Kept where filled in |
| `geology_unit` | Geology unit | — | – | Color |
| `loca_id` | Hole | — | – | `connect=`, per-hole water levels |

**Test depth** is `depth` as given (analysis §1.2, SPEC §8.2). The mid-drive depth from the increments is Phase 2. If the depths are the top of each test, the points sit up to 0.45 m (1.5 ft) high; the docstring says to give the mid-drive depth when it is known.

**Hints** (one per call, as P01): P01's list, plus "No 'spt_refusal' column: refusals can't be found. Add it, or 'spt_penetration' with its units." when both columns are missing from the input.

**Value flags handled:**
- refusal: a right-pointing filled triangle ▶ at the cap, or left out and counted (§7);
- blank N (not a refusal): counted, as P01;
- with `n="spt_n60"`, a test without an energy ratio: left out and counted.

P02 doesn't read `qualifier`. Refusal is the SPT's only flag.

**Minimum data:** as P01 (≥ 1 point, else "No data").

## 4. Analysis / calculations
`spt_profile()` runs `ht.analysis.spt()` on the data first (analysis §1.3), passing `hammer_efficiency=` and `units=`. Refusal, N60 and the cap are therefore exactly the analysis's. Nothing else is computed beyond P01's elevation and unit conversion.

## 5. Figure layout
As P01: single panel, the `profile` size, portrait.

## 6. Axes
As P01, with:
- **X axis:** the column `n`: linear, from 0. Label from the registry: "SPT N", "SPT N60" or "SPT N (capped)", with no unit.
- **X limits:** as P01: nice limits over the drawn values from 0, with the preset's typical range (0–50) used only for sparse data (plots README, "Presets"). When refusals are drawn at the cap, the upper limit is the nice limit above 1.05 × cap (120 for a cap of 100), so the markers aren't on the frame. `xlim=` overrides, as P01.
- **Presets** `spt_n`, `spt_n60` and `spt_n_capped` in `config/defaults.yaml`: quantity count, linear, start at zero, typical [0, 50]. The preset is picked from `n`; there is no `preset=` or `log=` argument.

## 7. Data marks
As P01, plus:

| Series | Mark | Color by | Size | Legend entry | Notes |
|---|---|---|---|---|---|
| Refusal, `refusal="cap"` | filled triangle ▶ at x = cap | unit color | 6 pt | ✔ gray ▶ "refusal (n)" | Footnote "n refusals, shown at N = 100" (the cap and N or N60 as plotted). Replaces the normal marker. Beyond `xlim`, drawn open at the edge and counted both ways, as P01 qualifiers |
| Refusal, `refusal="exclude"` | none | — | — | — | Footnote "n refusals not shown". The x-axis isn't extended for the cap |

- **Refusals are drawn at the cap whichever column is plotted.** A refusal is a refusal; its N60 isn't meaningful as a number.
- **A non-refusal value above the cap is drawn at its value.** N60 is not capped (analysis §1.3), so N = 90 with ER = 80 is drawn at 120.
- **Stats box** (`stats_box=`, as P01) includes refusals at the cap when they're drawn (SPEC §4), and the footnote says so.

**Draw order:** as P01, with refusals drawn with the qualifiers (above the markers).

## 8. Overlays and annotations
As P01: `strata`, `water_level`, `ranges`, `design_lines`, `reference_lines`, `stats_box`, `note`. `ranges` and `reference_lines` are in N (no units), e.g. a "Very dense" band from 50 to 100.

## 9. Units behavior
N, N60 and capped N are counts and never convert. Only the vertical axis changes (m / ft), as P01. `spt_penetration` needs units only when it's used to find refusals (analysis §1.3).

## 10. API
```python
def spt_profile(
    df: pd.DataFrame,
    *,
    n: Literal["spt_n", "spt_n60", "spt_n_capped"] = "spt_n",
    vs: Literal["elevation", "depth"] | None = None,
    refusal: Literal["cap", "exclude"] = "cap",
    hammer_efficiency: float | None = None,  # passed to ht.analysis.spt()
    cap: int | None = None,                  # passed to ht.analysis.spt(); None -> settings.spt_cap
    label: str | None = None,
    color_by: str | None = "geology_unit",
    marker_by: str | None = None,
    connect: bool = False,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    xaxis_position: Literal["top", "bottom"] = "bottom",
    secondary: Literal["depth"] | None = None,
    # overlays, as P01
    strata: pd.DataFrame | None = None,
    water_level: float | list[tuple[float, str]] | pd.DataFrame | None = None,
    ranges: pd.DataFrame | str | None = None,
    design_lines: pd.DataFrame | None = None,
    reference_lines: list[tuple[float, str]] | None = None,
    stats_box: bool | list[str] = False,
    stats_box_room: bool = True,
    note: str | None = None,
    # common
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```
P01's `value`, `preset`, `log` and `intervals` aren't arguments: the column is `n`, its preset follows, and an SPT is a point test.

**Examples:**
```python
spt = ht.read_csv("spt.csv", units={"depth": "ft", "ground_level": "ft", "spt_penetration": "in"})
fig, ax = ht.plot.spt_profile(spt, connect=True, strata=strata)
fig, ax = ht.plot.spt_profile(spt, n="spt_n60", hammer_efficiency=80, vs="depth")

sheet = ht.Sheet(layout=(1, 2))
ht.plot.spt_profile(spt, ax=sheet[0])
ht.plot.spt_histogram(sand, table="cohesionless", ax=sheet[1])
```

## 11. Edge cases and data quality
As P01, plus:

| Situation | Behavior |
|---|---|
| No `spt_n` column | The analysis's error, listing the columns |
| `n="spt_n60"`, some tests without N60 | Those tests left out (refusals still drawn at the cap) and counted: "n tests without an energy ratio not shown" |
| `n="spt_n60"`, no test has N60 | Error: "No test has N60, because no energy ratio is known. Set ht.settings.hammer_efficiency = 80, pass hammer_efficiency=80, or fill in 'energy_ratio'. Or plot N with n="spt_n"." With no N at all, there is no error: the plot shows "No data" |
| `n` or `refusal` not one of the allowed values | Error listing them, with an example |
| Refusal with a blank N | Drawn at the cap |
| Refusal with N above the cap (e.g. 150) | Drawn at the cap, as every refusal |
| Non-refusal N above the cap, `n="spt_n"` | Drawn at its value. The analysis doesn't make it a refusal (the draft's pitfall: never infer refusal from a large N) |
| `spt_penetration` without units, needed for a row | The analysis's `UnitsError`, with the `set_units` example |
| `xlim` below the cap, with refusals | Refusals drawn open at the edge with an arrow, counted as refusals and as beyond the limit |
| Neither `spt_refusal` nor `spt_penetration` | Plot drawn, no refusals; the hint in §3 |

## 12. Acceptance criteria and tests
- **Golden values:**
  - N60: N = 30, ER = 80 is drawn at 40.0 with `n="spt_n60"`; N = 90, ER = 80 at 120.0.
  - A refusal with N = 38 is drawn at 100; with `cap=50`, at 50.
  - 10.0 ft ↔ 3.048 m on the vertical axis, with N unchanged between US and SI.
- **Automated:**
  - default column and label "SPT N"; "SPT N60" and "SPT N (capped)" with `n=`;
  - `vs` depth and elevation; color by unit; `connect=True`; each P01 overlay passed through;
  - refusal markers: shape, color, position and count; legend "refusal (n)"; footnote text for both `refusal=` values;
  - the x upper limit clears the cap when there are refusals (120 for 100);
  - N60 partial (count) and none (error text);
  - the refusal hint when both refusal columns are missing, and not otherwise;
  - `assert_us_si_equivalent` on the vertical axis; `assert_no_global_state`, also with `ax=` on a `Sheet` panel;
  - empty input gives "No data".
- **Acceptance against test data** `tests/data/spt.csv`: four holes, three units plus fill, about 80 tests over 30 m, ER on two holes only, a few refusals (one with blank N, some found from `spt_penetration`), and blank N rows. The footnote counts are worked out by hand.
- **Visual check:** [`docs/work/m3-p02/visual-check.png`](../work/m3-p02/visual-check.png), a `Sheet` with N in US (with `connect=True`) and N60 in SI side by side, with strata and a water level.

## 13. References
- `docs/drafts/analysis.md` §1 and its references.
- ASTM D1586/D1586M-18, *Standard Test Method for Standard Penetration Test (SPT) and Split-Barrel Sampling of Soils*.

## 14. Open questions
None.

**Pitfalls:**
- Plotting the SPT *top* depth instead of the mid-drive depth (SPEC §8.2). For CSV input, the user gives the depth, and the docstring says which.
- Inferring refusal from a large N instead of using `spt_refusal`, `spt_penetration` and the cap (SPEC §4).
- Mixing N and N60 in one plot.

## 15. Future enhancements
- Color by any column (e.g. an upper/lower elevation split).
- N and N60 side by side as two panels with a shared vertical axis.
- Mid-drive depth from AGS increments (Phase 2).
