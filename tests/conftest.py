import pytest

import ags_kit as ak


@pytest.fixture(autouse=True)
def _restore_session_state():
    yield
    ak.settings.reset()
