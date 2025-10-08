import json
import os
from typing import Optional

from smolagents import Tool

from service.lksg_core.models import ToolLog, WorkLog
from service.lksg_core.tools.general_tools import DataStorage


class GoogleSearchWithSourceURLTool(Tool):
    name = "web_search"
    description = """Performs a google web search for your query then returns a string of the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."},
        "filter_year": {
            "type": "integer",
            "description": "Optionally restrict results to a certain year",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(
        self,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        provider: str = "serpapi",
    ):
        super().__init__()
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
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

    def forward(self, query: str, filter_year: Optional[int] = None) -> str:
        tool_log = ToolLog(
            tool_name=self.name,
            params={
                "query": query,
                "filter_year": str(filter_year) if filter_year is not None else "",
            },
        )
        self.work_log.tool_logs.append(tool_log)

        import requests

        try:
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
                    f"cdr:1,cd_min:01/01/{str(filter_year)},cd_max:12/31/{str(filter_year)}"
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
                    f" with filter year={filter_year}"
                    if filter_year is not None
                    else ""
                )
                result = f"No results found for '{query}'{year_filter_message}. Try with a more general query, or remove the year filter."
                tool_log.result = result
                return result

            web_snippets = []
            if self.organic_key in results:
                for idx, page in enumerate(results[self.organic_key]):
                    page["source_url"] = page["link"]
                    del page["link"]
                    web_snippets.append(json.dumps(page))
                    self.data_storage.store_with_source(
                        json.dumps(page), page["source_url"]
                    )

            result = "## Search Results\n" + "\n\n".join(web_snippets)
            tool_log.result = result
            return result

        except Exception as e:
            import traceback

            traceback.print_exc()
            tool_log.result = f"Error: {str(e)}"
            return "Error: " + str(e)
