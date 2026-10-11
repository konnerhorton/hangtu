import pytest

import ags_kit as ak
from ags_kit import units


@pytest.fixture(autouse=True)
def _restore_session_state():
    yield
    ak.settings.reset()
    units._reset_aliases()
