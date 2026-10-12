"""Session settings, available as ``ak.settings`` (docs/plots/P00-framework.md §3)."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from numbers import Real
from typing import Any

from matplotlib.colors import is_color_like

from hangtu import _config
from hangtu.errors import AgsKitError


def _display_units(value: Any) -> str:
    if value not in ("US", "SI"):
        raise AgsKitError(
            f'settings.display_units must be "US" or "SI", not {value!r}. '
            'Example: ak.settings.display_units = "SI"'
        )
    return value


def _display_overrides(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(unit, str) for key, unit in value.items()
    ):
        raise AgsKitError(
            "settings.display_overrides must be a dict of {quantity kind: unit}, "
            f"not {value!r}. "
            'Example: ak.settings.display_overrides = {"stress": "ksf"}'
        )
    if value:
        from hangtu import units  # imported here because units imports settings

        kinds = _config.quantity_kinds()
        for kind, unit in value.items():
            if kind not in kinds or kinds[kind]["canonical"] is None:
                convertible = [name for name in kinds if kinds[name]["canonical"]]
                raise AgsKitError(
                    f"settings.display_overrides can't set a unit for {kind!r}. "
                    f"Quantity kinds with units: {', '.join(convertible)}."
                )
            try:
                units.check_dimension(units.parse_unit(unit), kind)
            except AgsKitError as error:
                raise AgsKitError(
                    f"settings.display_overrides[{kind!r}]: {error}"
                ) from None
    return dict(value)


def _vertical_datum(value: Any) -> str | None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise AgsKitError(
            f"settings.vertical_datum must be a datum name or None, not {value!r}. "
            'Example: ak.settings.vertical_datum = "NAVD88"'
        )
    return value


def _palette(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AgsKitError(
            "settings.palette must be a dict of {geology unit: color}, "
            f'not {value!r}. Example: ak.settings.palette = {{"Alluvium": "tan"}}'
        )
    bad = [unit for unit, color in value.items() if not is_color_like(color)]
    if bad:
        raise AgsKitError(
            f"settings.palette has colors matplotlib doesn't recognize for {bad}. "
            'Use a color name ("tan"), a hex string ("#d2b48c") or an RGB tuple.'
        )
    return dict(value)


def _figure_sizes(value: Any) -> dict[str, tuple[float, float]]:
    example = (
        "Example: ak.settings.figure_sizes = "
        '{"default": (6.5, 4.5), "profile": (4.0, 6.5)}'
    )
    if not isinstance(value, dict) or "default" not in value:
        raise AgsKitError(
            "settings.figure_sizes must be a dict of {plot kind: (width, height)} "
            f'in inches that includes "default", not {value!r}. {example}'
        )
    sizes = {}
    for kind, size in value.items():
        if (
            not isinstance(size, list | tuple)
            or len(size) != 2
            or not all(_is_number(side) and side > 0 for side in size)
        ):
            raise AgsKitError(
                f"settings.figure_sizes[{kind!r}] must be (width, height) in inches, "
                f"both positive, not {size!r}. {example}"
            )
        sizes[kind] = (float(size[0]), float(size[1]))
    return sizes


def _hints(value: Any) -> bool:
    if not isinstance(value, bool):
        raise AgsKitError(f"settings.hints must be True or False, not {value!r}.")
    return value


def _hammer_efficiency(value: Any) -> float | None:
    if value is not None and not (_is_number(value) and 0 < value <= 100):
        raise AgsKitError(
            "settings.hammer_efficiency must be the energy ratio in percent, "
            f"greater than 0 and at most 100, or None, not {value!r}. "
            "Example: ak.settings.hammer_efficiency = 80"
        )
    return None if value is None else float(value)


def _spt_cap(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AgsKitError(
            "settings.spt_cap must be a positive whole number of blows, "
            f"not {value!r}. Example: ak.settings.spt_cap = 100"
        )
    return value


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


_VALIDATORS: dict[str, Callable[[Any], Any]] = {
    "display_units": _display_units,
    "display_overrides": _display_overrides,
    "vertical_datum": _vertical_datum,
    "palette": _palette,
    "figure_sizes": _figure_sizes,
    "hints": _hints,
    "hammer_efficiency": _hammer_efficiency,
    "spt_cap": _spt_cap,
}


def _unknown(name: str) -> str:
    return f"ak.settings has no setting {name!r}. Settings: {', '.join(_VALIDATORS)}."


def _defaults() -> dict[str, Any]:
    raw = _config.load("config/defaults.yaml")["settings"]
    return {name: validate(raw[name]) for name, validate in _VALIDATORS.items()}


class Settings:
    """Session settings with attribute access.

    Every assignment is checked, and a bad value raises ``AgsKitError`` saying
    what is allowed.

    Examples
    --------
    >>> ak.settings.display_units = "SI"
    >>> with ak.settings.override(display_units="US"):
    ...     fig, ax = ak.plot.profile(df, "hydraulic_conductivity")
    >>> ak.settings.reset()
    """

    __slots__ = ("_values",)

    def __init__(self) -> None:
        object.__setattr__(self, "_values", _defaults())

    def __getattr__(self, name: str) -> Any:
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(_unknown(name)) from None

    def __setattr__(self, name: str, value: Any) -> None:
        self._values[name] = self._validate(name, value)

    def __dir__(self) -> list[str]:
        return [*_VALIDATORS, "override", "reset"]

    def __repr__(self) -> str:
        lines = [f"    {name}={value!r}," for name, value in self._values.items()]
        return "Settings(\n" + "\n".join(lines) + "\n)"

    def reset(self) -> None:
        """Restore every setting to its default."""
        object.__setattr__(self, "_values", _defaults())

    @contextmanager
    def override(self, **values: Any) -> Iterator["Settings"]:
        """Change settings inside a ``with`` block, then restore them.

        The old values come back even if the block raises. If any new value is
        invalid, nothing is changed.
        """
        checked = {name: self._validate(name, value) for name, value in values.items()}
        saved = {name: self._values[name] for name in checked}
        self._values.update(checked)
        try:
            yield self
        finally:
            self._values.update(saved)

    @staticmethod
    def _validate(name: str, value: Any) -> Any:
        try:
            validate = _VALIDATORS[name]
        except KeyError:
            raise AgsKitError(_unknown(name)) from None
        return validate(value)


settings = Settings()
