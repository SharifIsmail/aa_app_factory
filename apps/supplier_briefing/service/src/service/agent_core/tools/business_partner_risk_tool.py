from pathlib import Path

import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import COL_BUSINESS_PARTNER_ID
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path


class BusinessPartnerRiskTool(Tool):
    name = "get_business_partner_risk_matrix"
    inputs = {
        "business_partner_id": {
            "type": "string",
            "description": f"The id ('{COL_BUSINESS_PARTNER_ID}') of the business partner to get the risk matrix for.",
        },
        "risk_type": {
            "type": "string",
            "description": "The type of risk to retrieve ('Brutto', 'Netto', 'Konkretes'). ",
        },
        "risk_tier": {
            "type": "string",
            "description": "The risk tier to filter by ('T0', 'T1', 'T1-n', 'Tn'). If not specified, all tiers will be included.",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool retrieves risk data for a business partner. "
        "It returns a pandas.DataFrame or pandas.Series containing the risk information. "
        "The return value of this tool is suitable to be returned to the user. "
        "Usage examples: "
        "risk_matrix_df = get_business_partner_risk_matrix('10000', 'Konkretes Risiko') # returns dataframe with risk_tier as index, legal position as columns and risk values as data. "
        "risk_values_series = get_business_partner_risk_matrix('10000', 'Brutto', 'T1') # returns series with risk values for T1 tier. "
    )

    def __init__(
        self,
        risk_per_business_partner_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = risk_per_business_partner_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

    def forward(
        self, business_partner_id: str, risk_type: str, risk_tier: str | None = None
    ) -> pandas.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"business_partner_id": business_partner_id},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        df = load_dataset_from_path(self.file_path)
        try:
            risk_matrix = df.loc[
                business_partner_id, risk_type, risk_tier or slice(None)
            ]
        except KeyError as e:
            error_msg = f"Either the business partner ID '{business_partner_id}' or the risk type '{risk_type}' does not exist in the data."
            logger.error(error_msg)
            raise KeyError(error_msg) from e
        if risk_matrix.empty:
            raise ValueError(
                f"No data found for business partner ID: {business_partner_id} and risk type: {risk_type}"
            )

        logger.info(f"Generated risk matrix data for ID: {business_partner_id}")

        return risk_matrix
