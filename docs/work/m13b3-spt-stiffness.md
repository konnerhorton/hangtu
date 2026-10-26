# M13 (b3): Young's modulus and shear wave velocity from SPT

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). Units (a), (b1) and (b2) built the judgments file and σ′v,
(N1)60 and the correlations framework, and the SPT correlations for φ′, s_u, σ′p/OCR and K0. This unit, (b3), is
the last of M13: stiffness, stage C of E (sheet 08) and Vs (sheet 10).

**Goal:** from a project's SPT data and its σ′v, an engineer gets estimates of Young's modulus and shear wave
velocity from published SPT correlations, on the framework as b1 and b2 left it: named on their rows, reading the
one input each was derived with, NaN with a reason outside its range, and comparable on P01 and P07.

**Why:** E from N is one of the most used and most misused SPT correlations in US practice. Its coefficients are
picked from a table by a soil description, and its unit is easy to misread: FHWA NHI-06-088 Table 5-16 gives
E = 4, 7, 10, 12 × (N1)60 in **tsf**, and the same factors read as **ksf** halve E (sheet 08 §2). Vs from N is the usual fallback for a site class or a G0 when no seismic
test was run. Both test parts of the framework the earlier units didn't:
- **a coefficient chosen by soil type** from the source's own wording, not a soil-type check on a single
  equation (b2's USCS map only says yes or no);
- **a target whose meaning depends on strain level.** E from N is a working-strain secant modulus; Vs gives a
  small-strain stiffness one to two orders of magnitude higher. An estimate that doesn't say which it is invites
  the classic mistake of using G0 as a design E (sheet 08 §7);
- constants in US customary units (tsf), converted with pint, where a golden value catches the unit trap.

**SPEC and TODO touched:** §4 (correlations: a coefficient by soil type), §10.3 (new registry columns), §12.4
(M13 done); TODO #20 (E and Vs settled here, closing it), #40 (deferred to M15), #41 (the warning's wording).

### Decided
1. **On the framework as b1 and b2 left it:** one function per published correlation, named target first
   (`<target>_<authors>_<year>`, SPEC §4); its entry in `config/correlations.yaml`; the one input column by
   registry name; NaN with `correlation_note`; bands as `<target>_lower`/`_upper` where the source gives one;
   chaining warns; the opt-in USCS map. A correlation whose equation, constants, N basis or range can't be
   verified against its source is cut, not built.
2. **Candidates** (sheets 08 and 10, analysis draft §4.2), to verify in the spec step:
   - **E:** AASHTO (2004) via FHWA NHI-06-088 Table 5-16, E = C (N1)60 tsf with C = 4, 7, 10, 12 by soil
     description (sheet 08 §5.1, [V] via an extract; ksi form in GEC 5 Table 8-11); Kulhawy & Mayne (1990),
     E/pa by N60 by soil type (analysis draft §4.2, [U]: not yet read in EPRI EL-6800).
   - **Vs:** Imai & Tonouchi (1982) and Ohta & Goto (1978), as given in GEC 5 Table 8-5 (sheet 10 §5.7, [V] for
     the GEC 5 form). The N basis needs checking: GEC 5 writes N60, while the original Japanese data are at the
     energy of their own hammers.
3. **Wave spec step** (process.md, "Stages and waves"): promote sheets 08 and 10 to `docs/site/parameters/`,
   publishing only [V] content and listing the methods not built here by wave (W2, W3, W5), verify the [U]
   citations the built correlations use and hand-calculate golden values, apply the publishing rule (TODO #30),
   and propose the new names against the registry.

### Out of scope
- G0 from Vs (G0 = ρVs²), E0 and the strain reduction E/E0 (sheet 08 §5.3), and γ0.7: stage B, W5. A G0 from a
  correlated Vs would also be chaining.
- E from s_u (Duncan & Buchignani 1976, [U]), from CPT, DMT, pressuremeter or the lab; ν; the Hardening Soil
  moduli (sheet 11).
- Vs from CPT, and site class (Vs30, ASCE 7).
- Relative density (M14); selection between estimates (M18).

### Decisions (intent review, 2026-10-26)
1. **Soil type for a coefficient: a required argument, with the USCS map on top.** A correlation whose
   coefficient depends on soil type takes a required argument naming the source's row (proposed `soil=`), with no
   default, like a judgment. With the existing `uscs=` opt-in, the row can come from `uscs_symbol` through
   hangtu's proposed map instead. One function per row was rejected: it multiplies functions for one
   correlation. Reason: the row is the engineer's reading of the log, so it is stated in the call, or read
   through a map that is visible and overridable (b2 review 4).
2. **The target is named in the correlation's own terms.** The column says what the source says the estimate
   is: for the SPT E correlations, a drained modulus (`drained_youngs_modulus`, to check against the registry),
   with the strain level and loading the source implies stated in the entry's `notes` and docstring. Reason: E
   without "drained" or a strain level is the ambiguity this unit exists to avoid, and W2 and W5 will add Eu,
   E50, Eur and E0 beside it.
3. **TODO #40 (correlation statistics) is deferred to M15**, where statistics are designed against their uses
   (comparison, characteristic values). b3 keeps scatter in `describe()` and the docstring, as b1 and b2 do.
4. **TODO #41's warning wording is done here**, in its own commit: the warning states the range only when some
   rows are outside it, and in the user's terms (e.g. field N over σ′v0/pa, not `normalized_n`). Its other
   question (gravelly sands under `not_for`, read from the group name or gradation) stays open unless the spec
   step finds b3 needs it.

### Open (for the spec step)
- **N basis of the Vs correlations.** GEC 5 Table 8-5 writes N60; check against the originals or a cited 60 %
  form (SPEC §4), and cut what can't be verified.
- **Kulhawy & Mayne (1990) E.** Read it in EPRI EL-6800: its equation, N basis, soil rows and whether its rows
  match AASHTO's, so both take the same `soil=` vocabulary or each its own.
