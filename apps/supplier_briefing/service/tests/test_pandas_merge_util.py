import pandas as pd
import pytest

from service.agent_core.data_management.columns import EMPTY_VALUES
from service.pandas_merge_util import ConflictColumns, outer_merge_with_left_preference


def test_basic_merge_no_conflict() -> None:
    left = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})
    right = pd.DataFrame({"id": [2, 3], "value": ["b", "c"]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})

    pd.testing.assert_frame_equal(merged, expected_merged)
    assert conflicts.empty


def test_conflict_detection_and_left_preference() -> None:
    left = pd.DataFrame({"id": [1], "name": ["Alice"]})
    right = pd.DataFrame({"id": [1], "name": ["Alicia"]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1], "name": ["Alice"]})

    expected_conflicts = pd.DataFrame(
        {
            "id": [1],
            ConflictColumns.COLUMN.value: ["name"],
            ConflictColumns.LEFT_DF_VALUE.value: ["Alice"],
            ConflictColumns.RIGHT_DF_VALUE.value: ["Alicia"],
        }
    )

    pd.testing.assert_frame_equal(merged, expected_merged)
    pd.testing.assert_frame_equal(conflicts, expected_conflicts)


def test_composite_key_merge() -> None:
    left = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "date": ["2023-01-01", "2023-01-01"],
            "amount": [100, 200],
        }
    )
    right = pd.DataFrame(
        {
            "customer_id": [2, 3],
            "date": ["2023-01-01", "2023-01-01"],
            "amount": [250, 300],
        }
    )

    merged, conflicts = outer_merge_with_left_preference(
        left, right, keys=["customer_id", "date"]
    )

    expected_merged = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "date": ["2023-01-01"] * 3,
            "amount": [100, 200, 300],
        }
    )

    expected_conflicts = pd.DataFrame(
        {
            "customer_id": [2],
            "date": ["2023-01-01"],
            ConflictColumns.COLUMN.value: ["amount"],
            ConflictColumns.LEFT_DF_VALUE.value: [200],
            ConflictColumns.RIGHT_DF_VALUE.value: [250],
        }
    )

    pd.testing.assert_frame_equal(merged, expected_merged)
    pd.testing.assert_frame_equal(conflicts, expected_conflicts)


def test_nulls_in_left_take_right() -> None:
    left = pd.DataFrame({"id": [1, 2], "value": [None, "b"]})
    right = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    pd.testing.assert_frame_equal(merged, expected_merged)
    assert conflicts.empty


def test_multiple_conflicts() -> None:
    left = pd.DataFrame({"id": [1], "a": [10], "b": [20]})
    right = pd.DataFrame({"id": [1], "a": [11], "b": [21]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1], "a": [10], "b": [20]})

    expected_conflicts = pd.DataFrame(
        {
            "id": [1, 1],
            ConflictColumns.COLUMN.value: ["a", "b"],
            ConflictColumns.LEFT_DF_VALUE.value: [10, 20],
            ConflictColumns.RIGHT_DF_VALUE.value: [11, 21],
        }
    )

    pd.testing.assert_frame_equal(merged, expected_merged)
    pd.testing.assert_frame_equal(
        conflicts.sort_values(ConflictColumns.COLUMN.value).reset_index(drop=True),
        expected_conflicts,
    )


def test_non_overlapping_columns() -> None:
    left = pd.DataFrame({"id": [1], "x": [10]})
    right = pd.DataFrame({"id": [1], "y": [20]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1], "x": [10], "y": [20]})
    pd.testing.assert_frame_equal(merged, expected_merged)
    assert conflicts.empty


def test_empty_dataframes() -> None:
    left = pd.DataFrame(columns=["id", "value"])
    right = pd.DataFrame(columns=["id", "value"])
    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected = pd.DataFrame(columns=["id", "value"])

    pd.testing.assert_frame_equal(merged, expected)
    assert conflicts.empty


def test_missing_keys() -> None:
    left = pd.DataFrame({"id": [1], "value": ["x"]})
    right = pd.DataFrame({"not_id": [1], "value": ["x"]})

    with pytest.raises(KeyError):
        outer_merge_with_left_preference(left, right, keys=["id"])


def test_mixed_types_and_conflict() -> None:
    left = pd.DataFrame({"id": [1], "val": ["10"]})
    right = pd.DataFrame({"id": [1], "val": [10]})  # int vs str

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1], "val": ["10"]})

    expected_conflicts = pd.DataFrame(
        {
            "id": [1],
            ConflictColumns.COLUMN.value: ["val"],
            ConflictColumns.LEFT_DF_VALUE.value: ["10"],
            ConflictColumns.RIGHT_DF_VALUE.value: [10],
        }
    )

    pd.testing.assert_frame_equal(merged, expected_merged)
    pd.testing.assert_frame_equal(conflicts, expected_conflicts)


@pytest.mark.parametrize("empty_value", EMPTY_VALUES)
def test_empty_value_in_left_df_replaced_by_right_df(empty_value: str | None) -> None:
    """Test that each EMPTY_VALUE in left_df is treated as empty and replaced by right_df value."""
    left = pd.DataFrame({"id": [1, 2], "value": [empty_value, "b"]})
    right = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    merged, conflicts = outer_merge_with_left_preference(left, right, keys=["id"])

    expected_merged = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

    pd.testing.assert_frame_equal(merged, expected_merged)
    assert conflicts.empty


def test_column_ordering() -> None:
    """Test that columns are ordered correctly: keys, left-only, shared, right-only."""
    left = pd.DataFrame(
        {"key1": [1], "key2": [2], "left_only": ["L"], "shared": ["S1"]}
    )
    right = pd.DataFrame(
        {"key1": [1], "key2": [2], "shared": ["S2"], "right_only": ["R"]}
    )

    merged, conflicts = outer_merge_with_left_preference(
        left, right, keys=["key1", "key2"]
    )

    expected_columns = ["key1", "key2", "shared", "left_only", "right_only"]
    assert list(merged.columns) == expected_columns

    expected_merged = pd.DataFrame(
        {
            "key1": [1],
            "key2": [2],
            "shared": ["S1"],
            "left_only": ["L"],
            "right_only": ["R"],
        }
    )

    pd.testing.assert_frame_equal(merged, expected_merged)
