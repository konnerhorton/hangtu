# GRAG fractions: read reported gradings into the gradation datasets

## Intent

### Goal
A sample whose grading is reported only as fractions in `GRAG`, with no `GRAT` curve, gets its fractions in
`p.grain_size_summary()` and `p.index_properties()`, so it can be classified (`uscs_symbol`), counted in fines
statistics and drawn where fractions are enough (P17). The engineer says once which fraction system the lab reported
in; hangtu never assumes it.

### Why
- **A real file lost most of its gradation data.** A 4.2 file extracted from a geotechnical report had 658 `GRAG`
  rows (gravel, sand, silt, clay, fines) and no `GRAT`. `p.grain_size_summary()` was empty, and `fines_content` was
  blank on every row of `p.index_properties()`: no lab USCS symbol, no clay activity, no fines statistics. Reports
  that print a summary table instead of curves are common, so any extractor working from them gives files like this.
- **Today only QC reads the fractions** (the fractions-sum check). The registry maps `GRAG_UC` and `GRAG_CC` and
  nothing else in `GRAG`; no dataset reads it.

### What the dictionary says (read before deciding)
AGS 4.2 defines the `GRAG` headings by size, with ISO 14688 boundaries:

| Heading | 4.2 description |
|---|---|
| `GRAG_VCRE` | Percentage of material tested greater than 63mm (cobbles) |
| `GRAG_GRAV` | … in range 63mm to 2mm (gravel) |
| `GRAG_SAND` | … in range 2mm to 63um (sand) |
| `GRAG_SILT` | … in range 63um to 2um (silt) |
| `GRAG_CLAY` | … less than 2um (clay) |
| `GRAG_FINE` | Percentage less than 63um |
| `GRAG_METH` | Test method |

But a lab reporting by ASTM D2487 (fines < 0.075 mm, gravel above 4.75 mm) puts its numbers in the same headings, and
`GRAG_METH` names the test (ASTM D6913, ISO 17892-4), which doesn't fix the reporting boundaries. Reading such a file as
ISO would put ASTM fines in an ISO column and give a wrong USCS symbol with no error. So the headings name a fraction,
and only the user can say what sizes it has (SPEC §2.6: never guess).

### Constraints
- **The system is stated, else no fractions** (intent review, decision 1). Without it, `GRAG`-only samples keep their
  rows with blank fractions, and one warning per call counts them and says how to state the system. The warning
  says that AGS defines the headings with ISO 14688 boundaries and that many labs report by ASTM in them.
- **Fractions are never converted between systems.** A fraction a system doesn't have, or that `GRAG` doesn't split
  finely enough, is blank. In particular `index_properties()` returns `astm_uscs` fractions, so `GRAG` reported by ISO
  14688 can't fill `fines_content` there (63 µm isn't 75 µm), though its clay can feed `clay_activity`.
- **No D-values without a curve.** `d10`, `d30` and `d60` stay blank; `uniformity_coefficient` and
  `curvature_coefficient` come from `GRAG_UC` and `GRAG_CC` where given.
- **A curve wins.** Where a specimen has `GRAT` points, everything comes from the curve as today, and `GRAG` isn't read
  for that specimen. Each row says which it came from.
- Never drop data silently; registry names only (SPEC §10.3); datasets don't stop on the file's data (`docs/data/datasets.md`
  §6.5).

### Out of scope
- The LDEN unit weight item from the same file (a user-defined heading); its own unit, once decided.
- A QC rule comparing `GRAG` with the curve on specimens that have both (to `docs/TODO.md`, with a trigger).
- Splitting `GRAG_VCRE` into cobbles and boulders, except where it is 0.
- The user's own fraction systems for `GRAG` (no rule says which heading fills which of their fractions).

### SPEC sections touched
- SPEC §2.6 (never guess), §4 (classification systems selectable; a setting, not a judgment, decision 4),
  §10.2–10.3 (datasets, registry).
- `docs/analysis/index-and-spt.md` §3.5 (fraction systems: how `GRAG` headings map to each system's fractions).
- `docs/data/datasets.md` §6.5 and §6.6 (rows from `GRAG`; the source column).
- `src/hangtu/columns.yaml` (the `GRAG` sources of the fraction columns; the new source column).

### Decisions (intent review, 2026-11-14)
1. **The fraction system of `GRAG` is stated by the user, else the fractions are left out with a warning.** Neither the
   AGS definition (ISO 14688) nor `GRAG_METH` is taken as the system: US labs often report ASTM fractions in ISO-defined
   headings, and a test method doesn't fix reporting boundaries.
2. **Two units.** This unit is the `GRAG` fractions only; the LDEN unit weight waits for its own decision (a heading map,
   possibly part of M16, or the extractor writing `LDEN_BDEN`).
3. **Which heading fills which fraction:**

   | System | From `GRAG` | Blank |
   |---|---|---|
   | `astm_uscs` | fines ← `GRAG_FINE` (else `GRAG_SILT` + `GRAG_CLAY`); sand ← `GRAG_SAND`; gravel ← `GRAG_GRAV`; cobbles and boulders ← 0 where `GRAG_VCRE` = 0 | cobbles and boulders where `GRAG_VCRE` > 0 |
   | `iso14688` | clay, silt, sand, gravel ← the heading of that name; cobbles and boulders as above | silt where only `GRAG_FINE` is given |
   | `aashto` | silt_clay ← fines as above; gravel ← `GRAG_GRAV`; boulders ← `GRAG_VCRE` | fine_sand, coarse_sand (`GRAG` doesn't split sand at 0.425 mm) |

   So from `aashto` `GRAG` the AASHTO group is blank wherever it needs the sand split; it is filled only where
   `aashto()` can decide on silt_clay and the limits alone (A-4 to A-7), if it can do that today.
4. **The system is a project setting,** `p.settings.grag_fraction_system = "astm_uscs"`, stored with the project like
   `vertical_datum`, so every dataset call reads it. There is no per-call argument: one file's `GRAG` was reported one
   way, and a setting keeps every dataset of the project consistent. A setting rather than a judgment: it is a fact
   about how the data was reported (like hammer efficiency, `docs/analysis/judgments.md` §5.10), not a choice of value.
5. **A source column**, `grading_source` (`"curve"` or `"reported"`), on `grain_size_summary()` and
   `index_properties()`, so the engineer can tell rows without D-values apart and filter on them. Checked against the
   registry in the spec step.
6. **`grain_size_summary()` gains one row per `GRAG` specimen with no `GRAT` points**, in file order after the
   curves, with the same columns; `p.grain_size()` (curve points) is unchanged. Its `fractions=` must match the
   `GRAG` system for those rows to be filled; otherwise they are blank and the warning says why.
7. **Test files:** a `GRAG`-only specimen (and one with both `GRAG` and `GRAT`) in the example site file through
   `_make_examples.py`, with invented values, and its US twin.
