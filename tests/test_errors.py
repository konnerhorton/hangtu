import pytest

import ags_kit as ak
from ags_kit.errors import warn


@pytest.mark.parametrize("error", [ak.UnitsError, ak.ColumnError])
def test_data_errors_are_ags_kit_and_value_errors(error):
    assert issubclass(error, ak.AgsKitError)
    assert issubclass(error, ValueError)


def test_hint_is_a_user_warning():
    assert issubclass(ak.AgsKitHint, UserWarning)


def test_warn_points_at_the_callers_line():
    with pytest.warns(ak.AgsKitHint, match="a hint") as record:
        warn("a hint", ak.AgsKitHint)
    assert record[0].filename == __file__
