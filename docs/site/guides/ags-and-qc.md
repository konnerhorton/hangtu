# AGS files and data checks

Read an AGS4 file into a project database, then check it.

```python
--8<-- "ags-and-qc.py"
```

``` { .text .no-copy }
--8<-- "ags-and-qc.txt"
```

## Reading an AGS file

`ht.Project.from_ags(path, db=...)` reads AGS4 versions 4.0.3 to 4.2 into a SQLite database. Values are converted to SI units as they are read, from the units the file gives, and shown in the project's display units on the way out. Flags such as `NP`, `<0.1` or a refusal are kept with the value.

Reading stops only when the file can't be read as AGS4 at all. Anything else (a value that doesn't match its type, a unit hangtu doesn't recognize) is kept as a finding for the data checks.

Settings given to `from_ags` belong to the project: `display_units="US"` and `vertical_datum="NAVD88"`, for example. The database keeps them, so `ht.Project.open("site.sqlite")` opens the project again without rereading the file. Pass `overwrite=True` to rebuild a database that already exists.

The vertical datum comes from the file when the file is clear about it: when every hole with a ground level names the same datum in `LOCA_DATM` and none has a local level (`LOCA_LOCZ`), that datum is the project's. `vertical_datum=` overrides it, and the data checks warn (L007) when the two disagree. Datum names are read from a table of known datums (`NAVD88`, `NGVD29`, `CGVD28`, `CGVD2013`, `ODN`, in any common spelling); add another with `ht.add_vertical_datum()`. `print(p.settings)` shows where the datum came from.

## Checking the data

`p.qc()` runs about 40 rules on locations, geology, depths, SPT, Atterberg limits, grading and permeability, and on the fields each group needs. Printed, the report counts findings by rule. `report.findings` is a table of every finding with its hole, depth and line in the file, and `report.to_csv("qc_report.csv")` saves it, with the rules used in `qc_report_rules.csv`.

Rules can be changed or turned off for a project, for example a tolerance with its unit:

```python
report = p.qc(rules={"G002": {"thresholds": {"depth_tolerance": "0.05 ft"}}})
```

Specimen depths just outside their sample, by up to 0.1 m, are reported as D008 (info, likely unit rounding in a lab table) rather than D007 (warning), so the specimens that are meters out stand out. The bound is D007's `rounding_tolerance`.

## Accepting reviewed findings

Some findings are correct by the rule but expected on a site: ground levels that differ from nearby holes in a valley, or velocity profiles that run below the borings. Once you have checked them, list them with a reason, and the report shows what is still open:

```yaml
# site_accepted.yaml
accepted:
  - rule_id: L005
    reason: Valley site; ground levels follow the topography.
  - rule_id: D003
    group: VSPR
    reason: Velocity profiles run to 30 m for Vs30, below the borings.
  - rule_id: D007
    loca_id: BH-12
    depth: 41.5 ft
    reason: Specimen depth checked against the lab sheet.
```

```python
report = p.qc(accepted="site_accepted.yaml")
```

Each entry needs a `rule_id` and a `reason`. `loca_id`, `group`, `heading` and `depth` narrow it, and a key left out matches anything, so `rule_id` alone accepts that rule on this site. A `depth` is written with its unit and matches a finding within 0.05 m. Entries match on content, not on line numbers, so they still apply to a revised file.

Accepted findings aren't hidden. They stay in `report.findings` with their severity, marked in the `accepted` and `reason` columns, and the printed report counts them next to the open ones. `report.accepted` lists each entry with how many findings it matched; one that matches nothing may be stale, for example after the file was fixed.

To accept findings you have reviewed in the table, build the entries from it with pandas:

```python
rows = report.findings.query("rule_id == 'D008' and loca_id == 'BH-3'")
entries = [
    {"rule_id": r.rule_id, "loca_id": r.loca_id, "depth": f"{r.depth:.2f} {r.depth_unit}",
     "reason": "Lab depths rounded from feet."}
    for r in rows.itertuples()
]
report = p.qc(accepted=entries)
```

Save `entries` with `yaml.safe_dump({"accepted": entries})` to keep them with the project.

## What ingest did

`p.diff(group)` compares each value in the file with what was stored, cell by cell: whether it was converted, flagged, reformatted or left unchanged. Use it to check the conversions on a new file.

## See also

- [`ht.Project`](../reference/project.md)
- [Datasets](datasets.md)
