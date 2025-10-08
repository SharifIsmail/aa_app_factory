from pathlib import Path

import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.constants import (
    DATA_SOURCE_HW,
)
from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_COUNTRY,
    COL_DATA_SOURCE,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.utils.products_utils import (
    create_categorized_products_dataframe,
    get_required_columns_for_country_products,
    is_empty_value,
)
from service.data_loading import load_dataset_from_path


class ProductsByCountryTool(Tool):
    name = "get_products_by_country"
    inputs = {
        "country_code": {
            "type": "string",
            "description": "The ISO country code (3-letter) of the country to search for products from (e.g., 'IND' for India, 'DEU' for Germany, 'USA' for United States).",
        },
        "include_trading_goods_only": {
            "type": "boolean",
            "description": "If true, only include products from 'Datenerfassung Handelsware (HW)' data source. If false, include all products regardless of data source. Defaults to true.",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool retrieves all products/articles with their categories sourced from business partners in a specific country. "
        "It returns a pandas.DataFrame containing unique articles and their appropriate categories/groups based on product type. "
        f"'ALL' is not a valid country code. The tool filters by country code ('{COL_COUNTRY}') and optionally "
        f"by data source to include only trading goods ('{DATA_SOURCE_HW}'). "
        "The return value of this tool is suitable to be returned to the user. "
        "If the tool does not return any results or matches you are searching for, it means we do not source the product from that country. "
        "Usage examples: "
        "products_df = get_products_by_country('IND') # returns dataframe with products from India (trading goods only) "
        "all_products_df = get_products_by_country('DEU', False) # returns all products from Germany"
    )

    def __init__(
        self,
        transaction_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = transaction_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

    def forward(
        self, country_code: str, include_trading_goods_only: bool = True
    ) -> pandas.DataFrame:
        if country_code.lower() == "all":
            raise ValueError(
                "'country_code' cannot be 'all', it is has to be a specific country."
            )
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "country_code": country_code,
                "include_trading_goods_only": include_trading_goods_only,
            },
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        # Load data with required columns for categorization
        required_columns = get_required_columns_for_country_products()
        df = load_dataset_from_path(self.file_path, columns=required_columns)

        # Create mask for country origin of business partner
        country_mask = df[COL_COUNTRY].isin([country_code])

        # Optionally filter by data source (trading goods only)
        if include_trading_goods_only:
            data_source_mask = df[COL_DATA_SOURCE] == DATA_SOURCE_HW
            mask = country_mask & data_source_mask
        else:
            mask = country_mask

        # Filter transactions
        results = df.loc[mask]

        if results.empty:
            raise ValueError(
                f"No transactions found for country code: {country_code}. We either do not have any transactions from the country you provided or the country code (three digit) was incorrect."
            )

        # Get unique combinations of article and categorization-relevant columns
        unique_products = results.drop_duplicates(
            subset=[COL_ARTICLE_NAME, COL_DATA_SOURCE]
        )

        # Filter out N.A. values from article names
        unique_products = unique_products[
            ~unique_products[COL_ARTICLE_NAME].apply(is_empty_value)
        ]

        result_df = create_categorized_products_dataframe(unique_products)

        logger.info(
            f"Found {len(result_df)} unique products from country {country_code} "
            f"(trading goods only: {include_trading_goods_only})"
        )

        return result_df
