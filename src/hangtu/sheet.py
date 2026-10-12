"""Multi-panel pages (docs/plots/P00-framework.md §13)."""

from os import PathLike
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from hangtu.errors import HangtuError

# Portrait width x height in inches.
SIZES = {
    "letter": (8.5, 11.0),
    "tabloid": (11.0, 17.0),
    "ansi_d": (22.0, 34.0),
    "a4": (8.27, 11.69),
    "a3": (11.69, 16.54),
}
ORIENTATIONS = ("landscape", "portrait")
MARGIN = 0.5  # inches
FORMATS = (".pdf", ".png", ".svg")

_Span = tuple[int, int, int, int]  # first row, end row, first column, end column


class Sheet:
    """A page of plot panels, saved as one PDF, PNG or SVG.

    Parameters
    ----------
    size
        ``"letter"``, ``"tabloid"``, ``"ansi_d"``, ``"a4"`` or ``"a3"``.
    layout
        ``(rows, columns)`` of the panel grid.
    title
        Text at the top left of the page.
    orientation
        ``"landscape"`` or ``"portrait"``.

    Examples
    --------
    >>> sheet = ak.Sheet("tabloid", layout=(2, 2), title="Site A")
    >>> ak.plot.profile(k, "hydraulic_conductivity", ax=sheet[0])
    >>> ak.plot.profile(su, "undrained_shear_strength", ax=sheet[1])
    >>> ak.plot.profile(w, "water_content", ax=sheet[1, :])  # a whole row
    >>> sheet.save("site_a.pdf")
    """

    def __init__(
        self,
        size: str = "tabloid",
        layout: tuple[int, int] = (1, 1),
        title: str | None = None,
        orientation: str = "landscape",
    ) -> None:
        key = str(size).lower().replace(" ", "_").replace("-", "_")
        if key not in SIZES:
            raise HangtuError(
                f"Sheet size {size!r} isn't available. Sizes: {', '.join(SIZES)}."
            )
        if orientation not in ORIENTATIONS:
            raise HangtuError(
                f'orientation must be "landscape" or "portrait", not {orientation!r}.'
            )
        if (
            not isinstance(layout, tuple)
            or len(layout) != 2
            or not all(isinstance(n, int) and n > 0 for n in layout)
        ):
            raise HangtuError(
                f"layout must be (rows, columns), two positive whole numbers, "
                f"not {layout!r}. Example: ak.Sheet(layout=(2, 2))"
            )
        width, height = SIZES[key]
        if orientation == "landscape":
            width, height = height, width
        self.rows, self.columns = layout
        self.figure: Figure = plt.figure(figsize=(width, height), layout="constrained")
        self.figure.get_layout_engine().set(
            rect=(
                MARGIN / width,
                MARGIN / height,
                1 - 2 * MARGIN / width,
                1 - 2 * MARGIN / height,
            )
        )
        self._grid = self.figure.add_gridspec(self.rows, self.columns)
        self._panels: dict[_Span, Axes] = {}
        self._owner: dict[tuple[int, int], _Span] = {}
        if title:
            self.figure.suptitle(
                title, x=MARGIN / width, ha="left", fontsize=12, fontweight="bold"
            )

    def __getitem__(self, key: int | tuple[int | slice, int | slice]) -> Axes:
        """Return the panel at ``key``, creating it on first access.

        ``sheet[i]`` counts panels row by row; ``sheet[r, c]`` picks one cell;
        slices span cells, e.g. ``sheet[0, :]`` for the whole first row.
        """
        span = self._span(key)
        if span in self._panels:
            return self._panels[span]
        cells = [
            (r, c) for r in range(span[0], span[1]) for c in range(span[2], span[3])
        ]
        taken = {self._owner[cell] for cell in cells if cell in self._owner}
        if taken:
            raise HangtuError(
                f"Panel {_describe(span)} overlaps panel {_describe(min(taken))}, "
                "which already exists. Each part of the sheet can be in one panel."
            )
        ax = self.figure.add_subplot(self._grid[span[0] : span[1], span[2] : span[3]])
        self._panels[span] = ax
        self._owner.update(dict.fromkeys(cells, span))
        return ax

    def _span(self, key: object) -> _Span:
        if isinstance(key, int) and not isinstance(key, bool):
            count = self.rows * self.columns
            index = key + count if key < 0 else key
            if not 0 <= index < count:
                raise HangtuError(
                    f"Panel {key} doesn't exist: the layout has {count} panels, "
                    f"numbered 0 to {count - 1} row by row."
                )
            row, column = divmod(index, self.columns)
            return row, row + 1, column, column + 1
        if isinstance(key, tuple) and len(key) == 2:
            rows = _range(key[0], self.rows, "row")
            columns = _range(key[1], self.columns, "column")
            return rows + columns
        raise HangtuError(
            f"Pick a panel with a number or [row, column], not {key!r}. "
            "Examples: sheet[0], sheet[1, 0], sheet[0, :] for a whole row."
        )

    def save(self, path: str | PathLike[str], dpi: int = 300) -> None:
        """Save the sheet. The format comes from the extension: .pdf, .png or .svg."""
        suffix = Path(path).suffix.lower()
        if suffix not in FORMATS:
            raise HangtuError(
                f"Can't save a sheet as {suffix or 'a file without an extension'}. "
                f"Use {', '.join(FORMATS)}, e.g. sheet.save('site_a.pdf')."
            )
        self.figure.savefig(path, dpi=dpi)


def _range(index: int | slice, count: int, name: str) -> tuple[int, int]:
    if isinstance(index, slice):
        start, stop, step = index.indices(count)
        if step == 1 and start < stop:
            return start, stop
    elif isinstance(index, int) and not isinstance(index, bool):
        position = index + count if index < 0 else index
        if 0 <= position < count:
            return position, position + 1
    raise HangtuError(
        f"{name.capitalize()} {index!r} doesn't exist: the layout has {count} "
        f"{name}s, numbered 0 to {count - 1}."
    )


def _describe(span: _Span) -> str:
    def part(start: int, stop: int) -> str:
        return str(start) if stop == start + 1 else f"{start}:{stop}"

    return f"[{part(span[0], span[1])}, {part(span[2], span[3])}]"
