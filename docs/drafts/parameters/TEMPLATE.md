# NN — <Parameter name>

Outline of a parameter's site page (`docs/site/parameters/NN-*.md`), followed by the checklist each function's
docstring covers. The page explains the parameter and compares the methods; the docstring holds each method's
equation, inputs, validity and source, once, and the page links to it in the API reference instead of restating
it. Pages follow the docs-site rules (CLAUDE.md, "Docs site").

---

| | |
|---|---|
| **Parameters** | <symbol (name)>, … |
| **Material** | Soil / Rock / Both |
| **Models that use it** | <Mohr–Coulomb, Hardening Soil, generalized Hoek–Brown, …> |
| **Depends on** | <links to the pages it takes inputs from> |
| **Feeds** | <links to the pages that use it> |

## What it is
<The behavior the parameter describes and what controls it: drainage, stress level, stress history, scale,
anisotropy, rate. Equations only where they define the parameter.>

## Why it matters to a design
<How it enters each kind of analysis (foundations, slopes, retaining structures, tunnels, numerical models) and
how sensitive the result is to it. By analysis type, not one project's.>

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|

## Typical values

| Material | Range | Source |
|---|---|---|

<Values with their citation. A source table or chart is not reproduced whole: give the values needed and the
locator.>

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| <Author (year), or "definition"> | <inputs> | <material, range> | <link to `ht.analysis.<name>` in the API reference> |

## How the methods compare
<Which method to prefer when, how far the estimates usually differ, which ones a measured value should overrule,
and how to combine them (stage D).>

## Variability
<Inherent COV by test and material, and the transformation error of each correlation, with sources.>

## Pitfalls
- <One line each. Once built, note how hangtu catches it: a QC rule id, a warning, or a docstring note.>

## References
<Full citations with DOI or URL.>

---

## Docstring checklist

Each function that derives or correlates the parameter covers, in its numpy docstring:

- **Equation**, in MathJax, with the symbols named.
- **Inputs**, as registry columns or arguments, with their units (SPEC §2.6). Constants stay in the source's units
  and are converted with pint.
- **Valid for:** the material and the range of the data behind it (region, test type, the variant of the input, such
  as N60 or (N1)60).
- **Scatter:** the stated error, R² or factor, if the source gives one.
- **Assumptions**, stated rather than claimed conservative.
- **Out of range:** NaN with a count, by reason; never clipped or extrapolated (SPEC §4).
- **Judgments taken**, with what each is keyed by and how it resolves (SPEC §4); none has a default.
- **Source**, with its locator (equation, table, page), verified in the wave's spec step.
