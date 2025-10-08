from pathlib import Path
from typing import TypedDict, cast

import pandas as pd
from loguru import logger
from pandas import Index
from pydantic import BaseModel
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_ARTICLE_NAME,
    COL_ARTIKELFAMILIE,
    COL_FRUIT_VEG_GROUP,
    COL_HAUPTWARENGRUPPE,
    COL_ID_ARTICLE_NAME,
    COL_ID_ARTIKELFAMILIE,
    COL_ID_FRUIT_VEG_GROUP,
    COL_ID_HAUPTWARENGRUPPE,
    COL_ID_UNTERWARENGRUPPE,
    COL_ID_WG_EBENE_3_WGI,
    COL_UNTERWARENGRUPPE,
    COL_WG_EBENE_3_WGI,
    EMPTY_VALUES,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.utils.fuzzy_search_utils import (
    FuzzySearchConfig,
    calculate_hybrid_fuzzy_search_score,
)
from service.data_loading import load_dataset_from_path


class Match(BaseModel):
    id_val: str
    text_val: str
    level: str
    text_column: str


class SearchLevelConfig(TypedDict):
    level: str
    text_column: str
    id_column: str
    priority: int


MAX_RESULTS_DEFAULT = 10


class FindCategoryOrProductTool(Tool):
    name = "find_category_or_product"
    inputs = {
        "search_term": {
            "type": "string",
            "description": "Search term to find matching categories or products across hierarchy levels using intelligent fuzzy and token matching. Use German terms, as the dataset is in German. Examples: 'Brot', 'Backwaren', 'Getränke'.",
        },
        "max_results": {
            "type": "integer",
            "nullable": True,
            "description": f"if set, raise exception if more than this number of results are found. Default is {MAX_RESULTS_DEFAULT}.",
        },
    }
    output_type = "any"
    description = (
        "This tool finds product categories by searching across all hierarchy levels. "
        "Returns a pandas.DataFrame containing the matching results. "
        "DataFrame columns: 'value' (the product or category name), 'column_name' (hierarchy level column name where search gave a hit). "
        f"Possible column_name values: '{COL_HAUPTWARENGRUPPE}', '{COL_WG_EBENE_3_WGI}', "
        f"'{COL_UNTERWARENGRUPPE}', '{COL_ARTIKELFAMILIE}', "
        f"'{COL_FRUIT_VEG_GROUP}', '{COL_ARTICLE_NAME}'. "
        "The 'column_name' value is the EXACT column name to use when filtering transactions data. "
        f"Example: If result shows value='Brot' and column_name='{COL_ARTIKELFAMILIE}', then filter transactions using: "
        f"transactions_df['{COL_ARTIKELFAMILIE}'] == 'Brot'. "
        "IMPORTANT: Returns a pandas.Dataframe. "
        "The data_id can be used with log_user_data tool's data_ids parameter. "
        "Usage example: "
        "search_results = find_category_or_product('Brot') "
        "# Returns: DataFrame with columns ['value', 'column_name'] containing matching products/categories"
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
        self.search_levels: list[SearchLevelConfig] = self._create_search_levels()
        # We use a very high first threshold to find exact matches in the resources first if possible
        self.fuzzy_config = FuzzySearchConfig(
            threshold_high=0.95, threshold_medium=0.8, threshold_low=0.5
        )

    @staticmethod
    def _create_search_levels() -> list[SearchLevelConfig]:
        return [
            {
                "level": "L1_Category",
                "text_column": COL_HAUPTWARENGRUPPE,
                "id_column": COL_ID_HAUPTWARENGRUPPE,
                "priority": 1,
            },
            {
                "level": "L3_Category",
                "text_column": COL_WG_EBENE_3_WGI,
                "id_column": COL_ID_WG_EBENE_3_WGI,
                "priority": 2,
            },
            {
                "level": "L4_Category",
                "text_column": COL_UNTERWARENGRUPPE,
                "id_column": COL_ID_UNTERWARENGRUPPE,
                "priority": 3,
            },
            {
                "level": "L5_Category",
                "text_column": COL_ARTIKELFAMILIE,
                "id_column": COL_ID_ARTIKELFAMILIE,
                "priority": 4,
            },
            {
                "level": "L5_Special_FruitVeg",
                "text_column": COL_FRUIT_VEG_GROUP,
                "id_column": COL_ID_FRUIT_VEG_GROUP,
                "priority": 4,
            },
            {
                "level": "L6_Product",
                "text_column": COL_ARTICLE_NAME,
                "id_column": COL_ID_ARTICLE_NAME,
                "priority": 5,
            },
        ]

    def _get_required_columns(self) -> list[str]:
        """
        Get all required columns for search operations to optimize data loading.
        """
        required_columns = set()
        for level_config in self.search_levels:
            required_columns.add(level_config["text_column"])
            required_columns.add(level_config["id_column"])
        return list(required_columns)

    def _find_matches_at_category_level(
        self,
        df: pd.DataFrame,
        query: str,
        min_score: float,
        level_config: SearchLevelConfig,
    ) -> list[Match]:
        text_column = level_config["text_column"]
        id_column = level_config["id_column"]
        level = level_config["level"]

        if text_column not in df.columns or id_column not in df.columns:
            return []

        unique_id_text_pairs_df = cast(
            pd.DataFrame,
            df[[id_column, text_column]].dropna().astype(str).drop_duplicates(),
        )

        scores = unique_id_text_pairs_df[text_column].apply(
            lambda text: calculate_hybrid_fuzzy_search_score(
                query, text, self.fuzzy_config
            )
        )

        unique_id_text_pairs_df = unique_id_text_pairs_df.copy()
        unique_id_text_pairs_df["fuzzy_score"] = scores

        # Filter based on score and empty values
        above_min_score_and_not_empty_mask = (
            (unique_id_text_pairs_df["fuzzy_score"] >= min_score)
            & (~unique_id_text_pairs_df[id_column].isin(EMPTY_VALUES))
            & (~unique_id_text_pairs_df[text_column].isin(EMPTY_VALUES))
        )

        filtered_df = unique_id_text_pairs_df[above_min_score_and_not_empty_mask]

        # Convert to Match objects
        matches = [
            Match(
                id_val=str(row[id_column]),
                text_val=str(row[text_column]),
                level=level,
                text_column=text_column,
            )
            for _, row in filtered_df.iterrows()
        ]

        return matches

    def _deduplicate_and_prioritize(self, all_matches: list[Match]) -> list[Match]:
        matches_by_name: dict[str, list[Match]] = {}

        for match in all_matches:
            text_name = match.text_val
            if text_name not in matches_by_name:
                matches_by_name[text_name] = []
            matches_by_name[text_name].append(match)

        level_priority = {
            config["level"]: config["priority"] for config in self.search_levels
        }

        prioritized_matches = []
        for matches in matches_by_name.values():
            best_match = min(matches, key=lambda m: level_priority.get(m.level, 999))
            prioritized_matches.append(best_match)

        return sorted(
            prioritized_matches, key=lambda m: level_priority.get(m.level, 999)
        )

    @staticmethod
    def _create_results_dataframe(
        final_matches: list[Match], max_results: int | None
    ) -> pd.DataFrame:
        column_names = Index(["value", "column_name"])

        if not final_matches:
            return pd.DataFrame(columns=column_names)

        if max_results is not None:
            if len(final_matches) > max_results:
                raise RuntimeError(
                    f"Number of results {len(final_matches)} exceeds the limit of {max_results}. "
                    "Please refine your search patterns or increase the max_results parameter in the function call"
                )

        simplified_data = [
            (match.text_val, match.text_column) for match in final_matches
        ]
        return pd.DataFrame(data=simplified_data, columns=column_names)

    def forward(
        self, search_term: str, max_results: int | None = MAX_RESULTS_DEFAULT
    ) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"search_term": search_term, "max_results": max_results},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        search_term_upper = search_term.upper().strip()

        if not search_term_upper:
            raise ValueError("Search term cannot be empty")

        required_columns = self._get_required_columns()
        df = load_dataset_from_path(self.file_path, columns=required_columns)

        thresholds = self.fuzzy_config.get_cascading_thresholds()
        all_matches: list[Match] = []

        for threshold in thresholds:
            all_matches = []
            for level_config in self.search_levels:
                level_matches = self._find_matches_at_category_level(
                    df, search_term_upper, threshold, level_config
                )
                all_matches.extend(level_matches)
            if all_matches:
                break

        final_matches = self._deduplicate_and_prioritize(all_matches)
        logger.info(
            f"Found {len(final_matches)} unique matches for search term: {search_term_upper}"
        )

        results_df = self._create_results_dataframe(
            final_matches, max_results=max_results
        )

        if len(results_df) > 0:
            logger.info(
                f"DataFrame created with {len(results_df)} rows and columns: {results_df.columns.tolist()}"
            )
        return results_df
