# M13 (b2): SPT correlations for s_u, σ′p/OCR and K0

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Unit (b1) (`docs/work/m13b1-spt-framework.md`) built (N1)60,
hammer efficiency by hole, the correlations framework and two φ′ correlations. The rest of the first SPT set
splits in two:
- **(b2)**, this one: strength and stress history, the SPT correlations for s_u (sheet 05), σ′p and OCR (06) and
  K0 (07), stage C of each.
- **(b3)**: stiffness, E (sheet 08) and Vs (10).

**Goal:** from a project's SPT data, its σ′v and, where a correlation needs it, a plasticity index, an engineer
gets estimates of s_u, σ′p/OCR and K0 from published SPT correlations, each on b1's framework: named on its rows,
reading the one input it was derived with, NaN with a reason outside its range, and comparable on P01 and P07.

**Why:** SPT is often the only data in the clays of a US project, and these correlations are applied by hand with
little check of the N basis or the soil they were derived from. They are also the first correlations on the
framework that aren't for sands, so they test the parts b1 left untested: a lab input (PI) beside N, a target in
stress units that converts for display, a field-N correlation, and a correlation published as a range.

**SPEC and TODO touched:** §4 (correlations: chaining discouraged, soil-class mapping; judgments: PI by geology
unit), §10.3 (new registry columns), §12.4 (M13 in four units: a, b1, b2, b3); P01 (a value range at a depth);
TODO #20 (s_u, σ′p/OCR, K0 settled here; E and Vs in b3), #37 (soil types, settled here as an opt-in USCS map).

### Decided
1. **Chaining is discouraged, not prevented.** A correlation's inputs are meant to be test data, or values derived
   directly from them (N60, (N1)60, σ′v), not another correlation's estimate: the transformation errors compound
   and the result reads as more certain than it is. The engineer may still do it; hangtu warns and records it
   (review decision 1) and offers no shortcut for it. K0 from φ′ and OCR (Mayne & Kulhawy 1982) and SHANSEP s_u
   from OCR are W3 (stage B), on measured inputs.
2. **On b1's framework, unchanged where it holds:** one function per published correlation, named after its
   source; its entry in `config/correlations.yaml` with the drift test; the one input column by registry name,
   with no argument to choose another; NaN with `correlation_note` and one warning by reason; every entry in
   `attrs["correlations"]`; the P01 footnote by note. A correlation whose equation, constants or range can't be
   verified against its source is cut, not built (b1 Decision 11).
3. **Candidates** (sheets 05–07, analysis draft §4.2), to verify in the spec step:
   - **s_u:** Stroud (1974), s_u = f1 N60 with f1 by PI; Sowers (1979), lines of s_u against N for low, medium
     and high plasticity; Terzaghi & Peck (1967), consistency classes giving a q_u band for an N range, the first
     range output.
   - **σ′p and OCR:** Mayne & Kemper (1988), σ′p ≈ 0.58 N pa, on field N (Kulhawy & Mayne 1990, Fig. 3-18).
   - **K0:** Kulhawy et al. (1989), K0 ≈ 0.073 N60 / (σ′v/pa), for clays, with its large bias stated (b = 2.16,
     δ = 0.70 on the TC304 database).
4. **Wave spec step** (process.md, "Stages and waves"): promote sheets 05, 06 and 07 to `docs/site/parameters/`,
   verify the [U] citations they use and hand-calculate golden values, apply the publishing rule (TODO #30), and
   propose the new names against the registry.

### Out of scope
- E and Vs (b3), and sheets 08 and 10.
- Stage B of each parameter: lab and vane s_u, the oedometer σ′p fits, Jaky and Mayne & Kulhawy K0 from measured
  φ′ and OCR, SHANSEP (W2, W3).
- CPT and DMT correlations (later waves). Relative density (M14).
- Selection between estimates and measured values (stage D, M18), and the two-panel correlation profile (TODO
  #38).
- PI keyed by depth within a unit, and PI from the nearest Atterberg test (not a good rule: review decision 4).

### Decisions (intent review, 2026-10-23)
1. **Chaining warns.** When an input column holds estimates (its rows carry a `correlation_name`), the function
   runs, warns that the input is itself an estimate and names that correlation, and records it on the rows in a
   new column (proposed `correlation_input`), since `correlation_name` is overwritten and `attrs` are easily lost.
   Reason: the engineer decides; the record keeps the chain reviewable.
2. **Range outputs, as target-specific columns.** A correlation that gives a band writes `<target>_lower` and
   `<target>_upper` (registry columns, so units and labels work) beside `<target>`, which holds the central value
   or NaN. Generic `estimate_lower` / `estimate_upper` columns were rejected: they would have no quantity in the
   registry. Reason: Terzaghi & Peck's classes are bands, and a band shouldn't be drawn as a point.
3. **P01 draws a value range at a depth.** When `<value>_lower` and `<value>_upper` exist, a horizontal bar
   between them at the test's depth, with the marker where there is a central value. A P01 spec change in this
   unit. Reason: valuable on its own, for any value reported as a range.
4. **Soil-class map, opt in** (TODO #37, option c). Each entry keeps the source's words in `applies_to`; beside
   them, hangtu's proposed USCS groups, labeled as hangtu's reading of the source, which a project can override.
   An argument (proposed `soil="uscs_symbol"`) turns it on; then rows outside the groups get NaN with a new note
   ("not for this soil") and rows with no class "soil type unknown". Without it, b1's rule holds: pass the rows
   a correlation applies to. USCS only for now. Reason: the mapping is an interpretation, so it is visible,
   overridable and never applied unasked.
5. **PI by geology unit, as a judgment.** `plasticity_index` in the judgments file, keyed by geology unit, with no
   default. A small general function puts a keyed judgment on the rows (as `vertical_stress()` puts σ′v), recorded
   in `attrs["judgments"]`; Stroud then reads the `plasticity_index` column like any input. The explicit argument
   always wins. A helper shows each unit's PI from the project's Atterberg tests (median, count, range) to inform
   the judgment; it never fills one in. Nearest-test PI was rejected as a rule; PI by depth may come later.

6. **A PI column on the rows wins over the judgments file**, with a warning when both are present and differ; the
   explicit argument wins over both. Reason: data the engineer put on the rows is the more specific choice.
7. **USCS comes from a column the user supplies** on the rows (`uscs_symbol`). hangtu doesn't derive it from
   `soil_class` or the log's description, and doesn't take it by geology unit. Reason: lab USCS is on samples, not
   SPT rows, and a derived class would be hangtu's guess.
8. **A band with no central value draws as the bar alone.** No midpoint is drawn or stored. Reason: a midpoint the
   source doesn't give would be hangtu's invention.
9. **Statistics on ranges are M15's:** a band is an interval, not two values. Noted as a constraint for M15
   (`docs/drafts/phase3-stats.md`) at the close-out, not designed here.

### Open (for the spec step)
- **Field N.** Mayne & Kemper read `spt_n`, not N60. Confirm from the source, and whether a field-N correlation
  should warn when the data has an energy ratio, since N60 would then be known.
- **σ′p or OCR as the target.** One correlation gives both (OCR = σ′p / σ′v0): one target column with the other
  derived, or two.
- **Size.** The P01 range bar, the soil map and the PI judgment each add work beyond the correlations. If the plan
  runs past one sitting, the P01 range bar goes first as its own small unit.
