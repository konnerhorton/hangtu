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


def test_logo_svgs_draw_every_character(tmp_path, monkeypatch):
    # Criterion 6: one pair of shapes for each "=" or ":" in the small mark.
    monkeypatch.setattr(prepare_site, "GENERATED", tmp_path)
    prepare_site.write_logo()
    _, small_mark = prepare_site.logo_marks()
    characters = sum(line.count("=") + line.count(":") for line in small_mark)
    for name in prepare_site.LOGO_COLORS:
        svg = (tmp_path / name).read_text(encoding="utf-8")
        assert svg.count("<rect ") == 2 * characters
        assert "<text" not in svg


def test_readme_opens_with_the_wordmark():
    # Criterion 6: the README's wordmark is the one in docs/img/logo.txt.
    wordmark, _ = prepare_site.logo_marks()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("```\n" + "\n".join(wordmark) + "\n```\n")


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
    expected = set()
    for name in ht.__all__:
        obj = getattr(ht, name)
        if inspect.ismodule(obj) and hasattr(obj, "__all__"):
            expected |= {f"hangtu.{name}.{member}" for member in obj.__all__}
        else:
            expected.add(f"hangtu.{name}")
    expected = {DOCUMENTED_AS.get(name, name) for name in expected - UNDOCUMENTED}
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
    [page for section in ["Guides", "Plots"] for page in _nav_pages(section)],
)
def test_page_opens_with_an_example(page):
    # Criterion 4: the example comes before the first section heading.
    text = (ROOT / "docs" / "site" / page).read_text(encoding="utf-8")
    example = text.find('--8<-- "')
    heading = text.find("\n## ")
    assert example != -1, "no example"
    assert heading == -1 or example < heading
