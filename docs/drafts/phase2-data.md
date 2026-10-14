# Phase 2 (data) — draft notes

**Status:** working notes, not a spec. **Parent:** SPEC §6, §7, §9 and §10, which hold the decided constraints.
**Use:** input for the Phase 2 intents at M4 (ingest, QC, datasets). Each intent's spec takes what it needs from here, and the decisions that end up applying to all of Phase 2 go back into `SPEC.md`.
Decisions marked **(decided)** were agreed in review. Everything else is a draft.

---

## Ingestion (SPEC §6)

### Pipeline
```
AGS file
  → python-ags4: check_file()                    → validation findings (stored, never blocking)
  → python-ags4: AGS4_to_dataframe()             → {group: DataFrame of text}, plus UNIT/TYPE rows
  → raw layer writer                             → raw_<GROUP> tables (TEXT, exactly as in the file, + _line)
  → version mapping to AGS 4.2                   → older versions mapped up (e.g. IPRG → FGHG)
  → typing + unit conversion + value flags       → canonical layer (SI) + value flags   [AGS 4.2-shaped, SPEC §7]
  → metadata writer                              → meta_* tables
```

### Versions
- Version notes: `ISPT_N60`, `SPEC_BASE` and `GRAG_CC` exist only in 4.1+.
- Field permeability is `IPRG` (4.0.x) or `FGHG`/`FGHS` (4.1+).
- Re-ingest with `overwrite=True` (proposed). The file's SHA-256 is stored and checked on open.

### Type mapping
| AGS TYPE | Stored as | Notes |
|---|---|---|
| `ID`, `PA`, `PT`, `PU`, `X`, `RL`, `RECORD LINK` | TEXT | Except numeric-text headings listed in `heading_quantities.yaml` (e.g. `LNMC_MC` is type `X`) |
| `XN` | REAL + value flags | e.g. `LLPL_PL` ("38 or NP"), `ISPT_WAT` ("Dry"), `GRAG_PDEN` ("#2.65") |
| `nDP`, `nSF`, `nSCI`, `MC`, `U` | REAL | |
| `DT` / `T` / `YN` / `DMS` | ISO text / seconds / 0-1 / decimal degrees | |

### Value flags (decided)
- Flags: `NP`, `DRY`, `REFUSAL`, `LT`/`GT` (bound kept), `ASSUMED` (value kept).
- Unrecognized text → flag `OTHER` + QC `T001`.
- Datasets expose flags as columns (`non_plastic`, `water_dry`, `spt_refusal`, `qualifier`).

### Dependency notes
- `python-ags4` 1.2.0 requires `pandas >=2.1,<3`.
- SQLite `STRICT` tables need SQLite ≥ 3.37.

### Units on ingest
Phase 1 unit rules (quantity kinds, aliases, pcf, SPT N) are in `docs/plots/P00-framework.md` §4. These apply only to AGS files:
1. **"ton"** (decided): short ton in an imperial context, metric tonne in a metric context.
   - Explicit strings resolve directly (`tsf` → short ton; `t/m2` → tonne).
   - A bare `ton`/`t` follows the file's unit system, inferred from the length unit of `LOCA_GL`/`GEOL_TOP`.
   - Each resolution is recorded (QC `U002`).
2. **Mixed units in one file** are handled per column.
3. **Vertical datum:** AGS4 has **no field for the datum of `LOCA_GL`**. It is implied by `LOCA_GREF`; `LOCA_DATM` is the local datum for `LOCA_LOCZ` only. The datum label (e.g. NAVD88) is therefore a setting. One datum per project; multiple datums are a Later item.
4. **Project settings:** the same keys as the session settings (P00 §3), stored in the project database. `to_yaml()`/`load_yaml()` export and import them.
5. **pcf in AGS headings** (open): `pcf` is read by the heading's quantity kind (P00 §4.3 #1). Check real US files for unit weights put into AGS *density* headings (`RDEN_BDEN`, `PTST_BDEN`, dictionary unit Mg/m³), or the reverse. References: ASTM D7263, ASTM D2937, FHWA NHI-16-072.
6. **SPT penetrations** (open): check whether US files fill `ISPT_PEN*` as 6-in increments (152.4 mm) or as nominal 150 mm values. They drive the mid-drive depth (SPEC §8.2), and are converted as lengths either way (P00 §4.3 #2).

**Acceptance tests:**
- **twin-file test**: the same data in an SI AGS file and a US AGS file ingests to identical canonical tables;
- the synthetic files pass python-ags4 validation (except the defects file);
- every `U002` resolution is tested.

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

### Framework
- `qc = p.qc()` returns a report with a readable summary. `qc.findings` columns: `rule_id, severity, group, loca_id, depth, heading, value, message, source_line`.
- **Rules live in YAML** (id, description, severity, enabled, thresholds). The logic lives in `qc/rules.py`. Projects can override.
- **`p.diff(group)`:** raw vs canonical, cell by cell (`_line`, raw text, raw unit, SI value, display value, flag, what changed).

### Level 1 rules
Defaults agreed for now; deeper review is TODO #6.

| ID | Rule | Severity | Default threshold |
|---|---|---|---|
| V*** | AGS validation finding | per rule | — |
| U001 / U002 / U003 | Unknown unit / unit resolved by convention / numeric heading with no unit | error / info / warning | — |
| T001 | Unrecognized text in a numeric column | info | — |
| L001 / L002 / L003 | Missing ground level / coordinates / final depth | error / warning / warning | — |
| L004 | Non-vertical hole | warning | HORN_INCL differs from 90° by > 2° |
| L005 | Ground level is an outlier compared with nearby holes | warning | > 3 m (10 ft) from the median of 5 nearest holes within 200 m |
| L006 | Vertical datum not set | info | — |
| G001 / G002 / G003 / G004 | No geology / gap / overlap / unmapped code | error / warning / error / warning | gap/overlap > 0.01 m |
| D001–D006 | Backward interval, negative depth, deeper than final depth, outside geology, straddles a boundary, duplicate | error, error, warning, warning, info, warning | D003: > final depth + 0.1 m |
| S001–S005 | SPT unparsed refusal, improbable N, no energy ratio, N inconsistent with increments, file N60 differs | warning, warning, info, warning, warning | S002: N > 100; S005: > 1 blow |
| A001–A004 | LL < PL, PI ≠ LL − PL, improbable LL, NP | error, warning, warning, info | A002: > 1; A003: LL < 10 or > 150 |
| P001–P004 | PSD not monotonic, % outside 0–100, fractions ≠ 100%, too few points | error, error, warning, info | P001: 0.5%; P003: ±2% |
| K001 | Permeability ≤ 0 or outside 1e-12 to 1 m/s | warning | — |
| C001 | Missing minimally useful fields | warning/info | below |

### Minimally useful fields
- `qc/min_fields.yaml`, overridable per project (TODO #7).
- `required` missing → warning, and the record is excluded from datasets unless `include_incomplete=True`. `recommended` missing → info.
- `SPEC_REF`/`SPEC_DPTH` are required for now (decided).

```yaml
LOCA: {required: [LOCA_ID, LOCA_GL, LOCA_FDEP], recommended: [LOCA_TYPE, LOCA_NATE, LOCA_NATN, LOCA_GREF, LOCA_STAR]}
GEOL: {required: [LOCA_ID, GEOL_TOP, GEOL_BASE, GEOL_DESC], recommended: [GEOL_LEG, GEOL_GEOL]}
SAMP: {required: [LOCA_ID, SAMP_TOP, SAMP_TYPE], recommended: [SAMP_REF, SAMP_ID, SAMP_BASE]}
ISPT: {required: [LOCA_ID, ISPT_TOP, ISPT_NVAL],
       recommended: [ISPT_REP, ISPT_NPEN, ISPT_ERAT, ISPT_TYPE, ISPT_HAM, ISPT_WAT, ISPT_CAS, ISPT_INC1-6, ISPT_PEN1-6]}
LLPL: {required: [<SPEC_KEY>, LLPL_LL, LLPL_PL], recommended: [LLPL_PI, LLPL_425, LLPL_PREP]}
LNMC: {required: [<SPEC_KEY>, LNMC_MC]}
GRAG: {required: [<SPEC_KEY>], recommended: [GRAG_GRAV, GRAG_SAND, GRAG_SILT, GRAG_CLAY, GRAG_FINE, GRAG_UC]}
GRAT: {required: [<SPEC_KEY>, GRAT_SIZE, GRAT_PERP], min_rows_per_specimen: 4}
PTST: {required: [<SPEC_KEY>, PTST_K], recommended: [PTST_TYPE, PTST_COND, PTST_TSTR]}
FGHG: {required: [LOCA_ID, FGHG_TOP, FGHG_BASE, FGHG_IPRM], recommended: [FGHG_TYPE]}   # IPRG in 4.0.x
# <SPEC_KEY> = LOCA_ID, SAMP_TOP, SAMP_REF, SAMP_TYPE, SAMP_ID, SPEC_REF, SPEC_DPTH
```

---

## Project access and datasets (SPEC §10)

### Project access
- `p.groups`;
- `p.table(group, raw=False)`;
- `p.locations`;
- `p.diff(group)`;
- `p.sql(...)` (read-only, SI).

### Dataset columns
| Method | Columns |
|---|---|
| `p.spt()` | loca_id, loca_type, depth, depth_basis, elevation, spt_n, spt_n_capped, spt_n60, energy_ratio, energy_source, spt_refusal, spt_penetration, geology_unit, soil_class, geology_description, remarks |
| `p.atterberg()` | loca_id, specimen keys, depth, depth_basis, elevation, liquid_limit, plastic_limit, plasticity_index, non_plastic, water_content, liquidity_index, consistency_index, plasticity_class_uscs, plasticity_class_bs5930, geology_unit, soil_class |
| `p.grain_size()` / `p.grain_size_summary()` | Long curves (particle_size, percent_passing) / one row per specimen (d10, d30, d60, uniformity_coefficient, curvature_coefficient, fractions, gradation_uscs) |
| `p.index_properties()` | One row per sample: Atterberg + water_content + PSD summary, uscs_symbol, aashto_group, aashto_group_index. Specimen combining rule: SPEC §13 #2 |
| `p.permeability()` | loca_id, depth, depth_top, depth_base, depth_basis, elevation, hydraulic_conductivity, qualifier, source (lab/field), test_type, geology_unit, soil_class |
