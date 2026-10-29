# Draft plot specs

**Status:** draft. These are notes for later units of work, not decisions. Each file follows `docs/plots/TEMPLATE.md` so it can be promoted to `docs/plots/PXX-*.md` when its unit of work starts (`docs/reference/process.md`). Until then, nothing here overrides `SPEC.md`, `docs/plots/README.md` or an approved plot spec.

Each draft ends with **pitfalls**: mistakes that are easy to make when implementing that figure, so the spec and tests guard against them.

---

## Index

| Draft | What it draws | Status in `docs/plots/README.md` | Milestone |
|---|---|---|---|
| [P02](../P02-spt-profile.md) | SPT N against elevation, colored by unit | built (promoted) | M3 |
| [P03](../P03-spt-histogram.md) | % of tests per density or consistency class, per unit | built (promoted) | M3 |
| [P04](../P04-plasticity-chart.md) | Plasticity chart with A/U lines and optional user regions | approved (promoted) | M8 |
| [P05](../P05-grain-size.md) | Grain size curves, fraction header band, envelopes, D-values | approved (promoted) | M8 |
| [P11](P11-failure-envelope.md) | Failure envelope with fitted c′–φ′: Mohr circles, s′–t or p′–q, optional idealized drained paths | listed | M11 |
| [P12](P12-triaxial-shearing.md) | Stress–strain curves and measured stress paths, with P11's envelope (P10 merged in) | listed | M11 |
| [P17](../P17-clogging-diagram.md) | Clogging potential zones, PI against consistency index | built (promoted) | M12 |
| [P19](P19-pmt-hardening-soil.md) | E50 against elevation from pressuremeter tests | listed | M23 |
| [P23](P23-lateral-earth-pressure.md) | PMT p0, σv, u, σ′v, σ′h and K0 against depth | listed | Later |
| [P24](P24-grouped-histogram.md) | Property histogram per unit | **proposed ID** | open |
| [P25](P25-size-fraction-comparison.md) | % gravel/sand/silt/clay/fines per unit | **proposed ID** | open (after M8) |
| [P26](P26-strength-from-plasticity.md) | φ′ and c′ correlated from PI, per unit | **proposed ID** | not yet placed |
| [P27](P27-published-distribution-comparison.md) | Histogram per unit against a published distribution | **proposed ID** | M15 (with P08) |
| [P28](P28-undrained-strength-from-spt.md) | N–s_u correlation chart; s_u from N per unit | **proposed ID** | correlation M13; chart open |
| [P29](P29-monitoring-coverage.md) | Dates with groundwater readings, per group of wells | **proposed ID** | not yet placed |
| [P30](P30-groundwater-time-series.md) | Groundwater elevation over time | **proposed ID** | not yet placed |

The IDs P24–P30 aren't in `docs/plots/README.md` yet; adding them is a decision for when each one is picked up.

---

## Cross-cutting findings

These come up in more than one draft. Each is a candidate for `SPEC.md` or `docs/plots/README.md`, to be decided when the first plot that needs it is specified.

1. **Grouping by any column.** Plots color by `geology_unit` by default. They should also accept any categorical column (`color_by="zone"`), with the user adding the column, e.g. an upper/lower split at an elevation: `df["zone"] = np.where(df.elevation > 120, "upper", "lower")`. P07 lists `group_by=` as a future enhancement.
2. **Correlations are analyses, drawn by existing plots.** *Decided for SPT correlations (SPEC §4, 2026-10-15).* Sørensen & Okkels (P26) and Sowers (P28) are functions that add columns; the figures are P07 (by unit) or P01 (against depth). Only their reference charts are new figures. Suggest a `ht.analysis.correlations` module with one function per published correlation, each citing its source and validity range and returning NaN plus a count outside it.
3. **Project reference data is user-supplied.** Published *standards* (A-line, USCS fractions) live in `config/defaults.yaml` with citations. Project- or region-specific ranges, envelopes, classification regions and statistics come in as user tables (`ranges=`, `baseline=`, `regions=`, `envelopes=`, `published=`), never bundled.
4. **A water unit weight setting.** P19 and P23 need γw. Suggest `ht.settings.water_unit_weight` (9.81 kN/m³ / 62.4 pcf), so the value is set once and never typed inline.
5. **New registry names.** Several drafts propose new columns (strength, pressuremeter, groundwater, size fractions). They're marked *proposed* in each file's §3 and must be checked against the whole registry before they're added (CLAUDE.md, "Naming").
