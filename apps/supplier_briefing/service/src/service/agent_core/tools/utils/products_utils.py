from __future__ import annotations

from typing import Any, Optional, Tuple

import pandas

from service.agent_core.constants import (
    DATA_SOURCE_HW,
    DATA_SOURCE_NHW,
)
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_BUSINESS_PARTNER_ID,
    COL_COUNTRY,
    COL_DATA_SOURCE,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_FRUIT_VEG_GROUP,
    COL_UNTERWARENGRUPPE,
    EMPTY_VALUES,
    OUTPUT_COL_ARTICLE_CATEGORY,
    OUTPUT_COL_ARTICLE_CATEGORY_SOURCE,
)
from service.agent_core.data_management.paths import get_data_dir
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNERS_PARQUET


def is_empty_value(value: Any) -> bool:
    """Check if value is considered empty (N.A., nan, empty string, None)."""
    if pandas.isna(value):
        return True
    str_value = str(value).strip()
    return str_value in EMPTY_VALUES


def get_business_partner_data_if_needed(
    transactions_df: pandas.DataFrame,
) -> Optional[pandas.DataFrame]:
    """Load business partner data if NHW transactions are present."""
    nhw_items = transactions_df[transactions_df[COL_DATA_SOURCE] == DATA_SOURCE_NHW]

    if nhw_items.empty:
        return None

    bp_file_path = get_data_dir() / BUSINESS_PARTNERS_PARQUET
    return load_dataset_from_path(
        bp_file_path, columns=[COL_BUSINESS_PARTNER_ID, COL_ESTELL_SEKTOR_GROB_RENAMED]
    )


def determine_product_category(
    row: pandas.Series, business_partner_data: Optional[pandas.DataFrame] = None
) -> Tuple[str, str]:
    data_source = row[COL_DATA_SOURCE]

    if data_source == DATA_SOURCE_NHW:
        category = ""
        category_source = COL_ESTELL_SEKTOR_GROB_RENAMED

        if business_partner_data is not None:
            business_partner_id = row[COL_BUSINESS_PARTNER_ID]
            bp_row = business_partner_data[
                business_partner_data[COL_BUSINESS_PARTNER_ID] == business_partner_id
            ]
            if not bp_row.empty:
                estell_value = bp_row.iloc[0][COL_ESTELL_SEKTOR_GROB_RENAMED]
                if not is_empty_value(estell_value):
                    category = estell_value

    elif data_source == DATA_SOURCE_HW:
        fruit_veg_value = row[COL_FRUIT_VEG_GROUP]

        if not is_empty_value(fruit_veg_value):
            category = (
                row[COL_ARTIKELFAMILIE]
                if not is_empty_value(row[COL_ARTIKELFAMILIE])
                else ""
            )
            category_source = COL_ARTIKELFAMILIE
        else:
            category = (
                row[COL_UNTERWARENGRUPPE]
                if not is_empty_value(row[COL_UNTERWARENGRUPPE])
                else ""
            )
            category_source = COL_UNTERWARENGRUPPE

    else:
        category = ""
        category_source = ""

    return category, category_source


def get_required_columns_for_categorization() -> list[str]:
    return [
        COL_BUSINESS_PARTNER_ID,
        COL_ARTICLE_NAME,
        COL_DATA_SOURCE,
        COL_UNTERWARENGRUPPE,
        COL_ARTIKELFAMILIE,
        COL_FRUIT_VEG_GROUP,
    ]


def get_required_columns_for_country_products() -> list[str]:
    return [
        COL_BUSINESS_PARTNER_ID,
        COL_ARTICLE_NAME,
        COL_DATA_SOURCE,
        COL_COUNTRY,
        COL_UNTERWARENGRUPPE,
        COL_ARTIKELFAMILIE,
        COL_FRUIT_VEG_GROUP,
    ]


def create_categorized_products_dataframe(
    unique_products: pandas.DataFrame,
) -> pandas.DataFrame:
    business_partner_data = get_business_partner_data_if_needed(unique_products)

    result_data = []
    for _, row in unique_products.iterrows():
        article_name = row[COL_ARTICLE_NAME]
        category, category_source = determine_product_category(
            row, business_partner_data
        )

        result_data.append(
            {
                COL_ARTICLE_NAME: article_name,
                OUTPUT_COL_ARTICLE_CATEGORY: category,
                OUTPUT_COL_ARTICLE_CATEGORY_SOURCE: category_source,
            }
        )

    result_df = pandas.DataFrame(result_data)
    result_df = result_df.drop_duplicates(subset=[COL_ARTICLE_NAME])
    return result_df
