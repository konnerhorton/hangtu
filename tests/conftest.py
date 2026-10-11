import matplotlib
import pytest

import ags_kit as ak
from ags_kit import units

matplotlib.use("Agg")

import matplotlib.pyplot as plt


@pytest.fixture(autouse=True)
def _restore_session_state():
    yield
    ak.settings.reset()
    units._reset_aliases()
    ak.plot.reset_palette()
    plt.close("all")
