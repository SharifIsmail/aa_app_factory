from litellm import completion
from pydantic import BaseModel

from service.agent_core.explainability.explainability_prompts import (
    SUMMARY_EXPLAINABILITY_PROMPT,
)
from service.agent_core.models import ToolLog
from service.data_preparation_file_mapping import FILE_CREATION_MAP
from service.dependencies import with_settings
from service.utils import strip_thinking_tags

NO_DATA_OPERATIONS_STRING = "Es wurden keine Daten abgerufen"


class ChatMessage(BaseModel):
    role: str
    content: str


class ExplainabilityLLMClient:
    """LLM client for generating explainability of smolagents steps using litellm.completion"""

    def __init__(self) -> None:
        self.settings = with_settings()

    def complete(self, messages: list[ChatMessage], model: str) -> str:
        raw_messages = [m.model_dump() for m in messages]
        response = completion(
            messages=raw_messages,
            model=model,
            vertex_credentials=self.settings.vertex_ai_credentials.get_secret_value(),
        )
        return response.choices[0].message.content

    def generate_explanation(
        self,
        step_model_output: str,
        tool_logs: list[ToolLog],
    ) -> str:
        """
        Generate an explanation for a step using the configured model and prompt template.

        Args:
            step_model_output: The model output from the step
            tool_logs: List of relevant tool logs for the step

        Returns:
            Processed explanation with thinking tags stripped, or NO_DATA_OPERATIONS_STRING
        """
        tool_logs_string = self._format_tool_logs(tool_logs)

        messages = [
            ChatMessage(
                role="user",
                content=SUMMARY_EXPLAINABILITY_PROMPT.format(
                    step_model_output=step_model_output,
                    no_data_operations_string=NO_DATA_OPERATIONS_STRING,
                    tool_logs_string=tool_logs_string,
                    file_creation_map=FILE_CREATION_MAP,
                    output_language=self.settings.target_output_language,
                ),
            )
        ]

        raw_content = self.complete(
            messages=messages, model=self.settings.model_explainability
        )

        explanation = strip_thinking_tags(raw_content)

        return explanation

    @staticmethod
    def _format_tool_logs(tool_logs: list[ToolLog]) -> str:
        """Convert a list of ToolLog objects into a formatted string for LLM consumption."""
        if not tool_logs:
            return "No tool logs available."

        formatted_logs: list[str] = []
        for i, log in enumerate(tool_logs, 1):
            log_entry = f"Tool {i}: {log.tool_name}\n"
            log_entry += f"Description: {log.description}\n"
            if log.data_source:
                log_entry += f"Original source: {log.data_source}\n"
            if log.result:
                log_entry += f"Result: {log.result}\n"
            else:
                log_entry += "Result: No result available\n"
            formatted_logs.append(log_entry)

        return "\n".join(formatted_logs)
