# SPT analysis

Find refusals, correct N to N60 and classify the tests.

```python
--8<-- "spt.py"
```

``` { .text .no-copy }
--8<-- "spt.txt"
```

## Refusal

A test is a refusal when `spt_refusal` says so. Where it is blank, a test is a refusal when its penetration, `spt_penetration`, is less than the full 450 mm (18 in). A refusal is never treated as a blank: plots draw it at the cap and count it.

## N60

N60 is the blow count corrected to 60% of the hammer's theoretical energy:

$$
N_{60} = N \, \frac{E_R}{60}
$$

where $N$ is the field blow count and $E_R$ is the energy ratio, in percent. $E_R$ comes from, in order:

1. the test's `energy_ratio` column (`ISPT_ERAT` in an AGS file);
2. `hammer_efficiency=` on the call: one number for every hole, or a value by hole, `hammer_efficiency={"BH01": 80, "BH02": 72}`. A hole not in the dict falls to the setting;
3. `ht.settings.hammer_efficiency`.

There is no default: with none of these, N60 stays blank. hangtu won't guess an energy ratio, because it varies widely from one hammer to another.

When the argument or the setting gives a test's energy ratio, a warning names the holes, the ratio and the number of tests, so an assumed value is never applied unnoticed. A hole in the dict that isn't in the data also warns, as a likely typo.

## The cap

`spt_n_capped` is N, limited to the cap, and every refusal is set to the cap. The cap is `cap=` on the call or `ht.settings.spt_cap`, 100 by default.

## Classes

`ht.analysis.spt_class()` classifies each test by relative density or consistency. Each class runs from its lower bound up to, not including, the next, so N = 10 is Medium dense:

| Cohesionless (`table="cohesionless"`) | N | Cohesive (`table="cohesive"`) | N |
|---|---|---|---|
| Very loose | < 4 | Very soft | < 2 |
| Loose | 4–10 | Soft | 2–4 |
| Medium dense | 10–30 | Medium stiff | 4–8 |
| Dense | 30–50 | Stiff | 8–15 |
| Very dense | ≥ 50 | Very stiff | 15–30 |
| | | Hard | ≥ 30 |

The tables are from Terzaghi & Peck (1948) and Peck, Hanson & Thornburn (1974). A refusal is "Refusal", whatever its N.

Which table applies is the engineer's call: select the rows it fits, such as the coarse soil, and pass only those. Choose `n=` too: the field N, N60 or capped N.

## See also

- [`ht.analysis.spt`](../reference/analysis.md#hangtu.analysis.spt), [`ht.analysis.spt_class`](../reference/analysis.md#hangtu.analysis.spt_class)
- [SPT profile](../plots/spt-profile.md), [SPT histogram](../plots/spt-histogram.md)
