# Phase 1 analyses — draft feature spec

**Status:** draft, to be split and finished with the plots that use it: SPT with P02–P03 (M3), classification and grain size with P04–P06 (M4).
**Parent:** SPEC §4. The cross-cutting analysis decisions are there. This file holds the detail. Depth conventions are in SPEC §8.

---

## 1. SPT (used by P02, P03)
- **N:** as reported (`spt_n`).
- **Refusal and partial penetration:** detected from a seating+test penetration below 450 mm, a test-drive penetration below 300 mm, or refusal patterns in the report string (e.g. `25/75 50/30`). Sets `spt_refusal=True`.
  - `spt_n_capped = min(N, spt_cap)`, `spt_cap = 100` (decided). No extrapolation by default; `refusal="extrapolate"` gives N = blows × 300 / penetration.
  - **Refusals are included by default as the cap value, with a note** (decided). `refusal="exclude"` drops them.
  - For fitting and characteristic values they are treated as censored (🔬 TODO #8).
- **N60** = N × ER/60. ER comes from the data (`energy_ratio`), else the `hammer_efficiency` setting. The default is **unset** (decided), so N60 is NULL until it is set.
- **Test depth:** middle of the test drive (decided), computed from the increment penetrations. Fallback when increments are missing: 🟡 `top + 300 mm`, adjusted for short total penetration (SPEC §8.2).
- **Qualitative classes** (decided structure; values to confirm, 🔬 TODO #4). Tables live in the config, classify on `spt_n60` by default, and use a lower-bound-inclusive convention (to confirm).
  - **Cohesionless** (Terzaghi & Peck 1948 / Peck, Hanson & Thornburn 1974): very loose 0–4, loose 4–10, medium dense 10–30, dense 30–50, very dense > 50.
  - **Cohesive** (Terzaghi & Peck 1948): very soft < 2, soft 2–4, medium stiff 4–8, stiff 8–15, very stiff 15–30, hard > 30.
  - Two histograms (decided). The user decides what is cohesive, via `soil_class` or by passing their own filtered data. 🔬 `soil_class` categories: TODO #3.

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
