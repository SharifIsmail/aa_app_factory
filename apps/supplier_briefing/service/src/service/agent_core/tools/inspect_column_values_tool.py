import pandas as pd
from smolagents import Tool

from service.agent_core.data_management.columns import (
    COL_COUNTRY,
    COL_ESTELL_SEKTOR_GROB_RENAMED,
    COL_HAUPTWARENGRUPPE,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.core.utils.pandas_json_utils import deserialize_pandas_object_from_json
from service.data_loading import DataFile, load_dataset_from_path

DEFAULT_MAX_VALUES = 100


class InspectColumnValuesTool(Tool):
    name = "inspect_column_values"
    inputs = {
        "column_name": {
            "type": "string",
            "description": "Name of the column to inspect for unique values",
        },
        "dataset_name": {
            "type": "string",
            "nullable": True,
            "description": "Name of the parquet dataset to inspect",
        },
        "data_id": {
            "type": "string",
            "nullable": True,
            "description": "ID of a previously saved DataFrame to inspect",
        },
        "max_values": {
            "type": "integer",
            "nullable": True,
            "description": f"Maximum number of unique values to return. An error is raised if the column has more unique values than this limit. Default is {DEFAULT_MAX_VALUES}.",
        },
    }
    output_type = "array"
    description = f"""Returns the first N unique values from a specified column as a list of strings.

**ALWAYS use this tool BEFORE filtering DataFrames manually** to understand the actual values in columns.

**Examples of what NOT to do:**
- ❌ df[df['{COL_COUNTRY}'] == 'Germany']  # Don't guess country names
- ❌ df[df['{COL_ESTELL_SEKTOR_GROB_RENAMED}'].str.contains('agriculture')]  # Don't guess sector names  
- ❌ df[df['Betrachtungszeitraum'] > '2024-07-20']  # Don't guess time range values
- ❌ df[df['{COL_HAUPTWARENGRUPPE}'] == 'Food']  # Don't guess product categories
- ❌ df.head()  # Do not use head() to inspect dataframes, as the header may contain only a subset of values.

- **Instead, ALWAYS do this first:**
- ✅ inspect_column_values('business_partners', '{COL_COUNTRY}')
- ✅ inspect_column_values('transactions', '{COL_HAUPTWARENGRUPPE}') 
- ✅ inspect_column_values(data_id='my_filtered_data', 'Risikotyp')

**Then use the exact values you see** in search_and_filter_columns_for_matches.

This prevents errors from typos, wrong assumptions, or non-existent values.
Provide exactly one of 'dataset_name' or 'data_id'.
    """

    def __init__(
        self,
        data_files: list[DataFile],
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
        repo_key: str,
    ):
        super().__init__()
        self.data_files = data_files
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self.repo_key = repo_key

    def _find_data_file(self, dataset_name: str) -> DataFile:
        for df in self.data_files:
            if (
                df.file_name == dataset_name
                or df.file_name == dataset_name + ".parquet"
            ):
                return df
        available_names = [df.file_name for df in self.data_files]
        raise ValueError(
            f"Dataset '{dataset_name}' not found. Available datasets: {available_names}"
        )

    def _load_with_limits(
        self, dataset_name: str | None, data_id: str | None
    ) -> pd.DataFrame:
        sources = [s for s in [dataset_name, data_id] if s]
        if len(sources) != 1:
            raise ValueError("Provide exactly one of 'dataset_name' or 'data_id'.")

        if dataset_name:
            obj = load_dataset_from_path(self._find_data_file(dataset_name).file_path)
        elif data_id:
            try:
                all_repo = self.data_storage.retrieve_all_from_repo(self.repo_key)
            except KeyError as e:
                raise ValueError(f"Repository {self.repo_key} not found") from e
            df_json = all_repo.get(data_id)
            if df_json is None:
                raise ValueError(f"No pandas object found with ID: {data_id}")
            obj = deserialize_pandas_object_from_json(df_json)

        if not isinstance(obj, pd.DataFrame):
            raise ValueError("Only DataFrame inputs are supported.")

        return obj

    def forward(
        self,
        column_name: str,
        dataset_name: str | None = None,
        data_id: str | None = None,
        max_values: int | None = DEFAULT_MAX_VALUES,
    ) -> list[str]:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "dataset_name": dataset_name,
                "data_id": data_id,
                "column_name": column_name,
                "max_values": max_values,
            },
        )
        self.work_log.tool_logs.append(tool_log)

        if not column_name:
            raise ValueError("'column_name' must be provided.")

        # Load data with memory checks
        df = self._load_with_limits(dataset_name, data_id)

        # Validate column exists
        if column_name not in df.columns:
            available_cols = list(df.columns)
            raise ValueError(
                f"Column '{column_name}' not found in DataFrame. Available columns: {available_cols}"
            )

        # Use value_counts() which is memory efficient and gives us frequency info
        value_counts = df[column_name].value_counts(dropna=False)

        # Get the first max_values unique values
        unique_values = value_counts.head(max_values).index.tolist()

        # Convert all values to strings for consistent output
        unique_values_str = [str(val) for val in unique_values]

        total_unique = len(value_counts)

        if max_values is not None and total_unique > max_values:
            raise RuntimeError(
                f"Column '{column_name}' has {total_unique:,} unique values, exceeding max_values={max_values}. "
                f"Increase the max_values parameter to see more."
            )

        tool_log.result = f"unique_values_returned: {len(unique_values_str)}, total_unique_in_column: {total_unique}, column: {column_name}"

        return unique_values_str
