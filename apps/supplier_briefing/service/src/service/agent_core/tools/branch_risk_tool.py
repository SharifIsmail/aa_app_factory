from pathlib import Path

import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path

RISK_TYPE_OPTIONS = ["Brutto", "Netto", "Konkretes Risiko"]
DEFAULT_RISK_TYPE = "Brutto"
SUPPLIER_TIER_OPTIONS = ["T0", "T1", "Tn", "T1-n"]
DEFAULT_SUPPLIER_TIER = "T0"


class BranchRiskTool(Tool):
    name = "get_branch_risk_matrix"
    inputs = {
        "branch_name": {
            "type": "string",
            "description": f"The branch name ('{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}') to get the risk matrix for.",
        },
        "risk_type": {
            "type": "string",
            "description": "The type of risk to retrieve ('Brutto', 'Netto', 'Konkretes Risiko'). "
            "If not specified, the tool will return data for all risk types.",
        },
        "supplier_tier": {
            "type": "string",
            "description": "The supplier tier to analyze ('T0', 'T1', 'T1-n', 'Tn'). "
            "If not specified, all tiers will be included.",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool retrieves risk matrix data for a specific branch (industry sector, NOT a resource). "
        "It returns a pandas.DataFrame or pandas.Series containing the risk information. "
        "The return value of this tool is suitable to be returned to the user. "
        "Usage examples: "
        "branch_risks_df = get_branch_risk_matrix('Lebensmitteleinzelhandel', 'Brutto') # returns dataframe with supplier_tier as index, countries as rows, legal positions as columns "
        "branch_risks_series = get_branch_risk_matrix('Lebensmitteleinzelhandel', 'Brutto', 'T0') # returns series with risk values for T0 tier "
    )

    def __init__(
        self,
        risk_per_branch_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = risk_per_branch_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

    def forward(
        self, branch_name: str, risk_type: str, supplier_tier: str = "T0"
    ) -> pandas.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "branch_name": branch_name,
                "risk_type": risk_type,
                "supplier_tier": supplier_tier,
            },
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        # Extract data for the specific branch, risk type, and tier
        df = load_dataset_from_path(self.file_path)
        try:
            branch_data = df.loc[(branch_name, risk_type, supplier_tier)]
        except KeyError:
            raise ValueError(
                f"No data found for branch: {branch_name}, risk type: {risk_type}, tier: {supplier_tier}"
            )

        if branch_data.empty:
            raise ValueError(
                f"No data found for branch: {branch_name}, risk type: {risk_type}, tier: {supplier_tier}"
            )

        logger.info(f"Generated branch risk matrix data for: {branch_name}")

        return branch_data
