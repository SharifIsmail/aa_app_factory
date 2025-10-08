import os
import time
from collections.abc import Sequence
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from loguru import logger
from smolagents import ChatMessage, LiteLLMModel
from smolagents.tools import Tool

from service.dependencies import with_settings


class LoggingLiteLLMModel(LiteLLMModel):
    """Wrapper for LiteLLMModel that adds message logging functionality for all model types."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        settings = with_settings()
        self.enable_llm_message_saving: bool = settings.enable_llm_message_saving
        self.llm_debug_folder: str = "llm_debug"

        if self.enable_llm_message_saving:
            Path(self.llm_debug_folder).mkdir(exist_ok=True)

    def generate(
        self,
        messages: Sequence[ChatMessage | dict[Any, Any]],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from: list[Tool] | None = None,
        **kwargs: Any,
    ) -> ChatMessage:
        """Override the generate method to add logging."""
        # Use model_id or a default value for logging
        model_id = self.model_id or "unknown_model"

        if self.enable_llm_message_saving:
            self._save_debug_messages(model_id, messages)

        response = super().generate(
            list(messages),
            stop_sequences=stop_sequences,
            response_format=response_format,
            tools_to_call_from=tools_to_call_from,
            **kwargs,
        )

        return response

    def __call__(
        self, messages: Sequence[ChatMessage | dict[Any, Any]], **kwargs: Any
    ) -> ChatMessage:
        """Override the call method as well for compatibility."""
        # Just delegate to generate which handles everything
        return self.generate(messages, **kwargs)

    def _save_debug_messages(
        self, model: str, messages: Sequence[ChatMessage | dict[Any, Any]]
    ) -> None:
        try:
            timestamp = time.time()
            dt = datetime.fromtimestamp(timestamp)
            readable_timestamp = dt.strftime("%Y-%m-%d_%H-%M-%S")
            milliseconds = int((timestamp % 1) * 1000)
            debug_file_path = os.path.join(
                self.llm_debug_folder,
                f"messages_{readable_timestamp}_{milliseconds:03d}.md",
            )

            with open(debug_file_path, "w") as f:
                self._write_debug_header(f, model, timestamp)
                self._write_messages(f, messages)
                self._write_debug_footer(f)

            logger.debug(f"Saved LLM messages to: {debug_file_path}")
        except Exception as e:
            logger.error(f"Failed to save LLM messages: {e}")

    def _write_debug_header(
        self, file: TextIOWrapper, model: str, timestamp: float
    ) -> None:
        formatted_time = datetime.fromtimestamp(timestamp).isoformat()
        file.write(f"# LLM Debug Log\n\n")
        file.write(f"**Model:** `{model}`\n\n")
        file.write(f"**Timestamp:** {formatted_time} (Unix: {int(timestamp)})\n\n")
        file.write("---\n\n")

    def _write_messages(
        self, file: TextIOWrapper, messages: Sequence[ChatMessage | dict[Any, Any]]
    ) -> None:
        for message in messages:
            self._write_single_message(file, message)

    def _write_single_message(
        self, file: TextIOWrapper, message: ChatMessage | dict[str, Any]
    ) -> None:
        if hasattr(message, "role") and hasattr(message, "content"):
            # ChatMessage object
            role = message.role
            content = message.content
        elif isinstance(message, dict):
            # Dictionary message
            role = message.get("role")
            content = message.get("content")
        else:
            logger.warning(f"Unknown message format: {type(message)}")
            return

        role_display = self._format_role(role)
        file.write(f"## {role_display}\n\n")

        if isinstance(content, str):
            file.write("```\n")
            file.write(content)
            file.write("\n```\n")
        elif isinstance(content, list):
            self._write_message_chunks(file, content)
        else:
            file.write("```\n")
            file.write(str(content))
            file.write("\n```\n")

        file.write("\n")

    def _format_role(self, role: Any) -> str:
        """Format role for display, handling various role types."""
        if hasattr(role, "value"):
            return str(role.value).upper()
        elif hasattr(role, "name"):
            return str(role.name).upper()
        else:
            return str(role).upper()

    def _write_message_chunks(self, file: TextIOWrapper, chunks: list) -> None:
        file.write("```\n")
        for chunk in chunks:
            if isinstance(chunk, dict) and "text" in chunk:
                text = chunk["text"]
            else:
                text = str(chunk)

            file.write(text)
            if not text.endswith("\n"):
                file.write("\n")
        file.write("```\n")

    def _write_debug_footer(self, file: TextIOWrapper) -> None:
        file.write("\n---\n")
        file.write("\n*End of LLM Debug Log*\n")
