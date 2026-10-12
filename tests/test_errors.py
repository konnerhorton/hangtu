import pytest

import hangtu as ht
from hangtu.errors import warn


@pytest.mark.parametrize("error", [ht.UnitsError, ht.ColumnError])
def test_data_errors_are_hangtu_and_value_errors(error):
    assert issubclass(error, ht.HangtuError)
    assert issubclass(error, ValueError)


def test_hint_is_a_user_warning():
    assert issubclass(ht.HangtuHint, UserWarning)


def test_warn_points_at_the_callers_line():
    with pytest.warns(ht.HangtuHint, match="a hint") as record:
        warn("a hint", ht.HangtuHint)
    assert record[0].filename == __file__
