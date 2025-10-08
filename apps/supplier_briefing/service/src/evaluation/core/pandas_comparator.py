"""
Pandas DataFrame and Series comparator with multiple comparison modes.

This module provides a flexible comparator for pandas DataFrames and Series
with different comparison strategies including exact matching, sorted matching,
and overlap scoring.
"""

from enum import StrEnum
from typing import Union

import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field


class PandasComparisonMode(StrEnum):
    """Comparison modes for pandas objects."""

    EXACT_MATCH = "exact_match"
    SORT_AND_EXACT_MATCH = "sort_and_exact_match"
    SCORE_OVERLAP = "score_overlap"


class PandasComparisonConfig(BaseModel):
    """Configuration for pandas comparison operations."""

    mode: PandasComparisonMode
    drop_index: bool = Field(
        default=True, description="Whether to drop index before comparison"
    )
    ignore_column_names: bool = Field(
        default=False, description="Whether to ignore column names when comparing"
    )


class PandasComparator:
    """
    A comparator for pandas DataFrames and Series with configurable comparison modes.

    Note: All pandas Series are automatically converted to DataFrames before comparison
    in all modes to ensure consistent behavior across comparison types.

    Supports three comparison modes. All modes first convert a Series to DataFrames
    1. Exact match: Direct comparison
    2. Sort & exact match: Sort by first column and then exact match
    3. Score overlap: Measure overlap between sorted DataFrames
    """

    def __init__(self, config: PandasComparisonConfig) -> None:
        self.config = config

    def compare(
        self,
        left: Union[pd.DataFrame, pd.Series],
        right: Union[pd.DataFrame, pd.Series],
    ) -> float:
        """
        Compare two pandas objects and return a similarity score between 0 and 1.

        Returns:
            Float between 0 and 1, where 1 means perfect match/overlap
        """
        # Convert Series to DataFrame
        left_df = self._to_dataframe(left)
        right_df = self._to_dataframe(right)

        match self.config.mode:
            case PandasComparisonMode.EXACT_MATCH:
                return self._exact_match(left_df, right_df)
            case PandasComparisonMode.SORT_AND_EXACT_MATCH:
                return self._sort_and_exact_match(left_df, right_df)
            case PandasComparisonMode.SCORE_OVERLAP:
                return self._score_overlap(left_df, right_df)
            case _:
                raise ValueError(f"Unknown comparison mode: {self.config.mode}")

    def _exact_match(self, left: pd.DataFrame, right: pd.DataFrame) -> float:
        """
        Perform exact match comparison on DataFrames.

        Returns:
            1.0 if exact match, 0.0 otherwise
        """
        # Apply preprocessing options
        left_processed = self._preprocess_dataframe(left)
        right_processed = self._preprocess_dataframe(right)

        return 1.0 if left_processed.equals(right_processed) else 0.0

    def _sort_and_exact_match(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
    ) -> float:
        """
        Sort DataFrames by first column and perform exact match.

        Returns:
            1.0 if exact match after sorting, 0.0 otherwise
        """

        # Apply preprocessing options
        left_processed = self._preprocess_dataframe(left)
        right_processed = self._preprocess_dataframe(right)

        if len(left_processed.columns) > 0 and len(right_processed.columns) > 0:
            left_sorted = self.try_sorting_by_first_column(
                left_processed, drop_index=self.config.drop_index
            )
            right_sorted = self.try_sorting_by_first_column(
                right_processed, drop_index=self.config.drop_index
            )

            return 1.0 if left_sorted.equals(right_sorted) else 0.0
        else:
            return 1.0 if left_processed.equals(right_processed) else 0.0

    def _score_overlap(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
    ) -> float:
        """
        Calculate overlap score between two DataFrames.

        The overlap is measured as the ratio of unique common rows to the total unique rows
        across both DataFrames.

        Returns:
            Float between 0 and 1 representing overlap ratio
        """

        # Check column names match before preprocessing
        if not self.config.ignore_column_names:
            # If we're not ignoring column names, they must match exactly
            if len(left.columns) != len(right.columns):
                return 0.0
            if not left.columns.equals(right.columns):
                return 0.0

        # Apply preprocessing options
        left_processed = self._preprocess_dataframe(left)
        right_processed = self._preprocess_dataframe(right)

        # Check that processed DataFrames have same number of columns
        if len(left_processed.columns) != len(right_processed.columns):
            return 0.0

        # Calculate overlap
        if left_processed.empty and right_processed.empty:
            return 1.0

        if left_processed.empty or right_processed.empty:
            return 0.0

        # Convert to sets of tuples for comparison
        left_tuples = set(left_processed.itertuples(index=False, name=None))
        right_tuples = set(right_processed.itertuples(index=False, name=None))

        # Calculate Jaccard similarity (intersection over union)
        size_of_intersection = len(left_tuples.intersection(right_tuples))
        size_of_union = len(left_tuples.union(right_tuples))

        return size_of_intersection / size_of_union

    @staticmethod
    def try_sorting_by_first_column(
        df: pd.DataFrame, drop_index: bool = False
    ) -> pd.DataFrame:
        if len(df.columns) > 0:
            try:
                df_sorted = df.sort_values(by=df.columns[0]).reset_index(
                    drop=drop_index
                )
            except Exception as e:
                logger.warning(f"Failed to sort pandas object: {e}")
                df_sorted = df.reset_index(drop=drop_index)
        else:
            df_sorted = df
        return df_sorted

    @staticmethod
    def _to_dataframe(obj: Union[pd.DataFrame, pd.Series]) -> pd.DataFrame:
        """
        Convert pandas object to DataFrame.
        """
        if isinstance(obj, pd.Series):
            return obj.to_frame()
        return obj.copy()

    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess dataframe: reset index and/or reset column names
        """

        result = df.copy().reset_index(drop=self.config.drop_index)

        if self.config.ignore_column_names and len(result.columns) > 0:
            # Rename columns to generic names
            result.columns = [f"col_{i}" for i in range(len(result.columns))]

        return result
