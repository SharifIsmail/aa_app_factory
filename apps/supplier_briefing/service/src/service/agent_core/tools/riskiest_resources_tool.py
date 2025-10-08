from pathlib import Path

import pandas as pd
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_RISKIEST_RESOURCE_BRUTTO,
    COL_RISKIEST_RESOURCE_KONKRET,
    COL_RISKIEST_RESOURCE_NETTO,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path


class RiskiestResourcesOfBusinessPartnerTool(Tool):
    name = "riskiest_resources_for_business_partner"
    inputs = {
        "business_partner_id": {
            "type": "string",
            "description": f"The id ('{COL_BUSINESS_PARTNER_ID}') of the business partner to analyze.",
        },
        "risk_type": {
            "type": "string",
            "description": "The type of riskiest resources to analyze. Options: 'konkret' (default), 'brutto', 'netto'.",
            "default": "konkret",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool finds the riskiest resources associated with a specific business partner."
        "It returns a pandas.DataFrame containing unique risky resources from the "
        "specified risk type column ('konkreter Risikoreichster Rohstoff', "
        "'Brutto Risikoreichster Rohstoff', or 'Netto Risikoreichster Rohstoff'). "
        "If the user does not specify a type, assume 'konkret'. "
        "Usage example: "
        "risky_resources = riskiest_resources_for_business_partner('1514', 'konkret') "
        "# Returns: DataFrame with columns: ['konkreter Risikoreichster Rohstoff']"
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
        self, business_partner_id: str, risk_type: str = "konkret"
    ) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"business_partner_id": business_partner_id, "type": risk_type},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        column_mapping = {
            "konkret": COL_RISKIEST_RESOURCE_KONKRET,
            "brutto": COL_RISKIEST_RESOURCE_BRUTTO,
            "netto": COL_RISKIEST_RESOURCE_NETTO,
        }

        if risk_type not in column_mapping:
            raise ValueError(
                f"Invalid type '{risk_type}'. Must be one of: {list(column_mapping.keys())}"
            )

        riskiest_resource_col = column_mapping[risk_type]
        required_columns = [COL_BUSINESS_PARTNER_ID, riskiest_resource_col]

        transactions = load_dataset_from_path(self.file_path, columns=required_columns)

        if riskiest_resource_col not in transactions.columns:
            raise ValueError(
                f"Column '{riskiest_resource_col}' not found in the dataset."
            )

        bp_transactions = transactions[
            transactions[COL_BUSINESS_PARTNER_ID] == business_partner_id
        ]

        if bp_transactions.empty:
            raise ValueError(
                f"Could not find the business partner with the id {business_partner_id}."
            )

        riskiest_resources = bp_transactions[riskiest_resource_col].unique()

        riskiest_resources = [
            resource for resource in riskiest_resources if resource is not None
        ]

        riskiest_resources_df = pd.DataFrame(
            riskiest_resources,
            columns=[riskiest_resource_col],
        )

        return riskiest_resources_df
