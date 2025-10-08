import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import (
    DataFile,
    load_dataset_from_path,
)


class PandasDataFrameTool(Tool):
    name = "get_pandas_dataframe"
    inputs = {
        "data_name": {
            "type": "string",
            "description": "The name of the data file containing the pandas DataFrame",
        }
    }
    output_type = "any"

    def __init__(
        self,
        data_files: list[DataFile],
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.data_files = data_files
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.is_initialized = True
        self.description = self._generate_description()

    def _generate_description(self) -> str:
        available_datasets = []

        for data_file in self.data_files:
            available_datasets.append(f"<dataset> {data_file.file_name} </dataset>")

        datasets_info = "\n".join(available_datasets)

        return f"""This tool returns the complete dataset as a pandas.DataFrame for analysis based on your selection. 
The detailed columns and schemas are described in your system prompt. Use this tool instead of calling `pd.load_parquet()`
{datasets_info}
"""

    def forward(self, data_name: str) -> pandas.DataFrame:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"data_name": data_name},
        )
        self.work_log.tool_logs.append(tool_log)

        if not data_name.endswith(".parquet"):
            data_name = data_name + ".parquet"

        # Find the requested data file
        selected_data_file = None
        for data_file in self.data_files:
            if data_file.file_name == data_name:
                selected_data_file = data_file
                break

        if selected_data_file is None:
            available_names = [df.file_name for df in self.data_files]
            raise ValueError(
                f"Data file '{data_name}' not found. Available data files: {available_names}"
            )

        # Load and return the dataset
        logger.info(
            f"Loading dataset: {selected_data_file.file_name} from {selected_data_file.file_path}"
        )
        return load_dataset_from_path(selected_data_file.file_path)
