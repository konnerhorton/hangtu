# 21 — Swelling of rock

| | |
|---|---|
| **Parameters** | εsw (free swell strain, %), swell rate (% per log cycle of time), σq0 / σ0 (maximum swelling stress, "suppression" or "critical" stress), kq (Grob swelling parameter, % per log cycle of stress), ηq (time parameter), direction (normal / parallel to bedding) |
| **Material** | Rock (argillaceous: shale, claystone, marl; clay-sulfate rock) |
| **Constitutive models that use it** | Swelling Rock model (PLAXIS UDSM, Wittke-Gattermann / Kiehl based); Lo & Hefny (1996) model; MC with imposed volumetric strain |
| **Depends on** | [02-index-properties](02-index-properties.md), [12-hydraulic-conductivity](12-hydraulic-conductivity.md) (rate of water access), [20-in-situ-stress-rock](20-in-situ-stress-rock.md) (stress relief), [23-slake-durability](23-slake-durability.md) |
| **Feeds** | Lining / invert design (outside this sheet set); [20-in-situ-stress-rock](20-in-situ-stress-rock.md) (time-dependent loads) |

## 1. Phenomenon
Argillaceous rock swells when excavation relieves stress and gives the rock access to water: osmotic / double-layer
water uptake by clay minerals (and, in clay-sulfate rock, the anhydrite → gypsum reaction) [3][4]. For purely
argillaceous rock the final swelling strain under oedometric conditions falls linearly with the logarithm of axial
stress and is zero above a maximum swelling stress (Grob's semi-logarithmic law) [3]; this law is not confirmed for
sulfatic claystones [3]. Swelling develops over months to decades and is commonly linear in log time. In bedded
shale it is orthotropic and strongly stress dependent: stress in one direction suppresses swell in that direction and
reduces it in the orthogonal directions [7]. The shales of southern Ontario (e.g. Queenston, Georgian Bay) show
time-dependent swelling after stress relief, anisotropic between layers, related to composition and clay fabric [6][8].

## 2. Units

| Parameter | SI | Imperial | Conversion |
|---|---|---|---|
| εsw, kq, swell rate | % (strain); % per log10 cycle (stress or time) | same | dimensionless |
| σq0 / σ0, swelling pressure | kPa (MPa) | psf; psi | 1 kPa = 20.885 psf = 0.1450 psi; 1 MPa = 145.04 psi (computed) |
| ηq | days (or years) | same | — |

## 3. Typical values

| Material | Range | Source |
|---|---|---|
| Purely argillaceous rock, oedometer | maximum swelling pressure and strain generally < 2 MPa and < 10 %; load stage often < 2 weeks | Madsen & Müller-Vonmoos (1989) via [3] p. 1273 [V] |
| Sulphatic claystone (anhydrite) | strain > 30 %, pressure ~8 MPa without reaching steady state; stages may take years | Pimentel (2003) via [3] p. 1273 [V] |
| Queenston shale (example FE input) | swelling potential vertical 0.525 %, horizontal 0.210 %; critical stress vertical 2070 kPa, horizontal 1600 kPa | [9] Table 1 [V] (units of "potential": per log cycle of time per the Lo & Hefny model [U]) |
| Southern Ontario shales | anisotropic; layers of one formation can differ greatly | [6] abstract [V] |

## 4. Tests

| Test | ASTM | ISO / BS (CSA) | AGS 4.2 group: headings | Delivers |
|---|---|---|---|---|
| Free swell (unconfined, or radially confined), strain vs time, by orientation | — (D4546-25 is for soils) | ISRM SM 1989 [4]; ISRM 1999 [5] | none for rock swell vs time (project user-defined group, e.g. "RSWL"); LSWL: LSWL_SWSI (Swelling Strain Index, %) | εsw(t), % per log cycle of time; normal and parallel to bedding |
| Maximum axial swelling stress (zero strain) | — | ISRM 1989 / 1999 [4][5] | LSWL: LSWL_SWPR (Swelling Pressure Index, kPa); CONG: CONG_SPRS (kPa) | σq0 (suppression stress) |
| Huder-Amberg multi-step oedometer (load–unload–reload, flood, unload stepwise to equilibrium) | — | ISRM 1999 [5]; ISO 17892-5 equipment | CONG: CONG_TYPE ("SWELL", "SWELLPRESS" abbreviations), CONG_SATH, CONG_SPRS; CONS: CONS_INCF, CONS_IVR, CONS_INCE | εq vs log σ → kq, σq0 |
| Semi-confined / null-swell tests (Lo et al.) | — | — | user-defined | Swell under constant stress; suppression stress |
| One-dimensional swell of soil (for weathered/ residual shale) | D4546-25 | BS 1377-5 [U] | CONG / CONS | Swell, swell pressure |

AGS units: LSWL_SWPR kPa, LSWL_SWSI %, CONG_SPRS kPa; LSWL_METH example "ISRM: Suggested method".

## 5. Derivations and correlations

### 5.1 Grob semi-logarithmic swelling law — Grob (1972)
$$\varepsilon_q^{i}(t=\infty) = -k_q^{i}\,\log_{10}\!\left(\frac{\sigma_i}{\sigma_{q0}^{i}}\right)\quad(\sigma_i \le \sigma_{q0}^{i};\ \text{zero above})$$
- **Inputs:** kq swelling parameter per log10 cycle of stress (%), σi axial stress in direction i, σq0 maximum swelling
  stress in that direction (both compression; PLAXIS sign convention uses −σ). Cut off at a small minimum stress
  (PLAXIS model: −10 kPa) to avoid unbounded swell [2].
- **Equivalent form:** ε = kq (1 − log10(σ/σ0)) is the same law with σ0 = σq0/10 (checked numerically). Confirm
  which reference stress a report means before using a "σ0" value.
- **Valid for:** purely argillaceous rock, oedometric (1D) tests [3]; applying it to anhydritic rock is debated [2][3].
- **Source:** [1] (original, not seen); [V] via [2] eq. 2, p. 48 and [3] p. 1272–1273. Einstein, Bischoff &
  Hofmann (1972) applied the same semi-log stress–strain relation to invert slabs in swelling shale [13] [U]; Wittke's
  formulation (Wittke 1978; 2014 Ch. 8) is the basis of the 3D law in §5.2 [14] [U].

### 5.2 Time dependence and 3D extension — Kiehl (1990); Wittke-Gattermann (1998)
$$\varepsilon_q(t) = \varepsilon_q(t=\infty)\left(1 - e^{-t/\eta_q}\right),\qquad \eta_q = 1/\left(A_0 + A_{el}\,\varepsilon_v^{el} + A_{pl}\,\varepsilon_v^{pl}\right)$$
- **Inputs:** ηq time parameter; A0, Ael, Apl depend on rock-mass permeability and swelling-layer thickness and usually
  cannot be derived from lab tests [2]. The 3D law applies Grob separately in each principal direction, with no
  interaction between directions [2]. A log(t) variant exists in later PLAXIS versions [U].
- **Source:** [V] via [2] eqs. 3–6, p. 48 (Kiehl 1990, Wittke-Gattermann 1998, Benz implementation).

### 5.3 Percent per log cycle of time (free swell)
$$\varepsilon_{sw}(t) = \varepsilon_{sw}(t_1) + S_t\,\log_{10}(t/t_1)$$
- **Inputs:** St swell rate (% per log cycle of time) by direction; t1 start of the linear part.
- **Valid for:** the linear log-time branch of free-swell tests on southern Ontario shales; Lo & Hefny (1996) combine
  St with a semi-log stress-suppression term similar to Grob [9] [U].
- **Source:** [U] (form inferred from the "% per log cycle" reporting convention; Lo & Hefny 1996 not seen).

## 6. Sensitivity in models

| Analysis | How the parameter enters | Sensitivity |
|---|---|---|
| Lining loads (resistance principle) | Rigid lining must carry pressure up to σq0 in the swelling direction | High: load set directly by σq0 and by the stress–strain curve near zero strain |
| Invert heave (yield principle / unsupported) | Strain at low stress (kq and σmin cut-off) × swelling-zone depth | High: semi-log law gives large strain at low stress |
| Time-dependence | ηq or % per log time; water access (k, drainage) | High for long-term loads; design life vs test duration |
| Anisotropy | Different kq, σq0 normal / parallel to bedding; tunnel orientation vs bedding | Moderate–high |
| Shafts and MTBM pipes in shale | Radial swell loads on shaft walls / pipe; invert heave of jacking pipes | Moderate–high |

**Typical variability:** no published COV located for kq or σq0. Swell data in shale vary strongly between layers of
one formation [6], so stratify by layer and orientation before statistics _[Judgment — for PE review]_. Long-term tests
may not reach a final state (especially sulfatic rock), so short tests under-estimate final swell [3].

## 7. Pitfalls and QA checks
- Record orientation (normal / parallel to bedding) for every result; do not pool directions.
- Check test duration: was the log-time line established, and was equilibrium reached at each Huder-Amberg stage?
- Distinguish "swelling pressure" (zero-strain stress, ISRM) from a suppression stress fitted to a log line.
- Check the swell-law parameterization (σq0 vs σ0 = σq0/10) and the logarithm base.
- Specimen disaggregation in free-swell tests (high clay, low saturation) invalidates strain readings [3].
- Pore-fluid chemistry (salinity, test fluid) changes swelling; record it.
- Do not apply Grob to anhydrite-bearing rock without explicit justification [2][3].

## References
[1] Grob, H. (1972). Schwelldruck im Belchentunnel. Proc. Int. Symp. für Untertagbau, Luzern, pp. 99–119. — [U] original not seen; page range [V] via [2], [3] reference lists
[2] Schädlich, B., Marcher, T. & Schweiger, H.F. (2013). Application of a constitutive model for swelling rock to tunnelling. Geotech. Eng. J. SEAGS & AGSSEA 44(3), 47–54. https://ph01.tci-thaijo.org/index.php/SEAGS_AGSSEA_Journal/article/view/259464 — [V] eqs. 2–6, p. 48
[3] Pimentel, E. & Anagnostou, G. (2013). New apparatus and experimental setup for long-term swelling tests on sulphatic claystones. Rock Mech. Rock Eng. 46(6). https://doi.org/10.1007/s00603-013-0396-5 (open copy https://doi.org/10.3929/ethz-b-000070389) — [V] pp. 1272–1276 (Grob law, free swell and Huder-Amberg tests, magnitudes)
[4] ISRM (1989). Suggested methods for laboratory testing of argillaceous swelling rocks (Commission on Swelling Rock; coord. H.H. Einstein). Int. J. Rock Mech. Min. Sci. & Geomech. Abstr. 26(5), 415–426. https://doi.org/10.1016/0148-9062(89)90937-6 — [V] citation; content [U]
[5] ISRM (1999). Suggested methods for laboratory testing of swelling rocks (coord. F.T. Madsen). Int. J. Rock Mech. Min. Sci. 36(3), 291–306. — [V] citation via [3]; content [V] only as summarised in [3]
[6] Lo, K.Y., Wai, R.S.C., Palmer, J.H.L. & Quigley, R.M. (1978). Time-dependent deformation of shaly rocks in southern Ontario. Can. Geotech. J. 15(4), 537–547. https://doi.org/10.1139/t78-057 — [V] abstract
[7] Lo, K.Y. & Lee, Y.N. (1990). Time-dependent deformation behaviour of Queenston shale. Can. Geotech. J. 27(4), 461–471. https://doi.org/10.1139/t90-061 — [V] abstract (orthotropic, stress dependent)
[8] Lee, Y.N. & Lo, K.Y. (1993). The swelling mechanism of Queenston shale. Proc. TAC Annual Conference, pp. 75–97. — [V] citation via [9]; content [U]
[9] Al-Maamori, H.M.S. & El Naggar, M.H. (2018). Performance of vertical shafts constructed in swelling shale using finite element method. GeoEdmonton 2018, CGS. https://members.cgs.ca/conferences/GeoEdmonton/papers/geo2018Paper252.pdf — [V] Table 1 and model description (Lo & Hefny 1996 ≈ Grob)
[10] Huder, J. & Amberg, G. (1970). Quellung in Mergel, Opalinuston und Anhydrit. Schweizerische Bauzeitung 88(43), 975–980. — [V] citation via [3]; content [U]
[11] Kiehl, J.R. (1990). Ein dreidimensionales Quellgesetz und seine Anwendung auf den Felshohlraumbau. Proc. 9. Nat. Felsmechanik Symp., Aachen, pp. 185–207. — [V] citation via [2]; content via [2]
[12] Einstein, H.H. (1996). Tunnelling in difficult ground — swelling behaviour and identification of swelling rocks. Rock Mech. Rock Eng. 29(3), 113–124. https://doi.org/10.1007/BF01032649 — [U] content
[13] Einstein, H.H., Bischoff, N. & Hofmann, E. (1972). Behaviour of invert slabs in swelling shale. Proc. Int. Symp. on Underground Openings, Lucerne. — [U] (citation not checked)
[14] Wittke, W. (2014). Rock Mechanics Based on an Anisotropic Jointed Rock Model (AJRM), Ch. 8 "Swelling Rock", pp. 181–208. Ernst & Sohn. https://doi.org/10.1002/9783433604281.ch8 — [V] citation (Crossref); content [U]
