import json
from enum import StrEnum
from pathlib import Path
from typing import List

import pandas as pd
from litellm import completion
from loguru import logger
from pydantic import BaseModel
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.agent_core.tools.find_category_or_product_tool import MAX_RESULTS_DEFAULT
from service.agent_core.tools.utils.fuzzy_search_utils import (
    FuzzySearchConfig,
    calculate_hybrid_fuzzy_search_score,
)
from service.data_loading import load_dataset_from_path
from service.dependencies import with_settings


class Sector(StrEnum):
    SECTOR_DETAILLIERT = COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED
    SECTOR_GROB = COL_ESTELL_SEKTOR_GROB_RENAMED


class BranchSearchResult(BaseModel):
    branch_name: str
    sector: Sector


class BranchNotFoundError(Exception):
    """Raised when no matching branches are found for a search term."""

    pass


class FindBranchesTool(Tool):
    MAX_RESULTS_DEFAULT = 20

    name = "find_branches"
    inputs = {
        "search_term": {
            "type": "string",
            "description": "Search term to find matching industry branches/sectors. "
            "The search term MUST be in English. "
            "Examples: 'automotive', 'food production', 'software development', 'textile manufacturing', 'retail', etc.",
        },
        "max_results": {
            "type": "integer",
            "nullable": True,
            "description": f"Maximum number of results to return. If exceeded, an error is raised suggesting to increase this limit. Default is {MAX_RESULTS_DEFAULT}.",
        },
    }
    output_type = "any"
    description = (
        "Finds matching branches (industry sectors) for a search term using intelligent fuzzy and token matching across both detailed and coarse estell sectors. "
        f"Searches values from '{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}' and '{COL_ESTELL_SEKTOR_GROB_RENAMED}'. "
        f"Returns results organized by sector category."
    )

    def __init__(
        self,
        risk_per_branch_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ) -> None:
        super().__init__()
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.file_path = risk_per_branch_file
        self.fuzzy_config = FuzzySearchConfig()

    @staticmethod
    def _extract_unique_sectors(df: pd.DataFrame, column_name: str) -> List[str]:
        """Extract unique sector names from a specific column."""
        if column_name not in df.columns:
            return []

        return df[column_name].dropna().astype(str).unique().tolist()

    def _collect_all_sectors(self, df: pd.DataFrame) -> dict[Sector, list[str]]:
        """Collect all unique sector names from both detailliert and grob sector columns."""
        return {
            Sector.SECTOR_DETAILLIERT: self._extract_unique_sectors(
                df, COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED
            ),
            Sector.SECTOR_GROB: self._extract_unique_sectors(
                df, COL_ESTELL_SEKTOR_GROB_RENAMED
            ),
        }

    def _search_in_branch_list(
        self,
        branch_names: List[str],
        query: str,
        min_score: float,
    ) -> List[str]:
        """Search for matches in a specific list of branch_names."""
        if not branch_names:
            return []

        branch_names_df = pd.DataFrame({"branch_names": branch_names})

        scores = branch_names_df["branch_names"].apply(
            lambda branch_name: calculate_hybrid_fuzzy_search_score(
                query, branch_name, self.fuzzy_config
            )
        )

        # Filter results based on minimum score
        results: List[str] = []
        for branch_name, score in zip(branch_names, scores):
            if score >= min_score:
                results.append(
                    branch_name,
                )
        return results

    def _search_all_sector_names(
        self,
        sector_collection: dict[Sector, list[str]],
        query: str,
        min_score: float,
    ) -> List[BranchSearchResult]:
        """Search for matches across all sector collections."""
        all_results: list[BranchSearchResult] = []

        for sector, branch_names in sector_collection.items():
            sector_results = self._search_in_branch_list(
                branch_names,
                query,
                min_score,
            )
            # Convert string results to BranchSearchResult objects
            for branch_name in sector_results:
                all_results.append(
                    BranchSearchResult(
                        branch_name=branch_name,
                        sector=sector,
                    )
                )

        return all_results

    def _find_best_matching_sector_names(
        self, sector_collection: dict[Sector, list[str]], query: str
    ) -> List[BranchSearchResult]:
        """Find the best matches using cascading thresholds."""
        thresholds = self.fuzzy_config.get_cascading_thresholds()

        for threshold in thresholds:
            results = self._search_all_sector_names(sector_collection, query, threshold)
            if results:
                return results

        return []

    @staticmethod
    def _create_llm_prompt(
        search_term: str, sector_collection: dict[Sector, list[str]]
    ) -> str:
        """Create prompt for LLM-based fallback search."""
        detailliert_branches = "\n".join(
            [f"- {branch}" for branch in sector_collection[Sector.SECTOR_DETAILLIERT]]
        )
        grob_branches = "\n".join(
            [f"- {branch}" for branch in sector_collection[Sector.SECTOR_GROB]]
        )

        return f"""Given the search term "{search_term}" and the following list of available industry branches, return only the branch(es) that match(es) the search term.

Available branches in {COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}:
{detailliert_branches}

Available branches in {COL_ESTELL_SEKTOR_GROB_RENAMED}:
{grob_branches}

Instructions:
- Return all matching branches in valid JSON format as shown below
- If no branches match in a sector category, return an empty list for that sector category
- Consider synonyms, related terms, and industry context
- Limit your results to the {MAX_RESULTS_DEFAULT} most fitting branch names
- Return ONLY the JSON object, no additional text

Return your answer in exactly this JSON format:

```json
{{
  "{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}": ["branch1", "branch2"],
  "{COL_ESTELL_SEKTOR_GROB_RENAMED}": ["branch1", "branch2"]
}}
```

Search term: {search_term}"""

    @staticmethod
    def _create_retry_llm_prompt() -> str:
        """Create a simpler prompt for retry attempts."""
        return f"""Your previous response was in invalid format. You need to adhere to the specified output format.

Return your answer in exactly this JSON format:

```json
{{
  "{COL_ESTELL_SEKTOR_DETAILLIERT_RENAMED}": ["branch1", "branch2"],
  "{COL_ESTELL_SEKTOR_GROB_RENAMED}": ["branch1", "branch2"]
}}
```
"""

    @staticmethod
    def _parse_llm_response(
        llm_response: str, sector_collection: dict[Sector, list[str]]
    ) -> List[BranchSearchResult]:
        """Parse LLM response with multiple parsing strategies."""
        if not llm_response or not llm_response.strip():
            raise ValueError("Empty LLM response received")

        # Clean the response - remove markdown code blocks if present
        cleaned_response = llm_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = (
                cleaned_response.replace("```json", "").replace("```", "").strip()
            )
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```", "").strip()

        parsed_response = json.loads(cleaned_response)

        results: List[BranchSearchResult] = []

        # Process matches for each sector
        for sector in [Sector.SECTOR_DETAILLIERT, Sector.SECTOR_GROB]:
            sector_key = sector.value
            if sector_key in parsed_response:
                sector_matches = parsed_response[sector_key]
                if isinstance(sector_matches, list):
                    for branch_name in sector_matches:
                        if (
                            isinstance(branch_name, str)
                            and branch_name in sector_collection[sector]
                        ):
                            results.append(
                                BranchSearchResult(
                                    branch_name=branch_name,
                                    sector=sector,
                                )
                            )

        return results

    def _llm_fallback_search_with_retry(
        self,
        search_term: str,
        sector_collection: dict[Sector, list[str]],
        max_retries: int = 2,
    ) -> List[BranchSearchResult]:
        """Perform LLM-based search with retry mechanism."""
        settings = with_settings()

        llm_response = ""

        prompt = self._create_llm_prompt(search_term, sector_collection)
        messages = [{"role": "user", "content": prompt}]

        # First attempt with detailed prompt
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0 and llm_response:
                    logger.info(
                        f"LLM search retry attempt {attempt + 1} for term: '{search_term}'"
                    )
                    prompt = self._create_retry_llm_prompt()
                    messages.append({"role": "user", "content": prompt})

                response = completion(
                    messages=messages,
                    model=settings.model_weak,
                    vertex_credentials=settings.vertex_ai_credentials.get_secret_value(),
                )
                llm_response = str(response.choices[0].message.content)
                messages.append({"role": "assistant", "content": llm_response})

                results = self._parse_llm_response(llm_response, sector_collection)

                return results

            except Exception as e:
                logger.error(f"LLM search attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    logger.error(
                        f"All LLM search attempts failed for term: '{search_term}'"
                    )

        raise RuntimeError(f"All LLM search attempts failed for term: '{search_term}'")

    def _llm_fallback_search(
        self, search_term: str, sector_collection: dict[Sector, list[str]]
    ) -> List[BranchSearchResult]:
        """Perform LLM-based search as fallback when fuzzy search returns no results."""
        return self._llm_fallback_search_with_retry(search_term, sector_collection)[
            :MAX_RESULTS_DEFAULT
        ]

    @staticmethod
    def _format_search_results(
        results: List[BranchSearchResult],
    ) -> dict[Sector, list[str]]:
        """Format search results into the expected output structure."""
        formatted_results: dict[Sector, list[str]] = {
            Sector.SECTOR_DETAILLIERT: [],
            Sector.SECTOR_GROB: [],
        }

        for result in results:
            sector_key = result.sector
            formatted_results[sector_key].append(result.branch_name)

        return formatted_results

    @staticmethod
    def _validate_search_term(search_term: str) -> None:
        if not search_term or not search_term.strip():
            raise ValueError("Search term cannot be empty")

    @staticmethod
    def _check_result_limit(
        formatted_results: dict[Sector, list[str]], max_results: int
    ) -> None:
        """Check if results exceed the maximum limit."""
        total_results = sum(len(matches) for matches in formatted_results.values())
        if total_results > max_results:
            raise ValueError(
                f"Search returned {total_results} total results, which exceeds max_results={max_results}. "
                f"Increase max_results to see more results."
            )

    def forward(
        self, search_term: str, max_results: int = MAX_RESULTS_DEFAULT
    ) -> dict[Sector, List[str]]:
        """
        Find matching branches using fuzzy search for a search term.

        Returns:
            Dictionary mapping sector categories to lists of branch_names.
        """
        # Log tool usage
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"search_term": search_term, "max_results": max_results},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        # Validate input
        self._validate_search_term(search_term)

        # Load data and collect sectors
        transactions_df = load_dataset_from_path(self.file_path)
        sector_collection = self._collect_all_sectors(transactions_df)

        # Search for matching branches
        branch_search_results = self._find_best_matching_sector_names(
            sector_collection, search_term.strip()
        )

        # If no fuzzy results found, fallback to LLM search
        if not branch_search_results:
            logger.info(
                f"No fuzzy matches found for '{search_term}', trying LLM fallback"
            )
            branch_search_results = self._llm_fallback_search(
                search_term.strip(), sector_collection
            )

        # Format results
        formatted_results = self._format_search_results(branch_search_results)

        # Check result limits
        self._check_result_limit(formatted_results, max_results)

        # Log results
        total_results = sum(len(matches) for matches in formatted_results.values())

        if total_results == 0:
            raise BranchNotFoundError(
                f"No branch names found for the search term '{search_term}'. This means either there are no branches "
                f"found matching this category or that you need to use a more specific search term. "
                f"Remember that the search term must be in english. You can try again with a similar search term."
            )

        logger.info(
            f"Found {total_results} matching branches for search term: '{search_term}'"
        )

        return formatted_results
