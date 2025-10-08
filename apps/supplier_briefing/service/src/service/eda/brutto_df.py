from typing import List, Tuple

import pandas as pd

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_DATA_SOURCE,
    COL_FINEST_PRODUCT_LEVEL,
)
from service.agent_core.model_tools_manager import DATA_DIR
from service.data_loading import load_dataset_from_path
from service.data_preparation import (
    BRUTTO_FILE_CLEANED_PARQUET,
    BRUTTO_FILE_PARQUET,
)

brutto_df = load_dataset_from_path(DATA_DIR / BRUTTO_FILE_PARQUET)
brutto_df_cleaned = load_dataset_from_path(DATA_DIR / BRUTTO_FILE_CLEANED_PARQUET)


def find_duplicate_key_combinations(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Find tuples of (COL_BUSINESS_PARTNER_ID, COL_FINEST_PRODUCT_LEVEL) that appear
    in more than one row in the dataframe.

    Args:
        df: The dataframe to analyze (e.g., brutto_df_cleaned)

    Returns:
        List of tuples (business_partner_id, finest_product_level) that have duplicates
    """
    assert COL_BUSINESS_PARTNER_ID in df.columns
    assert COL_FINEST_PRODUCT_LEVEL in df.columns

    # Count occurrences of each combination using value_counts (faster than groupby.size)
    combination_counts = df.value_counts(
        [COL_BUSINESS_PARTNER_ID, COL_FINEST_PRODUCT_LEVEL]
    )

    # Filter to combinations that appear more than once
    duplicates = combination_counts[combination_counts > 1]

    # Return as list of tuples
    return [(bp_id, product_level) for bp_id, product_level in duplicates.index]


def analyze_non_constant_columns(
    df: pd.DataFrame, business_partner_id: str, finest_product_level: str
) -> pd.DataFrame:
    """
    For a given combination of COL_BUSINESS_PARTNER_ID and COL_FINEST_PRODUCT_LEVEL,
    print the columns that are not constant (have different values) across the rows
    with that combination and return a DataFrame with only the non-constant columns
    for those rows.

    Args:
        df: The dataframe to analyze (e.g., brutto_df_cleaned)
        business_partner_id: The business partner ID value
        finest_product_level: The finest product level value

    Returns:
        DataFrame containing only the non-constant columns for rows with the
        specified key combination. Includes the key columns for reference.
    """
    # Filter to rows with the specified combination
    mask = (df[COL_BUSINESS_PARTNER_ID] == business_partner_id) & (
        df[COL_FINEST_PRODUCT_LEVEL] == finest_product_level
    )
    subset = df[mask]

    if len(subset) <= 1:
        print(
            f"No duplicates found for combination ({business_partner_id}, {finest_product_level})"
        )
        return pd.DataFrame()

    print(f"Analyzing {len(subset)} rows for combination:")
    print(f"  {COL_BUSINESS_PARTNER_ID}: {business_partner_id}")
    print(f"  {COL_FINEST_PRODUCT_LEVEL}: {finest_product_level}")
    print()

    non_constant_columns = []

    # Check each column for variability
    for column in df.columns:
        if column in [COL_BUSINESS_PARTNER_ID, COL_FINEST_PRODUCT_LEVEL]:
            # Skip the key columns as they are constant by definition
            continue

        unique_values = subset[column].nunique()
        if unique_values > 1:
            non_constant_columns.append(column)
            unique_vals = subset[column].unique()
            print(f"Column '{column}' has {unique_values} unique values:")
            print(f"  Values: {unique_vals}")
            print()

    if not non_constant_columns:
        print("All columns (except the key columns) are constant for this combination.")
        # Return empty DataFrame if no non-constant columns
        return pd.DataFrame()
    else:
        print(f"Summary: {len(non_constant_columns)} non-constant columns found:")
        for col in non_constant_columns:
            print(f"  - {col}")

    # Create result DataFrame with key columns + non-constant columns
    columns_to_include = [
        COL_BUSINESS_PARTNER_ID,
        COL_FINEST_PRODUCT_LEVEL,
    ] + non_constant_columns
    result_df = subset[columns_to_include].copy()

    return result_df


# Example usage functions
def analyze_all_duplicates(df: pd.DataFrame) -> None:
    """
    Convenience function to find and analyze all duplicate key combinations.
    Provides a final summary of all non-constant columns across all duplicates.

    Args:
        df: The dataframe to analyze (e.g., brutto_df_cleaned)
    """
    duplicates = find_duplicate_key_combinations(df)

    assert COL_BUSINESS_PARTNER_ID in df.columns
    assert COL_FINEST_PRODUCT_LEVEL in df.columns

    if not duplicates:
        print("No duplicate key combinations found!")
        print(
            f"({COL_BUSINESS_PARTNER_ID}, {COL_FINEST_PRODUCT_LEVEL}) appears to be a valid primary key."
        )
        return

    print(f"Found {len(duplicates)} duplicate key combinations:")
    print()

    # Collect all non-constant columns across all duplicates
    all_non_constant_columns = set()
    column_frequency: dict[str, int] = {}

    for i, (bp_id, product_level) in enumerate(duplicates, 1):
        print(f"=== Duplicate {i}/{len(duplicates)} ===")
        result_df = analyze_non_constant_columns(df, bp_id, product_level)
        print(result_df.to_string())

        # Extract non-constant column names (excluding the key columns)
        if not result_df.empty:
            non_constant_cols = [
                col
                for col in result_df.columns
                if col not in [COL_BUSINESS_PARTNER_ID, COL_FINEST_PRODUCT_LEVEL]
            ]

            # Add to our collection
            all_non_constant_columns.update(non_constant_cols)

            # Count frequency of each column
            for col in non_constant_cols:
                column_frequency[col] = column_frequency.get(col, 0) + 1

        print("=" * 50)
        print()

    # Final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total duplicate combinations: {len(duplicates)}")
    print(f"Total unique non-constant columns: {len(all_non_constant_columns)}")
    print()

    if all_non_constant_columns:
        print("Non-constant columns across all duplicates:")
        print("-" * 40)

        # Sort by frequency (most common first)
        sorted_columns = sorted(
            column_frequency.items(), key=lambda x: x[1], reverse=True
        )

        for col, frequency in sorted_columns:
            percentage = (frequency / len(duplicates)) * 100
            print(
                f"  {col:30} | {frequency:3}/{len(duplicates)} duplicates ({percentage:5.1f}%)"
            )
    else:
        print("No non-constant columns found in any duplicate combinations.")
        print(
            "This suggests the duplicates might be exact duplicates that can be simply removed."
        )


if __name__ == "__main__":
    brutto_df_handelsware = brutto_df[
        brutto_df[COL_DATA_SOURCE] == "Datenerfassung Handelsware (HW)"
    ]
    brutto_df_nicht_handelsware = brutto_df[
        brutto_df[COL_DATA_SOURCE] == "Datenerfassung Nicht-Handelsware (NHW)"
    ]

    analyze_all_duplicates(brutto_df_cleaned)
    analyze_all_duplicates(brutto_df_handelsware)
    analyze_all_duplicates(brutto_df_nicht_handelsware)

    # specific examples HW
    print(
        analyze_non_constant_columns(
            brutto_df_cleaned, "10000", "JAGDWURST NORDDEUTSCHER ART QS SK1"
        )
    )

    # specific examples NHW
    print(
        analyze_non_constant_columns(
            brutto_df_cleaned, "21374781", "LADENBAU REGALIERUNG/PODESTE"
        )
    )
