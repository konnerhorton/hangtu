<img src="https://raw.githubusercontent.com/konnerhorton/hangtu/main/docs/site/img/wordmark.svg" alt="hangtu" width="360">

*Hangtu* is Chinese for rammed earth, one of the oldest ways of building with soil: it raised city walls in China more than 4,500 years ago. `hangtu` respects the long tradition of humans building with earth materials while automating the mundane and leaving judgment to the engineer.

**Documentation:** [konnerhorton.github.io/hangtu](https://konnerhorton.github.io/hangtu/)

Plots, data checks and analyses for geotechnical engineers, in US or SI units. hangtu reads **AGS4** data files into a project database, checks them, and turns them into ready-made tables of SPT, Atterberg, grain size and permeability results that go straight into its plots. The plots also work on your own CSV files.

> **Status:** early release. Names and arguments may still change before 1.0.

## Install

```bash
pip install hangtu      # or: uv add hangtu
```

For the latest features, which the documentation follows, install from GitHub:

```bash
pip install git+https://github.com/konnerhorton/hangtu
```

hangtu needs Python 3.12 or later and runs on Windows, macOS and Linux.

## From an AGS file

```python
import hangtu as ht

# Read the file into a project database (here an example site that ships with hangtu).
p = ht.Project.from_ags(
    ht.examples.path("site.ags"), db="site.sqlite", display_units="US", vertical_datum="NAVD88"
)
p.set_geology_map(ht.examples.path("strata.csv"))  # geology codes -> units, order, colors

report = p.qc()  # check the data
print(report)
report.to_csv("qc_report.csv")  # every finding, with its hole, depth and line in the file

fig, ax = ht.plot.spt_profile(p.spt(), n="spt_n60")
fig.savefig("spt_profile.png")
```

<img src="https://raw.githubusercontent.com/konnerhorton/hangtu/main/docs/img/readme-spt.png" alt="SPT N60 against elevation, colored by geology unit, with refusals drawn at the cap and counted" width="440">

`p.spt()`, `p.atterberg()`, `p.grain_size()` and `p.permeability()` give one row per test, with its depth, elevation and geology unit joined on. They take filters such as `holes=`, `geology=` and `depth=`.

## From your own CSV files

Save an empty template, fill it in (in Excel or anything else that saves CSV), then read it back with its units:

```python
ht.template("spt").to_csv("my_spt.csv", index=False)  # an empty file to fill in

spt = ht.read_csv(
    ht.examples.path("spt.csv"),  # or your own file
    units={"ground_level": "ft", "depth": "ft", "elevation": "ft", "spt_penetration": "in"},
)
fig, ax = ht.plot.spt_histogram(spt[spt["soil_class"] == "coarse"], n="spt_n60")
```

`ht.columns("spt")` lists each template column with its description and unit. Both examples in full, with all four plots on one sheet, are in [`examples/`](https://github.com/konnerhorton/hangtu/tree/main/examples).

## What it does

- **AGS4 ingest** (versions 4.0.3 to 4.2) into a SQLite project database, with units read from the file and converted on the way in. Values such as `NP`, `<0.1` and refusals are kept as flags, never as blanks.
- **Data checks** (`p.qc()`): about 40 rules on locations, geology, depths, SPT, Atterberg limits, grading and permeability, plus required fields. Results come as a summary and a CSV report, and `p.diff()` compares two versions of a file.
- **Datasets** for SPT, Atterberg limits, grain size curves and permeability. Each test gets its depth (SPT at mid-drive), elevation and geology unit, and a geology map gives the units their order and colors.
- **Plots:** property profile (any property against depth or elevation, linear or log), SPT profile, SPT class histograms, and property by geology unit against a report's baseline. Each is an ordinary matplotlib figure.
- **SPT analysis:** N60 from the energy ratio, refusals and N classes.
- **Units that follow the data:** each column's units are declared once, and every plot converts to US or SI. hangtu never guesses a unit.
- **Nothing is dropped silently:** values beyond the axis limits, blanks and "less than" values are drawn or counted on the figure.
- **Printable sheets** (`ht.Sheet`): several plots on one tabloid or letter page, saved as PDF, PNG or SVG.

## Roadmap

| Version | Content |
|---|---|
| **v0.1** | Plot framework; property profile, property by geology unit, SPT profile and SPT histograms, with SPT N60 and classes. AGS4 ingest, data checks, and SPT, Atterberg, grain size and permeability datasets |
| v0.2 | Plasticity chart, grain size curves and water content profile; the analyses behind them (USCS plasticity classes, D10/D30/D60, Cu and Cc) and the index property datasets that use them |
| v0.3 | Statistics: distribution fitting, group comparisons, Eurocode 7 characteristic values |
| Later | Triaxial and consolidation, AGSi, DIGGS input, and more |

The full specification is in [SPEC.md](https://github.com/konnerhorton/hangtu/blob/main/SPEC.md), and each plot has its own spec in [docs/plots](https://github.com/konnerhorton/hangtu/tree/main/docs/plots).

## Who it's for

Geotechnical engineers comfortable writing short Python scripts. The library assumes scripting skills picked up in engineering or science work, not a software-development background.

## License

MIT
