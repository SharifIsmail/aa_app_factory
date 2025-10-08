import pandas as pd
import pytest
from pytest import approx

from evaluation.core.pandas_comparator import (
    PandasComparator,
    PandasComparisonConfig,
    PandasComparisonMode,
)

# -----------------------
# Exact Match Mode Tests
# -----------------------


@pytest.mark.parametrize(
    "df1,df2,expected",
    [
        # Identical DataFrames
        (
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            1.0,
        ),
        # Different DataFrames
        (
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            pd.DataFrame({"A": [1, 2, 4], "B": ["x", "y", "z"]}),
            0.0,
        ),
        # Different column names
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"B": [1, 2, 3]}), 0.0),
        # Different row order
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"A": [3, 2, 1]}), 0.0),
        # Empty DataFrames
        (pd.DataFrame(), pd.DataFrame(), 1.0),
    ],
)
def test_exact_match_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, expected: float
) -> None:
    """Test DataFrame comparisons in exact match mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.EXACT_MATCH)
    comparator = PandasComparator(config)
    assert comparator.compare(df1, df2) == expected


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        # Identical Series
        (pd.Series([1, 2, 3]), pd.Series([1, 2, 3]), 1.0),
        # Different Series
        (pd.Series([1, 2, 3]), pd.Series([1, 2, 4]), 0.0),
        # Empty Series
        (pd.Series([], dtype=object), pd.Series([], dtype=object), 1.0),
        # Identical Series, different names
        (pd.Series([1, 2, 3], name="A"), pd.Series([1, 2, 3], name="B"), 0.0),
    ],
)
def test_exact_match_series(s1: pd.Series, s2: pd.Series, expected: float) -> None:
    """Test Series comparisons in exact match mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.EXACT_MATCH)
    comparator = PandasComparator(config)
    assert comparator.compare(s1, s2) == expected


def test_exact_match_mixed_types() -> None:
    """Test that Series and DataFrame are never equal in exact match."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.EXACT_MATCH)
    comparator = PandasComparator(config)

    s1 = pd.Series([1, 2, 3])
    df1 = pd.DataFrame({"A": [1, 2, 3]})

    assert comparator.compare(s1, df1) == 0.0


# -----------------------
# Sort and Exact Match Mode Tests
# -----------------------


@pytest.mark.parametrize(
    "df1,df2,expected",
    [
        # Same data, different order
        (
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            pd.DataFrame({"A": [3, 1, 2], "B": ["z", "x", "y"]}),
            1.0,
        ),
        # Different data
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"A": [1, 2, 4]}), 0.0),
        # Empty DataFrames
        (pd.DataFrame(), pd.DataFrame(), 1.0),
        # Unsortable data (mixed types) - should fallback to direct comparison
        (pd.DataFrame({"A": [1, "text", 3]}), pd.DataFrame({"A": [1, "text", 3]}), 1.0),
        (pd.DataFrame({"A": [3, "text", 1]}), pd.DataFrame({"A": [1, "text", 3]}), 0.0),
    ],
)
def test_sort_exact_match_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, expected: float
) -> None:
    """Test DataFrame comparisons in sort and exact match mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.SORT_AND_EXACT_MATCH)
    comparator = PandasComparator(config)
    assert comparator.compare(df1, df2) == expected


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        # Same data, different order
        (pd.Series([3, 1, 2]), pd.Series([1, 2, 3]), 1.0),
        # Different data
        (pd.Series([1, 2, 3]), pd.Series([1, 2, 4]), 0.0),
    ],
)
def test_sort_exact_match_series(s1: pd.Series, s2: pd.Series, expected: float) -> None:
    """Test Series comparisons in sort and exact match mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.SORT_AND_EXACT_MATCH)
    comparator = PandasComparator(config)
    assert comparator.compare(s1, s2) == expected


def test_sort_exact_match_ignore_column_names() -> None:
    """Test that column names are ignored when configured."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SORT_AND_EXACT_MATCH, ignore_column_names=True
    )
    comparator = PandasComparator(config)

    df1 = pd.DataFrame({"A": [1, 2, 3]})
    df2 = pd.DataFrame({"B": [3, 1, 2]})

    assert comparator.compare(df1, df2) == 1.0


def test_sort_exact_match_drop_index() -> None:
    """Test that index is dropped when configured."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SORT_AND_EXACT_MATCH, drop_index=True
    )
    comparator = PandasComparator(config)

    df1 = pd.DataFrame({"A": [1, 2, 3]}, index=[10, 20, 30])
    df2 = pd.DataFrame({"A": [3, 1, 2]}, index=[100, 200, 300])

    assert comparator.compare(df1, df2) == 1.0


def test_sort_exact_match_series_and_dataframe() -> None:
    """Test that Series and equivalent DataFrame match after conversion, dropping column names and sorting."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SORT_AND_EXACT_MATCH, ignore_column_names=True
    )
    comparator = PandasComparator(config)

    s1 = pd.Series([3, 1, 2])
    df1 = pd.DataFrame({"A": [1, 2, 3]})

    assert comparator.compare(s1, df1) == 1.0


# -----------------------
# Score Overlap Mode Tests
# -----------------------


@pytest.mark.parametrize(
    "df1,df2,expected",
    [
        # Identical DataFrames - full overlap
        (
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]}),
            1.0,
        ),
        # No overlap
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"A": [4, 5, 6]}), 0.0),
        # Partial overlap: intersection {2, 3}, union {1, 2, 3, 4} -> 2/4 = 0.5
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"A": [2, 3, 4]}), 0.5),
        # Different order, same data - full overlap
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"A": [3, 1, 2]}), 1.0),
        # Empty DataFrames - full overlap
        (pd.DataFrame(), pd.DataFrame(), 1.0),
        # One empty DataFrame - no overlap
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame(), 0.0),
        # Multicolumn overlap: intersection {(1, "x")}, union {(1, "x"), (2, "y"), (3, "z")} -> 1/3
        (
            pd.DataFrame({"A": [1, 2], "B": ["x", "y"]}),
            pd.DataFrame({"A": [1, 3], "B": ["x", "z"]}),
            1 / 3,
        ),
        # Different column names but same single-column data - no overlap (column names matter by default)
        (pd.DataFrame({"A": [1, 2, 3]}), pd.DataFrame({"B": [1, 2, 3]}), 0.0),
    ],
)
def test_score_overlap_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, expected: float
) -> None:
    """Test DataFrame comparisons in score overlap mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.SCORE_OVERLAP)
    comparator = PandasComparator(config)
    result = comparator.compare(df1, df2)

    if isinstance(expected, float) and expected != 0.0 and expected != 1.0:
        # Use approximate comparison for fractional results
        assert result == approx(expected)
    else:
        assert result == expected


@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        # Identical Series - full overlap
        (pd.Series([1, 2, 3]), pd.Series([1, 2, 3]), 1.0),
        # Series overlap: intersection {3, 4}, union {1, 2, 3, 4, 5, 6} -> 2/6 = 1/3
        (pd.Series([1, 2, 3, 4]), pd.Series([3, 4, 5, 6]), 1 / 3),
        # No overlap
        (pd.Series([1, 2, 3]), pd.Series([4, 5, 6]), 0.0),
    ],
)
def test_score_overlap_series(s1: pd.Series, s2: pd.Series, expected: float) -> None:
    """Test Series comparisons in score overlap mode."""
    config = PandasComparisonConfig(mode=PandasComparisonMode.SCORE_OVERLAP)
    comparator = PandasComparator(config)
    result = comparator.compare(s1, s2)

    if isinstance(expected, float) and expected != 0.0 and expected != 1.0:
        # Use approximate comparison for fractional results
        assert result == approx(expected)
    else:
        assert result == expected


def test_score_overlap_drop_index() -> None:
    """Test drop_index option - should have full overlap after dropping index."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SCORE_OVERLAP, drop_index=True
    )
    comparator = PandasComparator(config)

    # Same data, different indices
    df1 = pd.DataFrame({"A": [1, 2, 3]}, index=[10, 20, 30])
    df2 = pd.DataFrame({"A": [1, 2, 3]}, index=[100, 200, 300])

    assert comparator.compare(df1, df2) == 1.0


def test_score_overlap_no_drop_index() -> None:
    """Test drop_index option - should have no overlap when not dropping index."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SCORE_OVERLAP, drop_index=False
    )
    comparator = PandasComparator(config)

    # Same data, different indices
    df1 = pd.DataFrame({"A": [1, 2, 3]}, index=[10, 20, 30])
    df2 = pd.DataFrame({"A": [1, 2, 3]}, index=[100, 200, 300])

    assert comparator.compare(df1, df2) == 0.0


def test_score_overlap_ignore_column_names() -> None:
    """Test ignore_column_names option - should have full overlap when ignoring column names."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SCORE_OVERLAP, ignore_column_names=True
    )
    comparator = PandasComparator(config)

    # Same data, different column names
    df1 = pd.DataFrame({"A": [1, 2, 3]})
    df2 = pd.DataFrame({"B": [1, 2, 3]})

    assert comparator.compare(df1, df2) == 1.0


def test_score_overlap_both_options() -> None:
    """Test both ignore_column_names and drop_index options together."""
    config = PandasComparisonConfig(
        mode=PandasComparisonMode.SCORE_OVERLAP,
        ignore_column_names=True,
        drop_index=True,
    )
    comparator = PandasComparator(config)

    # Different column names and indices but same data
    df1 = pd.DataFrame({"A": [1, 2, 3]}, index=[10, 20, 30])
    df2 = pd.DataFrame({"B": [1, 2, 3]}, index=[100, 200, 300])

    assert comparator.compare(df1, df2) == 1.0
