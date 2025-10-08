import pandas as pd
import pytest

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_GROUPING_FACHBEREICH,
    COL_PROCUREMENT_UNIT,
    COL_RESPONSIBLE_DEPARTMENT,
    COL_RISIKOROHSTOFFE,
    HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
    NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
)
from service.data_preparation import assert_column_depends_on_other_column


def test_transactions_contains_both_data_sources(transactions_df: pd.DataFrame) -> None:
    """Ensure transactions contains both Handelsware and Nicht-Handelsware."""
    data_sources = set(transactions_df[COL_DATA_SOURCE].unique())
    assert DATA_SOURCE_HW in data_sources
    assert DATA_SOURCE_NHW in data_sources


def test_transactions_row_count_vs_cleaned_files(
    transactions_df: pd.DataFrame,
    brutto_df_cleaned: pd.DataFrame,
    concrete_df_cleaned: pd.DataFrame,
) -> None:
    """
    Ensure transactions has at least as many rows as the larger cleaned file.
    """
    max_input_rows = max(len(brutto_df_cleaned), len(concrete_df_cleaned))
    assert len(transactions_df) >= max_input_rows


@pytest.mark.parametrize(
    "column",
    [
        COL_BUSINESS_PARTNER_ID,
        COL_BUSINESS_PARTNER_NAME,
        COL_PROCUREMENT_UNIT,
        COL_GROUPING_FACHBEREICH,
        COL_RESPONSIBLE_DEPARTMENT,
        COL_ESTELL_SEKTOR_GROB_RENAMED,
        COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    ],
)
def test_business_metadata_columns_preserved(
    transactions_df: pd.DataFrame,
    brutto_df_cleaned: pd.DataFrame,
    concrete_df_cleaned: pd.DataFrame,
    column: str,
) -> None:
    """Ensure business metadata columns have all their unique values preserved."""
    brutto_values = set(brutto_df_cleaned[column].dropna().unique())
    concrete_values = set(concrete_df_cleaned[column].dropna().unique())
    all_values = brutto_values | concrete_values
    all_values.discard("N.A.")

    transactions_values = set(transactions_df[column].dropna().unique())

    missing_values = all_values - transactions_values
    assert len(missing_values) == 0, (
        f"Missing {len(missing_values)} values in column '{column}' from transactions: {missing_values}"
    )


def test_all_article_names_preserved(
    transactions_df: pd.DataFrame,
    brutto_df_cleaned: pd.DataFrame,
    concrete_df_cleaned: pd.DataFrame,
) -> None:
    """Ensure all article names from cleaned files are in transactions."""
    brutto_articles = set(brutto_df_cleaned[COL_ARTICLE_NAME].dropna().unique())
    concrete_articles = set(concrete_df_cleaned[COL_ARTICLE_NAME].dropna().unique())
    all_articles = brutto_articles | concrete_articles
    all_articles.discard("N.A.")

    transactions_articles = set(transactions_df[COL_ARTICLE_NAME].dropna().unique())

    missing_articles = all_articles - transactions_articles
    assert len(missing_articles) == 0, (
        f"Missing {len(missing_articles)} article names from transactions"
    )


def test_risikorohstoffe_preserved_from_brutto(
    transactions_df: pd.DataFrame,
    brutto_df_cleaned: pd.DataFrame,
) -> None:
    """
    Ensure all Risikorohstoffe values from brutto_cleaned are in transactions.

    This column comes from the brutto file and should be preserved in the merge.
    """
    brutto_resources = set(brutto_df_cleaned[COL_RISIKOROHSTOFFE].dropna().unique())
    transactions_resources = set(transactions_df[COL_RISIKOROHSTOFFE].dropna().unique())

    missing_resources = brutto_resources - transactions_resources
    assert len(missing_resources) == 0, (
        f"Missing {len(missing_resources)} Risikorohstoffe values from transactions"
    )


def test_handelsware_pseudo_primary_key_components_present(
    transactions_df: pd.DataFrame,
) -> None:
    """Ensure all Handelsware pseudo primary key columns are in transactions."""
    hw_transactions = transactions_df[
        transactions_df[COL_DATA_SOURCE] == DATA_SOURCE_HW
    ]

    if len(hw_transactions) > 0:
        for col in HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS:
            assert col in transactions_df.columns, (
                f"Handelsware key column '{col}' missing from transactions"
            )


def test_nicht_handelsware_pseudo_primary_key_components_present(
    transactions_df: pd.DataFrame,
) -> None:
    """Ensure all Nicht-Handelsware pseudo primary key columns are in transactions."""
    nhw_transactions = transactions_df[
        transactions_df[COL_DATA_SOURCE] == DATA_SOURCE_NHW
    ]

    if len(nhw_transactions) > 0:
        for col in NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS:
            assert col in transactions_df.columns, (
                f"Nicht-Handelsware key column '{col}' missing from transactions"
            )


def test_business_partner_name_unique_per_id(transactions_df: pd.DataFrame) -> None:
    """Ensure each business partner ID has exactly one business partner name."""
    assert_column_depends_on_other_column(transactions_df, COL_BUSINESS_PARTNER_NAME)


def test_transactions_no_duplicate_rows(transactions_df: pd.DataFrame) -> None:
    duplicate_count = transactions_df.duplicated().sum()
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate rows"
