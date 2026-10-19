# Templates and columns

A template is an empty table with the columns hangtu expects. Save it as a CSV file, fill it in, and read it back.

```python
--8<-- "templates.py"
```

``` { .text .no-copy }
--8<-- "templates.txt"
```

## Templates

`ht.template(name)` returns the empty table; `.to_csv(path, index=False)` saves it. The file has one header row and no units row: declare the units when you read it back with `ht.read_csv()` (see [units](units.md)).

The `spt`, `atterberg`, `grain_size` and `permeability` templates have the same columns as the datasets an AGS project gives, so a filled-in template and an AGS file reach the plots in the same shape. Columns hangtu calculates, such as `spt_n60` and `elevation`, can be left blank. Every template and its columns are listed on the [column reference](../reference/columns.md#templates).

## The column registry

Every column name hangtu uses comes from one registry. `ht.columns()` lists them all; `ht.columns("spt")` lists one template's. For each column it gives a description, its quantity (length, stress, percent, ...) and the US and SI units it is shown in.

## Values that are not numbers

Some results are not plain numbers, and hangtu keeps them distinct from a blank:

- **non-plastic** soil: `non_plastic` is True and the limits are blank;
- **SPT refusal**: `spt_refusal` is True, or the penetration is less than 450 mm (18 in);
- **less than** or **greater than** a value, such as `<0.001` for a permeability, from an AGS file: kept with the value as a bound, and drawn or counted on a plot.

A blank is only ever a missing value.

## See also

- [`ht.template`](../reference/data.md#hangtu.template), [`ht.columns`](../reference/data.md#hangtu.columns)
- [Column reference](../reference/columns.md)
