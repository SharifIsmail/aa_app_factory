from typing import Any

import pandas
from smolagents import Tool

from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.core.utils.pandas_json_utils import deserialize_pandas_object_from_json
from service.data_schema_analysis import get_dataframe_metadata

MAX_ROWS_FOR_FULL_DISPLAY = 15
MAX_COLS_FOR_FULL_DISPLAY = 15


def format_dataframe_as_markdown(df: pandas.DataFrame) -> str:
    """Convert DataFrame to markdown table format"""
    markdown_result = df.to_markdown()
    return markdown_result if markdown_result is not None else str(df)


def should_show_full_dataframe(df: pandas.DataFrame) -> bool:
    """Determine if dataframe is small enough for full display"""
    return (
        len(df) <= MAX_ROWS_FOR_FULL_DISPLAY
        and len(df.columns) <= MAX_COLS_FOR_FULL_DISPLAY
    )


def format_dataframe_full_display(df: pandas.DataFrame) -> str:
    """Format small dataframe for complete display"""
    shape_info = f"({len(df)} rows × {len(df.columns)} columns)"
    header = f"COMPLETE DATAFRAME {shape_info}:"

    # str_representation = format_dataframe_as_markdown(df)
    str_representation = df.to_json(orient="split")

    return f"{header}\n\n{str_representation}"


def format_dataframe_schema_display(df: pandas.DataFrame) -> str:
    """Format large dataframe as schema information"""
    shape_info = f"({len(df)} rows × {len(df.columns)} columns)"
    header = f"DATAFRAME INSPECTION {shape_info}:"

    # Generate schema information
    schema = get_dataframe_metadata(df)
    schema_text = schema.to_prompt()

    return f"{header}\n\n{schema_text}"


def format_dataframe_for_inspection(df: pandas.DataFrame) -> str:
    """Format DataFrame for inspection, choosing between full display or schema based on size"""
    if should_show_full_dataframe(df):
        return format_dataframe_full_display(df)
    else:
        return format_dataframe_schema_display(df)


def prepare_dataframe_for_inspection(data: Any) -> pandas.DataFrame:
    """Convert Series to DataFrame and validate data type"""
    if not isinstance(data, (pandas.DataFrame, pandas.Series)):
        raise ValueError(f"Object is not a DataFrame or Series. Type: {type(data)}")

    # Convert Series to DataFrame for consistent handling
    if isinstance(data, pandas.Series):
        return data.to_frame()

    return data


class InspectDataTool(Tool):
    name = "inspect_data"
    inputs = {
        "data_id": {
            "type": "string",
            "description": "The unique data ID of a DataFrame or Series that was previously stored (returned by other tools).",
            "nullable": True,
        },
        "dataframe": {
            "type": "any",
            "description": "A pandas DataFrame or Series to inspect directly. Use this if you want to inspect data you have in memory.",
            "nullable": True,
        },
    }
    output_type = "string"
    description = (
        "Inspects a DataFrame or Series by showing complete data for small datasets or schema information for large ones. "
        "Provide either data_id (for stored data) or dataframe object directly."
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

    def forward(self, data_id: str | None = None, dataframe: Any | None = None) -> str:
        # Validate that exactly one parameter is provided
        if data_id is None and dataframe is None:
            raise ValueError("Either data_id or dataframe must be provided")
        if data_id is not None and dataframe is not None:
            raise ValueError(
                "Only one of data_id or dataframe should be provided, not both"
            )

        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "data_id": data_id,
                "has_dataframe": dataframe is not None,
                "dataframe_shape": str(dataframe.shape)
                if dataframe is not None and hasattr(dataframe, "shape")
                else None,
            },
        )
        self.work_log.tool_logs.append(tool_log)

        # Get the DataFrame either from storage or directly
        if data_id is not None:
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
            except AssertionError:
                raise ValueError(
                    f"Repository {self.repo_key} not found. You can only inspect data saved using `save_data`. Do not try to inspect the .parquet files."
                )

        else:
            # Use the provided DataFrame directly
            df = dataframe

        # Prepare DataFrame for inspection
        df = prepare_dataframe_for_inspection(df)

        # Format the DataFrame for inspection
        result = format_dataframe_for_inspection(df)

        return result
