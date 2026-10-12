import matplotlib.pyplot as plt
import pytest

import hangtu as ht


@pytest.mark.parametrize(
    ("size", "portrait"),
    [
        ("letter", (8.5, 11)),
        ("tabloid", (11, 17)),
        ("ANSI D", (22, 34)),
        ("a4", (8.27, 11.69)),
        ("A3", (11.69, 16.54)),
    ],
)
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_figure_size(size, portrait, orientation):
    expected = portrait if orientation == "portrait" else portrait[::-1]
    sheet = ht.Sheet(size, orientation=orientation)
    assert tuple(sheet.figure.get_size_inches()) == pytest.approx(expected)


def test_default_is_landscape_tabloid():
    assert tuple(ht.Sheet().figure.get_size_inches()) == (17, 11)


def test_margins_are_half_an_inch():
    sheet = ht.Sheet("letter", orientation="portrait")
    rect = sheet.figure.get_layout_engine().get()["rect"]
    assert rect == pytest.approx((0.5 / 8.5, 0.5 / 11, 1 - 1 / 8.5, 1 - 1 / 11))


def test_title_at_top_left():
    sheet = ht.Sheet(title="Site A")
    title = sheet.figure.get_suptitle()
    assert title == "Site A"
    text = sheet.figure._suptitle
    assert text.get_ha() == "left"
    assert text.get_fontsize() == 12
    assert text.get_fontweight() == "bold"


def test_panels_are_created_once_and_counted_row_by_row():
    sheet = ht.Sheet(layout=(2, 2))
    assert sheet[1] is sheet[0, 1]
    assert sheet[-1] is sheet[1, 1]
    assert len(sheet.figure.axes) == 2


def test_spanning_panel():
    sheet = ht.Sheet(layout=(2, 3))
    top = sheet[0, :]
    left = sheet[1, 0:2]
    assert sheet[0, 0:3] is top
    spec = top.get_subplotspec()
    assert (spec.rowspan, spec.colspan) == (range(0, 1), range(0, 3))
    assert left.get_subplotspec().colspan == range(0, 2)


def test_overlapping_panels_raise():
    sheet = ht.Sheet(layout=(2, 2))
    sheet[0, 1]
    with pytest.raises(ht.HangtuError, match=r"\[0, 0:2\] overlaps panel \[0, 1\]"):
        sheet[0, :]


@pytest.mark.parametrize(
    ("key", "message"),
    [
        (4, "Panel 4 doesn't exist: the layout has 4 panels"),
        ((2, 0), "Row 2 doesn't exist"),
        ((0, slice(1, 1)), "Column slice"),
        ("A", "Pick a panel"),
        (slice(0, 2), "Pick a panel"),
    ],
)
def test_bad_panel_keys(key, message):
    with pytest.raises(ht.HangtuError, match=message):
        ht.Sheet(layout=(2, 2))[key]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"size": "legal"}, "Sizes: letter, tabloid, ansi_d, a4, a3"),
        ({"orientation": "wide"}, '"landscape" or "portrait"'),
        ({"layout": (2, 0)}, r"\(rows, columns\)"),
        ({"layout": 4}, r"\(rows, columns\)"),
    ],
)
def test_bad_arguments(arguments, message):
    with pytest.raises(ht.HangtuError, match=message):
        ht.Sheet(**arguments)


@pytest.mark.parametrize("suffix", [".pdf", ".png", ".svg"])
def test_save(tmp_path, suffix):
    sheet = ht.Sheet("letter", layout=(1, 2), title="Site A")
    sheet[0].plot([0, 1], [0, 1])
    path = tmp_path / f"sheet{suffix}"
    sheet.save(path, dpi=50)
    assert path.stat().st_size > 0


def test_save_rejects_other_formats(tmp_path):
    with pytest.raises(ht.HangtuError, match=r"\.jpg.*\.pdf, \.png, \.svg"):
        ht.Sheet().save(tmp_path / "sheet.jpg")


def test_drawing_into_a_panel_adds_no_figure():
    sheet = ht.Sheet(layout=(1, 2))
    before = plt.get_fignums()
    sheet[0].plot([0, 1], [0, 1])
    assert plt.get_fignums() == before
