from loguru import logger
from smolagents import CodeAgent, LiteLLMModel, Tool

from service.agent_core.constants import REPO_PANDAS_OBJECTS
from service.agent_core.data_management.columns import (
    COL_BUSINESS_PARTNER_ID,
    COL_BUSINESS_PARTNER_NAME,
)
from service.agent_core.data_management.data_documentation import (
    DataDocumentation,
    DatasetName,
)
from service.agent_core.data_query_orchestration.prompts.data_analysis_agent_prompts import (
    DATA_ANALYSIS_AGENT_SYSTEM_PROMPT,
)
from service.agent_core.explainability.explainability_service import (
    ExplainabilityService,
)
from service.agent_core.models import DataStorage, ToolLog, WorkLog
from service.core.utils.generate_pandas_preview import generate_pandas_preview
from service.core.utils.pandas_json_utils import deserialize_pandas_object_from_json
from service.data_loading import DataFile, DataFileWithSchema
from service.dependencies import with_settings


class DataAnalysisAgentTool(Tool):
    name = "invoke_data_analysis_agent"
    inputs = {
        "task": {
            "type": "string",
            "description": "The data analysis task you want the agent to perform. Be specific about what you need (e.g., 'Filter business partners with high risk scores and calculate average transaction volumes by country')",
        },
        "data_ids": {
            "type": "array",
            "description": "List of data_ids that you want to pass to the agent. Can be left empty.",
            "nullable": True,
        },
    }
    output_type = "string"
    description = (
        "Invokes the data analysis agent to perform pandas data manipulations and analytics. "
        "The agent has access to all data files and can perform sophisticated data analysis tasks. "
        "Use this tool for data analytics tasks that go beyond the capabilities of more specialized tools."
        "Use this tool always in a separate python code block. Do not build complex logic around this tool call."
        "Returns a string of with the result of the agents solution. The answer will contain information about the saved dataframes that you can then use."
    )

    def __init__(
        self,
        lite_llm_models: dict[str, LiteLLMModel],
        data_analysis_tools: list[Tool],
        data_storage: DataStorage,
        execution_id: str,
        work_log: WorkLog,
    ):
        super().__init__()
        self.lite_llm_models = lite_llm_models
        self.data_analysis_tools = data_analysis_tools
        self.data_storage = data_storage
        self.execution_id = execution_id
        self.work_log = work_log
        self._agent = self._initialize_agent()

    def _initialize_agent(self) -> CodeAgent:
        """Initialize the data analysis agent with explainability callback if available."""
        settings = with_settings()

        step_callbacks = [
            ExplainabilityService.get_single_instance().make_callback(self.execution_id)
        ]

        agent = CodeAgent(
            model=self.lite_llm_models[settings.model_data_analysis_agent],
            tools=self.data_analysis_tools,
            additional_authorized_imports=["pandas", "numpy"],
            max_steps=10,
            verbosity_level=2,
            planning_interval=None,
            name="data_analysis_agent",
            provide_run_summary=False,
            code_block_tags="markdown",
            step_callbacks=step_callbacks,
        )

        return agent

    def _get_data_files(self) -> list[DataFile]:
        """Get the list of data files with their descriptions."""
        return DataDocumentation.get_data_files_with_descriptions(
            [
                DatasetName.RISK_PER_BUSINESS_PARTNER,
                DatasetName.RISK_PER_BRANCH,
                DatasetName.TRANSACTIONS,
                DatasetName.RESOURCE_RISKS_PROCESSED,
            ]
        )

    def _generate_description(self, data_files: list[DataFileWithSchema]) -> str:
        """Generate the description for the data analysis agent."""
        available_datasets = []
        for data_file in data_files:
            dataset_name = data_file.file_name.replace(".parquet", "")
            available_datasets.append(f"""
<dataset>
{dataset_name}
<description> {data_file.description}
</description>
<schema>
{data_file.data_schema.to_prompt()}
</schema>
</dataset>
    """)

        datasets_info = "\n".join(available_datasets)

        return f"""
    <datasets>
    {datasets_info}
    </datasets>
    """

    def _iterate_over_specified_dataframes(self, data_ids: list[str]) -> dict[str, str]:
        """
        Iterate over specified data IDs and generate enhanced previews of their DataFrames/Series.
        """
        results: dict[str, str] = {}

        if not data_ids:
            return results

        try:
            all_repo_data = self.data_storage.retrieve_all_from_repo(
                REPO_PANDAS_OBJECTS
            )

            for data_id in data_ids:
                try:
                    df_json = all_repo_data.get(data_id)
                    if df_json is None:
                        logger.warning(f"No data found for data_id: {data_id}")
                        results[data_id] = f"Error: No data found for ID {data_id}"
                        continue

                    assert isinstance(df_json, dict)
                    df = deserialize_pandas_object_from_json(df_json)

                    if df is not None:
                        enhanced_preview = generate_pandas_preview(df)
                        results[data_id] = enhanced_preview
                    else:
                        logger.warning(
                            f"Data with ID {data_id} is not a valid pandas object"
                        )
                        results[data_id] = (
                            f"Error: Invalid pandas object for ID {data_id}"
                        )

                except Exception as e:
                    logger.error(f"Failed to process data_id {data_id}: {str(e)}")
                    results[data_id] = f"Error: {str(e)}"

        except KeyError:
            logger.warning(f"Repository {REPO_PANDAS_OBJECTS} not found")
            for data_id in data_ids:
                results[data_id] = f"Error: Repository {REPO_PANDAS_OBJECTS} not found"

        return results

    def _get_current_data_ids(self) -> set[str]:
        try:
            all_repo_data = self.data_storage.retrieve_all_from_repo(
                REPO_PANDAS_OBJECTS
            )
            return set(all_repo_data.keys())
        except KeyError:
            return set()

    def _get_new_data_heads(self, new_data_ids: set[str]) -> dict[str, str]:
        """
        Get enhanced previews for new data IDs created during agent execution.
        """
        results: dict[str, str] = {}

        if not new_data_ids:
            return results

        try:
            all_repo_data = self.data_storage.retrieve_all_from_repo(
                REPO_PANDAS_OBJECTS
            )

            for data_id in new_data_ids:
                try:
                    df_json = all_repo_data.get(data_id)
                    if df_json is None:
                        continue

                    assert isinstance(df_json, dict)
                    df = deserialize_pandas_object_from_json(df_json)

                    if df is not None:
                        enhanced_preview = generate_pandas_preview(df)
                        results[data_id] = enhanced_preview

                except Exception as e:
                    logger.error(
                        f"Failed to get preview for new data_id {data_id}: {str(e)}"
                    )
                    results[data_id] = f"Error getting preview: {str(e)}"

        except KeyError:
            logger.warning(
                f"Repository {REPO_PANDAS_OBJECTS} not found when getting new data previews"
            )

        return results

    def forward(self, task: str, data_ids: list[str] = None) -> str:
        tool_log = ToolLog(
            tool_name=self.name,
            description=self.description,
            params={
                "task": task,
                "context": data_ids or "No additional context provided",
            },
        )
        self.work_log.tool_logs.append(tool_log)

        try:
            data_ids_before = self._get_current_data_ids()

            context_info = ""
            if data_ids:
                df_previews = self._iterate_over_specified_dataframes(data_ids)
                if df_previews:
                    context_parts = []
                    for data_id, df_preview in df_previews.items():
                        context_parts.append(
                            f"\n<data_id>{data_id}</data_id>\n<preview>\n{df_preview}\n</preview>"
                        )

                    context_info = "\n\n" + "\n\n".join(context_parts)

            # Build prefixed prompt including dataset documentation and DA agent system prompt
            data_files = self._get_data_files()
            data_files_with_schema = [
                data_file.add_schema() for data_file in data_files
            ]
            datasets_doc = self._generate_description(data_files_with_schema)
            da_preface = f"{datasets_doc}\n\n{DATA_ANALYSIS_AGENT_SYSTEM_PROMPT.format(glossary=DataDocumentation.get_glossary(), COL_BUSINESS_PARTNER_NAME=COL_BUSINESS_PARTNER_NAME, COL_BUSINESS_PARTNER_ID=COL_BUSINESS_PARTNER_ID)}"

            task_with_context = task + context_info
            if data_ids:
                task_with_context = f"Additional context for your task: {context_info} \n\n Your task: {task}"

            full_task_description = (
                f"{da_preface}\n\n<task>\n{task_with_context}\n</task>"
            )

            logger.info(f"Invoking data analysis agent with task: {task}")

            result = self._agent.run(full_task_description)

            data_ids_after = self._get_current_data_ids()
            new_data_ids = data_ids_after - data_ids_before

            new_data_previews = self._get_new_data_heads(new_data_ids)

            result_str = str(result) if result is not None else "No result returned"

            if new_data_ids:
                result_str += f"\n\n{'=' * 60}\n"
                result_str += f"New Data saved by the Data Analysis Agent\n"
                result_str += f"{'=' * 60}\n"
                result_str += f"Created {len(new_data_ids)} new data object(s): {list(new_data_ids)}\n\n"

                for data_id, preview_info in new_data_previews.items():
                    result_str += f"data_id: {data_id}\n"
                    result_str += f"{'-' * 50}\n"
                    result_str += f"{preview_info}\n"
                    result_str += f"{'-' * 50}\n\n"
            else:
                result_str += f"\n\n{'=' * 60}\n"
                result_str += f"NO NEW DATA CREATED\n"
                result_str += f"{'=' * 60}\n"
                result_str += (
                    "The agent completed the task without creating new data objects.\n"
                )

            tool_log.result = result_str

            return result_str

        except Exception as e:
            error_msg = f"Data analysis agent failed: {str(e)}"
            logger.error(error_msg)
            tool_log.result = error_msg
            raise Exception(error_msg)
