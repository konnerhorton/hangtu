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

## What ingest did

`p.diff(group)` compares each value in the file with what was stored, cell by cell: whether it was converted, flagged, reformatted or left unchanged. Use it to check the conversions on a new file.

## See also

- [`ht.Project`](../reference/project.md)
- [Datasets](datasets.md)
