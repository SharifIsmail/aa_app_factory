from pathlib import Path

import pandas as pd
from smolagents import Tool
from thefuzz import fuzz

from service.agent_core.data_management.columns import (
    COL_LAENDERHERKUENFTE,
    COL_ROHSTOFFNAME,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path

RISK_COLUMNS_PREFIX = "Brutto-Risiko"


class ResourceRiskTool(Tool):
    name = "get_resource_risk_profile"
    inputs = {
        "resource_names": {
            "type": "array",
            "description": (
                f"List of exact resource names (as found in column '{COL_ROHSTOFFNAME}'). "
                "These could be the exact names returned by the find_natural_resource_per_partner. "
                "Use full German resource names exactly as they appear in the dataset."
            ),
        },
        "limit_results": {
            "type": "integer",
            "description": "Optional: maximum number of rows to return.",
            "nullable": True,
        },
    }
    output_type = "any"
    description = (
        "This tool retrieves risk profiles for specific resources (raw materials) by exact name match. "
        "It does NOT mean that these resources are actually sourced from these countries and has no relation"
        "to actual suppliers. "
        "If you need information on risk of resources for specific suppliers, do not use this tool."
        "It returns a pandas.DataFrame containing the matching resources and all risk columns. "
        f"DataFrame columns: '{COL_ROHSTOFFNAME}' (resource name), '{COL_LAENDERHERKUENFTE}' (country origins), "
        "and all 'Brutto-Risiko' columns for different legal positions (Arbeitsschutz, Diskriminierung, etc.). "
        "Usage example: "
        "risk_df = get_resource_risk_profile(['HOLZ', 'HOLZPRODUKTE']) "
        "# Returns: DataFrame with resource risk data"
    )

    def __init__(
        self,
        resource_risk_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = resource_risk_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

    def _get_resources_by_exact_names(
        self, df: pd.DataFrame, resource_names: list[str]
    ) -> pd.DataFrame:
        """Get resources by exact name match."""
        mask = df[COL_ROHSTOFFNAME].isin(resource_names)
        return df.loc[mask]

    def _get_risk_columns(self, df: pd.DataFrame) -> list[str]:
        """Get all columns that contain risk information."""
        base_columns = [COL_ROHSTOFFNAME, COL_LAENDERHERKUENFTE]
        risk_columns = [
            col for col in df.columns if col.startswith(RISK_COLUMNS_PREFIX)
        ]
        return base_columns + risk_columns

    def _find_similar_resources(
        self, df: pd.DataFrame, search_terms: list[str], max_suggestions: int = 10
    ) -> list[str]:
        all_resources = df[COL_ROHSTOFFNAME].unique().tolist()

        unique_matches: dict[str, float] = {}
        for term in search_terms:
            for resource in all_resources:
                token_set_score = fuzz.token_set_ratio(term, resource)
                partial_score = fuzz.partial_ratio(term, resource)
                ratio_score = fuzz.ratio(term, resource)

                max_score = max(token_set_score, partial_score, ratio_score)

                if (
                    resource not in unique_matches
                    or max_score > unique_matches[resource]
                ):
                    unique_matches[resource] = max_score

        sorted_matches = sorted(
            unique_matches.items(), key=lambda x: x[1], reverse=True
        )

        return [resource for resource, _ in sorted_matches[:max_suggestions]]

    def forward(
        self, resource_names: list[str], limit_results: int | None = None
    ) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "resource_names": resource_names,
                "limit_results": limit_results,
            },
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        df = load_dataset_from_path(self.file_path)
        results = self._get_resources_by_exact_names(df, resource_names)

        if results.empty:
            similar_resources = self._find_similar_resources(df, resource_names)

            raise ValueError(
                f"No exact matches found for: {resource_names}. "
                f"Did you mean one of these resources? {similar_resources}"
            )

        results = results.drop_duplicates()

        relevant_columns = self._get_risk_columns(df)
        result_df = results[relevant_columns]

        if limit_results is not None:
            result_df = result_df.head(limit_results)

        if result_df.empty:
            raise ValueError(f"No risk data found for resources: {resource_names}")

        return result_df
