# Parameter reference sheets

**Status:** drafts, not decisions. One sheet per ground parameter, from the test data to the values a
constitutive model takes. Each wave's spec step promotes the sheets it covers to site pages
(`docs/site/parameters/NN-*.md`, from [`TEMPLATE.md`](TEMPLATE.md)), after checking their sources and what can be
published. Until then nothing here overrides `SPEC.md` or a feature spec. The roadmap is in SPEC §1.3 and §12.4.

## Conventions
- **Citation tags:** **[V]** = checked against the source (or an authoritative copy of it), with the locator
  (equation, table, page); **[U]** = not verified, to check before use. A wave's spec step verifies the [U] tags
  it relies on and hand-calculates golden values from the verified source.
- **AGS headings** are checked against the AGS 4.2 standard dictionary.
- **Judgments** are tagged _[Judgment — for review]_. Nothing here is a design value.
- **Unit conversions** are computed, not typed from memory.
- **What is reproduced:** values with their citation, and short sets of class boundaries as commonly cited. A
  source table or chart is not reproduced whole: the sheet gives the values it needs and the locator (TODO #30, settled in M13: `docs/work/m13a-judgments.md` Decision 9).
- **The sheets keep their draft structure** (§1–7 and references) until they are promoted; the promoted page
  follows the template, and each method's equation and source move into its function's docstring.

## Stages
Every parameter climbs four stages (SPEC §1.3): **A** data (a dataset in registry columns, QC from the pitfalls),
**B** direct derivation (definitions and fits on the test results), **C** correlations (SPEC §4), **D** selection
(sources compared, statistics, characteristic values or design lines, the model set).

## Index and status
Each stage cell gives the wave (W0–W6) or milestone that builds it, and **built** or **part built** once it is.
"—" means the stage doesn't apply or isn't planned yet. Each wave's close-out updates this table.

| # | Sheet | Parameters | A | B | C | D |
|---|---|---|---|---|---|---|
| 01 | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) | γ, γsat, σv0, u0, σ′v0 | **built** (`p.density()`, lab and field: M14 a) | **built** (σv0, u0, σ′v0: M13; γd and γsat from phase relations: M14 b) | — | M18 |
| 02 | [Index properties](02-index-properties.md) | w, LL, PL, PI, LI, Ic, activity, fines | **built** (M7, M8) | **built** (PI, LI, Ic, classes, with LI and Ic as analyses: M8; activity: M14 b) | — | M18 |
| 03 | [Specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) | Gs, e0, n | **part built** (ρs: `p.particle_density()`, M14 a); W2, W3 (specimen e0), W4 (rock n) | **built** (Gs, e0, n, S: `ht.analysis.phase_relations()`, M14 b) | — | M18 |
| 04 | [Drained shear strength of soil](04-drained-shear-strength-soil.md) | φ′, c′ | **part built** (triaxial: `p.triaxial()`, M11 a); M17 (shear box) | **part built** (triaxial: `mohr_coulomb_fit()`, M11 b); M17 (shear box) | **part built** (SPT φ′: M13 b1); W1 (others) | M18 |
| 05 | [Undrained shear strength](05-undrained-shear-strength.md) | su, su,r, St | W2 | W2; W3 (SHANSEP) | **part built** (SPT: M13 b2); later (CPT) | M18 |
| 06 | [Preconsolidation and compressibility](06-preconsolidation-and-compressibility.md) | σ′p, OCR, Cc, Cs/Cr | W3 | W3 | **part built** (SPT: M13 b2); later (CPT) | W3 |
| 07 | [At-rest earth pressure (soil)](07-at-rest-earth-pressure.md) | K0 | — | W3 | **part built** (SPT: M13 b2); later (CPT, DMT) | W3 |
| 08 | [Elastic stiffness of soil](08-elastic-stiffness-soil.md) | E, ν | W5 | W5 | **part built** (SPT: M13 b3); W5 (others) | W5 |
| 09 | [Dilatancy](09-dilatancy.md) | ψ (soil and rock mass) | — | W4 (rock), W5 (soil) | — | W4, W5 |
| 10 | [Small-strain stiffness](10-small-strain-stiffness.md) | Vs, G0, G0ref, γ0.7 | W5 | W5 | **part built** (SPT Vs: M13 b3); W5 (others) | W5 |
| 11 | [Hardening Soil stiffness](11-hardening-soil-stiffness.md) | Eoed, Eur,oed, E50ref, Eoedref, Eurref, m, pref, Rf, νur | W3 | W3 (Eoed, Eur,oed); W5 (full set) | W5 | W5 |
| 12 | [Hydraulic conductivity](12-hydraulic-conductivity.md) | k (soil, rock mass) | **part built** (`p.permeability()`); W6 | W3 (cv·mv); W6 | W6 | W6 |
| 13 | [Intact rock strength](13-intact-rock-strength.md) | σci, σt, Is50 | W4 | W4 | — | W4 |
| 14 | [Intact rock deformability](14-intact-rock-deformability.md) | Ei, νi | W4 | W4 | — | W4 |
| 15 | [Hoek–Brown constant mi](15-hoek-brown-mi.md) | mi | W2 | W2 (fit) | W4 | W4 |
| 16 | [GSI and disturbance](16-gsi-and-disturbance.md) | GSI, D, RQD, JCond89 | W4 (RQD) | W4 | — | W4 |
| 17 | [Rock mass strength](17-rock-mass-strength.md) | mb, s, a, σcm, σt,mass, equivalent c′, φ′ | — | W4 | — | W4 |
| 18 | [Rock mass modulus](18-rock-mass-modulus.md) | Em | — | W4 | — | W4 |
| 19 | [Post-peak (residual) rock mass](19-post-peak-rock-mass.md) | GSIr, mr, sr, ar | — | W4 | — | W4 |
| 20 | [In situ stress in rock](20-in-situ-stress-rock.md) | σH, σh, kH, kh | — | W4 | — | W4 |
| 21 | [Swelling of rock](21-swelling-rock.md) | free swell, swell pressure, Grob kq, σ0 | W3 | W3 | — | W3 |
| 22 | [Discontinuity shear strength](22-discontinuity-shear-strength.md) | φj, cj | W2 | W2 | — | M18 |
| 23 | [Slake durability](23-slake-durability.md) | Id1, Id2 | W4 | W4 | — | W4 |

Curves (triaxial stress–strain, rock triaxial, swelling against time, shear box displacement) come from the AGS
file with wave 0, after wave 2; wave 2 reads them from a CSV (SPEC §1.3). Stage D for the sheets whose derivations land in waves 1–2 is the selection milestone (M18); each
later wave builds stage D for its own sheets.
