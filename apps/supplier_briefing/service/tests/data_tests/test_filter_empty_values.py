import pandas as pd

from tests.data_tests.utils import filter_for_non_empty_values


def test_filter_empty_values_excludes_defaults_and_casts_to_strings() -> None:
    series = pd.Series(["Value", "N.A.", "", None, "Other", pd.NA])

    result = filter_for_non_empty_values(series)

    assert result.tolist() == ["Value", "Other"]
    assert all(isinstance(value, str) for value in result.tolist())


def test_filter_empty_values_honors_case_insensitive_custom_empties() -> None:
    series = pd.Series(["n.a.", "NaN", "Keep", "  Keep me  "])

    result = filter_for_non_empty_values(series, empty_values=["N.A.", "nan"])

    assert result.tolist() == ["Keep", "  Keep me  "]
