# From a CSV file

Fill in a template in Excel or anything else that saves CSV, read it back with its units, and plot it.

```python
--8<-- "csv-to-plot.py"
```

![SPT N60 classes in the coarse soil](../img/generated/csv-to-plot.png){ width="440" }

## Step by step

1. **Get a template.** `ht.template("spt")` is an empty table with the columns hangtu expects for SPT results. Save it, fill it in, one row per test. `ht.columns("spt")` describes each column and its quantity. The [templates guide](../guides/templates.md) lists them all.
2. **Read it with its units.** hangtu never guesses a unit, so every column with one is declared when you read the file: here depths in feet and the SPT penetration in inches. Columns in percent or counts, such as `spt_n`, need none. See [units](../guides/units.md).
3. **Plot it.** Each plot takes the table and returns a matplotlib figure and axes, in US or SI units. Here, the N60 classes of the coarse soil; `spt_n60` comes from each test's `energy_ratio`. See [SPT analysis](../guides/spt.md).

## Bounds

A value below or above what a test resolves can be written in its cell as it appears on the lab sheet: `<1e-9`, `> 200`. `ht.read_csv` reads it as the number, with `<` or `>` in the `qualifier` column (`remolded_qualifier` for a remolded strength), and adds that column if the file has none. The statistics then count the value as a bound rather than leave it out as text. A cell such as `<5 kPa` stays text and is named where it is read; a sign that disagrees with the one already in `qualifier` is an error naming the rows.

## The full example

The example below reads three files and draws four plots on one printable sheet. It is `examples/csv_to_plot.py` in the repository.

??? example "csv_to_plot.py"

    ```python
    --8<-- "csv_to_plot.py"
    ```

## See also

- [`ht.read_csv`](../reference/data.md#hangtu.read_csv), [`ht.template`](../reference/data.md#hangtu.template)
- [Plots](../plots/index.md)
