# Correlations

Each correlation is a function named after its source, in `ht.analysis.correlations`. It reads the one input column it was derived with and returns a copy of the data with the estimate, `correlation_name` and `correlation_note`. Where it doesn't apply, the estimate is blank and `correlation_note` says why. Its equation, inputs, range and sources are in its docstring, below, and in `df.attrs["correlations"]`.

::: hangtu.analysis.correlations.hatanaka_uchida_1996

::: hangtu.analysis.correlations.kulhawy_mayne_1990

::: hangtu.analysis.correlations.describe
