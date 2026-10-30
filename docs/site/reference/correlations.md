# Correlations

Each correlation is a function in `ht.analysis.correlations`, named after the property it estimates and its source (`<target>_<authors>_<year>`). It reads the one input column it was derived with and returns a copy of the data with the estimate, `correlation_name`, `correlation_note` and `correlation_input` (the correlation an input came from, where one did); a correlation published as a band gives `<target>_lower` and `<target>_upper` too. Every row also carries the source's statistics and advice: `correlation_data_count` (its n), `correlation_r_squared`, `correlation_scatter` (its own words) and `correlation_advice`, blank where the source states none. Where it doesn't apply, the estimate is blank and `correlation_note` says why. Its equation, inputs, range and sources are in its docstring, below, and in `df.attrs["correlations"]`.

::: hangtu.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996

::: hangtu.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990

::: hangtu.analysis.correlations.undrained_shear_strength_stroud_1974

::: hangtu.analysis.correlations.undrained_shear_strength_terzaghi_peck_1967

::: hangtu.analysis.correlations.preconsolidation_stress_mayne_kemper_1988

::: hangtu.analysis.correlations.overconsolidation_ratio_mayne_kemper_1988

::: hangtu.analysis.correlations.at_rest_earth_pressure_coefficient_kulhawy_et_al_1989

::: hangtu.analysis.correlations.drained_youngs_modulus_aashto_2004

::: hangtu.analysis.correlations.drained_youngs_modulus_kulhawy_mayne_1990

::: hangtu.analysis.correlations.shear_wave_velocity_imai_tonouchi_1982

::: hangtu.analysis.correlations.shear_wave_velocity_ohta_goto_1978

::: hangtu.analysis.correlations.describe
