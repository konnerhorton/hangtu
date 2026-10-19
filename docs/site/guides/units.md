# Units

Declare the units of your data once; every plot then shows them in US or SI units.

```python
--8<-- "units.py"
```

``` { .text .no-copy }
--8<-- "units.txt"
```

![The same SPT profile, drawn in SI units from data in feet](../img/generated/units.png){ width="440" }

## Declaring units

hangtu never guesses a unit. A column with a unit, such as a depth, needs it declared:

- when you read a CSV file: `ht.read_csv(path, units={"depth": "ft"})`;
- on a DataFrame you already have: `spt = ht.set_units(spt, {"depth": "ft"})`, which returns a new DataFrame.

Columns in percent, counts or with no dimension, such as `spt_n` or `liquid_limit`, need none. The [column reference](../reference/columns.md) gives each column's quantity. Data read from an AGS file takes its units from the file, so there is nothing to declare.

`ht.units_of(df)` shows what is declared. The units live in `df.attrs["units"]`; pandas `merge`, `join` and `concat` drop them, so declare them again on the result.

## Display units

Plots and datasets show values in **US** or **SI** units:

- a **plot** uses `display_units="SI"` (or `"US"`) on the call, else `ht.settings.display_units`, which is `"US"` by default;
- a **dataset** from an AGS project comes in `display_units=` on the call, else the project's display units.

Changing `ht.settings.display_units = "SI"` switches every plot in the session.

## When a unit is missing

A plot still draws a column with no declared units, but labels its axis "(units unknown)" and warns, saying how to declare them. An analysis that needs the unit stops with an error instead, because a wrong unit would give a wrong number.

## Unit names

Unit strings such as `"ft"`, `"in"`, `"m"`, `"kPa"`, `"pcf"` and `"cm/s"` are recognized. To use another spelling, add an alias with `ht.add_unit_alias("feet", "foot")`; for a new unit, `ht.define_unit()`.

## See also

- [`ht.read_csv`](../reference/data.md#hangtu.read_csv), [`ht.set_units`](../reference/data.md#hangtu.set_units), [`ht.units_of`](../reference/data.md#hangtu.units_of)
