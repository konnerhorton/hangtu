# P05 — Grain size distribution

| | |
|---|---|
| **ID / function** | P05 · `ht.plot.grain_size()` (uses `ht.analysis.gradation()`) |
| **Status** | built |
| **Type** | plot + analysis (D-values, fractions) |
| **Target version** | v0.2 (milestone M8) |
| **Depends on** | P00, the gradation analysis (`docs/drafts/analysis.md` §3) |
| **Related** | QC P001 (non-monotonic curves). P25 draft (fractions by unit). TODO #5 (verify the boundaries), #17 (sizes in mm). M8 intent: `docs/work/m8-index-plots.md` |

---

## 1. Purpose
Draws particle-size distribution curves, one per specimen, on a log size axis, with the soil fractions named in a band above. It answers: what is this soil, how well graded is it, and does it fall inside a project's or a specification's envelope. It's in the lab section of almost every report, and in filter and grouting design.

## 2. Reference figure
```
     ┌──────┬───────────────────────┬────────────────┬────────┐
     │      │         Sand          │     Gravel     │        │   ← fractions
     │Fines │ fine │ medium │ coarse│  fine  │ coarse│Cobbles │   ← parts
     └──────┴──────┴────────┴───────┴────────┴───────┴────────┘
            #140  #60      #10    3/8"   1-1/2"                    ← sieve labels,
          #200  #100  #40  #20  #4   3/4"   3"                       two rows when crowded
     ┌─────┴────┴─────┴─────┴────┴───┴─────┴────┴──────────────┐
 100 ┤                                                          │
     │                          __________________/           │
     │                   ______/ ░░░░ envelope ░░░░           │
  %  │            ______/ ┊D60                                │
 pass│     ______/ ┊D30   ┊                                   │
   0 ┼────┴────────┴──────┴───────────────────────────────────┤
    0.001     0.01      0.1       1        10       100   1000
                        Particle size (mm)
```
**A good version:**
- whole decades on the size axis, with minor gridlines, so values can be read off;
- the fraction band and the sieve labels come from one named system, so they can't disagree with each other or with the numbers;
- one curve per specimen, colored by unit, with points at the measured sizes;
- nothing is reshaped: a curve that rises toward finer sizes is drawn as measured and warned about.

## 3. Input data
**Row grain:** one row per curve point: the `grain_size` template, or `p.grain_size()`.

| Column | Description | Quantity kind | Req.? | Valid range | Notes |
|---|---|---|---|---|---|
| `specimen_id` | Curve identity | — | ✔ | | One curve per `loca_id` and `specimen_id` (analysis §3.4) |
| `particle_size` | Sieve or hydrometer size | particle_size | ✔ | > 0 | Needs units; shown in mm in both systems |
| `percent_passing` | % passing | percent | ✔ | 0–100 | |
| `loca_id` | Hole | — | – | | Curve identity |
| `geology_unit` | Geology unit | — | – | | Color (default) |
| `qualifier` | `<` or `>` | — | – | | Counted in the footnote; the point is drawn at its value |

**Hints** (one per call): "No 'geology_unit' column: all curves are drawn in one color."

**Minimum data:** two points per curve. A curve with fewer is skipped and counted.

## 4. Analysis / calculations
- Points are sorted by size **as rows**, with the analysis's sorting (`grading_curves()` in `_gradation.py`, which `gradation()` also uses), never one column at a time. The plot uses that function rather than `gradation()` itself, so short curves, blank points and unreached D-values are counted in the footnote instead of warned about.
- **Non-monotonic curves** (a rise of more than 0.5 percentage points toward finer sizes, QC P001's tolerance) are drawn as given, with one warning naming them.
- **D-values** (`d_values=`) come from the gradation analysis's `d_value()`, as in `ht.analysis.gradation()`: log-linear, never extrapolated. A D-value a curve doesn't reach isn't drawn and is counted. Curves the analysis can't use (fewer than two points, or non-monotonic) get none.
- **Fractions** in the header band come from the same fraction system as `gradation(fractions=)`: built in (`astm_uscs`, `aashto`, `iso14688`) or the user's (analysis §3.5).
- Nothing else is computed.

## 5. Figure layout
- **Panels:** the main axes, plus two thin axes above it sharing x: the sieve strip on the frame (0.05 in, plus 0.12 in per row of labels) and the fraction band above that (0.45 in). It's one figure element: with `ax=`, both are carved from the top of the axes given, so the plot still composes on a `Sheet`.
- **Legend and footnote** go below the x label, centered, the legend in up to four columns and the footnote under it, rather than on the right as on other plots: a column beside the axes squeezes the log axis, which needs its width to read sizes.
- **Default size:** `default` (6.5 × 4.5 in), landscape. `figsize=` covers a full Letter landscape sheet.
- `fig, ax` returns the main axes; the header is `ax.grain_size_header` (None with `fractions=None`) and the strip `ax.grain_size_sieves` (None with no sieve in the x range). Both come from one `make_axes_locatable(ax)` divider with `append_axes("top", ..., pad=0, sharex=ax)`, the strip first, which works under constrained layout.

## 6. Axes
| | X axis | Y axis |
|---|---|---|
| Quantity | `particle_size` | `percent_passing` |
| Label | `Particle size (mm)` | `Percent passing (%)` |
| Scale | log, whole decades | linear |
| Direction | coarse on the right (increasing to the right), in US and SI display alike; `reverse=True` puts coarse on the left | normal |
| Limits | whole decades covering the data, and at least 0.001–100 mm; a point on a whole decade moves that limit out one decade (P00 §8); `xlim=` overrides, exactly | 0–100, fixed |
| Ticks | decades labeled in plain numbers (0.001, 0.01, …, 100) | every 10 |
| Gridlines | major and minor (2–9) | every 10 |
| Secondary | sieve labels above the frame, under the band (`sieves=`) | — |

**Range constraints:**
- [x] Fixed y limits (0–100).
- [x] Log x: a whole number of decades, at least five.

## 7. Data marks
| Series | Mark | Color by | Legend entry | Notes |
|---|---|---|---|---|
| Curves | line 1 pt through the points, with 3 pt markers at each point | `geology_unit` (palette) | ✔ per unit, "Unit A (n = 6 curves)"; "All curves (n = 8)" with one color | `color_by` is any column that is the same for all of a curve's points (one that varies is an error). `color_by="specimen_id"`: one color per curve from the automatic cycle, in curve order and not remembered in the session palette; legend per curve |
| Points beyond `xlim` | open marker at the edge + arrow | curve color | footnote count | README policy |
| D-values | one curve: dashed leaders to both axes and a label "D60 = 0.711 mm" (3 significant figures); several curves: a small `|` tick across each curve at each D-value, no labels | black | — | `d_values=True` (D10, D30, D60) or a list |
| Envelopes | filled band between the lower and upper curves, alpha 0.2, outlined, under the gridlines | `envelope_colors=`, else gray | ✔ per envelope, after the curves | |

More than 20 curves with `color_by="specimen_id"`: the README legend rules apply, and the warning suggests coloring by unit.

**Draw order (bottom → top):** envelopes → gridlines → curves → D-value marks → sieve labels → footnote.

## 8. Overlays and annotations
| Overlay | Argument | Default | Source | Style | Notes |
|---|---|---|---|---|---|
| Fraction band | `fractions=` | `"astm_uscs"` | `config/fraction_systems.yaml` or the user's system | two rows: fraction names in the upper row, their parts (fine, medium, coarse) in the lower; a fraction without parts spans both, and a system without parts (`aashto`) has one row. Names are the fraction names with underscores as spaces, capitalized ("Silt clay"). Dividers at each boundary down through the main axes as light vertical lines (fraction boundaries solid, part boundaries dashed) | `None` hides the band and the dividers. Only fractions inside the x range are named, each centered on its visible part; a name narrower than 0.25 decade in view is left out |
| Sieve labels | `sieves=` | `"auto"`: US list in US display, ISO list in SI | `config/sieves.yaml` (new), cited | 6.5 pt, horizontal, in a strip above the frame and under the band, each over a short tick up from the frame. When any two neighbors are closer than 0.25 decade (the US list near #200), the labels alternate between two rows in size order; otherwise one row. Above the frame, so no curve crosses them | `"us"`, `"iso"`, `None`, or a list of `(size_mm, label)`; only sizes inside the x range are labeled |
| D-values | `d_values=` | off | `gradation()` | §7 | |
| Envelopes | `envelopes=` | off | user table (below) | §7 | |
| Note | `note=` | off | user | added to the footnote | |

**Sieve lists** (`config/sieves.yaml`) 🔬:
- `us` (ASTM E11 designations, written in ASCII so every font has them): 3" 75, 1-1/2" 37.5, 3/4" 19.0, 3/8" 9.5, #4 4.75, #10 2.00, #20 0.850, #40 0.425, #60 0.250, #100 0.150, #140 0.106, #200 0.075 mm.
- `iso` (labels in mm, at the ISO 14688-1 boundaries): 63, 20, 6.3, 2, 0.63, 0.2, 0.063.

**`envelopes=` format** (`ht.template("envelopes")`): one row per size: `label, particle_size, low, high`, with `low` and `high` the percent passing at that size. Rows sharing a `label` make one band, sorted by size as rows. `particle_size` needs units, from the table's own `attrs` (as P01's overlays). `label`, `low` and `high` are the existing overlay fields.

## 9. Units behavior
- Particle size is converted to mm on input and shown in mm in both systems (P00 §4.1, TODO #17).
- Only the sieve labels change with the display system (`sieves="auto"`). The curves and the band are the same, so a US and an SI figure differ only in those labels.

## 10. API
```python
def grain_size(
    df: pd.DataFrame,
    *,
    fractions: str | dict | os.PathLike | None = "astm_uscs",
    sieves: Literal["auto", "us", "iso"] | list[tuple[float, str]] | None = "auto",
    d_values: bool | list[int] = False,
    envelopes: pd.DataFrame | str | None = None,
    envelope_colors: dict[str, str] | None = None,
    color_by: str | None = "geology_unit",
    order: list[str] | None = None,
    reverse: bool = False,
    xlim: tuple[float, float] | None = None,
    note: str | None = None,
    palette: dict[str, str] | None = None,
    units: dict[str, str] | None = None,
    display_units: Literal["US", "SI"] | None = None,
    figsize: tuple[float, float] | None = None,
    ax: Axes | None = None,
    **style_overrides,
) -> tuple[Figure, Axes]:
```

**Example:**
```python
curves = p.grain_size(geology=["Alluvium"])
fig, ax = ht.plot.grain_size(curves, d_values=True)
fig, ax = ht.plot.grain_size(curves, fractions="iso14688", envelopes="filter_band.csv")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| Empty input | Axes with the band and a "No data" note; no error |
| Missing required column, no units for `particle_size`, sizes ≤ 0, passing outside 0–100, two points at one size in a curve, blank `specimen_id` | Errors from the analysis's checks (analysis §3.6) |
| Curve with fewer than two points | Not drawn; footnote "n curves with fewer than two points not shown" |
| Blank size or passing | Point left out; footnote count |
| Non-monotonic curve | Drawn as given; one warning naming the curves |
| D-value the curve doesn't reach | Not drawn; footnote "3 D-values not reached (D10 by 2 curves, D60 by 1 curve)" |
| D-value beyond `xlim` | Not drawn; counted as beyond the axis limit |
| `color_by` column that changes within a curve | Error naming the curves |
| A user fraction system | Validated by the analysis; its names and parts go in the band |
| Envelope with a blank or non-numeric size, `low` or `high`, `low` above `high`, values outside 0–100, a size ≤ 0 or twice, or fewer than two sizes | Error naming the envelope and its rows |
| Envelope table without units for `particle_size` | The plot data's units, with a warning; an error if the data have none either |
| More than 20 curves colored by specimen | README legend rules; warning suggests `color_by="geology_unit"` |

## 12. Acceptance criteria and tests
- **Band:** with `astm_uscs`, the dividers are at 0.075, 0.425, 2.0, 4.75, 19 and 75 mm (ASTM D2487); with `iso14688`, at 0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20 and 63 mm. Read back from the drawn artists.
- **Sieve labels:** "#200" at 0.075 mm and "#4" at 4.75 mm in US display; "0.063" at 0.063 mm in SI.
- **Curves:** a curve given in shuffled rows is drawn through its points in size order; a curve in inches lands where the same curve in mm does.
- **D-values:** the drawn D10, D30 and D60 of curve A (analysis §3.7) are at 0.1261, 0.300 and 0.7105 mm.
- **Envelopes:** a band's lower and upper edges pass through the table's points.
- **Direction:** `reverse=True` puts 100 mm left of 0.1 mm.
- **Counts:** the footnote counts short curves, blank points and unreached D-values.
- **Automated:** renders with each built-in system and a user's; `fractions=None` hides the band; `ax=` composes on a `Sheet`, header included; no `rcParams` change; US and SI differ only in sieve labels.
- **Visual check:** `docs/plots/img/P05-us.png` and `P05-si.png` from the example project's 14 grading curves (the fill and alluvium ones continuing into the fines from hydrometer tests) and an envelope, with D-values off, their default. The D-value ticks and the single-curve labels are checked by eye but not committed.
- **Test data:** the example project and synthetic curves (curve A, shuffled, inches, non-monotonic, short).

## 13. References
- ASTM D2487-17 (USCS fractions); ASTM D6913/D6913M (sieve analysis); ASTM E11 (sieve designations).
- AASHTO M 145 (AASHTO fractions).
- ISO 14688-1:2017 (ISO fractions).

## 14. Open questions
None open. Decided in review:
1. **Axis direction:** coarse on the right (size increasing to the right), the same default in US and SI display, so one figure serves both. `reverse=True` gives the coarse-on-the-left layout of some US forms (§6).
2. **Fraction dividers** run down through the main axes as light lines, so a curve can be read against the boundaries (§8).
3. **D-value labels** only for a single curve; ticks without labels for several (§7).
4. **Sieve lists** in a new `config/sieves.yaml`, with the ISO list at the fraction boundaries (§8). The labels sit above the frame and are horizontal (changed in the build's review from rotated labels inside the top edge, which curves near 100 % passing crossed).
5. **Envelope and fraction-system colors** are gray unless given, apart from geology unit colors (§7).

## 15. Future enhancements
- Envelopes computed from the data (min and max, or percentiles, per unit).
- User-defined PSD regions (v0.4, SPEC §1.3).
- Size fractions by unit (P25 draft).
