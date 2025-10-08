from pathlib import Path

import pandas as pd
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
BRANCH_COLUMN = COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED


class CompareBranchRisksTool(Tool):
    name = "compare_branch_risks"
    inputs = {
        "branch_names": {
            "type": "array",
            "description": f"The branch names ('{BRANCH_COLUMN}') to get the "
            "risk matrix for. At least two branches must be specified.",
        },
        "risk_type": {
            "type": "string",
            "description": "The type of risk to retrieve ('Brutto', 'Netto', 'Konkretes Risiko'). "
            "If the user does not specify a type, assume 'Brutto'. ",
            "nullable": True,
        },
        "supplier_tier": {
            "type": "string",
            "description": "The supplier tier to analyze ('T0', 'T1', 'T1-n', 'Tn'). "
            "If the user does not specify a tier, assume 'T0'. ",
            "nullable": True,
        },
        "country_code": {
            "type": "string",
            "description": "Optional 3-letter country code (e.g., 'DEU', 'BEL', 'FRA') to filter risk data for a specific country. "
            "If not specified, calculates the mean (average) of risk values across all countries. ",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool compares risk data for multiple branches (industry sector, NOT a resource). "
        "It returns a pandas.DataFrame with the risk comparison. "
        "When no country_code is specified, it calculates the mean (average) of risk values across all countries for each branch. "
        "Optionally filter by country code for country-specific risk analysis. "
        "The return value of this tool is suitable to be returned to the user. "
        "Usage examples: "
        f"branch_comparison_df = compare_branch_risks(['A 04 BEA 003 VEGETABLE AND MELON FARMING', 'A 04 BEA 004 FRUIT AND TREE NUT FARMING'], '{DEFAULT_RISK_TYPE}', '{DEFAULT_SUPPLIER_TIER}') "
        f"branch_comparison_df = compare_branch_risks(['D 10 BEA 217 BREWERIES', 'D 10 BEA 218 WINERIES'], '{DEFAULT_RISK_TYPE}', '{DEFAULT_SUPPLIER_TIER}', 'NLD') "
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

    def _get_branch_risk_scores(
        self,
        risk_data: pd.DataFrame,
        branch_name: str,
        risk_type: str,
        supplier_tier: str,
    ) -> pd.DataFrame:
        try:
            risk_scores = risk_data.loc[(branch_name, risk_type, supplier_tier)]
        except KeyError:
            raise ValueError(f"No data found for branch: {branch_name}")

        if risk_scores.empty:
            raise ValueError(f"No data found for branch: {branch_name}")

        return risk_scores

    def _process_country_specific_risks(
        self, risk_scores: pd.DataFrame, branch_name: str, country_code: str
    ) -> pd.DataFrame:
        country_risk_scores = risk_scores.loc[risk_scores.index == country_code]

        if country_risk_scores.empty:
            raise ValueError(
                f"Data was found for branch '{branch_name}' but no data was found branch and country combination: {country_code}"
            )

        country_risk_scores = country_risk_scores.copy()
        country_risk_scores[BRANCH_COLUMN] = branch_name
        return country_risk_scores

    def _aggregate_all_country_risks(
        self, risk_scores: pd.DataFrame, branch_name: str
    ) -> pd.DataFrame:
        mean_risk_scores = risk_scores.mean(numeric_only=True).to_frame().T.round(2)
        mean_risk_scores[BRANCH_COLUMN] = branch_name
        return mean_risk_scores

    def _validate_inputs(
        self,
        branch_names: list[str],
        risk_type: str,
        supplier_tier: str,
    ) -> None:
        if len(branch_names) < 2:
            raise ValueError("At least two branch names must be specified.")

        if risk_type not in RISK_TYPE_OPTIONS:
            raise ValueError(f"Invalid risk type. Must be one of {RISK_TYPE_OPTIONS}.")

        if supplier_tier not in SUPPLIER_TIER_OPTIONS:
            raise ValueError(
                f"Invalid supplier tier. Must be one of {SUPPLIER_TIER_OPTIONS}."
            )

    def forward(
        self,
        branch_names: list[str],
        risk_type: str = DEFAULT_RISK_TYPE,
        supplier_tier: str = DEFAULT_SUPPLIER_TIER,
        country_code: str | None = None,
    ) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "branch_names": branch_names,
                "risk_type": risk_type,
                "supplier_tier": supplier_tier,
                "country_code": country_code,
            },
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        self._validate_inputs(branch_names, risk_type, supplier_tier)

        risk_data = load_dataset_from_path(self.file_path)
        branch_risk_summaries = []

        for branch_name in branch_names:
            risk_scores = self._get_branch_risk_scores(
                risk_data, branch_name, risk_type, supplier_tier
            )

            if country_code:
                risk_summary = self._process_country_specific_risks(
                    risk_scores, branch_name, country_code
                )
            else:
                risk_summary = self._aggregate_all_country_risks(
                    risk_scores, branch_name
                )

            branch_risk_summaries.append(risk_summary)

        risk_comparison_df = pd.concat(branch_risk_summaries, ignore_index=True)
        risk_comparison_df = risk_comparison_df.set_index(BRANCH_COLUMN)
        risk_comparison_df.index.name = BRANCH_COLUMN
        return risk_comparison_df
