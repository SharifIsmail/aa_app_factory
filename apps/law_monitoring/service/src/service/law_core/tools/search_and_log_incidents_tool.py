import json
from typing import Optional

from loguru import logger
from smolagents import Tool
from smolagents.models import LiteLLMModel

from service.law_core.models import InsightData, ToolLog, WorkLog
from service.law_core.tools.google_search_with_source_url_tool import (
    GoogleSearchWithSourceURLTool,
)
from service.law_core.tools.log_insights_tool import LogInsightsDataTool
from service.storage.data_storage import DataStorage


class SearchAndExtractInsightsTool(Tool):
    name = "search_and_extract_insights"
    description = """Performs a google web search for insights data and logs them to the insights storage.
    
    IMPORTANT: Do not attempt to parse or iterate over the return value of this tool!
    
    This tool already logs the search results to storage for you automatically. The main purpose is the side effect
    of finding and storing insights data, not the return value itself. After calling this tool, move on to other
    tools like visit_webpage to explore the most relevant URLs from your search term.
    
    Example correct usage:
    ```
    # Find information
    search_and_extract_insights(query="your search query")
    
    # Then visit specific URLs directly, don't try to iterate over the return value
    visit_webpage("https://example.com/relevant-page")
    ```
    """
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
        google_search_repo_key: str,
        insights_repo_key: str,
        execution_id: str,
        work_log: WorkLog,
        model: LiteLLMModel,
        provider: str = "serpapi",
    ):
        super().__init__()
        self.google_search_repo_key = google_search_repo_key
        self.insights_repo_key = insights_repo_key
        self.search_tool = GoogleSearchWithSourceURLTool(
            data_storage=data_storage,
            repo_key=google_search_repo_key,
            execution_id=execution_id,
            work_log=work_log,
            provider=provider,
        )
        self.log_tool = LogInsightsDataTool(
            insights_data_storage=data_storage,
            work_log=work_log,
            model=model,
            insights_repo=insights_repo_key,
        )
        self.data_storage = data_storage
        self.work_log = work_log
        logger.info(
            f"SearchAndExtractInsightsTool initialized with insights_repo: {insights_repo_key}"
        )

    def forward(self, query: str, filter_year: Optional[int] = None) -> str:
        tool_log = ToolLog(
            tool_name=self.name, params={"query": query, "filter_year": filter_year}
        )
        self.work_log.tool_logs.append(tool_log)

        logger.info(f"Searching for: '{query}' with filter_year={filter_year}")

        # Perform the search and get structured results directly
        logger.info("Executing search using GoogleSearchWithSourceURLTool")
        search_results = self.search_tool.forward(query, filter_year)

        # Create InsightData objects from the structured search results
        insight_data_list = []

        # Process each search result
        for result in search_results:
            # Extract data from the structured result
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            source_url = result.get("source_url", "")

            # Create the value field by combining title and snippet
            value = (
                f"{title}: {snippet}"
                if title and snippet
                else (title or snippet or source_url)
            )

            # Create an InsightData object for the log tool
            insight = InsightData(
                title=title,
                source_url=source_url,
                value=value,
                timestamp=result.get("timestamp"),
            )
            insight_data_list.append(insight)
            logger.debug(f"Created InsightData from search result: {title}")

        logger.info(
            f"Created {len(insight_data_list)} InsightData objects from search results"
        )

        # Log the insights using the log tool
        if insight_data_list:
            logger.info(
                f"Logging {len(insight_data_list)} insight data objects to repository: {self.insights_repo_key}"
            )
            self.log_tool.forward(insight_data_list)

        tool_log.result = json.dumps(search_results, indent=2)
        logger.info("SearchAndExtractInsightsTool completed successfully")
        return json.dumps(search_results, indent=2)
