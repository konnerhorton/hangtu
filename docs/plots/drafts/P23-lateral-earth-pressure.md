# P23 — In-situ horizontal stress and K0 with depth (draft notes)

| | |
|---|---|
| **ID / function** | P23 · `ht.plot.lateral_stress_profile()` (+ `ht.analysis.in_situ_stress()`) |
| **Status** | idea (draft notes) |
| **Type** | plot + analysis |
| **Milestone** | Later (roadmap) |
| **Depends on** | P01 |
| **Related** | P19 (same PMT data). Cross-cutting finding 4 (`water_unit_weight`) |

---

## 1. Purpose
Estimates the at-rest earth pressure coefficient K0 from pressuremeter contact pressures and plots it with the vertical and horizontal stress profiles. Answers: what K0 do the PMTs imply, how does it vary with depth, and how sensitive is it to the water table and unit weight assumed. Used for shaft, excavation and retaining-wall design.

The figure shows p0 per test with an optional linear trend; computed σv, u, σ′v and σ′h profiles; and K0, all against depth, for one area at a time. The water table and unit weight are inputs the user varies.

## 2. Reference figure
Two panels sharing depth:
```
     Stress (kPa)                         K0
     0   500  1000  1500             0   0.5   1.0   1.5
   0 ┼────┼────┼────┤              0 ┼────┼─────┼────┤
     │╲ σv ╲u        │                │      ●         │
  10 ┤ ╲   ●╲  σ′h   │             10 ┤   ●    ●       │
Depth│  ╲ ● ╲  ╱     │                │     ●──trend   │
 (m) │   ╲  ●╲╱      │                │       ●        │
  30 ┤  σ′v ●  ╲     │             30 ┤    ●           │
     └───────────────┘                └────────────────┘
```

## 3. Input data
**Row grain:** one row per PMT test.

| Column | Description | Unit | Req.? | Notes |
|---|---|---|---|---|
| `pmt_contact_pressure` (proposed, as P19) | p0 ≈ total horizontal stress σh0 | kPa | ✔ | |
| `depth` | Test depth | m | ✔ | Stresses need depth below ground |
| `loca_id` | Hole | | – | Color/marker |
| `geology_unit` | | | – | |
| `bulk_unit_weight` | Per-test γ, if known | kN/m³ | – | Otherwise `unit_weight=` |

**Arguments (not columns):** `groundwater_depth` (m), `unit_weight` (kN/m³, constant or a strata table with γ per layer), `water_unit_weight` (default from settings).

## 4. Analysis / calculations
- σv(z) = Σ γi Δzi (constant γ: γ z).
- u(z) = γw (z − zw) for z > zw, else 0 (hydrostatic).
- σ′v = σv − u.
- **Per test:** σ′h = p0 − u(z); **K0 = σ′h / σ′v**.
- **Trend (optional):** OLS of p0 on depth (p0 = b0 + b1 z), then σ′h and K0 lines from the trend.
- **Result:** per-test σv, u, σ′v, σ′h, K0; trend coefficients and R².

## 5. Figure layout
Two panels, shared depth axis: stresses (left), K0 (right). `profile` size per panel. A twin x-axis would put two unrelated scales over the same points and is hard to read.

## 6. Axes
| | Left X | Right X | Y |
|---|---|---|---|
| Quantity | stress | K0 | depth (down) |
| Label | `Stress (kPa)` | `At-rest coefficient, K0` | `Depth (m)` |
| Limits | 0 to nice max | 0 to nice max | 0 to nice max |

## 7. Data marks
| Series | Panel | Mark |
|---|---|---|
| p0 per test | left | scatter, color by `loca_id` or unit |
| σv, u, σ′v | left | lines, labeled at their ends |
| σ′h from trend | left | dashed line |
| K0 per test | right | scatter |
| K0 from trend | right | line |

## 8. Overlays and annotations
- Assumptions box (on): γ, zw, γw, trend equation and R².
- `reference_lines=` on the K0 panel, e.g. Jaky 1 − sin φ′ or an OCR-based K0.

## 9. Units behavior
Stresses convert (kPa ↔ psf/ksf); depth m ↔ ft; γ kN/m³ ↔ pcf; K0 dimensionless.

## 10. API
```python
fig, axs, result = ht.plot.lateral_stress_profile(
    pmt, groundwater_depth=5, unit_weight=21.0, trend=True,
)
```

## 11. Edge cases and data quality
| Situation | Behavior |
|---|---|
| σ′v ≤ 0 near surface | K0 undefined; counted |
| p0 < u (σ′h < 0) | Drawn; warning (suspect p0) |
| Fewer than 2 tests | No trend; points only |

## 12. Acceptance criteria and tests
- Golden: z = 10 m, γ = 21 kN/m³, zw = 5 m, γw = 9.81 → σv = 210, u = 49.05, σ′v = 160.95 kPa; p0 = 250 kPa → σ′h = 200.95, K0 = 1.249.

## 13. References
- Jaky, J. (1944). The coefficient of earth pressure at rest. *J. Soc. Hungarian Architects and Engineers*.
- Mayne, P.W. & Kulhawy, F.H. (1982). K0–OCR relationships in soil. *J. Geotech. Eng. Div.* 108(GT6).
- Briaud, J.-L. (1992). *The Pressuremeter*. Balkema (p0 as σh0).

## 14. Open questions
- Is p0 a reliable estimate of σh0 for the PMT type used (a pre-bored Ménard test disturbs the borehole wall)? The function should say what p0 represents and let the user pass σh0 directly.

**Pitfalls:**
- Regressing depth on p0 (x on y) and inverting it: with scattered data that's a different line. p0 is the dependent variable.
- Typing γw inline (10 in one place, 9.81 in another). Use the setting.
- Computing K0 only from the trend, which hides the per-test scatter.
- Fixed axis limits that cut off data.

## 15. Future enhancements
- K0 from other sources (DMT, hydraulic fracture, OCR correlations) on the same panel.
