---
title: hangtu
---

![hangtu](img/wordmark.svg){ width="360" }

*Hangtu* is Chinese for rammed earth, one of the oldest ways of building with soil: it raised city walls in China more than 4,500 years ago. `hangtu` respects the long tradition of humans building with earth materials while automating the mundane and leaving judgment to the engineer.

Plots, data checks and analyses for geotechnical engineers, in US or SI units. hangtu reads **AGS4** data files into a project database, checks them, and turns them into tables of SPT, Atterberg, grain size and permeability results that go straight into its plots. The plots also work on your own CSV files.

```python
--8<-- "spt-profile.py"
```

![SPT N60 against elevation, colored by geology unit, with refusals drawn at the cap and counted](img/generated/spt-profile.png){ width="440" }

## What it does

- **AGS4 ingest** (versions 4.0.3 to 4.2) into a SQLite project database, with units read from the file. Values such as `NP`, `<0.1` and refusals are kept as flags, never as blanks.
- **Data checks:** about 40 rules on locations, geology, depths and tests, as a summary and a CSV report.
- **Datasets** for SPT, Atterberg limits, grain size and permeability, each test with its depth, elevation and geology unit.
- **Plots** that are ordinary matplotlib figures, in US or SI units, that never drop data silently.
- **Analyses** as plain functions on a DataFrame: SPT N60 and classes, plasticity and gradation.

## Where to start

- [Install](install.md) hangtu.
- Draw a first plot [from a CSV file](getting-started/csv.md) or [from an AGS file](getting-started/ags.md).

hangtu is for geotechnical engineers comfortable writing short Python scripts. It is MIT licensed, and the source is on [GitHub](https://github.com/konnerhorton/hangtu).
