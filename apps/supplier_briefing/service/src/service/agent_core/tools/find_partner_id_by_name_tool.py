from pathlib import Path
from typing import List, Tuple

import pandas as pd
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.utils.fuzzy_search_utils import (
    FuzzySearchConfig,
    calculate_hybrid_fuzzy_search_score,
)
from service.data_loading import load_dataset_from_path


class FindPartnerIdByNameTool(Tool):
    name = "find_partner_id_by_name"
    inputs = {
        "query": {
            "type": "string",
            "description": "Business partner name to search for. The search uses intelligent fuzzy and token matching.",
        },
        "max_results": {
            "type": "integer",
            "nullable": True,
            "description": "Maximum number of results to return. If more results would be found, raises an error with suggestions to increase this limit. Default is 100.",
        },
    }
    output_type = "any"
    description = (
        f"This tool finds business partner IDs ({COL_BUSINESS_PARTNER_ID}) using fuzzy search in the '{COL_BUSINESS_PARTNER_NAME}' column. "
        f"Returns a pandas.DataFrame indexed by '{COL_BUSINESS_PARTNER_ID}' with a single column '{COL_BUSINESS_PARTNER_NAME}', ranked by relevance. "
        "Examples: "
        "- Query 'Apple Inc' will find 'Apple Incorporated', 'Apple Inc.', 'Apple Computer Inc' "
        "- Query 'Microsoft Corp' will find 'Microsoft Corporation', 'Microsoft Germany GmbH' "
        "The algorithm automatically handles: word splitting/joining, minor typos, and word reordering."
    )

    def __init__(
        self,
        business_partner_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ) -> None:
        super().__init__()
        self.file_path = business_partner_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.fuzzy_config = FuzzySearchConfig()

    def _hybrid_fuzzy_and_token_search(
        self, df: pd.DataFrame, query: str, min_score: float
    ) -> List[Tuple[str, str]]:
        name_column = COL_BUSINESS_PARTNER_NAME
        id_column = COL_BUSINESS_PARTNER_ID

        # Create DataFrame for vectorized computation
        partners_df = df[[id_column, name_column]].copy()
        partners_df["partner_name_text"] = partners_df[name_column].astype(str)

        # Vectorized fuzzy score computation
        scores = partners_df["partner_name_text"].apply(
            lambda partner_name: calculate_hybrid_fuzzy_search_score(
                query, partner_name, self.fuzzy_config
            )
        )

        # Add scores to DataFrame
        partners_df["score"] = scores

        # Filter by minimum score
        filtered_df = partners_df[partners_df["score"] >= min_score]

        # Sort by score descending
        filtered_df = filtered_df.sort_values("score", ascending=False)

        results = [
            (str(row[id_column]), str(row[name_column]))
            for _, row in filtered_df.iterrows()
        ]

        return results

    def _deduplicate_results(
        self, results: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        seen_ids = set()
        unique_results = []

        for partner_id, partner_name in results:
            if partner_id not in seen_ids:
                seen_ids.add(partner_id)
                unique_results.append((partner_id, partner_name))

        return unique_results

    def forward(self, query: str, max_results: int = 100) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"query": query, "max_results": max_results},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        if not query or not query.strip():
            logger.error("Query cannot be empty")
            raise ValueError("Query for business partner search cannot be empty")

        # Load data
        df = load_dataset_from_path(
            self.file_path,
            columns=[
                COL_BUSINESS_PARTNER_ID,
                COL_BUSINESS_PARTNER_NAME,
            ],
        )

        thresholds = self.fuzzy_config.get_cascading_thresholds()
        results = []

        for threshold in thresholds:
            results = self._hybrid_fuzzy_and_token_search(df, query.strip(), threshold)
            if results:
                break

        unique_results = self._deduplicate_results(results)

        # Check if results exceed max_results and raise error if so
        if len(unique_results) > max_results:
            raise ValueError(
                f"Search returned {len(unique_results)} results, which exceeds max_results={max_results}. "
                f"Increase max_results to see more results."
            )

        results_df = pd.DataFrame(
            unique_results,
            columns=[COL_BUSINESS_PARTNER_ID, COL_BUSINESS_PARTNER_NAME],
        )
        # Sort by business partner IDs before setting the index
        results_df = results_df.sort_values(by=COL_BUSINESS_PARTNER_ID)
        if COL_BUSINESS_PARTNER_ID in results_df.columns:
            results_df = results_df.set_index(COL_BUSINESS_PARTNER_ID)
        results_df.index.name = COL_BUSINESS_PARTNER_ID

        return results_df
