# M13 (b1): (N1)60, hammer efficiency by hole and the correlations framework

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Unit (a) (`docs/work/m13a-judgments.md`) built the judgments
file, `p.stratigraphy()` and `vertical_stress()`. Unit (b) is split in two:
- **(b1)**, this one: the overburden correction and (N1)60, hammer efficiency by hole, the correlations framework,
  and the first correlations on it, φ′ from SPT (stage C of sheet 04).
- **(b2)**: the rest of the first SPT set on the same framework: s_u (sheet 05), σ′p/OCR (06), K0 (07), E (08) and
  Vs (10).

**Goal:** from a project's SPT data, its stratigraphy and its judgments, an engineer gets (N1)60 and estimates of φ′
from published SPT correlations. Each estimate names its correlation, states the N it was derived with and its
range, and returns NaN with a count where it doesn't apply, so several estimates compare on P01 (`color_by=`) or
P07.

**Why:** SPT is often the only strength data on a US project, and these correlations are what engineers apply to it
by hand, often without checking the N basis (field N, N60 or (N1)60) or the range. The framework is built and
reviewed once, on one parameter, before b2 adds five more.

**SPEC and TODO touched:** §4 (correlations; hammer efficiency by hole), §10.3 (new registry columns), §12.4 (M13
splits into a, b1, b2); TODO #20 (the φ′ part settled here; the rest in b2). `docs/drafts/analysis.md` §4 is
finished as this unit's spec (§4.1 "which C_N" is settled here).

### Decided
1. **(N1)60 = N60 × C_N**, from the σ′v column `vertical_stress()` returns. **C_N is chosen with `method=`**:
   Liao & Whitman (1986) and Kayen et al. (1992) to start, each with the cap its source gives (for Liao & Whitman,
   1.7 per Youd et al. 2001, to verify). The method and cap are recorded in `df.attrs`. A blank N60 or σ′v leaves
   (N1)60 blank, with a count.
2. **Rod-length, borehole-diameter and sampler corrections (C_R, C_B, C_S) are out of scope.** The docstring says
   they aren't applied. They come back when AGS rod and sampler data are read.
3. **Hammer efficiency by hole** (unit (a), Decision 8; SPEC §4): `hammer_efficiency=` also takes values by hole
   (`{"BH01": 80}`). `ISPT_ERAT` (`energy_ratio`) is still used first. When the argument or
   `ht.settings.hammer_efficiency` fills blanks, a warning names the holes. Applies to `ht.analysis.spt()`,
   `p.spt()` and the plots that take `hammer_efficiency=` (P02, P03).
4. **The correlations framework** follows SPEC §4 and analysis draft §4: `ht.analysis.correlations`, one function
   per published correlation, named after its source; metadata in one config file (proposed
   `config/correlations.yaml`) feeding the docstring checklist, `df.attrs` and plot footnotes; an explicit input
   (a column that doesn't match the correlation's N basis is an error, never a silent correction); NaN with a count
   by reason outside the range; long-format output with a column naming the correlation; correlations that give a
   range return lower and upper values. It is built general enough for b2's correlations, which take PI, a soil
   type or σ′v besides N.
5. **φ′ correlations** (sheet 04): Wolff (1989) fit to Peck, Hanson & Thornburn (1974); Kulhawy & Mayne (1990),
   after Schmertmann; Hatanaka & Uchida (1996). A correlation whose equation, constants or range can't be verified
   against its source is cut, not built.
6. **Wave spec step** (process.md, "Stages and waves"): promote sheet 04 to `docs/site/parameters/`, verify the
   [U] citations the φ′ correlations and C_N use and hand-calculate golden values from them, apply the publishing
   rule (TODO #30), and propose the new names against the registry.

### Out of scope
- b2's correlations (s_u, σ′p/OCR, K0, E, Vs) and sheets 05–08 and 10.
- C_R, C_B, C_S (Decision 2); the mid-drive test depth (analysis draft §1.2, Phase 2).
- Correlations from other inputs (PI, CPT qt, Is50): the framework allows them, M14 and later waves build them.
- Relative density (Skempton 1986; Meyerhof 1957): sheet 03 is M14's.
- New plots. Comparison is P01 and P07 as they are.
- Liquefaction triggering, and selection between estimates (stage D, M18).

### Open
- **Names** (to check against `columns.yaml` in the spec step): `spt_n1_60`, the C_N column
  (`spt_overburden_correction`?), the column naming the correlation (`correlation`?; `method` is taken), and the
  lower/upper columns for range outputs.
- **Soil type.** The φ′ correlations apply to sands. Whether a correlation reads `soil_class` / `uscs_symbol` from
  the row and returns NaN with a count for other soils, or the user filters the rows as `spt_class()` does
  (analysis draft §1.4, "which table is the user's call"). Decided here, since b2's correlations depend on it more.
- **Kulhawy & Mayne's N basis:** EPRI uses field N, practice (GEC 5) uses N60. Settle from the source in the spec
  step.
- **Hammer efficiency by hole as a DataFrame** (`loca_id, hammer_efficiency`) as well as a dict, to match how
  `water_level=` takes per-hole values.
