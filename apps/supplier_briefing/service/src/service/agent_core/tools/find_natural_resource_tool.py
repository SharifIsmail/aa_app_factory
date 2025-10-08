from pathlib import Path

import pandas as pd
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
    COL_COUNTRY,
    COL_GEFUNDENE_RISIKOROHSTOFFE,
    COL_RISIKOROHSTOFFE,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.utils.fuzzy_search_utils import (
    FuzzySearchConfig,
    calculate_hybrid_fuzzy_search_score,
)
from service.data_loading import load_dataset_from_path

DEFAULT_MAX_RESULTS = 100


class FindNaturalResourcesPerPartnerTool(Tool):
    name = "find_natural_resource_per_partner"
    inputs = {
        "resource_query": {
            "type": "string",
            "description": f"Natural resource name to search for (German). Searches the '{COL_RISIKOROHSTOFFE}' column.",
        },
        "country_code": {
            "type": "string",
            "description": "Optional three-letter country code (e.g., 'IND', 'BEL') to filter business partners by country. "
            "When provided, only business partners from this country will be considered in the search.",
            "nullable": True,
        },
        "max_results": {
            "type": "integer",
            "nullable": True,
            "description": f"if set, raise exception if more than this number of results are found. Default is {DEFAULT_MAX_RESULTS}.",
        },
    }
    output_type = "any"
    description = (
        f"This tool finds natural resources used by business partners from which we source products in the '{COL_RISIKOROHSTOFFE}' column. "
        f"Optionally filters results by country using three-letter country codes. "
        f"It returns a pandas.DataFrame indexed by '{COL_BUSINESS_PARTNER_ID}' with columns:  '{COL_BUSINESS_PARTNER_NAME}', '{COL_COUNTRY}', '{COL_GEFUNDENE_RISIKOROHSTOFFE}' (matched resources only, '/'-delimited, preserving original casing). "
        "If this tool does not return results, it means we do not source the resource from any business partner (or from the specified country). "
        "Use this tool to "
        "(a) find whether we source the resource from any business partner "
        "(b) find business partners that source a specific resource "
        "(c) find whether we source a resource from a specific country "
        "(d) find business partners from a specific country that supply/source certain resources "
        f"If there are more than `max_results` results, an error is raised. The default for max_results is {DEFAULT_MAX_RESULTS}. "
        f"The returned DataFrame is indexed by the business partner ID column ('{COL_BUSINESS_PARTNER_ID}') rather than a sequential index. "
        "Usage examples: "
        "find_natural_resource_per_partner('HOLZ') "
        "find_natural_resource_per_partner('ERDBEEREN', country_code='IND')"
    )

    def __init__(
        self,
        transactions_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = transactions_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        # We use a very high first threshold to find exact matches in the resources first if possible
        self.fuzzy_config = FuzzySearchConfig(
            threshold_high=0.95, threshold_medium=0.8, threshold_low=0.5
        )

    def _search_for_matching_resources(
        self, df: pd.DataFrame, query: str
    ) -> pd.DataFrame:
        """
        Search for matches using cascading thresholds.
        Returns the first non-empty results found, starting with the highest threshold.
        """
        thresholds = self.fuzzy_config.get_cascading_thresholds()

        # Try each threshold in descending order until we find matches
        for threshold in thresholds:
            # Optimized batch fuzzy score computation with caching
            resource_similarity_scores = (
                self._calculate_fuzzy_scores_for_resource_series(
                    df[COL_RISIKOROHSTOFFE], query
                )
            )

            similarity_over_threshold_mask = resource_similarity_scores >= threshold
            resources_above_threshold = df[similarity_over_threshold_mask]

            if not resources_above_threshold.empty:
                return resources_above_threshold

        # Return empty DataFrame if no matches found
        return pd.DataFrame(columns=df.columns)

    def _calculate_fuzzy_scores_for_resource_series(
        self, resources_series: pd.Series, query: str
    ) -> pd.Series:
        """
        Calculate fuzzy similarity scores between each resource in the series and the query.
        Returns a pd.Series with similarity scores corresponding to each resource in the input series.
        """
        # Get unique resource names to avoid redundant calculations
        unique_resources_df = pd.DataFrame({"resource_name": resources_series.unique()})

        # Vectorized fuzzy score computation
        scores = unique_resources_df["resource_name"].apply(
            lambda resource_name: calculate_hybrid_fuzzy_search_score(
                query, str(resource_name), self.fuzzy_config
            )
        )
        resource_to_similarity_score_map = dict(
            zip(unique_resources_df["resource_name"], scores)
        )

        # Map scores back to original series
        return resources_series.map(resource_to_similarity_score_map)

    @staticmethod
    def _split_and_explode_resources(df: pd.DataFrame) -> pd.DataFrame:
        # Split resources on '/' into individual items, strip whitespace, and explode to one-per-row
        split_series = df[COL_RISIKOROHSTOFFE].fillna("").astype(str).str.split("/")
        df_exploded = df.copy()
        df_exploded[COL_RISIKOROHSTOFFE] = split_series
        df_exploded = df_exploded.explode(COL_RISIKOROHSTOFFE, ignore_index=True)
        df_exploded[COL_RISIKOROHSTOFFE] = (
            df_exploded[COL_RISIKOROHSTOFFE].astype(str).str.strip()
        )
        # Drop empty strings after stripping
        df_exploded = df_exploded[df_exploded[COL_RISIKOROHSTOFFE] != ""]
        return df_exploded

    @staticmethod
    def _join_unique_preserving_order(series: pd.Series) -> str:
        seen: set[str] = set()
        ordered_unique: list[str] = []
        for value in series:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned and cleaned not in seen:
                    seen.add(cleaned)
                    ordered_unique.append(cleaned)
        return "/".join(ordered_unique)

    @staticmethod
    def _deduplicate_matches(all_matches: pd.DataFrame) -> pd.DataFrame:
        # Remove duplicates based on business partner ID and resource name combination
        unique_matches = all_matches.drop_duplicates(
            subset=[COL_BUSINESS_PARTNER_ID, COL_RISIKOROHSTOFFE]
        )
        return unique_matches

    @staticmethod
    def _filter_by_country(df: pd.DataFrame, country_code: str) -> pd.DataFrame:
        country_code_upper = country_code.upper()
        mask = df[COL_COUNTRY].str.upper() == country_code_upper
        filtered_df = df[mask]
        return filtered_df

    def forward(
        self,
        resource_query: str,
        country_code: str | None = None,
        max_results: int | None = DEFAULT_MAX_RESULTS,
    ) -> pd.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"resource_query": resource_query, "country_code": country_code},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        if not resource_query.strip():
            raise ValueError("Query for natural resource search cannot be empty")

        resource_query_upper = resource_query.upper().strip()

        relevant_columns = [
            COL_BUSINESS_PARTNER_ID,
            COL_BUSINESS_PARTNER_NAME,
            COL_COUNTRY,
            COL_RISIKOROHSTOFFE,
        ]
        df = load_dataset_from_path(self.file_path, columns=relevant_columns)

        # Reset index to ensure business partner ID is a regular column, not index
        if df.index.name == COL_BUSINESS_PARTNER_ID:
            df = df.reset_index()

        # Apply country filter if provided
        if country_code:
            df = self._filter_by_country(df, country_code)

        # Split and explode resources so each row has a single resource value
        df_exploded_resources = self._split_and_explode_resources(df)

        all_matches = self._search_for_matching_resources(
            df_exploded_resources, resource_query_upper
        )

        # Deduplicate by partner+resource
        if not all_matches.empty:
            unique_matches = self._deduplicate_matches(all_matches)
        else:
            unique_matches = pd.DataFrame(columns=relevant_columns)

        country_info = f" (filtered by country: {country_code})" if country_code else ""
        logger.info(
            f"Found {len(unique_matches)} unique business partner-resource matches for query: '{resource_query_upper}'{country_info}"
        )

        if unique_matches.empty:
            empty_df = pd.DataFrame(
                columns=[
                    COL_BUSINESS_PARTNER_NAME,
                    COL_COUNTRY,
                    COL_GEFUNDENE_RISIKOROHSTOFFE,
                ]
            )
            empty_df.index.name = COL_BUSINESS_PARTNER_ID
            return empty_df

        # Aggregate to one row per business partner with matched resources only
        aggregated = (
            unique_matches.sort_values(by=COL_BUSINESS_PARTNER_ID)
            .groupby(COL_BUSINESS_PARTNER_ID, as_index=True)
            .apply(
                lambda group: pd.Series(
                    {
                        COL_BUSINESS_PARTNER_NAME: group[
                            COL_BUSINESS_PARTNER_NAME
                        ].iloc[0],
                        COL_COUNTRY: group[COL_COUNTRY].iloc[0],
                        COL_GEFUNDENE_RISIKOROHSTOFFE: self._join_unique_preserving_order(
                            group[COL_RISIKOROHSTOFFE]
                        ),
                    }
                ),
                include_groups=False,
            )
        )

        # Enforce maximum results limit
        if max_results is not None and len(aggregated) > max_results:
            raise RuntimeError(
                f"Number of results {len(aggregated)} exceeds the limit of max_results={max_results}. "
                "Please refine your search patterns or increase the max_results parameter."
            )
        return aggregated
