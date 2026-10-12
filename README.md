# hangtu

Python tools for geotechnical engineers working with **AGS4** data files.

AGS is a data exchange format for ground investigation data. It was developed in the UK and is used worldwide, but outside the UK and Australia the tooling for actually *using* AGS data is thin. hangtu fills part of that gap. It turns an AGS file into a queryable database, checks its quality, and provides the analyses, statistics and plots a geotechnical engineer needs day to day, in US or SI units.

> **Status:** pre-alpha. The MVP is specified in [SPEC.md](SPEC.md) and nothing is built yet.

## What it will do (MVP)

- **Ingest** an AGS4 file into a SQLite database: validated with [python-ags4](https://gitlab.com/ags-data-format-wg/ags-python-library), typed, and converted to consistent units. Imperial and metric files are both supported.
- **Check data quality:** missing geology, incomplete test records, backward or improbable depths and elevations, unit problems. Results export to CSV.
- **Query common datasets:** SPT, Atterberg limits and grain size, with elevations computed and geology attached, and filters on any field.
- **Analyze:**
  - SPT N and N60 with density/consistency classes;
  - plasticity chart with USCS classes;
  - grain size curves with D10/D30/D60, Cu and Cc.
- **Statistics:** distribution fitting, group comparisons (t-test / Mann-Whitney), box plots against published ranges, and Eurocode 7 characteristic values.
- **Plot:** consistent, opinionated matplotlib figures that remain fully editable, and that can be combined onto printable sheets.

See [SPEC.md](SPEC.md) for the full specification and roadmap, and [docs/reference/eurocode7-summary.md](docs/reference/eurocode7-summary.md) for background on the characteristic-value methods.

## Quickstart (planned)

```bash
pip install hangtu      # or: uv add hangtu
```

```python
import hangtu as ht

p = ht.Project.from_ags("site.ags", db="site.sqlite", display_units="US")
p.qc().to_csv("qc_report.csv")

spt = p.spt()
fig, ax = ht.plot.spt_profile(spt, color_by="geology_unit")
fig.savefig("spt.png")
```

## Who it's for

Geotechnical engineers comfortable writing short Python scripts. The library assumes scripting skills picked up in engineering or science work, not a software-development background.

## License

MIT
