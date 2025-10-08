import hashlib
from typing import List

from loguru import logger
from smolagents import Tool

from service.agent_core.constants import REPO_PANDAS_OBJECTS
from service.agent_core.models import DataStorage, ToolLog, WorkLog


class PresentResultsTool(Tool):
    name = "present_results"
    inputs = {
        "data_ids": {
            "type": "array",
            "description": "A list of unique IDs (strings) referencing pandas DataFrames/Series stored in the analysis repository. The tool will load these data structures automatically.",
        },
        "dataframe_descriptions": {
            "type": "array",
            "description": "A list of descriptions for each pandas object, explaining what data it contains. The description should be short with a maximum of 25 words.",
        },
    }
    output_type = "string"
    description = (
        "This tool presents final results and findings to the end user. "
        "Use this tool to provide a summary of your analysis along with supporting data. "
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
        self,
        data_ids: List[str],
        dataframe_descriptions: List[str],
    ) -> str:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "data_ids": data_ids,
                "dataframe_descriptions": dataframe_descriptions,
            },
        )
        self.work_log.tool_logs.append(tool_log)

        # Load dataframes from PANDAS_OBJECTS repository (where save_data tool stores them)
        serialized_dataframes_with_descriptions = []

        # Get all data from the PANDAS_OBJECTS repository where dataframes are saved
        try:
            all_repo_data = self.data_storage.retrieve_all_from_repo(
                REPO_PANDAS_OBJECTS
            )
        except Exception as e:
            error_msg = f"Failed to retrieve data from repository {REPO_PANDAS_OBJECTS}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        for i, df_id in enumerate(data_ids):
            try:
                # Load the pandas structure from the repository data
                df_json = all_repo_data.get(df_id)
                if df_json is None:
                    msg = f"WARNING: No data found for ID: {df_id} in repository {REPO_PANDAS_OBJECTS}. Make sure to use save_data tool first to store the dataframe."
                    logger.warning(msg)
                    raise ValueError(msg)

                description = (
                    dataframe_descriptions[i]
                    if i < len(dataframe_descriptions)
                    else f"DataFrame {i + 1}"
                )

                serialized_df_with_description = {
                    "description": description,
                    "data": df_json,
                }
                serialized_dataframes_with_descriptions.append(
                    serialized_df_with_description
                )
            except Exception as e:
                logger.error(f"Error loading dataframe with ID {df_id}: {str(e)}")
                raise

        # Generate deterministic unique key based on content
        content_hash = hashlib.md5(
            f"{str(data_ids)}_{self.execution_id}".encode()
        ).hexdigest()[:8]
        unique_key = f"results_{content_hash}"

        # Store the final results
        results_data = {
            "dataframes": serialized_dataframes_with_descriptions,
            "execution_id": self.execution_id,
        }

        self.data_storage.store_to_repo(self.repo_key, unique_key, results_data)
        logger.info(
            f"Stored final results with {len(serialized_dataframes_with_descriptions)} dataframes in {self.repo_key} repository with key: {unique_key}"
        )

        return f"Successfully presented results with {len(serialized_dataframes_with_descriptions)} supporting dataframes"
