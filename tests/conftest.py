import contextlib
import copy
import io
import logging

import matplotlib
import pytest
from python_ags4 import AGS4

import hangtu as ht
from hangtu import units, vertical_datums

matplotlib.use("Agg")

import matplotlib.pyplot as plt


class CheckCache:
    """Reuse ``AGS4.check_file`` results across the run (docs/work/test-speed.md).

    The check takes most of an ingest and gives the same answer for the same
    text, so each text is checked once. A hit returns a copy of the result and
    logs the same records again, so ingest turns them into the same findings.
    Only calls with a text buffer are cached; a path goes to the real check.
    """

    def __init__(self, check):
        self.check = check
        self.enabled = True
        self.hits = 0
        self._results = {}

    def __call__(self, filepath_or_buffer, standard_AGS4_dictionary=None, **kwargs):
        if not (self.enabled and isinstance(filepath_or_buffer, io.StringIO)):
            return self.check(filepath_or_buffer, standard_AGS4_dictionary, **kwargs)
        key = (
            filepath_or_buffer.getvalue(),
            standard_AGS4_dictionary,
            tuple(sorted(kwargs.items())),
        )
        if key in self._results:
            self.hits += 1
            result, records = self._results[key]
            for record in records:
                logging.getLogger(record.name).handle(record)
            return copy.deepcopy(result)
        records = []
        logger = logging.getLogger("python_ags4")
        handler = _Records(records)
        logger.addHandler(handler)
        try:
            result = self.check(filepath_or_buffer, standard_AGS4_dictionary, **kwargs)
        finally:
            logger.removeHandler(handler)
        self._results[key] = (copy.deepcopy(result), records)
        return result

    @contextlib.contextmanager
    def disabled(self):
        self.enabled = False
        try:
            yield
        finally:
            self.enabled = True


class _Records(logging.Handler):
    def __init__(self, records):
        super().__init__(level=logging.DEBUG)
        self._records = records

    def emit(self, record):
        self._records.append(record)


@pytest.fixture(scope="session", autouse=True)
def check_cache():
    """The ``CheckCache`` in place of ``AGS4.check_file`` for the whole run."""
    cache = CheckCache(AGS4.check_file)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(AGS4, "check_file", cache)
        yield cache


@pytest.fixture(autouse=True)
def _restore_session_state():
    yield
    ht.settings.reset()
    units._reset_aliases()
    vertical_datums._reset()
    ht.plot.reset_palette()
    plt.close("all")
