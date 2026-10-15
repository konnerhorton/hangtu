# Phase 1 analyses — feature spec

**Status:** §1 SPT is decided (M3). §2–3 are drafts, to be finished with P04–P06 (M8). §4 is a draft, to be finished with M13. Analyses are specified here, apart from the plot specs, so they can be used without a plot.
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
- **Plasticity chart systems**, selectable per call (decided):
  - **USCS** (ASTM D2487): A-line PI = 0.73(LL − 20); U-line PI = 0.9(LL − 8); CL-ML zone; LL = 50 divider.
  - **BS 5930** (2015+A1:2020): A-line, plus bands at LL 35/50/70/90.
- **Classification:** USCS fine-grained symbol from LL/PI. The full USCS symbol and **AASHTO** group/group index need gradation as well (decided: USCS and AASHTO first).
- **Liquidity index** LI = (w − PL)/PI; **consistency index** Ic = (LL − w)/PI.
- **NP:** shown as a count on plots (decided).

## 3. Grain size (used by P05)
- **Dx:** log-linear interpolation, never extrapolated.
- **Cu** = D60/D10; **Cc** = D30²/(D10·D60).
- **USCS gradation:** GW if Cu ≥ 4 and 1 ≤ Cc ≤ 3; SW if Cu ≥ 6 and 1 ≤ Cc ≤ 3.
- **Size-fraction systems are configurable** (decided): `astm_uscs`, `aashto`, `iso14688`, or custom.
- **Sieve axis is configurable** (decided). Default US list: 3", 1½", ¾", ⅜", #4, #10, #20, #40, #60, #100, #140, #200. An ISO list is used in SI display.
- In Phase 2, fractions are always recomputed from the sieve data (AGS GRAG fractions use ISO boundaries).
- User-defined PSD regions are a v0.4 item.

## 4. SPT correlations (draft, M13)
The principles are decided in SPEC §4. The rest is a draft.

- **Module:** `ht.analysis.correlations`, one function per published correlation, named after the source (`sowers_1979`, `hatanaka_uchida_1996`). The docstring follows the same headings for every correlation: equation, source, applies to, doesn't apply to, input N, range, derived from, notes.
- **Metadata:** the same facts as a YAML entry in the config (proposed `config/correlations.yaml`), so the docstring, the result's `df.attrs` and a plot footnote all come from one place. Constants are kept in the source's units and converted with pint.
- **Input N is explicit.** Each correlation declares which N it was derived with. If the column the user passes doesn't match (field N into an N60 correlation), the function raises an error that names the expected column, rather than guessing a correction.
- **Out of range:** NaN plus a count, by reason (outside the N range, wrong soil type, refusal, missing input). Refusals give no estimate.
- **Output:** long format, one row per test and correlation, with the estimate in the target property's registry column and a column naming the correlation, so `profile(est, "friction_angle", color_by=<that column>)` compares several correlations against depth. Correlations that give a range (Sowers) return lower and upper values. Column names are to be checked against the registry (`method` is already the test method).
- **Comparison:** P01 and P07 draw the results. Overlaying measured values (lab s_u, φ′ from P11) on the estimates is the main use, so it should be one call.

### 4.1 Vertical stress and (N1)60
(N1)60 = N60 × C_N, with C_N from the effective vertical stress σ′v. Some correlations (Kulhawy & Mayne 1990) also take σ′v. So σ′v is its own function, and (N1)60 and the correlations take a σ′v column as input.

`ht.analysis.vertical_stress(df, *, unit_weight, groundwater, interpolation="step")` adds total vertical stress, hydrostatic pore pressure and σ′v (names to check against the registry). Decided 2026-10-15:
- **Unit weight** is a single value or a profile table (`depth` or `elevation`, `bulk_unit_weight`), passed in the call. It's a design profile, not raw lab data: one value per depth, otherwise an error that names the repeated depths.
  - `interpolation="step"`: each row applies from its depth down to the next row (discrete properties per interval, as design profiles usually are). `"linear"`: linear between rows (a trend).
  - The first row applies from the ground surface, and the last row continues down. Both are stated in the docstring.
  - Total (bulk) unit weight throughout; σ′v = σv − u. A submerged unit weight is never asked for.
  - A profile in elevation is converted to depth with each hole's `ground_level` (SPEC §8). A hole without one is an error.
- **Groundwater** is a single depth or elevation for every hole, or `{loca_id: level}`. With a dict, every hole in the data must be in it; the error lists the missing holes. The user picks a level for holes without a record (to rethink later).
- **Pore pressure** is hydrostatic: u = γw (z − z_w) below the water level and 0 above it. Perched water and artesian pressure are out of scope. γw is a new setting, `ht.settings.water_unit_weight` (9.81 kN/m³, 62.4 pcf; plot drafts cross-cutting finding 4).
- **Auditability:** the profile, the interpolation and the water level used for each hole go in `df.attrs`.
- **Assumptions**, stated in the docstring as for the correlations: level ground with laterally uniform layers; geostatic stress only, with no surcharge, structures or arching (near trenches, tunnels, walls and slopes σv isn't γz); hydrostatic pore pressure. The result isn't conservative in a fixed direction: a σ′v that's too high lowers (N1)60 (safe for strength) but also lowers OCR (unsafe for settlement), so the docstring says so instead of claiming conservatism.

Open: which C_N (Liao & Whitman 1986; others) and its cap.

**Later:** unit weight by geology unit, `unit_weight={"Fill": 19, "Clay": 18}`, integrated layer by layer through each hole's log (the M7 geology joins already give the intervals). A suggested value per unit could come from the lab data (the median `bulk_unit_weight`, as P07 shows it), for the user to accept or change.

### 4.2 Candidate correlations (TODO #20)
To choose and verify against the sources:

| Property | Candidates |
|---|---|
| Undrained shear strength | Terzaghi & Peck (1967); Sowers (1979) (P28 draft); Stroud (1974), f1 × N60 by PI |
| Friction angle | Peck, Hanson & Thornburn (1974), as fitted by Wolff (1989); Hatanaka & Uchida (1996); Kulhawy & Mayne (1990) |
| Relative density | Skempton (1986); Meyerhof (1957) |
| Young's modulus | Kulhawy & Mayne (1990), by soil type |
| Shear wave velocity | Imai & Tonouchi (1982) |
