from enum import Enum
from typing import Any, Tuple

import pandas as pd

from service.agent_core.data_management.columns import EMPTY_VALUES


class ConflictColumns(str, Enum):
    """Column names used in the conflicts DataFrame."""

    COLUMN = "column"
    LEFT_DF_VALUE = "left_df_value"
    RIGHT_DF_VALUE = "right_df_value"


def _is_empty_value(val: Any) -> bool:
    """
    Check if a value should be considered empty.
    This includes pandas NaN/None and values in EMPTY_VALUES.
    """
    if pd.isna(val):
        return True
    return val in EMPTY_VALUES


def _reorder_columns_by_preference(
    merged_df: pd.DataFrame,
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    keys: list[str],
) -> pd.DataFrame:
    """
    Reorder columns in merged DataFrame with the following order:
    (a) Keys columns first (in the order they are passed)
    (b) Shared columns (in left_df order)
    (c) Columns only in left_df
    (d) Columns only in right_df
    """
    column_order = []

    column_order.extend(keys)

    shared_cols_ordered = [
        col for col in left_df.columns if col in right_df.columns and col not in keys
    ]
    column_order.extend(shared_cols_ordered)

    left_only_cols = [
        col
        for col in left_df.columns
        if col not in right_df.columns and col not in keys
    ]
    column_order.extend(left_only_cols)

    right_only_cols = [
        col
        for col in right_df.columns
        if col not in left_df.columns and col not in keys
    ]
    column_order.extend(right_only_cols)

    final_column_order = [col for col in column_order if col in merged_df.columns]
    return merged_df[final_column_order]


def outer_merge_with_left_preference(
    left_df: pd.DataFrame, right_df: pd.DataFrame, keys: list[str]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merge two DataFrames (`left_df`, `right_df`) on one or more keys.

    Rules:
      - Full outer join on `keys`.
      - For every overlapping column, prefer `left_df` value if not in EMPTY_VALUES,
        otherwise take `right_df` value.
      - EMPTY_VALUES include pandas NaN/None and specific strings like "N.A.", "nan", "", "N.A.N.A.N.A.".
      - Returns:
          merged_df DataFrame with merged values,
          conflicts DataFrame listing conflicts (where left_df and right_df differ).

    Parameters
    ----------
    left_df : pd.DataFrame
        Preferred DataFrame (its values win in conflicts).
    right_df : pd.DataFrame
        Secondary DataFrame (used when left_df has empty values).
    keys : str or list of str
        Column(s) to join on. Must exist in both DataFrames.
    """

    for key in keys:
        if key not in left_df.columns:
            raise KeyError(f"Key '{key}' not found in left_df DataFrame")
        if key not in right_df.columns:
            raise KeyError(f"Key '{key}' not found in right_df DataFrame")

    merged = left_df.merge(
        right_df, on=keys, how="outer", suffixes=("_left_df", "_right_df")
    )

    # Overlapping columns (excluding the keys)
    shared_cols = set(left_df.columns) & set(right_df.columns) - set(keys)

    resolved_columns = {}
    conflicts = []

    for col in shared_cols:
        left_df_col = f"{col}_left_df"
        right_df_col = f"{col}_right_df"

        # Create combined column: left_df wins if not empty, otherwise take right_df
        left_is_empty = merged[left_df_col].apply(_is_empty_value)
        combined = merged[left_df_col].where(~left_is_empty, merged[right_df_col])

        # Preserve original dtype from left_df if possible, otherwise right_df
        original_dtype = (
            left_df[col].dtype if col in left_df.columns else right_df[col].dtype
        )
        resolved_columns[col] = combined.astype(original_dtype)

        # Conflict detection: both have non-empty values and they differ
        conflict_mask = (
            merged[left_df_col].apply(lambda x: not _is_empty_value(x))
            & merged[right_df_col].apply(lambda x: not _is_empty_value(x))
            & (merged[left_df_col] != merged[right_df_col])
        )

        conflict = merged.loc[conflict_mask, keys + [left_df_col, right_df_col]].copy()
        if not conflict.empty:
            conflict = conflict.rename(
                columns={
                    left_df_col: ConflictColumns.LEFT_DF_VALUE,
                    right_df_col: ConflictColumns.RIGHT_DF_VALUE,
                }
            )

            # Preserve original dtypes in conflicting columns
            left_original_dtype = left_df[col].dtype
            right_original_dtype = right_df[col].dtype

            conflict[ConflictColumns.LEFT_DF_VALUE] = conflict[
                ConflictColumns.LEFT_DF_VALUE
            ].astype(left_original_dtype)

            conflict[ConflictColumns.RIGHT_DF_VALUE] = conflict[
                ConflictColumns.RIGHT_DF_VALUE
            ].astype(right_original_dtype)

            conflict.insert(len(keys), ConflictColumns.COLUMN, col)
            conflicts.append(conflict)

    # Non-overlapping columns (only in one side)
    left_df_only = set(left_df.columns) - set(right_df.columns) - set(keys)
    right_df_only = set(right_df.columns) - set(left_df.columns) - set(keys)

    # Collect all DataFrames to concatenate at once
    frames_to_concat = [merged[keys]]

    if resolved_columns:
        frames_to_concat.append(pd.DataFrame(resolved_columns, index=merged.index))

    if left_df_only:
        frames_to_concat.append(merged[[col for col in left_df_only]])

    if right_df_only:
        frames_to_concat.append(merged[[col for col in right_df_only]])

    merged_df = pd.concat(frames_to_concat, axis=1)

    # Apply column ordering
    merged_df = _reorder_columns_by_preference(merged_df, left_df, right_df, keys)

    # Combine conflicts
    conflicts = (
        pd.concat(conflicts, ignore_index=True)
        if conflicts
        else pd.DataFrame(
            columns=keys
            + [
                ConflictColumns.COLUMN,
                ConflictColumns.LEFT_DF_VALUE,
                ConflictColumns.RIGHT_DF_VALUE,
            ]
        )
    )

    return merged_df, conflicts
