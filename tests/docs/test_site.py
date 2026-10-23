"""The docs site (docs/work/docs-site.md, Spec §8)."""

import importlib.util
import inspect
import re
import tomllib
from pathlib import Path

import pytest

import hangtu as ht

ROOT = Path(__file__).parents[2]
EXAMPLES = sorted((ROOT / "docs" / "site" / "examples").glob("*.py"))


def _load_prepare_site():
    script = ROOT / "docs" / "prepare_site.py"
    spec = importlib.util.spec_from_file_location("prepare_site", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare_site = _load_prepare_site()


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda path: path.name)
def test_page_example_runs_clean(tmp_path, script):
    # Criterion 3: each example runs in an empty folder after installing hangtu.
    done = prepare_site.run_example(script, tmp_path)
    assert done.returncode == 0, done.stderr
    assert done.stderr == ""  # no warning, no traceback
    if "savefig(" in script.read_text(encoding="utf-8"):
        assert (tmp_path / f"{script.stem}.png").is_file()


def _drawn(lines):
    characters = "".join(lines)
    marks = characters.count("=") + characters.count(":")
    letters = len(characters) - marks - characters.count(" ")
    return 2 * marks, letters


def test_logo_svgs_draw_every_character(tmp_path, monkeypatch):
    # Criterion 6: two shapes for each "=" or ":", one outline per letter,
    # and no text, so no font is needed.
    monkeypatch.setattr(prepare_site, "GENERATED", tmp_path)
    monkeypatch.setattr(prepare_site, "WORDMARK", tmp_path / "wordmark.svg")
    prepare_site.write_logo()
    wordmark, small_mark = prepare_site.logo_marks()
    for name, lines in [
        ("logo.svg", small_mark),
        ("favicon.svg", small_mark),
        ("wordmark.svg", wordmark),
    ]:
        svg = (tmp_path / name).read_text(encoding="utf-8")
        rects, letters = _drawn(lines)
        assert svg.count("<rect ") == rects, name
        assert svg.count("<path ") == letters, name
        assert "<text" not in svg


def test_committed_wordmark_is_current(tmp_path, monkeypatch):
    # The README links to the committed wordmark, so it must match logo.txt.
    monkeypatch.setattr(prepare_site, "GENERATED", tmp_path)
    monkeypatch.setattr(prepare_site, "WORDMARK", tmp_path / "wordmark.svg")
    prepare_site.write_logo()
    committed = ROOT / "docs" / "site" / "img" / "wordmark.svg"
    assert committed.read_text(encoding="utf-8") == (
        tmp_path / "wordmark.svg"
    ).read_text(encoding="utf-8"), "run docs/prepare_site.py and commit the result"


def test_readme_opens_with_the_wordmark():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith('<img src="https://raw.githubusercontent.com/')
    assert readme.splitlines()[0].count("docs/site/img/wordmark.svg") == 1


def _documented():
    pages = (ROOT / "docs" / "site" / "reference").glob("*.md")
    text = "\n".join(page.read_text(encoding="utf-8") for page in pages)
    return set(re.findall(r"^::: (\S+)", text, flags=re.MULTILINE))


# Exported but not documented, with the reason.
UNDOCUMENTED = {"hangtu.plot.common"}  # private helpers, free to change
# Documented through another object.
DOCUMENTED_AS = {"hangtu.settings": "hangtu._settings.Settings"}


def test_every_public_name_has_a_reference_entry():
    # Criterion 2. ht.Project's methods come with its class directive.
    # Modules with __all__ are searched, as ht.analysis.correlations is.
    expected = set()

    def add(path, obj):
        if path in UNDOCUMENTED:
            return
        if inspect.ismodule(obj) and hasattr(obj, "__all__"):
            for member in obj.__all__:
                add(f"{path}.{member}", getattr(obj, member))
        else:
            expected.add(path)

    for name in ht.__all__:
        add(f"hangtu.{name}", getattr(ht, name))
    expected = {DOCUMENTED_AS.get(name, name) for name in expected}
    assert expected - _documented() == set()


def test_columns_page_lists_every_column(tmp_path, monkeypatch):
    # Criterion 5.
    monkeypatch.setattr(prepare_site, "SITE", tmp_path)
    (tmp_path / "reference").mkdir()
    prepare_site.write_columns_page()
    page = (tmp_path / "reference" / "columns.md").read_text(encoding="utf-8")
    for name in ht.columns()["name"]:
        assert f"| `{name}` |" in page


def _nav_pages(section):
    config = tomllib.loads((ROOT / "zensical.toml").read_text(encoding="utf-8"))
    for entry in config["project"]["nav"]:
        if section in entry:
            return entry[section]
    raise AssertionError(f"No {section!r} section in the nav")


@pytest.mark.parametrize(
    "page",
    [
        page
        for section in ["Getting started", "Guides", "Plots"]
        for page in _nav_pages(section)
    ],
)
def test_page_opens_with_an_example(page):
    # Criterion 4: the example comes before the first section heading.
    text = (ROOT / "docs" / "site" / page).read_text(encoding="utf-8")
    example = text.find('--8<-- "')
    heading = text.find("\n## ")
    assert example != -1, "no example"
    assert heading == -1 or example < heading
