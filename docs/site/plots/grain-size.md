# Grain size distribution

Grading curves on a log particle-size axis, with the soil fractions named in a band above.

```python
--8<-- "grain-size.py"
```

![Grading curves from the example site, colored by geology unit, with the USCS fractions above](../img/generated/grain-size.png){ width="560" }

## What it shows

One curve per specimen, colored by geology unit, through its points as measured. The fraction band, its dividers and any D-values come from the same code as `ht.analysis.gradation()`, so they agree with its numbers. Particle size is in mm in both unit systems.

Nothing is reshaped or extrapolated: a curve that rises toward finer sizes is drawn as measured, with a warning, and gets no D-values. Short curves, blank points and D-values a curve doesn't reach are counted in the footnote.

## Common options

| Argument | Does |
|---|---|
| `fractions=` | The band's system: `"astm_uscs"` (the default), `"aashto"`, `"iso14688"`, your own, or None to hide it |
| `d_values=True` | Mark D10, D30 and D60 (or a list such as `[15, 85]`) |
| `sieves="auto"` | Sieve labels above the frame: ASTM E11 in US display, ISO in SI |
| `envelopes=` | Bands to compare with, such as a filter specification (`ht.template("envelopes")`) |
| `color_by="specimen_id"` | One color per curve |
| `reverse=True` | Coarse sizes on the left, as on some US forms |

## See also

- [`ht.plot.grain_size`](../reference/plot.md#hangtu.plot.grain_size), [`ht.analysis.gradation`](../reference/analysis.md#hangtu.analysis.gradation)
