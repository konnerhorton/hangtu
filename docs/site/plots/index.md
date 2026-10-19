# Plots

Every plot takes a DataFrame and returns an ordinary matplotlib figure and axes. Several go on one printable page with `ht.Sheet`.

```python
--8<-- "sheet.py"
```

![Two plots side by side on a letter sheet](../img/generated/sheet.png)

## What every plot shares

- **`fig, ax = ht.plot.<name>(df, ...)`**: change the figure with matplotlib as usual, then `fig.savefig("plot.png")` or `.pdf`.
- **`ax=`** draws on an axes you already have, such as a panel of a sheet: `ax=sheet[0]`, or `ax=sheet[1, :]` for a whole row.
- **`display_units=`** is `"US"` or `"SI"`; by default `ht.settings.display_units`. Axis labels carry the units. See [units](../guides/units.md).
- **Colors** follow the geology unit, from `ht.settings.palette` or a project's geology map, the same in every plot of a session.
- **Nothing is dropped silently.** Blanks, values beyond fixed axis limits, values ≤ 0 on a log axis and refusals are drawn at the edge or counted in a footnote.

## Sheets

`ht.Sheet(size, layout=(rows, columns), title=...)` is a page of panels: `"letter"`, `"tabloid"`, `"ansi_d"`, `"a4"` or `"a3"`, in landscape or portrait. `sheet.save("site.pdf")` writes it as PDF, PNG or SVG.

## The plots

| Plot | Shows |
|---|---|
| [Property profile](profile.md) | Any property against depth or elevation |
| [SPT profile](spt-profile.md) | SPT N or N60 against depth or elevation, with refusals |
| [SPT histogram](spt-histogram.md) | The share of tests in each density or consistency class |
| [Property by geology unit](geology-unit-comparison.md) | A property's spread in each geology unit, against a report's ranges |

## See also

- [`ht.plot`](../reference/plot.md), [`ht.Sheet`](../reference/data.md#hangtu.Sheet)
