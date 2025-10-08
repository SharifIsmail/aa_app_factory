from pathlib import Path

import pandas
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_BUSINESS_PARTNER_ID,
    COL_DATA_SOURCE,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.utils.products_utils import (
    create_categorized_products_dataframe,
    get_required_columns_for_categorization,
)
from service.data_loading import load_dataset_from_path


class BusinessPartnerProductsTool(Tool):
    name = "get_business_partner_products"
    inputs = {
        "business_partner_id": {
            "type": "string",
            "description": f"The id ('{COL_BUSINESS_PARTNER_ID}') of the business partner to get the products/articles for.",
        }
    }
    output_type = "any"
    description = (
        "This tool retrieves all products/articles with their categories/groups from a specific business partner. "
        f"It returns a pandas.DataFrame containing the unique articles ('{COL_ARTICLE_NAME}') "
        "The return value of this tool is suitable to be returned to the user. "
        "Usage example: "
        "products_df = get_business_partner_products('1514') # returns dataframe with articles and categories/groups"
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

    def forward(self, business_partner_id: str) -> pandas.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"business_partner_id": business_partner_id},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        if business_partner_id.lower() == "all":
            raise ValueError(
                "'ALL' is not a valid business partner ID. You need to provide a specific business partner ID to use this tool."
            )

        required_columns = get_required_columns_for_categorization()
        df = load_dataset_from_path(self.file_path, columns=required_columns)
        bp_transactions = df[df[COL_BUSINESS_PARTNER_ID] == business_partner_id]

        if bp_transactions.empty:
            raise ValueError(
                f"No transactions found for business partner ID: {business_partner_id}"
            )

        # Get unique combinations of article and categorization-relevant columns
        unique_products = bp_transactions.drop_duplicates(
            subset=[COL_ARTICLE_NAME, COL_DATA_SOURCE]
        )

        return create_categorized_products_dataframe(unique_products)
