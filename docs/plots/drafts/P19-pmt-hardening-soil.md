# P19 — Pressuremeter moduli to Hardening Soil stiffness (draft notes)

| | |
|---|---|
| **ID / function** | P19 · `ht.analysis.pressuremeter_stiffness()`; drawn with `ht.plot.profile()` (P01) or P20 |
| **Status** | idea (draft notes) |
| **Type** | analysis + profile plot |
| **Milestone** | M23 (wave 5) |
| **Depends on** | P01; P20 for multi-source comparison |
| **Related** | P20 (modulus from multiple sources), P23 (uses p0) |

---

## 1. Purpose
Converts Ménard pressuremeter results (E_M, p_L, p0) into the stiffness a Hardening Soil model needs (E_oed, E50) and plots it against elevation. Answers: what stiffness profile do the PMTs support for numerical modeling, and how sensitive is it to the choice of Ménard's α.

The figure is E50 against elevation, one point per test and α method, filtered to one area or structure by the user.

The roadmap's P19 also includes the pressuremeter curve itself; this draft covers only the derived moduli.

## 2. Reference figure
```
          E50 (kPa)
       0    50k   100k  150k
  150 ┼─────┼─────┼─────┤
      │  ●  ○              ● α from table
 Elev │     ● ○            ○ α from equation
 (m)  │        ●   ○
  120 ┤      ●  ○
      │           ●    ○
   90 ┼─────────────────┘
```

## 3. Input data
**Row grain:** one row per pressuremeter test.

| Column (proposed) | Description | Quantity kind | Unit | Req.? |
|---|---|---|---|---|
| `pmt_modulus` | Ménard modulus E_M | stress | kPa | ✔ |
| `pmt_limit_pressure` | Limit pressure p_L | stress | kPa | ✔ |
| `pmt_contact_pressure` | Contact pressure p0 (start of the pseudo-elastic phase; ≈ in-situ total horizontal stress) | stress | kPa | ✔ for the equation method |
| `uscs_symbol` | USCS group symbol | text | | ✔ for the table method |
| `depth` / `elevation`, `loca_id`, `geology_unit` | | | | ✔ one of depth/elevation |

All proposed names need the registry check. `pmt_` follows the "prefix test-specific quantities" rule (`spt_n`).

## 4. Analysis / calculations
- **Function:** `ht.analysis.pressuremeter_stiffness(df, *, alpha="table" | "equation" | float) -> DataFrame` adding the columns below.
- **α from Ménard's table** (rheological factor, by soil type and E_M/p_L). Soil type from USCS: CL/CH → clay, ML/MH → silt, SM/SP → sand, any G → sand and gravel. Ménard's values (to verify against Briaud 1992):

  | Soil | Overconsolidated | Normally consolidated | Weathered / remolded |
  |---|---|---|---|
  | Peat | — | α = 1 (any E/p_L) | — |
  | Clay | E/p_L > 16: 1 | 9–16: 2/3 | 7–9: 1/2 |
  | Silt | > 14: 2/3 | 8–14: 1/2 | 1/2 |
  | Sand | > 12: 1/2 | 7–12: 1/3 | 1/3 |
  | Sand and gravel | > 10: 1/3 | 6–10: 1/4 | 1/4 |

- **α from an equation** (source to find, §14): α = (E_M/p_L)^(1/n) / [k_E (p_L/p0)^(m/n)], with n = 2, m = 0.5, k_E = 3.5.
- **Moduli:** E_oed = E_M / α; E50 = E_oed / 1.15 (source to find, §14).
- **Result columns** (proposed): `pmt_rheological_factor`, `oedometer_modulus`, `secant_modulus_50` — names to check.
- **These are stress-level values**, at the test's in-situ stress, **not** the Hardening Soil reference values E50_ref at p_ref. Converting needs m and the stress state; out of scope here, stated in the docstring.

## 5. Figure layout
P01 profile (`profile` size), one point per test and method; or P20 when other sources are added.

## 6. Axes
P01 with a modulus preset: x `Secant stiffness, E50 (kPa)` (ksf/psi in US), linear from 0; y elevation.

## 7. Data marks
P01 marks; `marker_by="method"` distinguishes table and equation, so color stays with geology unit.

## 8. Overlays and annotations
P01 overlays.

## 9. Units behavior
All moduli and pressures convert together; α is dimensionless.

## 10. API
```python
pmt = ht.analysis.pressuremeter_stiffness(pmt, alpha="table")
fig, ax = ht.plot.profile(pmt, value="secant_modulus_50", marker_by="method")
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| USCS symbol doesn't map to a soil type | α NaN; counted; message lists the symbols |
| E/p_L outside every table row | α NaN; counted |
| p0 ≤ 0 or missing (equation) | NaN; counted |

## 12. Acceptance criteria and tests
- Golden (equation): E_M = 20 MPa, p_L = 2 MPa, p0 = 0.5 MPa → (10)^0.5 = 3.162; (4)^0.25 = 1.414; α = 3.162 / (3.5 × 1.414) = 0.639; E_oed = 31.3 MPa; E50 = 27.2 MPa.
- Golden (table): clay, E/p_L = 10 → α = 2/3.

## 13. References
- Ménard, L. (1975). The Ménard pressuremeter: interpretation and application of pressuremeter test results to foundation design. *Sols-Soils* 26.
- Briaud, J.-L. (1992). *The Pressuremeter*. Balkema.
- Schanz, T., Vermeer, P.A. & Bonnier, P.G. (1999). The hardening soil model: formulation and verification. *Beyond 2000 in Computational Geotechnics*, Balkema.

## 14. Open questions
- Source of the α equation and of E50 = E_oed / 1.15. Without a citation they shouldn't ship as built-ins; they could be a user `alpha=` callable.
- Is mapping soil type from USCS acceptable, or should the user supply the soil type per unit?

**Pitfalls:**
- Leaving out Ménard's weathered rows for silt, sand and gravel, or starting the normally consolidated rows at E/p_L = 0, so every low ratio gets an NC α.
- Returning None silently when no row matches.
- Calling the result E50_ref.

## 15. Future enhancements
- The pressuremeter curve with E_M and unload–reload moduli (the rest of P19).
