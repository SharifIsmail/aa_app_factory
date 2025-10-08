import gc
import os
import re
import time
from itertools import product
from typing import Any, Callable, Union

import numpy as np
import pandas as pd
from loguru import logger

from service.agent_core.constants import DATA_SOURCE_HW, DATA_SOURCE_NHW
from service.agent_core.data_management.columns import (
    COL_BETRACHTUNGSZEITRAUM_ENDE,
    COL_BETRACHTUNGSZEITRAUM_RANGE,
    COL_BETRACHTUNGSZEITRAUM_START,
    COL_BRUTTO_PRIORISIERUNG,
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_BUSINESS_PARTNER_UST_ID,
    COL_COUNTRY,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_DETAILLIERT_RAW,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RAW,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_GROUPING_FACHBEREICH,
    COL_ID_ARTICLE_NAME,
    COL_ID_ARTICLE_NAME_CONCRETE_FILE,
    COL_ID_ARTICLE_UNIQUE,
    COL_KONKRETE_PRIORISIERUNG,
    COL_NETTO_PRIORISIERUNG,
    COL_PART_OF_SCHWARZ,
    COL_PLACE_OF_PRODUCTION_ID,
    COL_PROCUREMENT_UNIT,
    COL_RELATIVE_PURCHASE_VALUE,
    COL_RESPONSIBLE_DEPARTMENT,
    COL_REVENUE_THRESHOLD,
    COL_REVENUE_TOTAL,
    COL_RISIKOROHSTOFFE,
    COL_ROHSTOFFNAME,
    COL_SCHWARZBESCHAFFUNG,
    HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
    NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.pandas_merge_util import outer_merge_with_left_preference
from service.risk_columns import RISK_COL_PREFIXES, RISK_COLUMN_PATTERN
from service.utils import standardize_date_format

RISK_MAP = {
    "niedrig": 1,
    "mittel": 2,
    "hoch": 3,
    "sehr hoch": 4,
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}

BUSINESS_PARTNER_METADATA_COLS = [
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_SCHWARZBESCHAFFUNG,
    COL_PROCUREMENT_UNIT,
    COL_PART_OF_SCHWARZ,
    COL_REVENUE_TOTAL,
    COL_RELATIVE_PURCHASE_VALUE,
    COL_GROUPING_FACHBEREICH,
    COL_RESPONSIBLE_DEPARTMENT,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_DATA_SOURCE,
    COL_NETTO_PRIORISIERUNG,
    COL_KONKRETE_PRIORISIERUNG,
    COL_BRUTTO_PRIORISIERUNG,
]

# Column name constants to reduce duplication
BRANCH_DETAIL_COL = COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED
COUNTRY_COL = COL_COUNTRY

# Multi-index column names for risk analysis
RISK_TYPE_COL = "Risikotyp"
SUPPLIER_LEVEL_COL = "Lieferantenebene"
LEGAL_POSITION_COL = "Rechtsposition"

BRUTTO_FILE_BASE = "brutto_file"
CONCRETE_FILE_BASE = "concrete_file"
RESOURCE_RISKS_BASE = "resource_risks"

BRUTTO_FILE_EXCEL = f"{BRUTTO_FILE_BASE}.xlsx"
CONCRETE_FILE_EXCEL = f"{CONCRETE_FILE_BASE}.xlsx"
RESOURCE_RISKS_EXCEL = f"{RESOURCE_RISKS_BASE}.xlsx"

BRUTTO_FILE_PARQUET = f"{BRUTTO_FILE_BASE}.parquet"
CONCRETE_FILE_PARQUET = f"{CONCRETE_FILE_BASE}.parquet"

BRUTTO_FILE_CLEANED_PARQUET = f"{BRUTTO_FILE_BASE}_cleaned.parquet"
CONCRETE_FILE_CLEANED_PARQUET = f"{CONCRETE_FILE_BASE}_cleaned.parquet"

BRUTTO_FILE_CLEANED_EXCEL = f"{BRUTTO_FILE_BASE}_cleaned.xlsx"
CONCRETE_FILE_CLEANED_EXCEL = f"{CONCRETE_FILE_BASE}_cleaned.xlsx"

RESOURCE_RISKS_PARQUET = f"{RESOURCE_RISKS_BASE}.parquet"
TRANSACTIONS_PARQUET = "transactions.parquet"
TRANSACTIONS_EXCEL = "transactions.xlsx"
BUSINESS_PARTNERS_PARQUET = "business_partners.parquet"
RISK_PER_BUSINESS_PARTNER_PARQUET = "risk_per_business_partner.parquet"
RISK_PER_BRANCH_PARQUET = "risk_per_branch.parquet"
RESOURCE_RISKS_PROCESSED_PARQUET = "resource_risks_processed.parquet"
CONFLICTS_HW_PARQUET = "conflicts_handelsware.parquet"
CONFLICTS_HW_EXCEL = "conflicts_handelsware.xlsx"
CONFLICTS_NHW_PARQUET = "conflicts_nicht_handelsware.parquet"
CONFLICTS_NHW_EXCEL = "conflicts_nicht_handelsware.xlsx"

EXPECTED_RAW_FILES = [
    BRUTTO_FILE_EXCEL,
    CONCRETE_FILE_EXCEL,
    RESOURCE_RISKS_EXCEL,
]

EXPECTED_OUTPUT_FILES = [
    BRUTTO_FILE_PARQUET,
    CONCRETE_FILE_PARQUET,
    RESOURCE_RISKS_PARQUET,
    TRANSACTIONS_PARQUET,
    BUSINESS_PARTNERS_PARQUET,
    RISK_PER_BUSINESS_PARTNER_PARQUET,
    RISK_PER_BRANCH_PARQUET,
    RESOURCE_RISKS_PROCESSED_PARQUET,
]


def assert_split_into_two_distinct_data_sources(df: pd.DataFrame) -> None:
    """Ensure the dataframe contains only the expected data source values."""
    data_source_values = df[COL_DATA_SOURCE]
    observed_sources = {value for value in data_source_values if value}
    assert observed_sources == {DATA_SOURCE_HW, DATA_SOURCE_NHW}

    for expected_source in (DATA_SOURCE_HW, DATA_SOURCE_NHW):
        source_subset = df[df[COL_DATA_SOURCE] == expected_source]
        assert not source_subset.empty


def get_all_business_partner_columns(df: pd.DataFrame) -> list[str]:
    risk_pattern = re.compile(RISK_COLUMN_PATTERN)
    risk_cols = [col for col in df.columns if risk_pattern.match(col)]
    metadata_cols = [col for col in BUSINESS_PARTNER_METADATA_COLS if col in df.columns]
    return metadata_cols + risk_cols


def is_str_nan(value: str) -> bool:
    return value == "N.A." or value == "nan"


def rename_estell_sektor_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy = df_copy.rename(
        columns={
            COL_ESTELL_SEKTOR_GROB_RAW: COL_ESTELL_SEKTOR_GROB_RENAMED,
            COL_ESTELL_SEKTOR_DETAILLIERT_RAW: COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
        }
    )
    return df_copy


def clean_business_partner_id_columns(df: pd.DataFrame) -> pd.DataFrame:
    business_partner_id_col = COL_BUSINESS_PARTNER_ID
    production_site_id_col = COL_PLACE_OF_PRODUCTION_ID

    df_copy = df.copy()

    if business_partner_id_col in df_copy.columns:
        df_copy[business_partner_id_col] = df_copy[business_partner_id_col].apply(
            lambda x: np.nan if is_str_nan(x) else x
        )

    if production_site_id_col in df_copy.columns:
        df_copy[production_site_id_col] = df_copy[production_site_id_col].apply(
            lambda x: np.nan if is_str_nan(x) else x
        )

    return df_copy


class ColumnProcessor:
    """
    A class for processing DataFrame columns with various cleaning and transformation operations.
    """

    def __init__(self, separator: str = "/") -> None:
        """
        Initialize the ColumnProcessor with a default separator.

        Args:
            separator: The separator character used for splitting values (default: "/")
        """
        self.separator = separator

    def _extract_raw_parts_from_value(self, value: str | None) -> list[str]:
        """
        Extract raw parts from a single value without any manipulation.

        Args:
            value: The value to extract parts from

        Returns:
            List of raw parts split by separator (empty list for null/NaN values)
        """
        if pd.isna(value) or is_str_nan(str(value)):
            return []

        # Convert to string and split on separator
        value_str = str(value)
        parts = value_str.split(self.separator)

        return parts

    def _clean_parts(self, parts: list[str]) -> list[str]:
        """
        Clean a list of parts by stripping whitespace and filtering out empty strings.

        Args:
            parts: List of raw parts to clean

        Returns:
            List of cleaned parts with whitespace stripped and empty strings filtered out
        """
        # Strip whitespace and filter out empty strings
        cleaned_parts = [part.strip() for part in parts if part.strip()]
        return cleaned_parts

    def _normalize_parts(self, parts: list[str]) -> list[str]:
        """
        Normalize a list of parts by converting them to uppercase.

        Args:
            parts: List of parts to normalize

        Returns:
            List of normalized parts converted to uppercase
        """
        # Convert to uppercase
        normalized_parts = [part.upper() for part in parts]
        return normalized_parts

    def _extract_and_clean_parts_from_value(self, value: str | None) -> list[str]:
        """
        Extract cleaned parts from a single value.

        Args:
            value: The value to extract parts from

        Returns:
            List of cleaned and uppercased parts (empty list for null/NaN values)
        """
        raw_parts = self._extract_raw_parts_from_value(value)
        cleaned_parts = self._clean_parts(raw_parts)
        normalized_parts = self._normalize_parts(cleaned_parts)

        return normalized_parts

    def sort_single_value(self, value: str | None) -> str:
        """
        Clean a single cell value by splitting at the separator, cleaning, and sorting.

        Args:
            value: The value to clean

        Returns:
            Cleaned and sorted string with parts separated by the configured separator
        """
        cleaned_parts = self._extract_and_clean_parts_from_value(value)

        if not cleaned_parts:
            return ""

        sorted_parts = sorted(cleaned_parts)

        # Join back with separator
        return self.separator.join(sorted_parts)

    def sort_separated_column(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """
        Sort a column containing separator-separated values by splitting on the separator,
        trimming whitespace, converting to uppercase, removing empty values, and sorting alphabetically.

        Args:
            df: DataFrame containing the column to clean
            column_name: Name of the column to clean

        Returns:
            DataFrame with cleaned column
        """
        df_copy = df.copy()

        if column_name not in df_copy.columns:
            msg = f"Column '{column_name}' not found in dataframe"
            raise ValueError(msg)

        logger.info(
            f"Cleaning '{column_name}' column: splitting on '{self.separator}', trimming, and sorting alphabetically"
        )
        df_copy[column_name] = df_copy[column_name].apply(self.sort_single_value)

        return df_copy


def fix_umsatzschwelle_typo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix typo in Umsatzschwelle column where "Umscatzschwelle" should be "Umsatzschwelle".

    Args:
        df: DataFrame containing the Umsatzschwelle column

    Returns:
        DataFrame with fixed typo in Umsatzschwelle column
    """
    UMSATZSCHWELLE = "Umsatzschwelle"
    UMSATZSCHWELLE_TYPO = "Umscatzschwelle"
    df_copy = df.copy()

    if COL_REVENUE_THRESHOLD not in df_copy.columns:
        raise RuntimeError(
            f"Column '{COL_REVENUE_THRESHOLD}' not found, skipping typo fix"
        )

    # Count occurrences before fixing
    mask = df_copy[COL_REVENUE_THRESHOLD].str.contains(UMSATZSCHWELLE, na=False)
    typo_count = mask.sum()

    if typo_count > 0:
        logger.info(
            f"Fixing typo '{UMSATZSCHWELLE_TYPO}' → '{UMSATZSCHWELLE}' in {typo_count} cells"
        )
        df_copy[COL_REVENUE_THRESHOLD] = df_copy[COL_REVENUE_THRESHOLD].str.replace(
            UMSATZSCHWELLE_TYPO, UMSATZSCHWELLE, regex=False
        )
        logger.info(f"Fixed {typo_count} typos in '{COL_REVENUE_THRESHOLD}' column")
    else:
        logger.info(f"No typos found in '{COL_REVENUE_THRESHOLD}' column")

    return df_copy


def standardize_date_column(
    df: pd.DataFrame, source_col: str, target_col: str
) -> pd.DataFrame:
    """
    Add standardized date column to dataframe if the date column exists.

    Args:
        df: DataFrame to process

    Returns:
        DataFrame with standardized date column added
    """
    df_copy = df.copy()

    if source_col in df_copy.columns:
        logger.info(f"Standardizing date format in column: {source_col}")
        df_copy[target_col] = df_copy[source_col].apply(standardize_date_format)
    else:
        raise RuntimeError(
            f"Date column '{source_col}' not found, skipping date standardization"
        )

    return df_copy


def create_aggregation_dict(
    columns: list[str],
) -> dict[str, Union[str, Callable[[Any], str]]]:
    agg_dict: dict[str, Union[str, Callable[[Any], str]]] = {}
    for col in columns:
        if "Risiko" in col:
            agg_dict[col] = "max"
        else:
            agg_dict[col] = lambda x: ", ".join(sorted(x.dropna().unique()))
    return agg_dict


def group_business_partners(df: pd.DataFrame) -> pd.DataFrame:
    available_cols = get_all_business_partner_columns(df)

    if not available_cols:
        raise ValueError("No business partner columns found in dataframe")

    if COL_BUSINESS_PARTNER_ID not in available_cols:
        raise ValueError("Business partner ID column not found")

    agg_dict = create_aggregation_dict(available_cols)

    result = df.groupby(COL_BUSINESS_PARTNER_ID).agg(agg_dict)

    return result  # type: ignore[return-value]


def parse_risk_column(col: str) -> tuple[str, str, str]:
    match = re.match(RISK_COLUMN_PATTERN, col)
    if match:
        risk_type = match.group(1).replace("-Risiko", "")
        tier = match.group(2)
        rechts = match.group(3)
        return (risk_type, tier, rechts)
    raise ValueError(f"Column '{col}' does not match expected risk column format")


def transform_risk_data_to_long_format(
    df: pd.DataFrame, exclude_maximales: bool = True
) -> pd.DataFrame:
    """Transform risk data from wide to long format with MultiIndex columns."""
    risk_pattern = re.compile(RISK_COLUMN_PATTERN)

    # Filter risk columns
    risk_cols = []
    for col in df.columns:
        if risk_pattern.match(col):
            if not exclude_maximales or not col.startswith("Maximales"):
                risk_cols.append(col)

    if not risk_cols:
        raise ValueError("No risk columns found in dataframe")

    # Keep only risk columns
    df_clean = df[risk_cols].copy()

    # Parse columns and create multi-index
    parsed_columns = [parse_risk_column(col) for col in df_clean.columns]
    valid_columns = [col for col in parsed_columns if col is not None]

    new_columns = pd.MultiIndex.from_tuples(
        valid_columns, names=[RISK_TYPE_COL, SUPPLIER_LEVEL_COL, LEGAL_POSITION_COL]
    )

    df_clean.columns = new_columns

    # Stack to create long format
    result = df_clean.stack([RISK_TYPE_COL, SUPPLIER_LEVEL_COL], future_stack=True)
    result = result.sort_index()

    return result  # type: ignore[return-value]


def reshape_risk_data(df_grouped: pd.DataFrame) -> pd.DataFrame:
    # Set business partner ID as index if it exists as a column
    if COL_BUSINESS_PARTNER_ID in df_grouped.columns:
        df_with_index = df_grouped.set_index(COL_BUSINESS_PARTNER_ID)
    else:
        df_with_index = df_grouped

    return transform_risk_data_to_long_format(df_with_index, exclude_maximales=True)


def add_maximum_risk_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add maximum risk columns for each tier and risk type combination."""
    df_copy = df.copy()

    tiers = ["T0", "T1", "Tn", "T1-n"]
    risk_types = ["Konkretes Risiko", "Brutto-Risiko", "Netto-Risiko"]

    tier_risk_combinations = product(tiers, risk_types)

    tier_risk_column_groups = {}
    for tier, risk_type in tier_risk_combinations:
        pattern = re.compile(f"^{risk_type} {tier} .*$")
        matching_columns = [col for col in df_copy.columns if pattern.match(col)]
        tier_risk_column_groups[(tier, risk_type)] = matching_columns
        assert len(matching_columns) == 10, (
            f"Expected 10 columns for {risk_type} {tier}, but got {len(matching_columns)}"
        )

    for (tier, risk_type), columns in tier_risk_column_groups.items():
        df_copy[f"Maximales {risk_type} {tier}"] = df_copy[columns].max(axis=1)

    return df_copy


def create_risk_per_branch_data(combined_df: pd.DataFrame) -> pd.DataFrame:
    """Create risk analysis aggregated by branch and country."""
    # Check if required columns exist
    required_cols = [BRANCH_DETAIL_COL, COUNTRY_COL]
    missing_cols = [col for col in required_cols if col not in combined_df.columns]
    if missing_cols:
        raise ValueError(f"Required columns missing: {missing_cols}")

    # Find risk columns for grouping
    risk_pattern = re.compile(RISK_COLUMN_PATTERN)
    risk_cols = [col for col in combined_df.columns if risk_pattern.match(col)]

    if not risk_cols:
        raise ValueError("No risk columns found in dataframe")

    # Group by branch and country, taking max risk values
    risk_by_branch_and_country: pd.DataFrame = combined_df.groupby(
        [BRANCH_DETAIL_COL, COUNTRY_COL]
    )[risk_cols].max()  # type: ignore[assignment]

    # Transform to long format using the common helper
    result = transform_risk_data_to_long_format(
        risk_by_branch_and_country, exclude_maximales=False
    )

    # Reorder index to: branch, type, tier, country
    result = result.reorder_levels(
        [BRANCH_DETAIL_COL, RISK_TYPE_COL, SUPPLIER_LEVEL_COL, COUNTRY_COL]
    )
    result = result.sort_index()

    return result  # type: ignore[return-value]


def process_resource_risks_data() -> pd.DataFrame:
    """Process resource risks data from parquet file."""
    data_dir = get_data_dir()
    input_path = data_dir / RESOURCE_RISKS_PARQUET

    if not input_path.exists():
        raise FileNotFoundError(f"Resource risks parquet file not found: {input_path}")

    logger.info("Processing resource risks data...")
    df = pd.read_parquet(input_path)

    df = df.rename(
        columns={
            "Durchschnittliches Rohstoffrisiko auf Basis statistischer Herkunftsländer": COL_ROHSTOFFNAME
        }
    )

    # Save processed data
    output_path = data_dir / RESOURCE_RISKS_PROCESSED_PARQUET
    df.to_parquet(output_path)
    logger.info(f"✓ Resource risks data processed and saved to {output_path}")

    return df


def clean_inconsistent_country_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean inconsistent country codes in the dataset by keeping only the first
    country code encountered for each business partner ID.

    Multiple country codes for the same business partner ID are considered
    data errors in the pseudonymized data and should be eliminated to ensure
    consistency across all derived datasets.

    Args:
        df: DataFrame with potential inconsistent country codes

    Returns:
        DataFrame with consistent country codes (first occurrence kept per business partner)
    """
    df_copy = df.copy()

    # Find business partners with multiple country codes
    country_per_partner = df_copy.groupby(COL_BUSINESS_PARTNER_ID)[
        COL_COUNTRY
    ].nunique()
    inconsistent_partners = country_per_partner[country_per_partner > 1].index

    if len(inconsistent_partners) > 0:
        logger.warning(
            f"Found {len(inconsistent_partners)} business partners with inconsistent country codes"
        )

        # For each inconsistent business partner, get the first country code encountered
        first_country_per_partner = df_copy.groupby(COL_BUSINESS_PARTNER_ID)[
            COL_COUNTRY
        ].first()

        # Update all rows for inconsistent partners to use the first country code
        for partner_id in inconsistent_partners:
            first_country = first_country_per_partner[partner_id]
            mask = df_copy[COL_BUSINESS_PARTNER_ID] == partner_id
            original_countries = df_copy.loc[mask, COL_COUNTRY].unique()

            logger.info(
                f"   Partner {partner_id}: {original_countries} → {first_country}"
            )
            df_copy.loc[mask, COL_COUNTRY] = first_country

        logger.info(
            f"✅ Country code inconsistencies resolved for {len(inconsistent_partners)} business partners"
        )
    else:
        logger.info("✅ No country code inconsistencies found")

    return df_copy


def clean_business_partner_name(dataframes: list[pd.DataFrame]) -> list[pd.DataFrame]:
    """
    Business partner names are not unique due to pseudonymization errors.
    This function makes sure that each business partner ID has a unique name among all dataframes.
    """

    dataframe_copies = [df.copy() for df in dataframes]

    for df in dataframe_copies:
        assert COL_BUSINESS_PARTNER_ID in df.columns, (
            f"{COL_BUSINESS_PARTNER_ID} column missing"
        )
        assert COL_BUSINESS_PARTNER_NAME in df.columns, (
            f"{COL_BUSINESS_PARTNER_NAME} column missing"
        )
        # check the type of columns
        assert df[COL_BUSINESS_PARTNER_ID].dtype == object, (
            f"{COL_BUSINESS_PARTNER_ID} column is not of type object"
        )
        assert df[COL_BUSINESS_PARTNER_NAME].dtype == object, (
            f"{COL_BUSINESS_PARTNER_NAME} column is not of type object"
        )
    # build a dictionary of business partner id to name
    partner_id_to_name: dict[str, str] = {}
    warned_partner_ids = set()

    for df in dataframe_copies:
        for _, row in df.iterrows():
            partner_id = row[COL_BUSINESS_PARTNER_ID]
            partner_name = row[COL_BUSINESS_PARTNER_NAME]
            if partner_id not in partner_id_to_name:
                partner_id_to_name[partner_id] = partner_name
            else:
                if (
                    partner_name != partner_id_to_name[partner_id]
                    and partner_id not in warned_partner_ids
                ):
                    logger.warning(
                        f"Business partner ID {partner_id} has multiple names: for example "
                        f"'{partner_id_to_name[partner_id]}' and '{partner_name}'. "
                        f"Using the first one for all entries."
                    )
                    warned_partner_ids.add(partner_id)

    # update all dataframes to use the name from the dictionary
    for df in dataframe_copies:
        df[COL_BUSINESS_PARTNER_NAME] = df[COL_BUSINESS_PARTNER_ID].map(
            partner_id_to_name
        )

    return dataframe_copies


def clean_revenue_values(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Clean revenue values by handling German number format and comma-separated values.

    Args:
        df: DataFrame to process
        column_name: Name of the revenue column to clean

    Returns:
        DataFrame with cleaned revenue values in a new column with '_clean' suffix
    """
    # Create a copy to avoid modifying the original DataFrame
    df_copy = df.copy()
    clean_col = column_name + "_clean"

    # Step 1: Keep only the first value of comma-separated revenue strings
    df_copy[clean_col] = df_copy[column_name].str.split(",").str[0]

    # Step 2: Convert German format → float
    # Remove thousand separators (dots) and convert decimal separator (comma to dot)
    try:
        df_copy[clean_col] = (
            df_copy[clean_col]
            .str.replace(".", "", regex=False)  # Remove thousand separator
            .str.replace(",", ".", regex=False)  # Convert comma to dot for decimal
        )
        df_copy[clean_col] = pd.to_numeric(df_copy[clean_col], errors="coerce")
    except Exception as e:
        print(f"Warning: Error converting revenue values to numeric: {e}")
        return df_copy

    return df_copy


def rename_concrete_file_columns(concrete_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns in concrete file to match brutto file column naming
    """
    concrete_df = concrete_df.copy()

    # Rename the article designation column to match brutto file
    old_name = COL_ID_ARTICLE_NAME_CONCRETE_FILE
    new_name = COL_ID_ARTICLE_NAME

    logger.info(f"Renaming column '{old_name}' to '{new_name}'")
    concrete_df = concrete_df.rename(columns={old_name: new_name})
    logger.info(f"✓ Column renamed successfully")

    return concrete_df


def drop_ust_id_and_unique_article_id_columns(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Drop columns that do not provide information
    """
    brutto_df_copy = brutto_df.copy()
    concrete_df_copy = concrete_df.copy()

    brutto_df_copy = brutto_df_copy.drop(columns=[COL_BUSINESS_PARTNER_UST_ID])
    logger.info(f"   Dropped {COL_BUSINESS_PARTNER_UST_ID} from brutto_df")

    concrete_df_copy = concrete_df_copy.drop(columns=[COL_ID_ARTICLE_UNIQUE])
    logger.info(f"   Dropped {COL_ID_ARTICLE_UNIQUE} from concrete_df")

    return brutto_df_copy, concrete_df_copy


def create_and_save_business_partners(combined_df: pd.DataFrame) -> pd.DataFrame:
    business_partner_grouped = group_business_partners(combined_df)
    business_partner_grouped = add_maximum_risk_columns(business_partner_grouped)

    # Clean revenue values before exporting data to parquet
    if COL_REVENUE_TOTAL in business_partner_grouped.columns:
        print(f"Cleaning revenue values in column: {COL_REVENUE_TOTAL}")
        business_partner_grouped = clean_revenue_values(
            business_partner_grouped, COL_REVENUE_TOTAL
        )
    else:
        print(
            f"Warning: Revenue column '{COL_REVENUE_TOTAL}' not found, skipping revenue cleaning"
        )

    output_path = get_data_dir() / BUSINESS_PARTNERS_PARQUET
    business_partner_grouped.to_parquet(output_path)

    return business_partner_grouped


def create_and_save_risk_per_business_partner(
    business_partner_grouped: pd.DataFrame,
) -> None:
    risk_data = reshape_risk_data(business_partner_grouped)
    output_path = get_data_dir() / RISK_PER_BUSINESS_PARTNER_PARQUET
    risk_data.to_parquet(output_path)


def create_and_save_risk_per_branch(combined_df: pd.DataFrame) -> None:
    risk_per_branch = create_risk_per_branch_data(combined_df)
    output_path = get_data_dir() / RISK_PER_BRANCH_PARQUET
    risk_per_branch.to_parquet(output_path)


def split_dataframe_by_data_source(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataframe into two based on data source values."""
    assert_split_into_two_distinct_data_sources(df)

    df_hw = df[df[COL_DATA_SOURCE] == DATA_SOURCE_HW].copy()
    df_nhw = df[df[COL_DATA_SOURCE] == DATA_SOURCE_NHW].copy()

    return df_hw, df_nhw


def split_and_merge_brutto_and_concrete_along_data_source_column(
    brutto_df_cleaned: pd.DataFrame,
    concrete_df_cleaned: pd.DataFrame,
    create_conflicts_files: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merges brutto and concrete dataframes after split in data source values"""
    brutto_hw_dataframe, brutto_nhw_dataframe = split_dataframe_by_data_source(
        brutto_df_cleaned
    )
    concrete_hw_dataframe, concrete_nhw_dataframe = split_dataframe_by_data_source(
        concrete_df_cleaned
    )
    logger.info("Joining brutto and concrete datasets on pseudo primary key columns...")

    # We merge the brutto and concrete dataframes with preference for the brutto file because the brutto file
    # contains the "ground truth" before risk assessment were added by the third party supplier
    merged_hw_df, conflicts_hw = outer_merge_with_left_preference(
        brutto_hw_dataframe,
        concrete_hw_dataframe,
        keys=list(HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS),
    )
    merged_nhw_df, conflicts_nhw = outer_merge_with_left_preference(
        brutto_nhw_dataframe,
        concrete_nhw_dataframe,
        keys=list(NICHT_HANDELSWARE_PSEUDO_PRIMARY_KEY_COMPONENT_COLUMNS),
    )

    if create_conflicts_files:
        conflicts_hw_output_path = get_data_dir() / CONFLICTS_HW_PARQUET
        conflicts_nhw_output_path = get_data_dir() / CONFLICTS_NHW_PARQUET

        conflicts_hw.to_parquet(conflicts_hw_output_path)
        conflicts_nhw.to_parquet(conflicts_nhw_output_path)

    return merged_hw_df, merged_nhw_df


def clean_original_dataframes(
    brutto_df: pd.DataFrame, concrete_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    concrete_df_copy = concrete_df.copy()
    brutto_df_copy = brutto_df.copy()

    logger.info("Renaming concrete file columns...")
    concrete_df_copy_renamed = rename_concrete_file_columns(concrete_df_copy)
    del concrete_df_copy
    gc.collect()

    concrete_df_copy_cleaned_ids = clean_business_partner_id_columns(
        concrete_df_copy_renamed
    )
    del concrete_df_copy_renamed
    gc.collect()

    brutto_df_copy_cleaned_id = clean_business_partner_id_columns(brutto_df_copy)
    del brutto_df_copy
    gc.collect()

    concrete_df_copy_cleaned_country_codes = clean_inconsistent_country_codes(
        concrete_df_copy_cleaned_ids
    )
    del concrete_df_copy_cleaned_ids
    gc.collect()

    brutto_df_copy_cleaned_country_codes = clean_inconsistent_country_codes(
        brutto_df_copy_cleaned_id
    )
    del brutto_df_copy_cleaned_id
    gc.collect()

    concrete_df_renamed = rename_estell_sektor_columns(
        concrete_df_copy_cleaned_country_codes
    )
    del concrete_df_copy_cleaned_country_codes
    gc.collect()

    brutto_df_renamed = rename_estell_sektor_columns(
        brutto_df_copy_cleaned_country_codes
    )
    del brutto_df_copy_cleaned_country_codes
    gc.collect()

    logger.info("Sorting Risikorohstoffe column...")
    column_processor = ColumnProcessor(separator="/")

    brutto_df_copy_sorted = column_processor.sort_separated_column(
        brutto_df_renamed, COL_RISIKOROHSTOFFE
    )
    assert brutto_df_copy_sorted.shape == brutto_df_renamed.shape
    del brutto_df_renamed
    gc.collect()

    logger.info("Fixing Umsatzschwelle typo...")
    brutto_df_copy_sorted_typo_fixed = fix_umsatzschwelle_typo(brutto_df_copy_sorted)
    assert brutto_df_copy_sorted_typo_fixed.shape == brutto_df_copy_sorted.shape
    del brutto_df_copy_sorted
    gc.collect()

    logger.info("Fix partner names...")
    brutto_df_copy_partner_fixed, concrete_df_copy_partner_fixed = (
        clean_business_partner_name(
            [brutto_df_copy_sorted_typo_fixed, concrete_df_renamed]
        )
    )
    assert isinstance(brutto_df_copy_partner_fixed, pd.DataFrame)
    assert isinstance(concrete_df_copy_partner_fixed, pd.DataFrame)
    del brutto_df_copy_sorted_typo_fixed
    del concrete_df_renamed
    gc.collect()

    assert_column_depends_on_other_column(
        brutto_df_copy_partner_fixed, COL_BUSINESS_PARTNER_NAME
    )
    assert_column_depends_on_other_column(
        concrete_df_copy_partner_fixed, COL_BUSINESS_PARTNER_NAME
    )

    logger.info("Dropping unnecessary columns...")
    brutto_df_copy_dropped, concrete_df_copy_dropped = (
        drop_ust_id_and_unique_article_id_columns(
            brutto_df_copy_partner_fixed, concrete_df_copy_partner_fixed
        )
    )
    del brutto_df_copy_partner_fixed
    del concrete_df_copy_partner_fixed
    gc.collect()

    logger.info("Removing duplicate rows...")
    brutto_df_dedup = brutto_df_copy_dropped.drop_duplicates()
    logger.info(
        f"deduplication of brutto_df changed the number of rows from {brutto_df_copy_dropped.shape[0]} to {brutto_df_dedup.shape[0]}"
    )

    concrete_df_dedup = concrete_df_copy_dropped.drop_duplicates()
    logger.info(
        f"deduplication of concrete_df changed the number of rows from {concrete_df_copy_dropped.shape[0]} to {concrete_df_dedup.shape[0]}"
    )

    assert brutto_df_dedup.shape[0] <= brutto_df_copy_dropped.shape[0]
    assert brutto_df_dedup.shape[1] == brutto_df_copy_dropped.shape[1]
    assert concrete_df_dedup.shape[0] <= concrete_df_copy_dropped.shape[0]
    assert concrete_df_dedup.shape[1] == concrete_df_copy_dropped.shape[1]

    return brutto_df_dedup, concrete_df_dedup


def create_derived_dataframes(
    brutto_df_cleaned: pd.DataFrame, concrete_df_cleaned: pd.DataFrame
) -> None:
    logger.info("=== Creating Derived Dataframes ===")

    logger.info("Joining datasets to build transactions dataframe...")
    handelsware_df, nicht_handelsware_df = (
        split_and_merge_brutto_and_concrete_along_data_source_column(
            brutto_df_cleaned, concrete_df_cleaned
        )
    )

    logger.info("Concatenate datasets for downstream aggregations...")
    combined_df = pd.concat(
        [
            handelsware_df,
            nicht_handelsware_df,
        ],
        ignore_index=True,
    )

    assert_column_depends_on_other_column(combined_df, COL_BUSINESS_PARTNER_NAME)

    logger.info(
        f"   Combined dataset: {len(combined_df)} rows, {len(combined_df.columns)} columns"
    )

    logger.info("Cleaning inconsistent country codes...")
    combined_df_clean = clean_inconsistent_country_codes(combined_df)
    assert COL_ESTELL_SEKTOR_GROB_RENAMED in combined_df_clean.columns
    assert COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED in combined_df_clean.columns
    logger.info("   ✅ Country code cleaning complete")

    logger.info("Standardizing date formats...")
    combined_df_date_standardized = standardize_date_column(
        combined_df_clean,
        COL_BETRACHTUNGSZEITRAUM_RANGE,
        "standardized_date",
    )
    logger.info("   ✅ Date standardization complete")

    logger.info("Processing date ranges into start and end dates...")
    combined_df_date_standardized[COL_BETRACHTUNGSZEITRAUM_START] = (
        combined_df_date_standardized["standardized_date"].str.split("-").str[0]
    )
    combined_df_date_standardized[COL_BETRACHTUNGSZEITRAUM_ENDE] = (
        combined_df_date_standardized["standardized_date"].str.split("-").str[1]
    )
    combined_df_date_standardized = combined_df_date_standardized.drop(
        columns=["standardized_date", COL_BETRACHTUNGSZEITRAUM_RANGE]
    )
    logger.info("   ✅ Date range processing complete")

    logger.info("Saving transactions data...")
    transactions_output_path = get_data_dir() / TRANSACTIONS_PARQUET
    combined_df_date_standardized.to_parquet(transactions_output_path)
    file_size = os.path.getsize(transactions_output_path) / (1024 * 1024)  # MB
    logger.info(
        f"   ✅ Transactions data saved ({file_size:.2f} MB): {transactions_output_path}"
    )

    logger.info("Creating business partners data...")
    business_partner_grouped = create_and_save_business_partners(combined_df_clean)
    logger.info(
        f"   ✅ Business partners data created: {len(business_partner_grouped)} unique partners"
    )

    logger.info("Creating risk per business partner data...")
    create_and_save_risk_per_business_partner(business_partner_grouped)
    logger.info("   ✅ Risk per business partner data created")

    logger.info("Creating risk per branch data...")
    create_and_save_risk_per_branch(combined_df_clean)
    logger.info("   ✅ Risk per branch data created")

    logger.info("Processing resource risks data...")
    process_resource_risks_data()
    logger.info("   ✅ Resource risks data processed")

    logger.info("All derived dataframes created successfully!")
    logger.info("   Generated files:")
    for filename in EXPECTED_OUTPUT_FILES:
        file_path = get_data_dir() / filename
        if file_path.exists():
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            logger.info(f"   ✅ {filename} ({file_size:.2f} MB)")
        else:
            raise RuntimeError(f"   ⚠️  {filename} (missing)")


def convert_excel_file_to_parquet(
    input_filename: str, output_filename: str, skip_rows: int = 2
) -> bool:
    data_dir = str(get_data_dir())
    input_path = os.path.join(data_dir, input_filename)
    output_path = os.path.join(data_dir, output_filename)

    if not os.path.exists(input_path):
        logger.error(f"❌ File not found: {input_filename}")
        raise FileNotFoundError

    logger.info(f"📊 Converting {input_filename} to Parquet format...")
    logger.info(f"   Source: {input_path}")
    logger.info(f"   Target: {output_path}")
    logger.info(f"   Skipping first {skip_rows} rows")

    # Load Excel file
    logger.info("   Reading Excel file...")
    df = pd.read_excel(input_path, skiprows=skip_rows)
    logger.info(f"   Loaded {len(df)} rows and {len(df.columns)} columns")

    # Convert all columns to string initially
    logger.info("   Converting columns to string format...")
    for col in df.columns:
        df[col] = df[col].astype(str)

    # Process risk columns with special mapping
    risk_cols = [
        col for col in df.columns if any(prefix in col for prefix in RISK_COL_PREFIXES)
    ]
    if risk_cols:
        logger.info(f"  Processing {len(risk_cols)} risk columns with risk mapping...")
        for col in risk_cols:
            df[col] = df[col].replace(RISK_MAP).astype("float64")
    else:
        logger.info("   No risk columns found for mapping")

    # Save to Parquet
    logger.info("   Saving to Parquet format...")
    df.to_parquet(output_path)

    # Get file size for logger
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    logger.info(f"✅ {input_filename} conversion complete ({file_size:.2f} MB)")
    return True


def convert_excel_to_parquet() -> None:
    logger.info("=== Excel to Parquet Conversion ===")
    files_to_convert = [
        (BRUTTO_FILE_EXCEL, BRUTTO_FILE_PARQUET, 2),
        (CONCRETE_FILE_EXCEL, CONCRETE_FILE_PARQUET, 2),
        (RESOURCE_RISKS_EXCEL, RESOURCE_RISKS_PARQUET, 0),
    ]

    logger.info(
        f"Starting conversion of {len(files_to_convert)} Excel files to Parquet format"
    )

    for i, (input_file, output_file, skip_rows) in enumerate(files_to_convert, 1):
        logger.info(f"Processing file {i}/{len(files_to_convert)}: {input_file}")
        convert_excel_file_to_parquet(input_file, output_file, skip_rows)

    logger.info(f"Excel to Parquet conversion completed successfully!")
    logger.info(f"   Processed {len(files_to_convert)} files")


def convert_parquet_to_excel() -> None:
    logger.info("=== Parquet to Excel Conversion ===")
    files_to_convert = [
        (BRUTTO_FILE_CLEANED_PARQUET, BRUTTO_FILE_CLEANED_EXCEL),
        (CONCRETE_FILE_CLEANED_PARQUET, CONCRETE_FILE_CLEANED_EXCEL),
        (TRANSACTIONS_PARQUET, TRANSACTIONS_EXCEL),
        (CONFLICTS_HW_PARQUET, CONFLICTS_HW_EXCEL),
        (CONFLICTS_NHW_PARQUET, CONFLICTS_NHW_EXCEL),
    ]

    logger.info(
        f"Starting conversion of {len(files_to_convert)} Parquet files to Excel format"
    )

    for i, (input_file, output_file) in enumerate(files_to_convert, 1):
        logger.info(f"Processing file {i}/{len(files_to_convert)}: {input_file}")
        pd.read_parquet(get_data_dir() / input_file).to_excel(
            get_data_dir() / output_file
        )

    logger.info(f"Parquet to Excel conversion completed successfully!")
    logger.info(f"   Processed {len(files_to_convert)} files")


def check_raw_files_exist() -> bool:
    data_dir = get_data_dir()
    return all((data_dir / filename).exists() for filename in EXPECTED_RAW_FILES)


def check_output_files_exist() -> bool:
    data_dir = get_data_dir()
    return all((data_dir / filename).exists() for filename in EXPECTED_OUTPUT_FILES)


def data_preparation() -> None:
    """
    Main data preparation function that orchestrates the entire pipeline.

    This function handles:
    1. Converting Excel files to Parquet format (3 files)
    2. Creating derived dataframes (8 processing steps)
    """

    start_time = time.time()

    logger.info("=" * 60)
    logger.info("STARTING DATA PREPARATION PIPELINE")
    logger.info("=" * 60)
    logger.info("Pipeline Overview:")
    logger.info("  Phase 1: Excel to Parquet conversion (3 files)")
    logger.info("  Phase 2: Derived dataframes creation (9 steps)")
    logger.info("")

    # Phase 1: Excel to Parquet conversion
    phase1_start = time.time()
    logger.info("PHASE 1: Excel to Parquet Conversion")
    logger.info("-" * 40)
    try:
        convert_excel_to_parquet()
        phase1_time = time.time() - phase1_start
        logger.info(f"✅ Phase 1 completed in {phase1_time:.2f} seconds")
    except Exception as e:
        logger.error(f"❌ Phase 1 failed: {str(e)}")
        raise

    logger.info("")

    # Data Cleaning
    logger.info("=== Data Cleaning ===")
    brutto_df_cleaned, concrete_df_cleaned = clean_original_dataframes(
        brutto_df=load_dataset_from_path(get_data_dir() / BRUTTO_FILE_PARQUET),
        concrete_df=load_dataset_from_path(get_data_dir() / CONCRETE_FILE_PARQUET),
    )
    brutto_df_cleaned.to_parquet(get_data_dir() / BRUTTO_FILE_CLEANED_PARQUET)
    concrete_df_cleaned.to_parquet(get_data_dir() / CONCRETE_FILE_CLEANED_PARQUET)

    # Phase 2: Create derived dataframes
    phase2_start = time.time()
    logger.info("PHASE 2: Derived Dataframes Creation")
    logger.info("-" * 40)
    try:
        create_derived_dataframes(brutto_df_cleaned, concrete_df_cleaned)
        phase2_time = time.time() - phase2_start
        logger.info(f"✅ Phase 2 completed in {phase2_time:.2f} seconds")
    except Exception as e:
        logger.error(f"❌ Phase 2 failed: {str(e)}")
        raise

    # Final summary
    total_time = time.time() - start_time
    logger.info("")
    logger.info("=" * 60)
    logger.info("DATA PREPARATION PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)
    logger.info(f"Total execution time: {total_time:.2f} seconds")
    logger.info(f"   Phase 1 (Excel conversion): {phase1_time:.2f}s")
    logger.info(f"   Phase 2 (Derived dataframes): {phase2_time:.2f}s")
    logger.info("")
    logger.info("Output files ready for use:")
    data_dir = get_data_dir()
    for filename in EXPECTED_OUTPUT_FILES:
        file_path = data_dir / filename
        if file_path.exists():
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            logger.info(f"   ✅ {filename} ({file_size:.2f} MB)")
    logger.info("=" * 60)


def assert_column_depends_on_other_column(
    df: pd.DataFrame,
    dependant_column: str,
    independent_columns: list[str] = [COL_BUSINESS_PARTNER_ID],
    allowed_number_of_ids_multiple_values: int = 0,
) -> None:
    id_column_value_counts = df.groupby(independent_columns)[dependant_column].nunique()
    ids_with_multiple_column_values = id_column_value_counts[id_column_value_counts > 1]

    if len(ids_with_multiple_column_values) > allowed_number_of_ids_multiple_values:
        raise AssertionError(
            f"Some values of the columns '{independent_columns}' exist with different values in the column '{dependant_column}'. There are {len(ids_with_multiple_column_values)} ids with multiple values."
        )


if __name__ == "__main__":
    data_preparation()
