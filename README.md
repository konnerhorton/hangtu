# hangtu

Plots and analyses for geotechnical engineers, in US or SI units. hangtu works on plain pandas DataFrames and CSV files now; reading **AGS4** data files directly comes in a later release.

> **Status:** pre-alpha. The plot framework, the property profile and the property-by-geology-unit plot are built. The rest of the first release is in progress (see [Roadmap](#roadmap)). Function names and arguments may still change.

## What it does now

- **Property profile** (`ht.plot.profile`): any property against depth or elevation, colored by geology unit, on a linear or log axis. Optional strata bands, water levels, published ranges, design lines and a summary table.
- **Property by geology unit** (`ht.plot.geology_unit_comparison`): the spread of a property in each geology unit, as percentiles or a box plot, optionally against baseline values from a report.
- **Units that follow the data:** declare each column's units once (`ht.read_csv(..., units=...)`) and every plot converts to US or SI display units. hangtu never guesses a unit.
- **Nothing is dropped silently:** values beyond the axis limits, blanks and "less than" values are drawn or counted on the figure.
- **Printable sheets** (`ht.Sheet`): several plots on one tabloid or letter page, saved as PDF, PNG or SVG.
- **CSV templates** (`ht.template`) with the column names each plot expects, and `ht.columns()` to list and describe them.

Every figure is an ordinary matplotlib figure, so you can keep editing it with matplotlib.

## Install

```bash
pip install hangtu      # or: uv add hangtu
```

hangtu needs Python 3.12 or later and runs on Windows, macOS and Linux.

## Quickstart

Start from a template, fill it in (in Excel or anything else that saves CSV), then plot it:

```python
import hangtu as ht

ht.template("permeability").to_csv("perm.csv", index=False)  # an empty CSV to fill in

lengths = ["depth", "depth_top", "depth_base", "ground_level", "elevation"]
k = ht.read_csv(
    "perm.csv",
    units={**dict.fromkeys(lengths, "ft"), "hydraulic_conductivity": "cm/s"},
)
fig, ax = ht.plot.profile(k, "hydraulic_conductivity", preset="hydraulic_conductivity")
fig.savefig("permeability.png")

fig, ax = ht.plot.geology_unit_comparison(k, "hydraulic_conductivity", display_units="SI")
```

## Roadmap

hangtu is released plot-first: plots are what engineers use day to day, and they only need a DataFrame, so they come before AGS ingest.

| Version | Content |
|---|---|
| **v0.1** (in progress) | Plot framework; property profile and property by geology unit (done); SPT profile, SPT histograms, plasticity chart, grain size curves and water content profile; the analyses behind them (SPT N60 and classes, USCS plasticity classes, D10/D30/D60, Cu and Cc) |
| v0.2 | Read **AGS4** files (4.0.3–4.2) into a SQLite database, with data-quality checks and ready-made SPT, index property, grain size and permeability datasets that feed the plots directly |
| v0.3 | Statistics: distribution fitting, group comparisons, Eurocode 7 characteristic values |
| Later | Triaxial and consolidation, AGSi export, DIGGS input, and more |

The full specification is in [SPEC.md](https://github.com/konnerhorton/hangtu/blob/main/SPEC.md), and each plot has its own spec in [docs/plots](https://github.com/konnerhorton/hangtu/tree/main/docs/plots).

## Who it's for

Geotechnical engineers comfortable writing short Python scripts. The library assumes scripting skills picked up in engineering or science work, not a software-development background.

## License

MIT
