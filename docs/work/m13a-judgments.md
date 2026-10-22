# m13a-judgments

## Intent
M13 is wave 1's first milestone (SPEC §1.3, §12.4). It splits in two units: **(a)**, this one, the judgments file
and `vertical_stress()`; **(b)** C_N / (N1)60, the hammer-efficiency changes, the correlations framework and the
first correlation set.

**Goal:** a project's judgments (unit weights, water levels) in one file with units and reasons, read the same way
by every analysis that needs them (SPEC §4: judgments have no defaults), and the first such analysis: total, pore
and effective vertical stress, integrated through each hole's log.

**SPEC and TODO touched:** §2.6 (units in the file), §4 (judgments, precedence), §10 (`p.stratigraphy()`), §12.4
(M13); TODO #30 (settled here), #33 (closed: hammer efficiency is data). `docs/drafts/analysis.md` §4.1 (the depth
profile and `interpolation=` go away).

### Draft shape of `judgments.yaml`
```yaml
# judgments.yaml: this project's judgments (SPEC §4)
unit_weight:
  by: geology_unit            # the log column the values are matched on (geology_unit, uscs_symbol, ...)
  units: {bulk_unit_weight: kN/m3, saturated_unit_weight: kN/m3}
  values:
    Fill:     {bulk_unit_weight: 18.5, reason: median LDEN, n=12}
    Alluvium: {bulk_unit_weight: 19.0, saturated_unit_weight: 20.0, reason: ...}
  # or, for a quick look: project: {bulk_unit_weight: 19.0, reason: ...}
water_level:
  units: {depth: m}
  project: {depth: 3.0, reason: ...}      # optional
  by_hole:
    BH01: {depth: 2.5, reason: standpipe reading 2026-09-14}
    BH02: {depth: 3.0, reason: assumed equal to BH01, no record}
```

### Decided
1. **Units inside the file:** a required `units:` block per judgment; SPEC §2.6 resolution; missing → error naming
   the judgment.
2. **Unit weight is by stratigraphy, not by depth.** Parameters are generally on an engineering-unit basis.
   - Values per unit, matched by string on a configurable log column (`by:`), so user-defined units or USCS
     classes both work, provided the log carries that column.
   - `bulk_unit_weight` required; `saturated_unit_weight` optional, used below the water table where given.
   - One project-wide value is allowed, with a required `reason`.
   - `interpolation=` and the depth profile from analysis draft §4.1 go away; "by geology unit" moves from Later
     into this unit.
3. **σv is integrated through each hole's log**, so the log is an input: from the M7 geology joins for a
   `Project`; for CSV, a per-hole strata table (`loca_id, depth_top, depth_base, <unit column>`).
4. **Water level:** `by_hole` entries plus an optional project-wide value with a required `reason`.
   - An unlisted hole uses the project value, with a warning naming the holes.
   - An unlisted hole with no project value → **error** naming the holes.
5. **Precedence:** direct argument (`unit_weight=...`) → `judgments=j` → the Project's judgments carried in
   `df.attrs` → error. An argument overriding a file value warns. `judgments=j` differing from the Project's file
   warns.
6. **Lookup:** a `Judgments` object, `j = ht.judgments("judgments.yaml")`, re-read on each call; `p.judgments` on a
   Project, carried by its datasets in `df.attrs`. When attrs are lost (merge, concat) the error says to pass
   `judgments=`.
7. **Recorded on the result:** each judgment's value, key and source (argument, or path + SHA-256) in
   `df.attrs["judgments"]`.
8. **Hammer efficiency is data, not a judgment** (closes TODO #33). `ISPT_ERAT` → `energy_ratio` is already used
   first. Unit (b) adds: a warning when the argument or setting fills blanks, naming the holes; values by hole
   (`hammer_efficiency={"BH01": 80}`).
9. **γw stays a setting** (`ht.settings.water_unit_weight`). New TODO: γw as a judgment for sites that need two
   values (seawater and fresh).

10. **String matching:** a unit in the log with no value → error; a judgment for a unit not in the data → warning.
11. **Log edges:** a gap between layers, a log starting below 0, or a hole with no log → error naming the hole and
    depth range. A test below the log base carries the last layer down, with a warning.
12. **CSV log is a new template, per hole** (`loca_id` required). The P01 `strata` overlay template is not
    extended: it stays a single stratigraphy with forgiving rules, while the stress log is complete and strict.
    An idealized profile applied to every hole is not in this unit.
    The overlay's bands now take the points' colors, from the data's palette first (`plot-review-fixes`), so a
    table that went through the geology map colors the same as the points.
13. **Template name:** `ht.template("stratigraphy")`: `loca_id, depth_top, depth_base, geology_unit` (the `by:`
    column may be another, e.g. `uscs_symbol`). `log` was rejected: it collides with `log=True` for log axes.

14. **`p.stratigraphy()` is a public dataset**, in the same shape as `ht.template("stratigraphy")` (SPEC §2.6
    template rule): GEOL layers with `geology_unit` through the geology map (datasets.md §5.2), `soil_class`,
    `geology_description`, `source_line`. Users can inspect it, export it, edit it (reclass by USCS, say) and pass
    it back. New section in `docs/data/datasets.md`.
15. **The log is always passed explicitly:** `vertical_stress(p.spt(), stratigraphy=p.stratigraphy(),
    judgments=p.judgments)`. It's data the user may have edited, so it's never picked up from attrs.
16. **Overlapping layers (QC G003) → error** naming the holes and depths and pointing to `p.qc()`. This differs
    from the datasets' placement rule (deepest top wins, datasets.md §5.4) because stress can't be integrated
    through two layers at once.

17. **Publishing (TODO #30) is settled in unit (a)'s spec**, with sheet 01 as the first page promoted to
    `docs/site/parameters/`. Starting point: values with citations, short sets of class boundaries; no whole
    tables or charts reproduced. Sheet 01's [U] items (ISRM 1979, Duncan 2000's COV table, ISO 18674-4) are
    verified or cut.

### Names (agreed; checked against `columns.yaml`, `defaults.yaml` and the plot arguments; no collisions)
`water_level` replaces `groundwater` everywhere, including the file sample above. `stratigraphy` is in depth only
(no elevation pair).

| Name | Kind | Quantity | Label | Notes |
|---|---|---|---|---|
| `total_vertical_stress` | column | stress | Total vertical stress, σ_v0 | |
| `pore_pressure` | column | stress | Pore pressure, u_0 | In situ; hydrostatic in M13, the method in attrs. Test-specific pore pressures get a test prefix (`cpt_…`, `triaxial_…`) |
| `effective_vertical_stress` | column | stress | Effective vertical stress, σ′_v0 | |
| `saturated_unit_weight` | column / file field | unit_weight | Saturated unit weight, γ_sat | Beside the existing `bulk_unit_weight` |
| `water_level` | argument + judgment key | – | – | Replaces `groundwater` from the draft: P01 already has `water_level=` with a per-hole `loca_id, depth\|elevation` DataFrame, so the same format serves both |
| `unit_weight` | argument + judgment key | – | – | |
| `water_unit_weight` | setting | unit_weight | Unit weight of water, γ_w | 9.81 kN/m³ / 62.4 pcf |
| `stratigraphy` | template, argument | – | – | `vertical_stress(df, *, stratigraphy=..., judgments=...)` |
| `ht.judgments(path)` → `Judgments`; `p.judgments` | API | – | – | |

### Open
- **`strata=` and `p.stratigraphy()`.** The overlay takes one stratigraphy with a depth or elevation pair;
  `p.stratigraphy()` is per hole and in depth only. Either `strata=` accepts it (for one hole, or with a
  `loca_id` filter), or the user picks one hole's layers. Settle in the spec step.
