from pathlib import Path
from typing import Union

import pandas
from loguru import logger
from smolagents import Tool

from service.agent_core.data_management.columns import COL_BUSINESS_PARTNER_ID
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.data_loading import load_dataset_from_path
from service.data_preparation import BUSINESS_PARTNER_METADATA_COLS

BUSINESS_PARTNER_SUMMARY_COLUMNS = [
    *BUSINESS_PARTNER_METADATA_COLS,
    "Maximales Konkretes Risiko T0",
    "Maximales Konkretes Risiko T1",
    "Maximales Konkretes Risiko Tn",
]


class SummarizeBusinessPartnersTool(Tool):
    name = "summarize_business_partners"
    inputs = {
        "business_partner_ids": {
            "type": "any",
            "description": f"The id(s) ('{COL_BUSINESS_PARTNER_ID}') of the business partner(s) to summarize. "
            f"Can be either a single string ID or a list of string IDs.",
        }
    }
    output_type = "any"
    description = (
        "This tool summarizes business partner data from a specified file. "
        "It accepts either a single business partner ID (string) or multiple IDs (list of strings). "
        "For a single ID, it returns a pandas.Series containing the business partner information. "
        "For multiple IDs, it returns a pandas.DataFrame with each business partner as a separate row. "
        "The return value of this tool is suitable to be returned to the user. "
        "Usage examples: "
        "partner_summary = summarize_business_partners('10000') "
        "# Returns: Series with partner metadata and risk summaries. "
        "partners_summary = summarize_business_partners(['10000', '10001', '10002']) "
        "# Returns: DataFrame with multiple partners' metadata and risk summaries. "
        f"Columns: {', '.join(BUSINESS_PARTNER_SUMMARY_COLUMNS)}"
    )

    def __init__(
        self,
        business_partner_file: Path,
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.file_path = business_partner_file
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log

    def forward(
        self, business_partner_ids: Union[str, list[str]]
    ) -> Union[pandas.Series, pandas.DataFrame]:
        if isinstance(business_partner_ids, str):
            ids_list = [business_partner_ids]
            return_single = True
        else:
            ids_list = business_partner_ids
            return_single = False

        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={"business_partner_ids": business_partner_ids},
            data_source=self.file_path.name,
        )
        self.work_log.tool_logs.append(tool_log)

        df = load_dataset_from_path(
            self.file_path, columns=BUSINESS_PARTNER_SUMMARY_COLUMNS
        )

        # Check if all requested IDs exist
        missing_ids = [bp_id for bp_id in ids_list if bp_id not in df.index]
        if missing_ids:
            raise ValueError(
                f"No data found for business partner ID(s): {', '.join(missing_ids)}"
            )

        # Get the summary data for all requested IDs
        summary_data = df.loc[ids_list, BUSINESS_PARTNER_SUMMARY_COLUMNS]

        if return_single:
            # Return Series for single ID
            result = summary_data.iloc[0]
            logger.info(
                f"Generated business partner summary for ID: {business_partner_ids}"
            )
        else:
            # Return DataFrame for multiple IDs
            result = summary_data
            logger.info(
                f"Generated business partner summaries for IDs: {', '.join(ids_list)}"
            )

        return result
