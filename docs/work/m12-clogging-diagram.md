# M12: P17 clogging diagram

## Intent

### Goal
`ht.plot.clogging_diagram()` places fine-grained specimens on the Thewes & Burger (2004) chart of clay clogging potential for TBM drives, with plasticity index across and consistency index up, and returns each specimen's zone so a GBR or TBM specification can quote the counts ("High: 14 of 52").

### Why
- M12 is the last unit of wave 1 (SPEC §1.3, §12.4). The rest of the wave is done: vertical stress and the SPT correlations (M13), phase relations and activity (M14).
- Clogging potential is a routine input to tunnel GBRs, and the chart is drawn by hand today from the same Atterberg and water content results hangtu already joins.
- The data is in place: `p.atterberg()` gives one row per specimen with `water_content`, `liquid_limit`, `plastic_limit`, `plasticity_index`, `non_plastic` and `consistency_index`, and `ht.analysis.plasticity()` adds PI and Ic to a CSV table. M12 adds no data and no new analysis of Ic.

### Constraints
- **Axes (TODO #21, settled):** x is `plasticity_index`, y is `consistency_index`, as in the paper. The draft's working layout (LL against Ic) was wrong and its zone polygons are not used.
- **Zones come from the paper, not from memory.** Each zone's coordinates are checked against the published figure in the spec step and kept in a config file with the citation (as `config/plasticity_systems.yaml` does for P04). Only the boundary values and the citation are published, not the figure.
- Plot contract (SPEC §3, `docs/plots/README.md`): a plot that runs an analysis returns `(fig, ax, result)`; styling in a context manager; legend and sizes per P00.
- Never drop data silently (SPEC §3): Ic < 0 (wetter than the liquid limit, common in soft clays), Ic or PI beyond the axes, NP specimens, and specimens missing w or a limit are drawn at the edge or counted in the footnote, each distinct.
- Zones are labeled with text, not told apart by color alone (`docs/plots/README.md`).
- Nothing converts: PI is a percentage and Ic is dimensionless.

### Out of scope
- The Hollmann & Thewes (2013) diagram (P18), which adds a gradation screen first. Not yet placed (SPEC §1.3).
- Any change to how Ic is computed or how w is paired with LL and PL (M7, M8).
- Clogging from mineralogy, cutterhead design or conditioning agents: the chart is a screen on index properties only, and the docstring says so.

### SPEC sections touched
- §12.4: M12 marked done at close-out; §1.3's wave 1 row is then complete.
- `docs/plots/drafts/P17-clogging.md` is promoted to `docs/plots/P17-clogging.md` in the spec step, with the corrected axes and verified zones.
- `docs/TODO.md` #21 is resolved in the spec step, once the zone coordinates are checked.
- New config file for the zones; registry `used_by` for `plasticity_index` gains P17.

### Proposed (for review)
1. 🟡 **The input is `p.atterberg()` or any table with w, LL and PL (or PI).** Ic is computed by `ht.analysis.plasticity()` when the column is absent, never by a second formula.
2. 🟡 **`result` is a DataFrame**, one row per input row, with `clogging_zone` (the zone's name, or blank with the reason it couldn't be placed). A new registry name, checked against the registry in the spec step.
3. 🟡 **`zones=` takes a user table** in the same shape as the config, so a variant from another source (such as the draft's LL-based layout) can be drawn without being built in.
4. 🟡 **Color by `geology_unit`** by default, like P04.
