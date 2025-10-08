from typing import Any

import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.core.utils.pandas_json_utils import deserialize_pandas_object_from_json


class LoadDataTool(Tool):
    name = "load_data"
    inputs = {
        "data_id": {
            "type": "string",
            "description": "The unique ID of a DataFrame or Series that was previously stored using save_data tool.",
        },
    }
    output_type = "any"
    description = "Loads a pandas DataFrame or Series that was previously saved using the save_data tool."

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

    def forward(self, data_id: str) -> Any:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"data_id": data_id},
        )
        self.work_log.tool_logs.append(tool_log)

        # Retrieve the DataFrame from storage
        try:
            all_repo_data = self.data_storage.retrieve_all_from_repo(self.repo_key)
            df_json = all_repo_data.get(data_id)
            assert isinstance(df_json, dict)
            df = deserialize_pandas_object_from_json(df_json)
            if df is None:
                raise ValueError(f"No DataFrame/Series found with ID: {data_id}")
        except KeyError:
            raise ValueError(f"Repository {self.repo_key} not found")

        if not isinstance(df, (pandas.DataFrame, pandas.Series)):
            raise ValueError(
                f"Object with ID {data_id} is not a DataFrame or Series. Type: {type(df)}"
            )

        logger.info(
            f"Successfully loaded DataFrame/Series with ID: {data_id}, shape: {df.shape}"
        )

        return df
