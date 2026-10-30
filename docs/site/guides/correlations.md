# (N1)60 and correlations

Correct N60 for overburden, then estimate a parameter from published correlations, each named on its rows, and compare them on one profile. The first example estimates φ′ in sand; [Bands and PI](#bands-and-pi) estimates s_u in clay.

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

Each published correlation is a function in `ht.analysis.correlations`, named after the property it estimates and its source (`<target>_<authors>_<year>`), so tab completion groups them by property. For the effective friction angle φ′ of sand:

| Function | Reads | Range |
|---|---|---|
| [`effective_friction_angle_hatanaka_uchida_1996`](../reference/correlations.md#hangtu.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996) | `spt_n1_60` | 4.55 ≤ (N1)60 ≤ 39 |
| [`effective_friction_angle_kulhawy_mayne_1990`](../reference/correlations.md#hangtu.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990) | `spt_n60`, `effective_vertical_stress` | N60 ≤ 60; 0 < σ′v ≤ 300 kPa |

Each one:

- **reads the one N it was derived with,** by its column name, and has no argument to read another. A correlation on (N1)60 given only N60 stops with an error that says to run `spt_n1_60()` first, so field N never goes into an (N1)60 equation unnoticed.
- **reads the soil type only when asked** (see [Soil type](#soil-type)). By default, pass the rows a correlation applies to, as for `spt_class()`. These are for relatively clean sands; the example's Terrace is a sand with gravel, at the edge of what they cover. On a project, check the gradation first.
- **returns every row,** with the estimate in the property's column (`effective_friction_angle`), `correlation_name`, `correlation_note` and `correlation_input`. `correlation_note` says why there's no estimate: `input blank`, `refusal`, `below range`, `above range`, `not for this soil` or `soil type unknown`. Outside its range a correlation gives a blank, never a clipped or extrapolated value. `correlation_input` names the correlation an input came from, where one did (see [Chaining](#chaining)).
- **records what it is** in `df.attrs["correlations"]`: the equation, inputs, range and sources of every correlation. `ht.analysis.correlations.describe(name)` returns the same entry when the attrs are lost.

Passing the whole Terrace instead of its upper part shows how much of a dense sand falls outside these ranges:

``` { .text .no-copy }
UserWarning: effective_friction_angle_hatanaka_uchida_1996 gave no estimate for 21 of 33 rows (9 refusal, 12 above range; see 'correlation_note'). Its range is 4.55 ≤ (N1)60 ≤ 39; outside it the estimate is blank, never extrapolated.
UserWarning: effective_friction_angle_kulhawy_mayne_1990 gave no estimate for 12 of 33 rows (9 refusal, 3 above range; see 'correlation_note'). Its range is N60 ≤ 60; 0 < σ′v ≤ 300 kPa; outside it the estimate is blank, never extrapolated.
```

## Comparing estimates

Results from the same input concatenate with `pd.concat`, one row per test and correlation, and keep their units. `ht.plot.profile(..., color_by="correlation_name")` draws them together, and its footnote counts the blank estimates by their `correlation_note`: "9 refusals, no estimate", "12 above range, no estimate". The two correlations above differ by about 3° here; which to use, or how to combine them with measured values, is the engineer's call (stage D). [Drained shear strength of soil](../parameters/04-drained-shear-strength-soil.md) compares the methods.

## Scatter and advice

Every row also carries what its source says about the correlation's quality, so it travels with the estimate through a merge or a CSV, where `df.attrs` is lost:

| Column | What it holds |
|---|---|
| `correlation_data_count` | the n the source fit the correlation to |
| `correlation_r_squared` | the source's r² |
| `correlation_scatter` | the source's statement of its scatter, in its words, or "Not stated." |
| `correlation_advice` | the source's advice on use, quoted with its citation; or hangtu's own, marked "hangtu:"; blank where there is none |

Each is blank where the source states none, never 0. The example prints them for the two φ′ correlations above: Hatanaka & Uchida give "±3° for most of the data" and Kulhawy & Mayne no statistic, with GEC 5's caution about shallow depths as its advice.

Where a source gives a standard deviation in the target's terms, it goes on the rows as `<target>_correlation_standard_deviation`, in the target's units. Mayne & Kemper (σ′p, OCR) and Kulhawy et al. (K0) give one, but whether each is on arithmetic or log values is still being checked against the sources, so none is on the rows yet; until then it is in `correlation_scatter`. Checks of a correlation on other databases, such as Ching & Schweckendiek's (2021) for K0 (measured K0 averaged about twice the estimate), are in `ht.analysis.correlations.describe(name)["evaluations"]`, not on the rows: using them is part of selecting a value.

## Bands and PI

Some sources give a band rather than a value. Terzaghi & Peck (1967) give s_u by class of N; Stroud (1974), as FHWA GEC 5 gives it, gives f1 at PI ≳ 30 and PI ≅ 15 and nothing between. A correlation published as a band writes it in `<target>_lower` and `<target>_upper` and leaves the value blank where the source gives no central value: hangtu doesn't invent a midpoint.

Stroud also reads PI, which is rarely tested at the depth of an SPT. It is a judgment by geology unit (see [Judgments](judgments.md)): `ht.stats.describe()` shows what the Atterberg tests say, and `add_judgment()` puts the chosen value on the rows, from `value=` or the project's judgments file.

```python
--8<-- "correlations-clay.py"
```

``` { .text .no-copy }
--8<-- "correlations-clay.txt"
```

![Undrained shear strength against depth in B-3, as bands by correlation](../img/generated/correlations-clay.png){ width="440" }

PI 23.5 falls between GEC 5's two values, so Stroud gives the band 4.5 N60 to 5.5 N60 kPa; at PI 30 or more it gives the value 4.5 N60, and below 15 no estimate. Terzaghi & Peck read field N, Stroud N60: each reads the N it was derived with. `ht.plot.profile()` draws each band as a bar at its depth, the two correlations' bars for one test a little apart so neither hides the other, and the open top class of Terzaghi & Peck (N ≥ 30) as a caret ▷ at its lower bound. The footnote counts the rows shown as a range.

## Soil type

The correlations for clay (s_u, σ′p, OCR, K0) can read the soil type, if the rows carry a `uscs_symbol` column. hangtu doesn't derive USCS: the column is the user's, from the logs or the laboratory. With `uscs="proposed"`, a correlation gives no estimate outside the groups hangtu reads the source's words as (CL and CH for "clays"), with `not for this soil`, or where the symbol is blank, with `soil type unknown`. `describe(name)` gives the groups and why (`uscs`, `uscs_basis`); a list of groups, `uscs=["CL", "CH", "CL-ML"]`, replaces them. Run on the whole example profile, with `uscs_symbol` mapped from the geology units, the OCR correlation leaves out the Terrace sand:

``` { .text .no-copy }
UserWarning: overconsolidation_ratio_mayne_kemper_1988 gave no estimate for 33 of 65 rows (33 not for this soil; see 'correlation_note'). [...]
```

## Stiffness: the soil row and the strain level

Some sources give a coefficient by soil type. AASHTO (2004) gives E = C (N1)60 tsf with C = 4, 7, 10 or 12 for its
rows from silts to gravels; Kulhawy & Mayne (1990) give E/pa = C N60 with C = 5, 10 or 15 for sands with fines,
clean normally consolidated and clean overconsolidated sands. Which row a layer belongs to is the engineer's reading
of the log, so `soil=` is required: one row name for every test, or `{geology_unit: row}`. hangtu never infers it.
`uscs=` checks the row and never chooses it, because a USCS symbol can't tell a fine sand from a coarse one, or a
normally consolidated sand from an overconsolidated one. The row each test used is in `correlation_soil`.

The two Vs correlations, Imai & Tonouchi (1982) and Ohta & Goto (1978), are for all soils, in the 60 % forms Wair et
al. (2012) give for the sources' Japanese N.

```python
--8<-- "correlations-stiffness.py"
```

``` { .text .no-copy }
--8<-- "correlations-stiffness.txt"
```

![Drained Young's modulus and shear wave velocity against depth, by correlation](../img/generated/correlations-stiffness.png){ width="660" }

**Mind the strain level.** Both E correlations give a drained, working-strain secant modulus, the E for a settlement
estimate. Vs is a small-strain property: a G0 = ρVs² from it is far stiffer, and needs a reduction for strain
before it stands in for E. hangtu names the column for what it is (`drained_youngs_modulus`), so the two aren't
mixed up. AASHTO's constants are in tsf, as the source gives them; read as ksf they would halve E, so hangtu
converts them with pint. [Elastic stiffness](../parameters/08-elastic-stiffness-soil.md) and
[small-strain stiffness](../parameters/10-small-strain-stiffness.md) compare the methods.

## Chaining

A correlation's inputs are meant to be test data. When an input column holds another correlation's estimates (its rows carry that correlation's `correlation_name` and the input is its target), the call still runs, but warns once, naming the input and where it came from, and writes the upstream correlation to `correlation_input` on those rows. Chaining compounds the errors of both, and the result reads as more certain than it is. None of today's correlations reads another's target; the check is there for those that will, such as K0 from φ′ and OCR.

## See also

- [`ht.analysis.spt_n1_60`](../reference/analysis.md#hangtu.analysis.spt_n1_60), [`ht.analysis.add_judgment`](../reference/analysis.md#hangtu.analysis.add_judgment), [`ht.stats.describe`](../reference/stats.md#hangtu.stats.describe), [correlations reference](../reference/correlations.md)
- [Undrained shear strength](../parameters/05-undrained-shear-strength.md), [preconsolidation](../parameters/06-preconsolidation-and-compressibility.md), [at-rest earth pressure](../parameters/07-at-rest-earth-pressure.md), [elastic stiffness](../parameters/08-elastic-stiffness-soil.md) and [small-strain stiffness](../parameters/10-small-strain-stiffness.md): the methods compared
- [SPT analysis](spt.md): refusal, N60 and the energy ratio
- [Judgments and vertical stress](judgments.md): σ′v from the project's unit weights and water levels
