# 23 — Slake durability

| | |
|---|---|
| **Parameters** | Id1 (first-cycle slake durability index, %), Id2 (second-cycle index, %), fragment description (retained / passing) |
| **Material** | Rock (shale, mudstone, claystone, marl, weak or weathered rock) |
| **Constitutive models that use it** | None — behavior index, not a model input |
| **Depends on** | [02-index-properties](02-index-properties.md) (PI for Gamble's durability-plasticity chart) |
| **Feeds** | [16-gsi-and-disturbance](16-gsi-and-disturbance.md) (weathering / degradation context), [21-swelling-rock](21-swelling-rock.md) (screening of argillaceous rock) |

## 1. Phenomenon
Slaking is the breakdown of argillaceous rock on wetting and drying: air compression in pores, clay swelling and
loss of weak cementation reduce lumps to flakes, silt and clay. The slake durability test measures the dry mass
retained in a 2 mm mesh drum after rotating lumps in water and oven drying [1][2]. It is an index of resistance to
weakening and disintegration, used qualitatively and for classification [3]. The second cycle (Id2) is the usual
reporting value; Id1 is reported when Id2 is very low (AGS: "if SDI1 or SDI2 is between 0 % and 10 %"). Results
depend on lump shape, initial water content, slaking fluid chemistry and temperature, so it is a comparative index.

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| Id1, Id2 | % (dry mass retained / initial dry mass) | % | none |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Classes by Id2 (Franklin & Chandra type) | Very low 0–25; Low 25–50; Medium 50–75; High 75–90; Very high 90–95; Extremely high 95–100 | Franklin & Chandra (1972), as commonly cited [U] |
| Gamble (1971) classes, Id1 / Id2 | Very high > 99 / > 98; High 98–99 / 95–98; Medium high 95–98 / 85–95; Medium 85–95 / 60–85; Low 60–85 / 30–60; Very low < 60 / < 30 | [4] [U] (seen only in a lecture-slide reproduction) |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Slake durability (two-cycle) | D4644-16 (withdrawn 2025, no replacement; the 2016 edition used three drying and two wetting cycles) | ISRM SM 1979 [2]; no ISO / BS EN equivalent found | ASDI: ASDI_SDI1, ASDI_SDI2 (%), ASDI_SOLN (fluid, temperature), ASDI_INDR, ASDI_PADR, SPEC_PREP, ASDI_METH | Id1, Id2, fragment description |
| Rapid field identification of swelling / slaking rock (jar slake) | — | ISRM SM 1994 [5] | none (descriptive) | Qualitative slaking class |
| Plasticity of slaked material | D4318 | ISO 17892-12 | LLPL | PI for the durability-plasticity chart |

ASDI_METH example in the dictionary: "ISRM: Suggested method for determining slake durability index."

## 5. Derivations and correlations

### 5.1 Index definition — Franklin & Chandra (1972); ISRM (1979)
$$I_{d2} = \frac{C - D}{A - D}\times 100\,\%$$
- **Inputs:** A = initial dry mass of lumps + drum, C = dry mass retained after the 2nd cycle + drum, D = drum mass.
  Id1 uses the mass after the 1st cycle (B).
- **Procedure:** ten lumps of about 40–60 g (≈ 450–550 g total), 2 mm mesh drum, 20 rpm for 10 min per cycle,
  oven drying at 105 °C between cycles [2] [U].
- **Source:** [1] [V] citation; formula and procedure [U] (standard text not seen).

### 5.2 Durability-plasticity classification — Gamble (1971)
- Combines Id2 with plasticity index of the slaked material; Gamble considered Id2 the best single durability
  measure for most rocks [4] [U].
- **Source:** [4] [U].

No correlation from Id2 to a model parameter is recommended; Id2 is a behavior index _[Judgment — for PE review]_.

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| TBM / MTBM excavation in shale | Low Id2 indicates face and cutterhead-chamber degradation, fines generation, slurry thickening and clogging risk (with clay stickiness, cf. Thewes) | Qualitative; high consequence for slurry separation and MTBM jacking |
| Invert / exposed rock | Low Id2: invert softening under water and traffic, need for prompt mud slab / lining | Qualitative |
| Muck handling and disposal | Slaking muck becomes slurry; affects separation plant, haulage, re-use | Qualitative |
| Shafts and open cuts | Wall raveling on wetting-drying; protection needs | Qualitative |
| Swelling screening | Low durability flags argillaceous rock for swell testing (sheet 21) | Screening only |

**Typical variability:** no published COV located; repeat tests on one lithology commonly differ by several
percentage points at high Id2 and much more at low Id2 _[Judgment — for PE review]_. Report by layer; do not average
across lithologies.

## 7. Pitfalls and QA checks
- Not a model input: do not correlate Id2 to strength or stiffness for design.
- Check which index is reported (Id1 vs Id2) and the number of cycles (ASTM D4644-16 differs from older editions).
- Record initial water content and lump preparation (SPEC_PREP); air-dried vs as-received changes results.
- Record slaking fluid (ASDI_SOLN): distilled vs site water changes slaking of clay-rich rock.
- Fragment descriptions (ASDI_INDR, ASDI_PADR) are needed to separate "retained but softened" from durable rock.
- ASTM D4644 is withdrawn (2025): cite the edition actually used by the lab.

## References
[1] Franklin, J.A. & Chandra, R. (1972). The slake-durability test. Int. J. Rock Mech. Min. Sci. 9(3), 325–328. https://doi.org/10.1016/0148-9062(72)90001-0 — [V] citation (Crossref); content [U]
[2] ISRM (1979). Suggested methods for determining water content, porosity, density, absorption and related properties and swelling and slake-durability index properties. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 16(2), 143–156. https://doi.org/10.1016/0148-9062(79)91453-0 — [V] citation (Crossref, two parts 143–151 and 151–156); content [U]
[3] ASTM D4644-16. Standard Test Method for Slake Durability of Shales and Other Similar Weak Rocks (withdrawn 2025). https://store.astm.org/d4644-16.html — [V] status, scope 1.1, significance 5.1–5.2
[4] Gamble, J.C. (1971). Durability-plasticity classification of shales and other argillaceous rocks. PhD thesis, University of Illinois at Urbana-Champaign. — [U] (classes seen only in https://www.slideshare.net/slideshow/durability-test-for-rock-mass/65645913)
[5] ISRM (1994). Suggested methods for rapid field identification of swelling and slaking rocks. Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 31(5), 547–550. https://doi.org/10.1016/0148-9062(94)90156-2 — [V] citation (Crossref); content [U]
