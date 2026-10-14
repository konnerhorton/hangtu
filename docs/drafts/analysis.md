# Phase 1 analyses — feature spec

**Status:** §1 SPT is decided (M3). §2–3 are drafts, to be finished with P04–P06 (M8). Analyses are specified here, apart from the plot specs, so they can be used without a plot.
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
2. else True if `spt_penetration` < 450 mm (seating plus test drive not completed), False if ≥ 450 mm;
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
