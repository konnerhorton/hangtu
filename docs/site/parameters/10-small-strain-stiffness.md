# Small-strain stiffness

| | |
|---|---|
| **Parameters** | Vs (shear wave velocity), G0 = Gmax (small-strain shear modulus), γref and γ0.7 (reference shear strains) |
| **Material** | Soil (Vs is also measured in rock) |
| **Models that use it** | HS-small (G0ref, γ0.7); site response; E0 for an equivalent modulus with a strain reduction |
| **Depends on** | [Unit weight and vertical stress](01-unit-weight-and-vertical-stress.md) (ρ, σ′); [preconsolidation](06-preconsolidation-and-compressibility.md) (OCR) |
| **Feeds** | [Elastic stiffness](08-elastic-stiffness-soil.md) (E from G0 with a strain reduction); site response |

## What it is

Below a very small shear strain, soil is close to linear elastic, with its largest shear stiffness G0. G0 is set by
void ratio, mean effective stress, stress history and fabric, and is best measured in place by the shear wave
velocity (Loehr et al. 2016, §8.4, p. 8-5):

$$
G_0 = \rho \, V_s^2, \qquad \rho = \gamma_t / g, \qquad E_0 = 2 G_0 (1 + \nu)
$$

(Loehr et al. 2016, Eqs. 8.1 and 8.4). Shear waves don't propagate through fluids, so Vs in a saturated soil is
"largely unaffected by the presence of water" and measures the skeleton (§8.2, p. 8-3; §8.4, p. 8-6). Beyond the elastic threshold, the secant modulus falls along an S-shaped curve with log strain; plasticity
and confining stress move the curve to larger strains. γref is the strain at G/G0 = 0.5, and γ0.7, used by
HS-small, the strain at G/G0 = 0.722.

## Why it matters to a design

| Analysis | How it enters | Sensitivity |
|---|---|---|
| Site response, vibration | Vs profile, G0 and G/G0 curves directly | High |
| Numerical models, HS-small | G0ref and γ0.7 set the stiffness at small strains away from the works | High for far-field movements and trough width |
| Numerical models, Mohr–Coulomb | E0 only after a reduction for strain ([elastic stiffness](08-elastic-stiffness-soil.md)) | High if E0 is used unreduced: displacements too small |
| Limit equilibrium stability | not used | Low |

## Units

| Parameter | SI | US customary | Conversion |
|---|---|---|---|
| Vs | m/s | ft/s | 1 m/s = 3.2808 ft/s |
| ρ | Mg/m³ | pcf (lb/ft³) | 1 Mg/m³ = 62.43 lb/ft³; ρ = γt / g |
| G0 | MPa | ksf, psi | 1 MPa = 20.885 ksf = 145.04 psi |
| γref, γ0.7 | – | – | strain, often quoted in % (1 × 10⁻⁴ = 0.01 %) |

For example, ρ = 2.0 Mg/m³ and Vs = 200 m/s (656 ft/s) give G0 = 80 MPa (computed).

## Typical values

| Material | Range | Source |
|---|---|---|
| γref (static), 21 clays and silts, 67 tests | 0.00036–0.0021 (averages by test series) | Vardanega & Bolton (2014), Table 1 |
| γ0.7 from PI by Vardanega & Bolton, PI = 10, 20, 30, 50 % | 0.61, 1.21, 1.82, 3.03 × 10⁻⁴ | computed from Vardanega & Bolton (2014), Eqs. 1a–1b |
| Gmax / E_D (dilatometer), sands | 2.72 ± 0.59 (calibration chamber); 2.2 ± 0.7 (field) | Loehr et al. (2016), Table 8-9 |

## Tests

| Test | ASTM | ISO / BS | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Crosshole seismic | D4428/D4428M | – | `ISTA`: `ISTA_WVL`, `ISTA_WVTY` | Vs and Vp by depth |
| Downhole seismic; seismic CPT or DMT | D7400/D7400M | ISO 22476-1, -11 (CPT, DMT) | `ISTA` as above | interval Vs |
| Surface waves (SASW, MASW) | – | – | none in AGS 4.2 | a Vs profile by inversion; resolution falls with depth |
| Bender elements; resonant column | D8295; D4015 | – | `LDYN`; `RESG`, `RESD`, `RESP` | laboratory G0, lowered by disturbance; G/G0 to about 0.1 % |
| SPT (correlation input) | D1586/D1586M | ISO 22476-3 | `ISPT`: `ISPT_NVAL` | N, for the correlations below |

## Methods

| Method | Uses | Applies to | Function |
|---|---|---|---|
| Imai & Tonouchi (1982), Vs = 93.7 N60^0.31 m/s, in Wair et al.'s (2012) 60 % form | N60 | all soils; 0 < N60 ≤ 447 | [`ht.analysis.correlations.shear_wave_velocity_imai_tonouchi_1982()`](../reference/correlations.md#hangtu.analysis.correlations.shear_wave_velocity_imai_tonouchi_1982) |
| Ohta & Goto (1978), Vs = 82.1 N60^0.35 m/s, in Wair et al.'s (2012) 60 % form | N60 | Quaternary soils; 2.23 ≤ N60 ≤ 223 | [`ht.analysis.correlations.shear_wave_velocity_ohta_goto_1978()`](../reference/correlations.md#hangtu.analysis.correlations.shear_wave_velocity_ohta_goto_1978) |
| G0 = ρ Vs² (Loehr et al. 2016, Eq. 8.1) | Vs, γt | all soils | W5 |
| Hardin-type G0 from void ratio and mean stress (Loehr et al. 2016, Eqs. 8.7–8.10) | e, σ′m, OCR, PI | soils like those tested | W5 |
| γref from PI, Vardanega & Bolton (2014), Eqs. 1a–2b | PI | clays and silts | W5 |
| Vs from CPT (Loehr et al. 2016, Table 8-8) | q_t | by soil, per the source | later |

Wair et al. converted both SPT correlations from the sources' Japanese N, assuming the 67 % energy typical of
Japanese practice. FHWA GEC 5 repeats them in its Table 8-5, but its notes column is shifted a row against Wair et
al.'s table: it labels Imai & Tonouchi's all-soils equation "Tertiary" and Ohta & Goto's Quaternary one
"Holocene". hangtu follows Wair et al. The equations, ranges and sources are in the reference entries.

## How the methods compare

Measured Vs is the basis wherever there is one; the SPT correlations are for when there isn't. They give a
small-strain value: a G0 or E0 from them is far stiffer than a working-strain modulus, and needs a reduction for
strain before it stands in for one ([elastic stiffness](08-elastic-stiffness-soil.md)). The two SPT correlations
are close at moderate N: at N60 = 10, 191 m/s (Imai & Tonouchi) and 184 m/s (Ohta & Goto) (computed). Choosing a
design value is stage D (M18).

## Variability

- Imai & Tonouchi (1982): n = 1654 pairs from 386 borings at 250 sites in Japan, r² = 0.75; Ohta & Goto (1978):
  289 pairs, r² = 0.52 (Wair et al. 2012, §4.1.2–4.1.3 and Table 4.2).
- Through G0 ∝ Vs², a 10 % error in Vs is about 21 % in G0 (computed).
- Gmax / E_D for sands: COV about 22 % (calibration chamber) and 32 % (field), from Loehr et al. (2016), Table 8-9
  (computed).

## Pitfalls

- Use the total density in ρ = γt / g, not the dry or buoyant one.
- Laboratory G0 (bender elements, resonant column) is usually lower than field G0, because of disturbance.
- γref (G/G0 = 0.5) is not γ0.7 (G/G0 = 0.722): convert before entering HS-small.
- Don't use G0 or E0 as a design E without a reduction for strain.
- Downhole Vs at depth, and surface-wave Vs in thin deep layers, are less reliable.
- The SPT correlations read N60. hangtu raises if the column isn't there, and never corrects field N into it.

## References

- Imai, T. and Tonouchi, K. (1982). Correlation of N value with S-wave velocity and shear modulus. *Proceedings of
  the 2nd European Symposium on Penetration Testing*, Amsterdam, 67–72.
- Loehr, J.E., Lutenegger, A., Rosenblad, B. and Boeckmann, A. (2016). *Geotechnical Site Characterization.*
  Geotechnical Engineering Circular No. 5, FHWA NHI-16-072.
  <https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi16072.pdf>
- Ohta, Y. and Goto, N. (1978). Empirical shear wave velocity equations in terms of characteristic soil indexes.
  *Earthquake Engineering and Structural Dynamics* 6(2), 167–187. <https://doi.org/10.1002/eqe.4290060205>
- Vardanega, P.J. and Bolton, M.D. (2014). Stiffness of clays and silts: modeling considerations. *Journal of
  Geotechnical and Geoenvironmental Engineering* 140(6), 06014004.
  <https://doi.org/10.1061/(ASCE)GT.1943-5606.0001104>
- Wair, B.R., DeJong, J.T. and Shantz, T. (2012). *Guidelines for Estimation of Shear Wave Velocity Profiles.*
  PEER Report 2012/08, Pacific Earthquake Engineering Research Center.
  <https://peer.berkeley.edu/sites/default/files/webpeer-2012-08-bernard_r._wair_jason_t._dejong_and_thomas_shantz.pdf>
