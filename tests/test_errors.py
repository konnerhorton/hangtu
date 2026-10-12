import pytest

import hangtu as ak
from hangtu.errors import warn


@pytest.mark.parametrize("error", [ak.UnitsError, ak.ColumnError])
def test_data_errors_are_hangtu_and_value_errors(error):
    assert issubclass(error, ak.HangtuError)
    assert issubclass(error, ValueError)


def test_hint_is_a_user_warning():
    assert issubclass(ak.HangtuHint, UserWarning)


def test_warn_points_at_the_callers_line():
    with pytest.warns(ak.HangtuHint, match="a hint") as record:
        warn("a hint", ak.HangtuHint)
    assert record[0].filename == __file__
