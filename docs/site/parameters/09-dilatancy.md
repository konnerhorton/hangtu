# Dilatancy

| | |
|---|---|
| **Parameters** | ψ (dilatancy angle) of soil; I_R (Bolton's relative dilatancy index) |
| **Material** | Soil (rock masses: later, with the Hoek–Brown set) |
| **Models that use it** | Mohr–Coulomb (non-associated flow), Hardening Soil and HS-small (with a dilatancy cut-off) |
| **Depends on** | [Drained shear strength](04-drained-shear-strength-soil.md) (φ′, φ′cv); [specific gravity and void ratio](03-specific-gravity-and-void-ratio.md) (relative density) |
| **Feeds** | the Mohr–Coulomb set ([selection](../guides/selection.md#model-sets)) |

## What it is

Dilatancy is the plastic increase in volume that comes with shearing a dense soil: the grains have to ride over one
another. The dilatancy angle ψ is the angle of the plastic strain increment, the rate of volume change against the
rate of shear strain. It is smaller than φ′: ψ = φ′ would be associated flow, which overstates the volume increase,
and the Mohr–Coulomb model is non-associated for that reason (Vermeer & de Borst 1984).

In a sand, ψ grows with relative density and falls with mean effective stress, and it is zero at the critical
state, where the soil shears at constant volume. The same dilatancy makes the peak φ′ larger than the critical
state angle φ′cv, which is why ψ can be estimated from the two (Bolton 1986). A very dense sand has a ψ of about
15° and a loose sand a few degrees, and "normally consolidated clays show no dilatancy at all" (Vermeer & de Borst
1984, p. 13). ψ isn't constant in reality: a constant ψ in a model is a simplification that lets the soil dilate
without limit.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Drained numerical models in sand (Mohr–Coulomb, Hardening Soil) | volume change in the plastic zones; arching around a tunnel or an excavation | Moderate: a ψ above 0 reduces settlement and raises the load a footing or anchor takes |
| Undrained analyses in effective stress | a ψ above 0 drives the pore pressure down without limit, so the strength keeps rising | High, and a pitfall: use ψ = 0 or a dilatancy cut-off |
| Limit analysis (bearing capacity, face stability) | upper-bound solutions assume associated flow, ψ = φ′ | Moderate: non-associated flow gives a lower capacity |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| ψ | degrees (°) | degrees (°) | 1 rad = 57.2958° |
| I_R | – | – | dimensionless |

## Typical values

| Material | Range | Source |
|---|---|---|
| Very dense sand | ψ about 15° | Vermeer & de Borst (1984), p. 13 |
| Loose sand | a few degrees | Vermeer & de Borst (1984), p. 13 |
| Normally consolidated clay | 0 | Vermeer & de Borst (1984), p. 13 |
| Clean quartz sand at p′ = 100 kPa, Dr 50 % and 80 % | ψ about 6° and 12° (triaxial compression) | computed from Kulhawy & Mayne (1990), Eqs. 4-5 and 4-6, p. 4-10, and Eq. 4-16, p. 4-20 |

The computed sand values take I_R = Dr (10 − ln p′) − 1, φ′ − φ′cv = 3 I_R and ψ = (φ′ − φ′cv) / 0.8.

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Drained triaxial (CD) with volume change | D7181 | ISO 17892-9; BS 1377-8 | `TREG`: `TREG_TYPE`; `TRET`: `TRET_STV`, `TRET_STRN`, `TRET_DEVF` | the rate of volume change at peak, from the full curves, not only the values at failure |
| Direct shear with vertical displacement | D3080/D3080M | ISO 17892-10; BS 1377-7 | `SHBT`: `SHBT_PDIN`, `SHBT_PDIS`, `SHBT_NORM` | tan ψ ≈ −δy/δx at peak |
| Pressuremeter in sand | D4719 | ISO 22476-4, -6 | `PMTP`: `PMTP_AD` | ψ from the expansion curve |

hangtu doesn't read ψ from test curves yet.

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Bolton's relation, as Kulhawy & Mayne (1990) give it, Eq. 4-16, p. 4-20 | the selected φ′ and φ′cv (a judgment) | coarse-grained units, φ′ − φ′cv up to 12° | the Mohr–Coulomb set, [`ht.stats.mohr_coulomb_set()`](../reference/stats.md#hangtu.stats.mohr_coulomb_set) |
| ψ = 0 (Vermeer & de Borst 1984, p. 13) | — | fine-grained units, normally consolidated | the Mohr–Coulomb set |
| A selected value | your value, with its reason | any unit | the `selection` judgment, read by [`ht.stats.select()`](../reference/stats.md#hangtu.stats.select) |
| Bolton (1986) from relative density, I_R = Dr (10 − ln p′) − 1 (Kulhawy & Mayne 1990, Eqs. 4-5 to 4-7, p. 4-10) | Dr, p′ at failure in kPa | clean quartz and feldspar sands | later |
| From the test curves (definition) | the plastic strain increments | CD triaxial, direct shear | later |

Bolton's relation is the one the set applies to a coarse unit:

$$
\phi'_{tc} = \phi'_{cv} + 0.8\,\psi \quad\Rightarrow\quad \psi = \frac{\phi' - \phi'_{cv}}{0.8}
$$

- **φ′** is the unit's selected φ′, from the same set, and **φ′cv** the
  [`critical_state_friction_angle`](../guides/judgments.md#the-critical-state-friction-angle) judgment, the one the
  shear box conversion reads.
- **A φ′ below φ′cv** gives ψ = 0, with a note giving the negative value the relation would give. A cautious φ′ at or
  below φ′cv is a normal case, so it doesn't warn.
- **The limit:** the relation was drawn from sands with I_R up to 4, and Kulhawy & Mayne (1990, p. 4-10) say I_R
  "should be limited to 4 unless detailed laboratory test data indicate otherwise". In triaxial compression that is
  φ′ − φ′cv = 3 I_R = 12°, where ψ = 15°. Beyond it, ψ is blank with the reason and a warning, never clipped to 15°:
  give ψ as a selection.
- **The stress condition.** Kulhawy & Mayne write the relation with the triaxial compression φ′, the basis of
  hangtu's φ′ (the shear box conversion targets it too). Other secondary sources give the same 0.8 for plane strain,
  with 5 I_R in place of 3 I_R, and Bolton's paper hasn't been checked for which it states. The value ψ =
  (φ′ − φ′cv) / 0.8 is the same in every reading; only the limit would differ.

A **fine** unit gets ψ = 0. An overconsolidated clay may dilate (Obrzud & Truty 2018, p. 107); give its ψ as a
selection. A unit whose `soil_class` is `fill`, `rock`, `organic`, blank or anything other than `coarse` or `fine`
is an error asking for a selected ψ: guessing would put a rule where only you can judge.

## How the methods compare

A ψ measured on the unit's own soil, from the volume change of drained tests, overrules a relation. Until hangtu
reads one, give it as a selection. Bolton's relation is the next best: it ties ψ to the φ′ you selected and the φ′cv
you judged, so the two can't drift apart. Its value is only as good as φ′ − φ′cv, and it moves 1.25° for each
degree of either. The common rule of thumb ψ = φ′ − 30° is Bolton's relation with φ′cv fixed at 30° and the factor
left out, so hangtu doesn't offer it.

The relation is for a peak φ′. A cautious selected φ′, such as a characteristic value, gives a smaller ψ than the
peak would, and the set's provenance shows which φ′ it used.

## Variability

No coefficient of variation is commonly published for ψ. Derived from φ′ and φ′cv, it carries their uncertainty,
amplified by 1/0.8: an uncertainty of ±2° in φ′ is ±2.5° in ψ, on a value of 0 to 15°.

## Pitfalls

- ψ must be smaller than φ′.
- Take a peak ψ with a peak φ′. With φ′cv as the design angle (large strains, progressive failure), take ψ = 0.
- A constant ψ dilates without limit. Use a dilatancy cut-off where the model has one (Hardening Soil).
- An undrained analysis in effective stress with ψ above 0 overstates the strength.
- Bolton's I_R: p′ in kPa, I_R limited to 4. hangtu leaves ψ blank beyond the limit rather than clipping it.
- Reading ψ from a triaxial test needs the full volume change record, not only `TRET_STV` at failure.

## References

- Bolton, M.D. (1986). The strength and dilatancy of sands. *Géotechnique* 36(1), 65–78.
  <https://doi.org/10.1680/geot.1986.36.1.65>
- Kulhawy, F.H. and Mayne, P.W. (1990). *Manual on Estimating Soil Properties for Foundation Design.* EPRI EL-6800,
  Electric Power Research Institute. <https://restservice.epri.com/publicdownload/EL-6800/0/Product>
- Obrzud, R.F. and Truty, A. (2018). *The Hardening Soil Model: A Practical Guidebook.* Z_Soil.PC 100701 report,
  revised 21.10.2018, Zace Services.
- Vermeer, P.A. and de Borst, R. (1984). Non-associated plasticity for soils, concrete and rock. *Heron* 29(3),
  1–64.
