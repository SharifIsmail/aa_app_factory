import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from smolagents import Tool

from service.law_core.models import ToolLog, WorkLog
from service.storage.data_storage import DataStorage


class GoogleSearchWithSourceURLTool(Tool):
    name = "web_search"
    description = """Performs a google web search for your query then returns a list of the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."},
        "filter_year": {
            "type": "integer",
            "description": "Optionally restrict results to a certain year",
            "nullable": True,
        },
    }
    output_type = "object"

    def __init__(
        self,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        repo_key: str,
        provider: str = "serpapi",
    ):
        super().__init__()
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.repo_key = repo_key
        self.provider = provider

        if provider == "serpapi":
            self.organic_key = "organic_results"
            api_key_env_name = "SERPAPI_API_KEY"
        else:
            self.organic_key = "organic"
            api_key_env_name = "SERPER_API_KEY"
        self.api_key = os.getenv(api_key_env_name)
        if self.api_key is None:
            raise ValueError(
                f"Missing API key. Make sure you have '{api_key_env_name}' in your env variables."
            )

    def forward(
        self, query: str, filter_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs a Google search and returns structured results as a list of dictionaries.
        Each dictionary contains information about a search result.
        """
        tool_log = ToolLog(
            tool_name=self.name, params={"query": query, "filter_year": filter_year}
        )
        self.work_log.tool_logs.append(tool_log)

        if self.provider == "serpapi":
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "google_domain": "google.com",
            }
            base_url = "https://serpapi.com/search.json"
        else:
            params = {
                "q": query,
                "api_key": self.api_key,
            }
            base_url = "https://google.serper.dev/search"
        if filter_year is not None:
            params["tbs"] = (
                f"cdr:1,cd_min:01/01/{filter_year},cd_max:12/31/{filter_year}"
            )

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            results = response.json()
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            tool_log.result = error_msg
            raise ValueError(error_msg)

        if self.organic_key not in results.keys():
            if filter_year is not None:
                error_msg = f"No results found for query: '{query}' with filtering on year={filter_year}. Use a less restrictive query or do not filter on year."
            else:
                error_msg = f"No results found for query: '{query}'. Use a less restrictive query."
            tool_log.result = error_msg
            raise Exception(error_msg)

        if len(results[self.organic_key]) == 0:
            year_filter_message = (
                f" with filter year={filter_year}" if filter_year is not None else ""
            )
            result_msg = f"No results found for '{query}'{year_filter_message}. Try with a more general query, or remove the year filter."
            tool_log.result = result_msg
            return []  # Return empty list for no results

        # Create structured results list
        structured_results = []

        if self.organic_key in results:
            for idx, page in enumerate(results[self.organic_key]):
                # Extract data from search result
                title = page.get("title", "")
                snippet = page.get("snippet", "")
                source_url = page.get("link", "")
                timestamp = datetime.now().isoformat()

                # Create a structured result dictionary
                formatted_result = {
                    "title": title,
                    "snippet": snippet,
                    "source_url": source_url,
                    "position": idx + 1,
                    "timestamp": timestamp,
                }

                # Add to our structured results list
                structured_results.append(formatted_result)

                # Store the search result in the repository
                data_key = (
                    f"search_result_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                self.data_storage.store_to_repo(
                    self.repo_key, data_key, formatted_result
                )

                logger.info(
                    "Stored search result {} with source URL: {}",
                    idx + 1,
                    source_url,
                )

        # Create a readable string version for the tool log
        result_summary = "## Search Results\n"
        for result in structured_results:
            result_summary += (
                f"- {result['title']}: {result['snippet']} ({result['source_url']})\n"
            )

        tool_log.result = result_summary
        return structured_results
