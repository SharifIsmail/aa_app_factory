import hashlib
import re
from typing import Any

import pandas as pd
from loguru import logger
from smolagents import Tool

from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.core.utils.pandas_json_utils import serialize_pandas_object_to_json

SAVE_MAX_CELLS = (
    1_000_000  # corresponds to roughly 10-20 MBs for mix of int64, float64, and strings
)
SAVE_MAX_COLUMNS = 30


class SaveDataTool(Tool):
    name = "save_data"
    inputs = {
        "data": {
            "type": "any",
            "description": "The pandas DataFrame or Series to save. This should be a non-empty DataFrame/Series you created during your analysis.",
        },
        "description": {
            "type": "string",
            "description": "A clear description of what this DataFrame/Series contains and why it's relevant to the analysis.",
        },
        "data_type": {
            "type": "string",
            "description": "Type of data being saved (e.g., 'analysis_result', 'filtered_data', 'aggregated_summary', 'custom_calculation'). This helps categorize the saved data.",
            "nullable": True,
        },
    }
    output_type = "string"
    description = (
        "Saves a pandas DataFrame or Series to the repository and returns a unique ID."
        "Use this tool also to save data that is relevant context for answering a question, "
        "even if the question is a yes/no question."
        "Use the returned ID in present_results tool to include this data in the final report. "
    )

    def __init__(
        self,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        repo_key: str,
    ):
        super().__init__()
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.repo_key = repo_key

    def forward(
        self, data: Any, description: str, data_type: str = "analysis_result"
    ) -> str:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "description": description,
                "data_type": data_type,
                "dataframe_shape": str(data.shape)
                if hasattr(data, "shape")
                else "unknown",
            },
        )
        self.work_log.tool_logs.append(tool_log)

        # Validate input is a pandas DataFrame or Series
        if not isinstance(data, (pd.DataFrame, pd.Series)):
            raise ValueError(
                f"Input must be a pandas DataFrame or Series, got {type(data)}. "
                f"If you have a list, convert it to a DataFrame first using: "
                f"pd.DataFrame(your_list, columns=['column_name']) for simple lists, or "
                f"pd.DataFrame(your_list) for lists of dictionaries."
            )

        if data.size > SAVE_MAX_CELLS:
            raise ValueError(
                f"DataFrame/Series too large ({data.size:,} cells). Maximum allowed: {SAVE_MAX_CELLS:,} cells. Reduce by applying better filters, or avoid saving the dataframe."
            )

        # Check column count for DataFrames
        if isinstance(data, pd.DataFrame) and data.shape[1] > SAVE_MAX_COLUMNS:
            raise ValueError(
                f"DataFrame has too many columns ({data.shape[1]}). Maximum allowed: {SAVE_MAX_COLUMNS} columns. Consider reducing the number of columns by selecting only the most relevant ones."
            )

        if data.empty or data.size == 0:
            raise ValueError(
                "The provided DataFrame/Series is empty and cannot be saved."
            )

        def _clean_for_id(text: str) -> str:
            cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
            cleaned = re.sub(r"\s+", "_", cleaned.strip())
            return cleaned

        descriptive_name = _clean_for_id(description)
        if not descriptive_name:
            descriptive_name = _clean_for_id(data_type) or "data"

        content_hash = hashlib.md5(
            f"{data_type}_{description}_{str(data.shape)}".encode()
        ).hexdigest()[:2]

        data_id = f"{descriptive_name}_{content_hash}"

        # Store the pandas data to the repository
        self.data_storage.store_to_repo(
            self.repo_key, data_id, serialize_pandas_object_to_json(data)
        )
        logger.info(
            f"Stored DataFrame/Series with ID: {data_id}, description: {description}"
        )

        return data_id
