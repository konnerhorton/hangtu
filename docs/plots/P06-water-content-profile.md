# P06 — Water content profile with Atterberg limits

| | |
|---|---|
| **ID / function** | P06 · `ht.plot.water_content_profile()` (built on `ht.plot.profile()`) |
| **Status** | approved |
| **Type** | plot |
| **Milestone** | M8 |
| **Depends on** | P01 (with text values, TODO #15), the plasticity analysis (`docs/drafts/analysis.md` §2) |
| **Related** | P04 (the same specimens on the chart). `docs/data/datasets.md` §6.2, §6.6. SPEC §4 (NP). M8 intent: `docs/work/m8-index-plots.md` |

---

## 1. Purpose
Shows water content against depth or elevation with each specimen's plastic limit and liquid limit as a bar, so the reader sees where the natural water content sits in the plastic range. It answers: is the soil near its liquid limit (soft, sensitive) or near its plastic limit (stiff), does that change with depth, and do the units differ. A standard figure in the lab section of a report and in the design of cuttings and foundations on clay.

## 2. Reference figure
```
          Water content, w, and Atterberg limits (%)
          0     10     20     30     40     50     60
     0 ┼──────┼──────┼──────┼──────┼──────┼──────┤
       │            ├────●────────┤                │   ├ PL   ● w   ┤ LL
     5 ┤          ├──────●──────┤                  │
       │                     ●                     │   (w only)
Depth 10┤             ├──────────┤                 │   (limits only)
 (ft)  │      ◇ NP                ●                 │   ◇ non-plastic at its w
    15 ┤               ├──────●───────────┤        │
       │                                           │
    20 ┼───────────────────────────────────────────┘
                        Legend: ■ Unit A  ■ Unit B   ├─┤ PL to LL   ● w
```
**A good version:**
- the bar and the dot of one specimen share its depth exactly, so w reads against PL and LL at a glance;
- the bar ends are marked (short ticks), so PL and LL can't be mistaken for each other's direction (PL is always the left end);
- NP specimens are visible: they have a water content but no bar;
- every specimen is either drawn or counted.

## 3. Input data
**Row grain:** one row per specimen (`atterberg` template, `p.atterberg()`) or per sample (`p.index_properties()`). Both have the columns below.

| Column | Description | Quantity kind | Req.? | Notes |
|---|---|---|---|---|
| `water_content` | w | percent | ✔ one of `water_content` or both limits | The point |
| `liquid_limit`, `plastic_limit` | LL, PL | percent | ✔ (see above) | The bar's ends |
| `non_plastic` | NP flag | bool | – | NP: the point is drawn as NP, with no bar |
| `depth` or `elevation` (+ `ground_level`) | Vertical position | length | ✔ as P01 | P01 §3 |
| `geology_unit` | Geology unit | — | – | Color |
| `loca_id`, `depth_top`, `depth_base`, … | | | – | As P01 |

**Hints:** P01's, plus "No 'plastic_limit' column: the limits bars aren't drawn." when the limits are missing.

**Value flags:** NP (from `non_plastic`, and as text `NP` in `water_content` through P01's text values); `<`/`>` qualifiers on `water_content` as P01.

**Minimum data:** none ("No data" note, as P01).

## 4. Analysis / calculations
- `plastic_limit` and `liquid_limit` are read as given. PL is **not** computed from LL − PI: a row with LL and PI but no PL is drawn as "one limit only" (§7), counted in the footnote, and named in a warning, so the user can find the PL or remove the row.
- No other calculation. LI and Ic aren't drawn (P07 and P17 use them).

## 5. Figure layout
As P01: a single profile panel, `profile` size, portrait. `water_content_profile()` calls `profile()` for the water content, with `preset="water_content"`, and draws the bars into the same axes, so every P01 overlay and argument works unchanged.

## 6. Axes
As P01 with the `water_content` preset, except:
- **x label:** "Water content, w, and Atterberg limits (%)".
- **x limits:** start at 0 and run to a nice number above the largest of w, PL and LL, so every bar is inside the axes. `xlim=` overrides, and bars beyond it are clipped at the edge with an arrow and counted.

## 7. Data marks
| Series | Mark | Color by | Legend entry | Notes |
|---|---|---|---|---|
| Water content | P01's markers (filled, 5 pt) | `geology_unit` | ✔ per unit (P01) | |
| Limits bar | horizontal line PL to LL at the row's vertical position, 1.2 pt, with 4 pt vertical end ticks | unit color | ✔ one gray entry "PL to LL" | Drawn below the marker |
| Limits without w | the bar only | unit color | | Counted nowhere: nothing is missing |
| NP specimen | w drawn as an open marker (P01's text-value shape for NP, at its w, not at the edge) | unit color | ✔ "non-plastic (n)" | No bar. An NP specimen without w is counted in the footnote |
| Bar beyond `xlim` | clipped at the edge, open arrow | unit color | footnote count | README policy |
| Only one limit (LL or PL) | no bar; a single end tick at that limit | unit color | footnote "n specimens with one limit" | One warning names the rows, and says when a PI is given that PL wasn't computed from it |

**Draw order (bottom → top):** P01's overlays → limits bars → water content markers → notes.

## 8. Overlays and annotations
Everything P01 offers (`strata=`, `water_level=`, `ranges=`, `design_lines=`, `reference_lines=`, `stats_box=`, `note=`), passed through. `stats_box=` summarizes water content only.

| Overlay | Argument | Default | Notes |
|---|---|---|---|
| Limits bars | `limits=` | on | `False` draws P01 alone |

## 9. Units behavior
As P01: the vertical axis converts; percentages don't.

## 10. API
```python
def water_content_profile(
    df: pd.DataFrame,
    *,
    limits: bool = True,
    vs: Literal["elevation", "depth"] | None = None,
    color_by: str | None = "geology_unit",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    # every other P01 argument, passed through to profile()
    **profile_arguments,
) -> tuple[Figure, Axes]:
```
`value` and `preset` are fixed (`water_content`); passing them is an error that says so.

**Example:**
```python
fig, ax = ht.plot.water_content_profile(p.index_properties(), vs="elevation")
fig, ax = ht.plot.water_content_profile(p.atterberg(geology=["Upper Clay"]), strata=strata)
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Neither `water_content` nor both limits | Error naming the columns |
| PL > LL | Bar not drawn; warning naming the rows (impossible) |
| Text in `water_content` (`NP`, `dry`) | P01's text values (P01 §3) |
| Text in a limit column | Error naming the rows; use `non_plastic` for NP |
| w beyond LL or below PL | Drawn as given: that is what the plot is for |
| Duplicate rows | Drawn as given |

## 12. Acceptance criteria and tests
- **Geometry:** for a specimen at 10 ft with PL 20, LL 45 and w 30, the bar runs from x = 20 to x = 45 at y = 10, and the marker is at (30, 10).
- **No PL from PI:** LL 45, PI 25, PL blank draws a single tick at 45, is counted in the footnote, and the warning names the row and says PL wasn't computed.
- **NP:** an NP specimen with w 18 is an open marker at 18 with no bar, counted in the legend entry; without w, counted in the footnote.
- **Limits:** the default x limit covers an LL of 72 (to 80); with `xlim=(0, 50)`, that bar is clipped with an arrow and counted.
- **P01 passes through:** `strata=`, `water_level=` and `stats_box=` behave as in P01; `limits=False` gives P01's figure.
- **Datasets:** `p.atterberg()` and `p.index_properties()` both draw with no warning.
- **Automated:** renders against depth and elevation; `ax=` composes on a `Sheet`; no `rcParams` change; US and SI differ only in the vertical axis.
- **Visual check:** `docs/plots/img/P06-us.png` and `P06-si.png` from the example project.
- **Test data:** the example project, and synthetic frames for the cases above.

## 13. References
- ASTM D4318 (liquid limit, plastic limit, plasticity index).
- ASTM D2216 (water content).

## 14. Open questions
None open. Decided in review:
1. **NP with a water content** is drawn at its w as an open marker, not at the axis edge: unlike a text value, it has a position (§7).
2. **One limit only** draws a single end tick, so a measured LL isn't lost (§7).
3. **PL isn't computed from LL − PI**: the row is drawn with one limit, counted and warned about, so the user finds the PL or removes the row (§4).

## 15. Future enhancements
- Liquidity index as a second x axis or panel.
- Several profiles side by side (w, s_u, γ) with a shared vertical axis (P01 §15).
