# Correlations

Each correlation is a function in `ht.analysis.correlations`, named after the property it estimates and its source (`<target>_<authors>_<year>`). It reads the one input column it was derived with and returns a copy of the data with the estimate, `correlation_name` and `correlation_note`; a correlation published as a band gives `<target>_lower` and `<target>_upper` too. Where it doesn't apply, the estimate is blank and `correlation_note` says why. Its equation, inputs, range and sources are in its docstring, below, and in `df.attrs["correlations"]`.

::: hangtu.analysis.correlations.effective_friction_angle_hatanaka_uchida_1996

::: hangtu.analysis.correlations.effective_friction_angle_kulhawy_mayne_1990

::: hangtu.analysis.correlations.undrained_shear_strength_stroud_1974

::: hangtu.analysis.correlations.undrained_shear_strength_terzaghi_peck_1967

::: hangtu.analysis.correlations.describe
