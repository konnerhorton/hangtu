import matplotlib
import pytest

import hangtu as ht
from hangtu import units, vertical_datums

matplotlib.use("Agg")

import matplotlib.pyplot as plt


@pytest.fixture(autouse=True)
def _restore_session_state():
    yield
    ht.settings.reset()
    units._reset_aliases()
    vertical_datums._reset()
    ht.plot.reset_palette()
    plt.close("all")
