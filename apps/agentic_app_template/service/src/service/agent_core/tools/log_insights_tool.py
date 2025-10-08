from typing import List

from loguru import logger
from smolagents import Tool
from smolagents.models import LiteLLMModel

from service.agent_core.models import DataStorage, InsightData, ToolLog, WorkLog


class LogInsightsDataTool(Tool):
    name = "log_insights_data_to_queue"
    description = """Log one or multiple discovered insights to the data processing queue for further analysis"""
    inputs = {
        "insights_data": {
            "type": "array",
            "description": "A list of InsightData objects (each is a dict with the required fields).",
        }
    }
    output_type = "string"

    def __init__(
        self,
        insights_data_storage: DataStorage,
        work_log: WorkLog = None,
        model: LiteLLMModel = None,
        insights_repo: str = "GOOGLE_SEARCH",
    ):
        super().__init__()
        if model is None:
            raise ValueError("Model must be provided to this tool")
        self.insights_data_storage = insights_data_storage
        self.work_log = work_log
        self.model = model
        self.insights_repo = insights_repo
        logger.info(
            f"LogInsightsDataTool initialized with insights_repo: {insights_repo}"
        )

    def forward(self, insights_data: List[InsightData]) -> str:
        tool_log = None
        if self.work_log:
            tool_log = ToolLog(
                tool_name=self.name, params={"insights_data": insights_data}
            )
            self.work_log.tool_logs.append(tool_log)

        logger.info(
            f"Processing {len(insights_data)} insights for repository: {self.insights_repo}"
        )

        insights_added = 0
        for insight_data in insights_data:
            insight_key = (
                f"insight_{self.insights_data_storage.repo_length(self.insights_repo)}"
            )
            logger.debug(
                f"Storing insight data with key '{insight_key}' to repository '{self.insights_repo}'"
            )

            self.insights_data_storage.store_to_repo(
                self.insights_repo, insight_key, insight_data.to_dict()
            )
            insights_added += 1

        queue_length = self.insights_data_storage.repo_length(self.insights_repo)
        if insights_added == 0:
            result = f"No valid insights were stored. Queue remains at {queue_length} insights."
        elif insights_added == 1:
            result = f"1 insight logged successfully. Queue now contains {queue_length} insights."
        else:
            result = f"{insights_added} insights logged successfully. Queue now contains {queue_length} insights."

        logger.info(result)

        if tool_log:
            tool_log.result = result

        return result
