# Phase 2 (data) — draft notes

**Status:** working notes, not a spec. **Parent:** SPEC §6, §7, §9 and §10, which hold the decided constraints.
**Use:** input for the Phase 2 intents (ingest, QC and the M7 datasets are specified in `docs/data/ingest.md`, `qc.md` and `datasets.md`; the M8 datasets are still here). Each intent's spec takes what it needs from here, and the decisions that end up applying to all of Phase 2 go back into `SPEC.md`.
Decisions marked **(decided)** were agreed in review. Everything else is a draft.

---

## Ingestion (SPEC §6)
Moved to [`docs/data/ingest.md`](../data/ingest.md) (M5). Research items still open, not blocking ingest:
- **pcf in AGS headings:** check real US files for unit weights put into AGS *density* headings (`RDEN_BDEN`, `PTST_BDEN`, dictionary unit Mg/m³), or the reverse. References: ASTM D7263, ASTM D2937, FHWA NHI-16-072.
- **SPT penetrations:** check whether US files fill `ISPT_PEN*` as 6-in increments (152.4 mm) or as nominal 150 mm values. They drive the mid-drive depth (SPEC §8.2), and are converted as lengths either way (P00 §4.3 #2).

---

## Data model (SPEC §7)

**Metadata tables:**
- `meta_project` (settings);
- `meta_source` (file, hash, versions);
- `meta_heading` (original and resolved units, quantity kind);
- `meta_value_flag`;
- `meta_geology_map`;
- `qc_validation`.

**Canonical layer** (decided): AGS 4.2-shaped tables in SI. The rules are in SPEC §7.

---

## Data quality (SPEC §9)
Moved to [`docs/data/qc.md`](../data/qc.md) (M6).

---

## Project access and datasets (SPEC §10)
Project access and the M7 datasets (`p.spt()`, `p.atterberg()`, `p.grain_size()`, `p.permeability()`) moved to [`docs/data/datasets.md`](../data/datasets.md). What's left waits for the M8 analyses:

| Method | Columns |
|---|---|
| `p.atterberg()` | adds plasticity_class_uscs, plasticity_class_bs5930 |
| `p.grain_size_summary()` | One row per specimen: d10, d30, d60, uniformity_coefficient, curvature_coefficient, fractions, gradation_uscs |
| `p.index_properties()` | One row per sample: Atterberg + water_content + PSD summary, uscs_symbol, aashto_group, aashto_group_index. Specimen combining rule: SPEC §13 #2 |
