# Phase 1 analyses — feature spec

**Status:** §1 SPT is decided (M3). §2–3 Atterberg limits, classification and grain size are decided (M8), except values marked 🔬. §4 is specified in M13's units of work (`docs/work/m13b1-spt-framework.md`). Analyses are specified here, apart from the plot specs, so they can be used without a plot.
**Parent:** SPEC §4. The cross-cutting analysis decisions are there. This file holds the detail. Depth conventions are in SPEC §8.

---

## 1. SPT (used by P02, P03)

**Status:** decided (M3). Everything in this section is decided except where marked 🔬.

### 1.1 Purpose
Turns SPT results as reported into the values the plots and an engineer need: whether each test is a refusal, N60, and N capped for refusals. It also gives each test a relative-density or consistency class. Both work without a plot: `ht.analysis.spt(df)` returns the table with the derived columns, ready to export or filter.

### 1.2 Input
One row per SPT test, as `ht.template("spt")`.

| Column | Required | Used for |
|---|---|---|
| `spt_n` | ✔ | N as reported |
| `energy_ratio` | – | N60, per row (%) |
| `spt_refusal` | – | Refusal, where filled in |
| `spt_penetration` | – | Refusal, where `spt_refusal` is blank. Needs units (`small_length`) |
| `spt_n60` | – | Kept where filled in; only blanks are computed |
| `depth`, `elevation`, `geology_unit`, … | – | Passed through unchanged |

**Test depth** is `depth` as given. Mid-drive depth from the increment penetrations (SPEC §8.2) needs the AGS increments, which the CSV template doesn't have, so it is Phase 2.

### 1.3 `ht.analysis.spt()`
```python
spt(df, *, hammer_efficiency=None, cap=None, units=None) -> pandas.DataFrame
```
Returns a copy of `df` with `spt_refusal`, `spt_n60` and `spt_n_capped` added, or their blanks filled in. It never drops, reorders or changes other rows or columns, and keeps `df.attrs["units"]`. `df` itself is not modified.

**Refusal** (`spt_refusal`), for each row:
1. the row's `spt_refusal`, where it is filled in;
2. else True if `spt_penetration` < 450 mm (seating plus test drive not completed), False if ≥ 450 mm, compared with a 1e-6 mm slack so 450 mm written in another unit isn't a refusal by rounding;
3. else False: with neither, the reported N stands.

`spt_refusal` accepts True/False, 1/0 and the text true/false/yes/no in any case; anything else is an error. The units of `spt_penetration` are resolved as SPEC §2.6 and are needed only when step 2 is used.

**N60** (`spt_n60`) = N × ER / 60, where ER, for each row, is:
1. the row's `energy_ratio`;
2. else `hammer_efficiency=`;
3. else `ht.settings.hammer_efficiency`;
4. else none, and N60 stays blank (SPEC §4: there is no default).

An `spt_n60` already filled in is kept. N60 is computed for refusals too; the plots decide how refusals are drawn.

**Capped N** (`spt_n_capped`) = min(N, cap), and = cap for every refusal, including a refusal with a blank N. `cap` is `cap=`, else `ht.settings.spt_cap` (100). Only N is capped. N60 isn't: a non-refusal N60 above 100 is a real value.

**Refusals in plots and statistics** are included by default at the cap, with a note (SPEC §4). For fitting and characteristic values they are censored (🔬 TODO #8, Phase 3).

### 1.4 `ht.analysis.spt_class()`
```python
spt_class(df, *, n="spt_n", table="cohesionless") -> pandas.Series
```
Returns each test's class as an ordered categorical, in table order with "Refusal" last. It runs `spt()` on `df` first, so the refusal rule is the same.

- **Which table** is the user's call: they pick `table=` and pass the rows it applies to. `soil_class` isn't read.
- **Which value:** the column named by `n` (`spt_n`, `spt_n60` or `spt_n_capped`). For N60, set `ht.settings.hammer_efficiency`, fill in `energy_ratio`, or run `spt()` first with `hammer_efficiency=`; what `spt()` filled in is kept.
- **Lower bound inclusive:** a class runs from its lower bound up to, not including, the next one. N = 0 is "very loose", N = 10 "medium dense", N = 50 "very dense".
- **A refusal** is "Refusal" only, whatever its N. A blank value gives a blank class.

The tables are in `config/spt_classes.yaml`, each a list of `{name, lower}`:

| `cohesionless` (relative density) | N | `cohesive` (consistency) | N |
|---|---|---|---|
| Very loose | 0–4 | Very soft | 0–2 |
| Loose | 4–10 | Soft | 2–4 |
| Medium dense | 10–30 | Medium stiff | 4–8 |
| Dense | 30–50 | Stiff | 8–15 |
| Very dense | ≥ 50 | Very stiff | 15–30 |
| | | Hard | ≥ 30 |

Sources: Terzaghi & Peck (1948); Peck, Hanson & Thornburn (1974). User-defined bins are a later addition.

**Pitfall:** `pd.cut` bins are right-closed by default, which drops N = 0 and puts N = 4 in "very loose". The golden values in §1.6 catch it.

### 1.5 Errors
Each says what is wrong, where (the rows, listed as the plots do) and what to do (SPEC §11).
- No `spt_n` column: list the columns available.
- `spt_n` not numeric, or negative.
- `energy_ratio` or `hammer_efficiency` outside (0, 100]. The hint says an energy ratio of 0.8 is entered as 80.
- `cap` not a positive whole number.
- `spt_refusal` holding something other than the values above.
- `spt_penetration` with no units when a row needs it (`UnitsError`, with the `set_units` example).
- `spt_class`: an unknown `table` (list the two); `n` other than the three columns in §1.4; negative values in the `n` column (an `spt_n60` filled in by the user).

### 1.6 Acceptance criteria and golden values
Worked by hand.

**N60**
- N = 30, ER = 80 → 40.0. N = 25, ER = 55 → 22.917.
- ER from the row is used in preference to `hammer_efficiency=`, which is used in preference to the setting.
- No ER anywhere → blank. An `spt_n60` already filled in is kept.

**Refusal**
- `spt_refusal` given → kept.
- Blank, with penetration 300 mm → True; 450 mm → False; 12 in (304.8 mm) → True; 18 in (457.2 mm) → False.
- Blank, with no penetration → False.

**Capped N**
- N = 120 → 100. A refusal with N = 38 → 100. A refusal with blank N → 100.
- `cap=50`, and `ht.settings.spt_cap = 50`, give 50.

**Classes**
- Cohesionless, N = [0, 4, 10, 29, 30, 50, 51] → very loose, loose, medium dense, medium dense, dense, very dense, very dense.
- Cohesive, N = [0, 1, 2, 4, 8, 15, 30, 31] → very soft, very soft, soft, medium stiff, stiff, very stiff, hard, hard.
- A refusal with N = 12 → "Refusal".
- Every row with a value lands in exactly one class.

**Rows**
- The output has the same rows in the same order, and keeps `attrs["units"]`. `df` is unchanged.

### 1.7 Phase 2
- Mid-drive depth from increments (SPEC §8.2).
- Refusal from a test-drive penetration below 300 mm, and from report strings such as `25/75 50/30`.
- `refusal="extrapolate"`: N = blows × 300 / penetration. It needs the blows in the partial drive.

## 2. Atterberg limits and classification (used by P04, P06)

**Status:** decided (M8, [intent](../work/m8-index-plots.md#intent)). Values marked 🔬 are checked against the standard before the build (TODO #5).

### 2.1 Purpose
Gives each specimen its plasticity index, liquidity and consistency indices, and its class on the plasticity chart. For specimens with both Atterberg limits and a grading, it also gives the full USCS group symbol and the AASHTO group and group index. Each is a plain function, usable without a plot. P04 draws the chart lines from the same config, so the chart and the classes can't disagree.

### 2.2 Input
`plasticity()` takes one row per specimen, as `ht.template("atterberg")` or `p.atterberg()`:

| Column | Required | Used for |
|---|---|---|
| `liquid_limit` | ✔ (column) | Classes, Ic |
| `plastic_limit` | – | PI where `plasticity_index` is blank; LI |
| `plasticity_index` | – | Classes, LI, Ic. Computed as LL − PL where blank |
| `non_plastic` | – | NP specimens (true/false, read as `spt_refusal` is in §1.3) |
| `water_content` | – | LI, Ic |
| others | – | Passed through unchanged |

`uscs()` and `aashto()` take one row per specimen with the Atterberg columns above **and** the gradation columns from `gradation()` (§3.4), as `p.index_properties()` gives them (M8, data for P06). A CSV user with lab-reported fractions types them in the same columns.

### 2.3 Config: plasticity systems
Lines and bands live in `config/plasticity_systems.yaml`, each system with its citation. `plasticity()`, `uscs()` and P04 all read it.

**`uscs`** (ASTM D2487-17) 🔬:
- A-line: PI = 0.73 (LL − 20). U-line: PI = 0.9 (LL − 8), with its vertical part at LL = 16 below PI = 7 (P04 draws it; no class uses it).
- LL = 50 divides low (L) from high (H) plasticity; LL = 50 is H.
- CL-ML zone: 4 ≤ PI ≤ 7, on or above the A-line.

**`bs5930`** (BS 5930:2015+A1:2020) 🔬 (you are confirming the bands):
- The same A-line.
- Plasticity terms by LL, lower bound inclusive: L (low) < 35, I (intermediate) 35–50, H (high) 50–70, V (very high) 70–90, E (extremely high) ≥ 90.

### 2.4 `ht.analysis.plasticity()`
```python
plasticity(df) -> pandas.DataFrame
```
Returns a copy of `df` with these columns added, or their blanks filled. It never drops, reorders or changes other rows, and keeps `df.attrs["units"]`:

| Column | Rule |
|---|---|
| `plasticity_index` | Kept where given. Blank → LL − PL where both are given. Blank for NP |
| `liquidity_index` | (w − PL) / PI. Blank for NP, or when PI ≤ 0 |
| `consistency_index` | (LL − w) / PI. Blank likewise |
| `plasticity_class_uscs` | §2.5 |
| `plasticity_class_bs5930` | §2.5 |

`p.atterberg()` computes its LI and Ic with this function from M8 on, so they're defined once.

### 2.5 Plasticity classes
A point is **on or above** the A-line when PI ≥ 0.73 (LL − 20) − 1e-9. The slack keeps a point exactly on the line on the clay side, as both standards put it.

**USCS** (`plasticity_class_uscs`), the fine-grained symbol from LL and PI only:

| Condition | Class |
|---|---|
| LL < 50, PI > 7, on or above the A-line | CL |
| LL < 50, 4 ≤ PI ≤ 7, on or above the A-line | CL-ML |
| LL < 50, PI < 4 or below the A-line | ML |
| LL ≥ 50, on or above the A-line | CH |
| LL ≥ 50, below the A-line | MH |

**BS 5930** (`plasticity_class_bs5930`): C (above or on the A-line) or M (below), then the plasticity term from LL: `CL`, `CI`, `CH`, `CV`, `CE`, `ML`, `MI`, … .

- **NP** is classified as PI = 0 for the class only (D2487 puts non-plastic fines with ML or MH). `plasticity_index` stays blank, so NP stays distinct everywhere else. An NP specimen with no LL is `ML` in USCS and blank in BS 5930 (the term needs LL).
- **OL and OH are never given** (M8 intent, decision 3; TODO #22). The docstring says the USCS class is the inorganic one, and that an organic soil must be identified by the user.
- **Blank** LL, or a blank PI on a plastic specimen, gives a blank class.

### 2.6 `ht.analysis.uscs()`
```python
uscs(df) -> pandas.DataFrame
```
Adds `uscs_symbol`, the USCS group symbol (ASTM D2487-17, Figures 1 and 3) 🔬. Group names are out of scope.

**Fractions** are from `gradation(..., fractions="astm_uscs")`: `gravel_content`, `sand_content`, `fines_content`, and `cobbles_content`/`boulders_content` where present. D2487 classifies the part finer than 75 mm, so each is divided by (100 − cobbles − boulders) first. The `fraction_system` column must say `astm_uscs`. If the column is missing, the error asks the user to add it, which confirms that typed-in fractions use the ASTM boundaries (4.75 mm and 0.075 mm). hangtu doesn't assume it.

**Fine-grained** (fines ≥ 50%): the USCS plasticity class (§2.5).

**Coarse-grained** (fines < 50%):
- **G or S:** G when gravel > sand, otherwise S (D2487: more than half of the coarse fraction retained on the 4.75 mm sieve).
- **W or P:** W when Cu ≥ 4 (gravel) or Cu ≥ 6 (sand), and 1 ≤ Cc ≤ 3; otherwise P. The limits and the 5% and 12% fines boundaries are compared with a 1e-9 slack, as the A-line is, so a value exactly on one (Cc = 0.3²/(0.1 × 0.9)) stays on the inclusive side. Cu and Cc come from `uniformity_coefficient` and `curvature_coefficient`, or from `d10`, `d30` and `d60` where those are blank.
- **M or C** from the fines' USCS plasticity class: ML or MH → M; CL or CH → C; CL-ML → C-M.

| Fines | Symbol |
|---|---|
| < 5% | GW, GP, SW, SP |
| 5–12% (both inclusive) | Dual: GW-GM, GW-GC, GP-GM, GP-GC, SW-SM, SW-SC, SP-SM, SP-SC. CL-ML fines count as C 🔬 |
| > 12% | GM, GC, GC-GM, SM, SC, SC-SM |

**Blank symbol, counted in one warning by reason:** no fractions; fines ≥ 5% with no plasticity class; fines ≤ 12% with no Cu or Cc (D10 often can't be found when fines are near 10% and there's no hydrometer, §3.3). hangtu never picks between two symbols it can't tell apart.

### 2.7 `ht.analysis.aashto()`
```python
aashto(df) -> pandas.DataFrame
```
Adds `aashto_group` (e.g. `A-2-6`, `A-7-5`) and `aashto_group_index` (a whole number) by AASHTO M 145 🔬.

**Input:** LL, PI (NP allowed), and the percent passing 2.00, 0.425 and 0.075 mm. These come from `gradation(..., fractions="aashto")`: passing 0.075 mm = `silt_clay_content`, passing 0.425 mm = that plus `fine_sand_content`, and passing 2.00 mm = that plus `coarse_sand_content`. The `fraction_system` column must say `aashto`. As in USCS, the classification uses the part finer than 75 mm.

**Rounding:** M 145's limits are whole numbers with gaps (LL ≤ 40, LL ≥ 41). LL, PI and the passing percentages are rounded to whole numbers (half up) before they're compared 🔬.

**Groups**, tested left to right; the first that fits is the group:

| Group | Passing 2.00 mm | 0.425 mm | 0.075 mm | LL | PI |
|---|---|---|---|---|---|
| A-1-a | ≤ 50 | ≤ 30 | ≤ 15 | | ≤ 6 |
| A-1-b | | ≤ 50 | ≤ 25 | | ≤ 6 |
| A-3 | | ≥ 51 | ≤ 10 | | NP |
| A-2-4 | | | ≤ 35 | ≤ 40 | ≤ 10 |
| A-2-5 | | | ≤ 35 | ≥ 41 | ≤ 10 |
| A-2-6 | | | ≤ 35 | ≤ 40 | ≥ 11 |
| A-2-7 | | | ≤ 35 | ≥ 41 | ≥ 11 |
| A-4 | | | ≥ 36 | ≤ 40 | ≤ 10 |
| A-5 | | | ≥ 36 | ≥ 41 | ≤ 10 |
| A-6 | | | ≥ 36 | ≤ 40 | ≥ 11 |
| A-7-5 | | | ≥ 36 | ≥ 41 | ≥ 11, and PI ≤ LL − 30 |
| A-7-6 | | | ≥ 36 | ≥ 41 | ≥ 11, and PI > LL − 30 |

NP counts as PI = 0 against the PI limits. A-3 needs NP.

**Group index**, with F = passing 0.075 mm:
- GI = (F − 35)[0.2 + 0.005 (LL − 40)] + 0.01 (F − 15)(PI − 10).
- A-2-6 and A-2-7 use only the PI term: 0.01 (F − 15)(PI − 10).
- A-1-a, A-1-b, A-2-4, A-2-5 and A-3: 0.
- Negative → 0. Rounded to the nearest whole number. No upper limit.

**Blank, counted in one warning:** a missing passing percentage, LL or PI could decide the group. Groups are tested left to right; one that a known value rules out is skipped, so a soil with F = 60 needs no passing 2.00 mm, but one that might be A-1-b with the passing 0.425 mm missing is blank.

### 2.8 Errors
Each says what is wrong, where (the rows) and what to do (SPEC §11).
- No `liquid_limit` column (`plasticity()`): list the columns available.
- LL, PL, PI or w not numeric; any negative.
- PL above LL on a specimen not marked NP (impossible; the error suggests checking the columns or marking it NP).
- A specimen marked `non_plastic` that also has a PI: NP has no PI, so the user blanks one or the other.
- `non_plastic` holding something other than true/false (read as `spt_refusal`).
- `uscs()`/`aashto()`: a required column missing, or `fraction_system` missing or naming another system.

**Warnings** (one per kind per call): PI > LL (impossible, kept); PI given and more than 1 percentage point from LL − PL (the PI given is kept; QC A002 does the same check on AGS files); classes and symbols left blank, by reason.

### 2.9 Acceptance criteria and golden values
Worked by hand.

**Indices**
- LL = 45, PL = 20, w = 30, PI blank → PI = 25, LI = 0.40, Ic = 0.60.
- PI given as 24 with LL − PL = 25: 24 is kept and a warning names the row.
- NP: PI, LI and Ic blank.

**USCS plasticity class**
- (LL, PI) = (45, 25) → CL; (60, 20) → MH (A-line 29.2); (22, 5) → CL-ML; (30, 6) → ML (A-line 7.3); (50, 30) → CH; (40, 14.6), on the A-line → CL; (49.9, 3.9) → ML.
- NP with LL 35 → ML; NP with LL 55 → MH.

**BS 5930 class**
- (34.9, 15) → CL; (35, 15) → CI; (60, 20) → MH; (95, 70) → CE.

**USCS symbol** (fractions as % of the part finer than 75 mm)
- Gravel 60, sand 35, fines 5 (CL), Cu 5, Cc 2 → GW-GC.
- Same, Cu 3.9 → GP-GC.
- Sand 96, fines 4, Cu 5.63, Cc 1.00 → SP (Cu < 6).
- Sand 80, fines 20, fines ML → SM; fines CL-ML → SC-SM.
- Gravel 45, sand 45, fines 10 → S (equal is not "more than half").
- Gravel 45, sand 37, fines 8, cobbles 10 (% of total) → rescaled 50.0, 41.1, 8.9 → G, with a dual symbol.
- Fines 50, (45, 25) → CL.
- Fines 8 with no Cu → blank, counted.

**AASHTO**
- F = 60, LL = 45, PI = 20 → A-7-6 (20 > 45 − 30), GI = 25 × 0.225 + 0.01 × 45 × 10 = 5.625 + 4.5 = 10.125 → 10.
- F = 30, LL = 35, PI = 15 → A-2-6, GI = 0.01 × 15 × 5 = 0.75 → 1.
- F = 40, LL = 25, PI = 5 → A-4, GI = 0.625 − 1.25 < 0 → 0.
- Passing 2.00/0.425/0.075 = 40/20/10, PI 4 → A-1-a, GI 0.
- Passing 0.425 = 80, 0.075 = 5, NP → A-3; the same with LL 20, PI 2 → A-2-4.
- F = 30, LL = 40.4, PI = 8 → LL rounds to 40, so A-2-4, not A-2-5.

**Rows:** the output has the same rows in the same order, and keeps `attrs["units"]`. `df` is unchanged.

**Pitfalls:**
- Comparing a point to the A-line with `>` and float noise, so a point on the line flips to M.
- Classifying USCS on fractions of the whole sample when it has cobbles.
- Testing AASHTO groups in any order but left to right: A-2-4 also fits many A-1 soils.

## 3. Grain size (used by P05)

**Status:** decided (M8), as §2.

### 3.1 Purpose
Turns grading curves (one row per sieve or hydrometer point) into one row per specimen: D-values, Cu, Cc and the size fractions of a named system. The P05 header band and sieve labels read the same fraction system, so the band and the numbers can't disagree.

### 3.2 Input
One row per curve point, as `ht.template("grain_size")` or `p.grain_size()`.

| Column | Required | Used for |
|---|---|---|
| `specimen_id` | ✔ | Curve identity, with `loca_id` where present |
| `particle_size` | ✔ | Needs units (`particle_size` kind, SPEC §2.6); converted to mm |
| `percent_passing` | ✔ | 0–100 |
| others | – | Carried to the output when constant within the curve (§3.4) |

### 3.3 D-values
- Points are sorted by `particle_size`, **as rows**. Blank passing or size: the point is left out and counted.
- **Log-linear interpolation** between the two points that bracket x: log Dx = log s₁ + (x − p₁)/(p₂ − p₁) · (log s₂ − log s₁). A point exactly at x gives its size.
- **Never extrapolated:** if the finest point passes more than x%, or the coarsest less, Dx is blank and counted.
- **Several crossings** (a flat run at x, or a small dip): the finest size where the curve reaches x.
- **Non-monotonic curves:** a drop of more than 0.5 percentage points (QC P001's tolerance) toward finer sizes gives blank D-values and fractions for that curve, with a warning naming it. Smaller drops are treated as noise.
- `d_values=(10, 30, 60)` by default. Any whole number 1–99 is allowed, as a column `d<x>`; `d15`, `d50` and `d85` (filter criteria) join the registry, and other values give a column outside it, which the docstring says.
- **Cu** = D60/D10 and **Cc** = D30²/(D10 · D60), where those D-values exist.

### 3.4 `ht.analysis.gradation()`
```python
gradation(df, *, fractions="astm_uscs", d_values=(10, 30, 60), units=None) -> pandas.DataFrame
```
Returns **one row per curve**, in order of first appearance: the identity columns; every other input column that is constant within each curve (depth, elevation, geology unit, …); the `d<x>` columns; `uniformity_coefficient`; `curvature_coefficient`; one `<fraction>_content` column per fraction of the system; and `fraction_system`. Columns that vary within a curve (`particle_size`, `percent_passing`, `qualifier`, `source_line`) aren't carried, which the docstring says. D-values are in mm (`attrs["units"]`). Curves with fewer than two points get a row with blanks, counted in a warning.

USCS gradation (W or P) depends on whether the soil is a gravel or a sand, so it is part of `uscs_symbol` (§2.6) rather than a column of its own (the `gradation_uscs` column in the M7 notes is dropped).

### 3.5 Fraction systems
A **fraction system** is one data structure (M8 intent, decision 5): a name, a citation, and an ordered list of fractions, each with lower and upper sizes in mm and optional named parts (fine, medium, coarse) for the P05 header band. Columns are made from the main fractions only.

- **Built in** (`config/fraction_systems.yaml`) 🔬:

| System | Fractions (mm) | Parts |
|---|---|---|
| `astm_uscs` (ASTM D2487-17) | fines < 0.075; sand 0.075–4.75; gravel 4.75–75; cobbles 75–300; boulders ≥ 300 | sand: fine < 0.425, medium < 2.0, coarse; gravel: fine < 19, coarse |
| `aashto` (AASHTO M 145) | silt_clay < 0.075; fine_sand 0.075–0.425; coarse_sand 0.425–2.0; gravel 2.0–75; boulders ≥ 75 | – |
| `iso14688` (ISO 14688-1:2017) | clay < 0.002; silt 0.002–0.063; sand 0.063–2.0; gravel 2.0–63; cobbles 63–200; boulders ≥ 200 | silt, sand and gravel: fine, medium, coarse at 0.0063/0.02, 0.2/0.63, 6.3/20 |

  USCS has no clay–silt boundary, so `astm_uscs` has one fines fraction (M8 intent, decision 5).
- **The user's own:** `fractions=` takes a dict in the same structure, or the path to a YAML file holding one, with a `name` that goes in `fraction_system` and isn't one of the built-in names (so `uscs()` can't mistake it for `astm_uscs`). It is checked (sizes increasing, no gaps or overlaps, names unique) and errors say which fraction is wrong. Its fraction names make columns `<name>_content`, which must not collide with an existing registry column.

**A fraction's percentage** = P(upper) − P(lower), where P(size) is the passing at that size:
- interpolated log-linearly on the curve (as §3.3), and given exactly at a point;
- P(0) = 0;
- above the coarsest point: 100 if the coarsest point passes 100%, else blank;
- below the finest point: 0 if the finest point passes 0%, else blank.

A fraction needing a blank P is blank, never estimated: without a hydrometer, ISO clay and silt are blank. The fractions of a curve sum to 100 when none is blank.

**Column names:** `fines_content`, `sand_content`, `gravel_content`, `cobbles_content`, `boulders_content`, `silt_content`, `clay_content`, `silt_clay_content`, `fine_sand_content`, `coarse_sand_content`, and `fraction_system`. A fraction name means different sizes in different systems (gravel starts at 4.75 mm in USCS, 2.0 mm in AASHTO and ISO), which is why every row carries `fraction_system`, and `uscs()` and `aashto()` check it. It is a column rather than an attribute so it survives a CSV export.

### 3.6 Errors
- A required column missing; `particle_size` with no units (`UnitsError`, with the `set_units` example).
- `particle_size` ≤ 0; `percent_passing` outside 0–100; two points at the same size in one curve (rows listed).
- A blank `specimen_id` (rows listed): its points can't be put on a curve.
- An unknown `fractions` name (list the three); a malformed user system; `d_values` outside 1–99.

**Warnings** (one per kind per call): points with a blank size or passing; curves with fewer than two points; non-monotonic curves; D-values or fractions left blank because the curve doesn't reach them.

### 3.7 Acceptance criteria and golden values
Worked by hand on curve A: sizes 0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75 mm passing 4, 12, 30, 55, 75, 90, 100%.

- D10 = 0.075 × 2^0.75 = **0.1261 mm**; D30 = **0.300 mm** (on a point); D60 = 0.6 × (1.18/0.6)^0.25 = **0.7105 mm**.
- Cu = **5.633**, Cc = **1.004**.
- `astm_uscs`: fines **4.0**, sand **96.0**, gravel **0.0**, cobbles **0.0**, boulders **0.0** (above 4.75 mm, P = 100).
- `aashto`: silt_clay **4.0**; P(0.425) = **42.56**, so fine_sand **38.56**; P(2.0) = **86.42**, so coarse_sand **43.86**; gravel **13.58**.
- `iso14688`: clay, silt and sand **blank** (P(0.063) is below the finest point, which passes 4%); gravel **13.58**; cobbles **0.0**.
- With the 30% point removed: D30 is interpolated between 0.15 and 0.6 (worked in the test).
- A curve that starts at 15% passing: D10 blank, counted.
- A drop of 0.4 points is computed; a drop of 2 points blanks the curve and warns.
- `particle_size` in inches is converted before interpolating (1 in = 25.4 mm).
- A user system with an overlap is an error naming both fractions.

**Pitfalls** (from the P05 draft):
- Sorting `particle_size` and `percent_passing` independently, which re-pairs the points.
- Typos in boundaries: fine/medium sand is 0.425 mm, not 0.475; fine/coarse gravel is 19 mm, not 20. The config test checks every boundary against the table above.
- Interpolating linearly in size instead of log size.

## 4. SPT correlations (M13)
The principles are decided in SPEC §4. The framework, C_N and (N1)60 are specified in `docs/work/m13b1-spt-framework.md` (Spec), decided 2026-10-22; that spec settles the points below where they differ (the column is `correlation_name`; the function has no argument choosing its input column; docstrings are written by hand and tested against the config). The list stays as the draft it was.

- **Module:** `ht.analysis.correlations`, one function per published correlation, named after the source (`sowers_1979`, `hatanaka_uchida_1996`). The docstring follows the same headings for every correlation: equation, source, applies to, doesn't apply to, input N, range, derived from, notes.
- **Metadata:** the same facts as a YAML entry in the config (proposed `config/correlations.yaml`), so the docstring, the result's `df.attrs` and a plot footnote all come from one place. Constants are kept in the source's units and converted with pint.
- **Input N is explicit.** Each correlation declares which N it was derived with. If the column the user passes doesn't match (field N into an N60 correlation), the function raises an error that names the expected column, rather than guessing a correction.
- **Out of range:** NaN plus a count, by reason (outside the N range, wrong soil type, refusal, missing input). Refusals give no estimate.
- **Output:** long format, one row per test and correlation, with the estimate in the target property's registry column and a column naming the correlation, so `profile(est, "friction_angle", color_by=<that column>)` compares several correlations against depth. Correlations that give a range (Sowers) return lower and upper values. Column names are to be checked against the registry (`method` is already the test method).
- **Comparison:** P01 and P07 draw the results. Overlaying measured values (lab s_u, φ′ from P11) on the estimates is the main use, so it should be one call.

### 4.1 Vertical stress and (N1)60
(N1)60 = N60 × C_N, with C_N from the effective vertical stress σ′v. Some correlations (Kulhawy & Mayne 1990) also take σ′v. So σ′v is its own function, and (N1)60 and the correlations take a σ′v column as input.

`ht.analysis.vertical_stress()` is specified in `docs/work/m13a-judgments.md` (Spec), decided 2026-10-22: unit weights by a log column from the judgments file, integrated through each hole's stratigraphy, and water levels by hole. That replaces the depth profile and `interpolation=` drafted here on 2026-10-15. Still from that draft: the hydrostatic pore pressure, γw as the setting `ht.settings.water_unit_weight`, and the assumptions stated in the docstring (level ground with laterally uniform layers; geostatic stress only, with no surcharge, structures or arching; hydrostatic pore pressure; not conservative in a fixed direction, since a σ′v that's too high lowers (N1)60, safe for strength, but also lowers OCR, unsafe for settlement).

C_N is settled in `docs/work/m13b1-spt-framework.md`: Liao & Whitman (1986) or Kayen et al. (1992) by a required `method=`, capped at 1.7, blank above 300 kPa (Youd et al. 2001).

### 4.2 Candidate correlations (settled in M13 b1–b3; the built set is in `src/hangtu/config/correlations.yaml`)
Friction angle is built in M13 unit (b1) (Hatanaka & Uchida 1996; Kulhawy & Mayne 1990; Wolff 1989 cut, TODO #36). Undrained shear strength, σ′p/OCR and K0 are unit (b2)'s, specified in `docs/work/m13b2-spt-strength-history.md` (decided 2026-10-23): Stroud (1974), Terzaghi & Peck (1967) as a band, Mayne & Kemper (1988) for σ′p and for OCR, and Kulhawy et al. (1989) for K0; Sowers (1979) cut (TODO #39). Functions are named target first (`undrained_shear_strength_stroud_1974`). Young's modulus and Vs are unit (b3)'s, specified in `docs/work/m13b3-spt-stiffness.md` (decided 2026-10-26): AASHTO (2004) on (N1)60 and Kulhawy & Mayne (1990) on N60 for drained E, each with a coefficient by a required soil row (`soil=`), and Imai & Tonouchi (1982) and Ohta & Goto (1978) for Vs in Wair et al.'s (2012) N60 forms. The table is the draft it was:

| Property | Candidates |
|---|---|
| Undrained shear strength | Terzaghi & Peck (1967); Sowers (1979) (P28 draft); Stroud (1974), f1 × N60 by PI |
| Friction angle | Peck, Hanson & Thornburn (1974), as fitted by Wolff (1989); Hatanaka & Uchida (1996); Kulhawy & Mayne (1990) |
| Relative density | Skempton (1986); Meyerhof (1957) |
| Young's modulus | Kulhawy & Mayne (1990), by soil type |
| Shear wave velocity | Imai & Tonouchi (1982) |
