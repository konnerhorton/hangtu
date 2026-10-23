# (N1)60 and correlations

Correct N60 for overburden, then estimate a parameter from published correlations, each named on its rows, and compare them on one profile.

```python
--8<-- "correlations.py"
```

``` { .text .no-copy }
--8<-- "correlations.txt"
```

![Effective friction angle against depth, colored by correlation](../img/generated/correlations.png){ width="440" }

## (N1)60

`ht.analysis.spt_n1_60()` multiplies N60 by the overburden correction C_N, from the effective vertical stress at the test that [`vertical_stress()`](judgments.md) adds:

$$
(N_1)_{60} = C_N \, N_{60}
$$

C_N has two forms, chosen with `method=`, which has no default:

| `method=` | C_N | Source |
|---|---|---|
| `"liao_whitman_1986"` | (pa / σ′v)^0.5 | Liao & Whitman (1986); Youd et al. (2001), Eq. 9 |
| `"kayen_1992"` | 2.2 / (1.2 + σ′v / pa) | Kayen et al. (1992); Youd et al. (2001), Eq. 10 |

Both are capped at 1.7, with pa = 100 kPa. They differ by up to about 12 % between 25 and 300 kPa. Above 300 kPa, Youd et al. (2001) say C_N should be estimated by other means, so C_N and (N1)60 are blank there, with a warning. The rod-length, borehole-diameter and sampler corrections aren't applied. `df.attrs["spt_n1_60"]` records the method, the cap and pa.

## Correlations

Each published correlation is a function in `ht.analysis.correlations`, named after its source. For the effective friction angle φ′ of sand:

| Function | Reads | Range |
|---|---|---|
| [`effective_friction_angle_hatanaka_uchida_1996`](../reference/correlations.md#hangtu.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996) | `spt_n1_60` | 4.55 ≤ (N1)60 ≤ 39 |
| [`effective_friction_angle_kulhawy_mayne_1990`](../reference/correlations.md#hangtu.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990) | `spt_n60`, `effective_vertical_stress` | N60 ≤ 60; 0 < σ′v ≤ 300 kPa |

Each one:

- **reads the one N it was derived with,** by its column name, and has no argument to read another. A correlation on (N1)60 given only N60 stops with an error that says to run `spt_n1_60()` first, so field N never goes into an (N1)60 equation unnoticed.
- **doesn't read the soil type.** These are for relatively clean sands: pass the rows a correlation applies to, as for `spt_class()`. The example's Terrace is a sand with gravel, at the edge of what they cover; on a project, check the gradation first.
- **returns every row,** with the estimate in the property's column (`effective_friction_angle`), `correlation_name`, and `correlation_note`, which says why there's no estimate: `input blank`, `refusal`, `below range` or `above range`. Outside its range a correlation gives a blank, never a clipped or extrapolated value.
- **records what it is** in `df.attrs["correlations"]`: the equation, inputs, range and sources of every correlation. `ht.analysis.correlations.describe(name)` returns the same entry when the attrs are lost.

Passing the whole Terrace instead of its upper part shows how much of a dense sand falls outside these ranges:

``` { .text .no-copy }
UserWarning: effective_friction_angle_hatanaka_uchida_1996 gave no estimate for 21 of 33 rows (9 refusal, 12 above range; see 'correlation_note'). Its range is 4.55 ≤ spt_n1_60 ≤ 39; outside it the estimate is blank, never extrapolated.
UserWarning: effective_friction_angle_kulhawy_mayne_1990 gave no estimate for 12 of 33 rows (9 refusal, 3 above range; see 'correlation_note'). Its range is spt_n60 ≤ 60; 0 < effective_vertical_stress ≤ 300; outside it the estimate is blank, never extrapolated.
```

## Comparing estimates

Results from the same input concatenate with `pd.concat`, one row per test and correlation, and keep their units. `ht.plot.profile(..., color_by="correlation_name")` draws them together, and its footnote counts the blank estimates by their `correlation_note`: "9 refusals, no estimate", "12 above range, no estimate". The two correlations above differ by about 3° here; which to use, or how to combine them with measured values, is the engineer's call (stage D). [Drained shear strength of soil](../parameters/04-drained-shear-strength-soil.md) compares the methods.

## See also

- [`ht.analysis.spt_n1_60`](../reference/analysis.md#hangtu.analysis.spt_n1_60), [correlations reference](../reference/correlations.md)
- [SPT analysis](spt.md): refusal, N60 and the energy ratio
- [Judgments and vertical stress](judgments.md): σ′v from the project's unit weights and water levels
