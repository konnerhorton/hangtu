"""Plot presets (docs/plots/P01-property-profile.md §6, plots README "Presets")."""

from dataclasses import dataclass

from ags_kit import _config
from ags_kit.errors import AgsKitError


@dataclass(frozen=True)
class Preset:
    """Named settings for plotting a common quantity.

    ``typical`` is in the quantity's canonical unit (the % value for percent).
    It only sets default axis limits when the data are sparse.
    """

    name: str
    column: str
    label: str
    quantity: str
    log: bool
    start_at_zero: bool
    typical: tuple[float, float]


def _presets() -> dict[str, dict]:
    return _config.load("config/defaults.yaml")["presets"]


def preset_names() -> list[str]:
    """Return the names of the shipped presets."""
    return list(_presets())


def preset(name: str) -> Preset:
    """Return the preset called ``name``.

    Raises ``AgsKitError`` listing the presets when there is no such preset.
    """
    entries = _presets()
    if name not in entries:
        raise AgsKitError(
            f"There is no preset named {name!r}. Presets: {', '.join(entries)}. "
            'Example: preset="hydraulic_conductivity"'
        )
    entry = entries[name]
    low, high = entry["typical"]
    return Preset(
        name=name,
        column=entry["column"],
        label=entry["label"],
        quantity=entry["quantity"],
        log=entry["log"],
        start_at_zero=entry["start_at_zero"],
        typical=(float(low), float(high)),
    )
