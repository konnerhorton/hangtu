# Plots

Every plot takes a DataFrame and returns `(fig, ax)`, an ordinary matplotlib figure and axes. Pass `ax=` to draw on an axes you already have, such as a panel of an `ht.Sheet`. A plot that runs an analysis returns its result too: `distribution_fit` returns `(fig, axs, result)`, `representative_profile` returns `(fig, ax, result)`, and `failure_envelope`, `triaxial_shearing`, `shear_box_envelope`, `hoek_brown_envelope` and `consolidation_curve` return `(fig, ax, fit)`. `consolidation_coefficients` draws two panels sharing an axis and returns `(fig, axs)`.

::: hangtu.plot.profile

::: hangtu.plot.spt_profile

::: hangtu.plot.spt_histogram

::: hangtu.plot.geology_unit_comparison

::: hangtu.plot.geology_unit_comparisons

::: hangtu.plot.plasticity_chart

::: hangtu.plot.clogging_diagram

::: hangtu.plot.grain_size

::: hangtu.plot.water_content_profile

::: hangtu.plot.distribution_fit

::: hangtu.plot.representative_profile

::: hangtu.plot.failure_envelope

::: hangtu.plot.triaxial_shearing

::: hangtu.plot.shear_box_envelope

::: hangtu.plot.hoek_brown_envelope

::: hangtu.plot.consolidation_curve

::: hangtu.plot.consolidation_coefficients

## Colors

::: hangtu.plot.legend_handles

::: hangtu.plot.palette_cmap

::: hangtu.plot.reset_palette

## Style

::: hangtu.plot.style
