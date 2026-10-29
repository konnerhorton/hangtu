"""DescribeResult: frame, dict and text (docs/work/m15a-describe.md, Decision 2)."""

import json
import math

import pandas as pd
import pytest

import hangtu as ht
from hangtu.plot._overlays import format_number

STATISTICS = [
    "count",
    "mean",
    "standard_deviation",
    "coefficient_of_variation",
    "minimum",
    "percentile_5",
    "percentile_25",
    "median",
    "percentile_75",
    "percentile_95",
    "maximum",
]
COUNTS = [
    "count_at_least",
    "count_at_most",
    "count_non_plastic",
    "count_assumed",
    "count_range",
    "count_text",
    "count_blank",
]


def _result(**kwargs):
    df = pd.DataFrame(
        {
            "geology_unit": ["A"] * 5 + ["B"] * 4,
            "undrained_shear_strength": [10, 12, 15, 20, 23, 40, 41.5, 47, 1290],
        }
    )
    df = ht.set_units(df, {"undrained_shear_strength": "kPa"})
    df.attrs["judgments"] = {"bulk_unit_weight": {"source": "judgments.yaml"}}
    return ht.stats.describe(
        df, value="undrained_shear_strength", by="geology_unit", **kwargs
    )


def test_frame_columns_and_units():
    # AC 14
    frame = _result().to_frame()
    assert list(frame.columns) == ["geology_unit", *STATISTICS, *COUNTS]
    assert frame.attrs["units"] == dict.fromkeys(
        [s for s in STATISTICS if s not in ("count", "coefficient_of_variation")],
        "kPa",
    )
    assert frame["count"].dtype.kind == "i"


def test_fields():
    result = _result()
    assert result.kind == "property"
    assert result.function == "describe"
    assert result.value == "undrained_shear_strength"
    assert result.by == ("geology_unit",)
    assert result.percentile_method == "Hyndman & Fan (1996) definition 7"
    assert result.judgments == {"bulk_unit_weight": {"source": "judgments.yaml"}}
    assert result.hangtu_version == ht.__version__


def test_dict_is_json():
    data = _result().to_dict()
    text = json.dumps(data)
    assert "NaN" not in text
    assert data["groups"][0]["statistics"]["percentile_5"] is None
    assert data["groups"][0]["key"] == {"geology_unit": "A"}


def test_text_holds_every_number_of_the_frame():
    result = _result()
    text = str(result)
    frame = result.to_frame()
    for name in STATISTICS:
        for value in frame[name]:
            if not math.isnan(value):
                shown = str(int(value)) if name == "count" else format_number(value)
                assert shown in text, (name, value)
    assert text.splitlines()[0] == "undrained_shear_strength (kPa)"
    assert "P5/P95 need 20 values: A, B." in text
    assert repr(result) == text
    assert result._repr_html_().startswith("<pre>")


def test_result_is_frozen_and_keeps_no_frame():
    result = _result()
    with pytest.raises(AttributeError):
        result.unit = "psf"
    assert not any(isinstance(v, pd.DataFrame) for v in vars(result).values())
