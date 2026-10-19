# From an AGS file

Read an AGS4 file into a project database, check it, and plot a dataset.

```python
--8<-- "ags-to-plot.py"
```

![SPT N60 against elevation from the example AGS file](../img/generated/ags-to-plot.png){ width="440" }

## Step by step

1. **Read the file.** `ht.Project.from_ags()` reads the file into a SQLite database (`site.sqlite`), with units read from the file. `display_units="US"` gives every dataset in US units; `"SI"` gives SI.
2. **Map the geology.** `set_geology_map()` reads a CSV that maps the file's geology codes to the units you report on, with their order and colors.
3. **Check the data.** `p.qc()` runs the data checks. Printing it gives a count of findings per rule; `p.qc().to_csv("qc_report.csv")` writes every finding with its hole, depth and line in the file. See [AGS ingest and QC](../guides/ags-and-qc.md).
4. **Plot a dataset.** `p.spt()` is one row per SPT test, with its depth, elevation and geology unit, ready for the plots. See [datasets](../guides/datasets.md).

## The full example

The example below also writes the QC report and draws four plots on one printable sheet. It is `examples/ags_qc_plot.py` in the repository.

??? example "ags_qc_plot.py"

    ```python
    --8<-- "ags_qc_plot.py"
    ```

## See also

- [`ht.Project`](../reference/project.md)
- [Plots](../plots/index.md)
