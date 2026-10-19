# SPT profile

SPT N or N60 against depth or elevation, with refusals drawn at the cap and counted.

```python
--8<-- "spt-profile.py"
```

![SPT N60 against elevation, colored by geology unit](../img/generated/spt-profile.png){ width="440" }

## What it shows

One point per test, colored by geology unit. The data first goes through `ht.analysis.spt()`, which finds refusals and works out N60 and capped N (see [SPT analysis](../guides/spt.md)). A refusal is a filled triangle at the cap, and the footnote counts them. Field N and N60 are never mixed on one plot.

Give each test's depth as the middle of its test drive when you know it; a test's top depth plots it up to 1.5 ft (0.45 m) high. Datasets from an AGS project do this already.

## Common options

| Argument | Does |
|---|---|
| `n="spt_n60"` | Plot N60 (or `"spt_n"`, `"spt_n_capped"`) |
| `hammer_efficiency=` | The energy ratio for tests without `energy_ratio` |
| `refusal="exclude"` | Leave refusals out (still counted) |
| `cap=` | The blow count refusals are drawn at |
| `connect=True` | Join each hole's tests with a line |
| `vs=`, `xlim=`, `strata=`, ... | As the [property profile](profile.md) |

## See also

- [`ht.plot.spt_profile`](../reference/plot.md#hangtu.plot.spt_profile)
