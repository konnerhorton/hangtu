"""Session settings, available as ``ht.settings`` (docs/plots/P00-framework.md §3)."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from numbers import Real
from typing import Any

from matplotlib.colors import is_color_like

from hangtu import _config, vertical_datums
from hangtu.errors import HangtuError, HangtuHint, warn


def _display_units(value: Any) -> str:
    if value not in ("US", "SI"):
        raise HangtuError(
            f'settings.display_units must be "US" or "SI", not {value!r}. '
            'Example: ht.settings.display_units = "SI"'
        )
    return value


def _display_overrides(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(unit, str) for key, unit in value.items()
    ):
        raise HangtuError(
            "settings.display_overrides must be a dict of {quantity kind: unit}, "
            f"not {value!r}. "
            'Example: ht.settings.display_overrides = {"stress": "ksf"}'
        )
    if value:
        from hangtu import units  # imported here because units imports settings

        kinds = _config.quantity_kinds()
        for kind, unit in value.items():
            if kind not in kinds or kinds[kind]["canonical"] is None:
                convertible = [name for name in kinds if kinds[name]["canonical"]]
                raise HangtuError(
                    f"settings.display_overrides can't set a unit for {kind!r}. "
                    f"Quantity kinds with units: {', '.join(convertible)}."
                )
            try:
                units.check_dimension(units.parse_unit(unit), kind)
            except HangtuError as error:
                raise HangtuError(
                    f"settings.display_overrides[{kind!r}]: {error}"
                ) from None
    return dict(value)


def _vertical_datum(value: Any, hint: bool = True) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise HangtuError(
            f"settings.vertical_datum must be a datum name or None, not {value!r}. "
            'Example: ht.settings.vertical_datum = "NAVD88"'
        )
    short_name = vertical_datums.match(value)
    if short_name is not None:
        return short_name
    if hint and settings.hints:
        warn(
            f'Vertical datum "{value}" isn\'t in the datum table, so it is kept as '
            "written. If it is a named datum, add it with "
            f'ht.add_vertical_datum("<short name>", name="{value}") so its other '
            "spellings match it.",
            HangtuHint,
        )
    return value


def _palette(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HangtuError(
            "settings.palette must be a dict of {geology unit: color}, "
            f'not {value!r}. Example: ht.settings.palette = {{"Alluvium": "tan"}}'
        )
    bad = [unit for unit, color in value.items() if not is_color_like(color)]
    if bad:
        raise HangtuError(
            f"settings.palette has colors matplotlib doesn't recognize for {bad}. "
            'Use a color name ("tan"), a hex string ("#d2b48c") or an RGB tuple.'
        )
    return dict(value)


def _figure_sizes(value: Any) -> dict[str, tuple[float, float]]:
    example = (
        "Example: ht.settings.figure_sizes = "
        '{"default": (6.5, 4.5), "profile": (4.5, 6.0)}'
    )
    if not isinstance(value, dict) or "default" not in value:
        raise HangtuError(
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
            raise HangtuError(
                f"settings.figure_sizes[{kind!r}] must be (width, height) in inches, "
                f"both positive, not {size!r}. {example}"
            )
        sizes[kind] = (float(size[0]), float(size[1]))
    return sizes


def figure_size(kind: str) -> tuple[float, float]:
    """Return the settings size of a plot kind, else the ``default`` size.

    Each size is the whole figure in inches, legend and footnote included.
    """
    sizes = settings.figure_sizes
    return sizes.get(kind, sizes["default"])


def _hints(value: Any) -> bool:
    if not isinstance(value, bool):
        raise HangtuError(f"settings.hints must be True or False, not {value!r}.")
    return value


def _hammer_efficiency(value: Any) -> float | None:
    if value is not None and not (_is_number(value) and 0 < value <= 100):
        raise HangtuError(
            "settings.hammer_efficiency must be the energy ratio in percent, "
            f"greater than 0 and at most 100, or None, not {value!r}. "
            "Example: ht.settings.hammer_efficiency = 80"
        )
    return None if value is None else float(value)


def _spt_cap(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise HangtuError(
            "settings.spt_cap must be a positive whole number of blows, "
            f"not {value!r}. Example: ht.settings.spt_cap = 100"
        )
    return value


def _summary_min_count(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise HangtuError(
            "settings.summary_min_count must be a whole number of at least 1, "
            f"not {value!r}. Example: ht.settings.summary_min_count = 5"
        )
    return value


#: GEOL headings that can hold a layer's code (SPEC §8.3, datasets.md §5.1).
GEOLOGY_KEYS = ("GEOL_GEOL", "GEOL_GEO2", "GEOL_LEG", "GEOL_FORM", "GEOL_BGS")


def _geology_key(value: Any) -> str:
    if value not in GEOLOGY_KEYS:
        raise HangtuError(
            f"settings.geology_key must be one of {', '.join(GEOLOGY_KEYS)}, "
            f'not {value!r}. Example: p.settings.geology_key = "GEOL_FORM"'
        )
    return value


def _water_unit_weight(value: Any) -> str:
    from hangtu import units  # imported here because units imports settings

    example = 'Example: ht.settings.water_unit_weight = "62.4 pcf"'
    try:
        magnitude, _ = units.parse_quantity(value, "unit_weight")
    except HangtuError as error:
        raise HangtuError(
            "settings.water_unit_weight must be a unit weight with its unit, "
            f"not {value!r}: {error} {example}"
        ) from None
    if magnitude <= 0:
        raise HangtuError(
            f"settings.water_unit_weight must be positive, not {value!r}. {example}"
        )
    return value.strip()


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
    "summary_min_count": _summary_min_count,
    "geology_key": _geology_key,
    "water_unit_weight": _water_unit_weight,
}


#: Settings holding a quantity string; checked on assignment, not at import.
_QUANTITY_SETTINGS = ("water_unit_weight",)


def _unknown(name: str) -> str:
    return f"ht.settings has no setting {name!r}. Settings: {', '.join(_VALIDATORS)}."


def _defaults() -> dict[str, Any]:
    raw = _config.load("config/defaults.yaml")["settings"]
    # units imports settings, so a quantity setting can't be parsed while the
    # session settings are first built; tests/test_settings.py checks it.
    return {
        name: raw[name] if name in _QUANTITY_SETTINGS else validate(raw[name])
        for name, validate in _VALIDATORS.items()
    }


class Settings:
    """Session settings with attribute access.

    Every assignment is checked, and a bad value raises ``HangtuError`` saying
    what is allowed.

    Examples
    --------
    >>> ht.settings.display_units = "SI"
    >>> with ht.settings.override(display_units="US"):
    ...     fig, ax = ht.plot.profile(df, "hydraulic_conductivity")
    >>> ht.settings.reset()
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
    def _validate(name: str, value: Any, hint: bool = True) -> Any:
        """Check ``value``; ``hint=False`` reads a stored value back quietly."""
        try:
            validate = _VALIDATORS[name]
        except KeyError:
            raise HangtuError(_unknown(name)) from None
        if name == "vertical_datum":
            return _vertical_datum(value, hint)
        return validate(value)


settings = Settings()
