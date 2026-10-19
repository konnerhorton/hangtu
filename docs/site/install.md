# Install

hangtu needs Python 3.12 or later and runs on Windows, macOS and Linux.

=== "Latest (recommended)"

    The latest version from GitHub. It has every feature on this site.

    ```bash
    pip install git+https://github.com/konnerhorton/hangtu
    ```

    Or, in a [uv](https://docs.astral.sh/uv/) project:

    ```bash
    uv add git+https://github.com/konnerhorton/hangtu
    ```

=== "Released"

    The last release on PyPI. It can be behind this site, which follows the latest version.

    ```bash
    pip install hangtu
    ```

    Or, in a uv project:

    ```bash
    uv add hangtu
    ```

To check which version you have:

```python
import hangtu as ht

print(ht.__version__)
```

Next: draw a first plot [from a CSV file](getting-started/csv.md) or [from an AGS file](getting-started/ags.md).
