import json
import time
import traceback
from typing import Any, Callable

import requests
import tiktoken
from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import ModelResponse
from loguru import logger
from pydantic import BaseModel
from smolagents import MessageRole

from service.agent_core.model_settings_service import model_settings_service
from service.dependencies import with_settings
from service.utils import strip_thinking_tags

CONTEXT_WINDOW_SAFEGUARD_FACTOR = 0.8


class ApiMessage(BaseModel):
    role: str
    content: str


class MessageTokenInfo(BaseModel):
    api_parts_count: int
    token_count: int


class ParsedMessagesResult(BaseModel):
    api_messages: list[ApiMessage]
    message_tokens: list[MessageTokenInfo]
    message_roles: list[str]


class MessageConverter:
    """Handles conversion of messages between different formats for LLM APIs."""

    def __init__(self, model: str, enable_token_counting: bool = False) -> None:
        """
        Initialize the message converter with built-in role mappings.

        Args:
            model: The model identifier to determine context window limits
            enable_token_counting: Whether to enable token counting functionality
        """
        self.model = model
        self.role_mapping: dict[MessageRole, str] = {
            MessageRole.SYSTEM: "system",
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
        }
        self.enable_token_counting = enable_token_counting
        self._tokenizer = None
        self.max_context_window = self._get_max_context_window(model)

        if enable_token_counting:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")

    def _get_max_context_window(self, model: str) -> int:
        """
        Get the maximum context window for the given model from the settings service.

        Args:
            model: The model identifier

        Returns:
            Maximum context window size

        Raises:
            ValueError: If model is not found in the settings service
        """
        model_name = model.split("/")[-1]

        return model_settings_service.get_max_context_window(model_name)

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens in the text, or -1 if token counting is disabled

        Raises:
            RuntimeError: If tokenizer fails and token counting is enabled
        """
        if not self.enable_token_counting:
            return -1

        tokenizer = self._tokenizer
        if tokenizer is None:
            raise RuntimeError(
                "Tokenizer is not initialized while token counting is enabled"
            )

        return len(tokenizer.encode(text))

    def _parse_messages_to_api_format(self, messages: list) -> ParsedMessagesResult:
        """
        Parse messages and compute token counts per original message.

        Returns structured data with API messages, token information, and roles.
        """
        api_messages: list[ApiMessage] = []
        message_tokens: list[MessageTokenInfo] = []
        message_roles: list[str] = []

        for m in messages:
            role = self.role_mapping[m["role"]]
            content = m["content"]
            parts: list[ApiMessage] = []
            token_count_for_message = 0

            if isinstance(content, str):
                parts.append(ApiMessage(role=role, content=content))
                token_count_for_message += self.count_tokens(content)
            elif isinstance(content, list):
                for chunk in content:
                    chunk_text = chunk["text"]
                    parts.append(ApiMessage(role=role, content=chunk_text))
                    token_count_for_message += self.count_tokens(chunk_text)
            else:
                raise TypeError(
                    f"Expected content to be str or list, got {type(content)}"
                )

            api_messages.extend(parts)
            message_tokens.append(
                MessageTokenInfo(
                    api_parts_count=len(parts), token_count=token_count_for_message
                )
            )
            message_roles.append(role)

        return ParsedMessagesResult(
            api_messages=api_messages,
            message_tokens=message_tokens,
            message_roles=message_roles,
        )

    def _trim_messages_to_context_window(
        self, parsed_result: ParsedMessagesResult
    ) -> list[ApiMessage]:
        """
        Drop earliest consecutive messages until the total token count fits,
        respecting structural rules: never drop initial system, drop only
        (user, assistant) pairs from the head.
        """
        # If token counting is disabled, return as-is (explicit behavior, no fallback estimation)
        if not self.enable_token_counting:
            return parsed_result.api_messages

        total_tokens = sum(
            token_info.token_count for token_info in parsed_result.message_tokens
        )
        safe_max_context = self.max_context_window * CONTEXT_WINDOW_SAFEGUARD_FACTOR

        if total_tokens <= safe_max_context:
            return parsed_result.api_messages

        api_parts_to_drop = 0
        tokens_to_drop = 0

        # Never drop the very first system message if present
        start_idx = (
            1
            if parsed_result.message_roles
            and parsed_result.message_roles[0] == "system"
            else 0
        )

        i = start_idx
        while (
            i + 1 < len(parsed_result.message_tokens)
            and (total_tokens - tokens_to_drop) > safe_max_context
        ):
            if not (
                parsed_result.message_roles[i] == "user"
                and parsed_result.message_roles[i + 1] == "assistant"
            ):
                raise ValueError(
                    f"Expected alternating user/assistant message sequence, but found "
                    f"'{parsed_result.message_roles[i]}' followed by "
                    f"'{parsed_result.message_roles[i + 1]}' at positions {i} and {i + 1}"
                )

            api_parts_to_drop += (
                parsed_result.message_tokens[i].api_parts_count
                + parsed_result.message_tokens[i + 1].api_parts_count
            )
            tokens_to_drop += (
                parsed_result.message_tokens[i].token_count
                + parsed_result.message_tokens[i + 1].token_count
            )
            i += 2

        if tokens_to_drop == 0:
            return parsed_result.api_messages

        logger.warning(
            "Context window exceeded: %s > %s. Dropping head: %s API part(s) across %s messages.",
            total_tokens,
            safe_max_context,
            api_parts_to_drop,
            i - start_idx,
        )

        if start_idx == 1:
            # Preserve the system message
            system_message_parts = parsed_result.message_tokens[0].api_parts_count
            system_slice = parsed_result.api_messages[:system_message_parts]
            trimmed_slice = parsed_result.api_messages[
                system_message_parts + api_parts_to_drop :
            ]
            return system_slice + trimmed_slice
        else:
            return parsed_result.api_messages[api_parts_to_drop:]

    def convert_messages(self, messages: list) -> list[dict[str, str]]:
        """
        Convert messages from smolagents format to API format.
        Trims earliest messages if token count exceeds context window (only when
        token counting is enabled).

        Args:
            messages: List of messages in smolagents format

        Returns:
            List of messages in API format, possibly trimmed to fit context window

        Raises:
            TypeError: If message content is neither string nor list
        """
        parsed_result = self._parse_messages_to_api_format(messages)
        trimmed_messages = self._trim_messages_to_context_window(parsed_result)

        # Convert back to dict format for compatibility with existing API
        return [message.model_dump() for message in trimmed_messages]


class AALLMProvider(CustomLLM):
    def __init__(self) -> None:
        settings = with_settings()
        self.api_url = f"{settings.inference_api_url.rstrip('/')}/chat/completions"
        self.api_key = settings.authentication_token.get_secret_value()

        # Validate authentication token
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError(
                "AA_TOKEN (SERVICE_AUTHENTICATION_TOKEN) is missing or empty! "
                "Please ensure your .env file contains a valid authentication token."
            )

        self.role_mapping = {
            MessageRole.SYSTEM: "system",
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
        }
        self.max_retries = 5
        self.retry_delay = 1  # seconds
        self.logger = logger

    def completion(
        self,
        model: str,
        messages: list,
        api_base: str = None,
        custom_prompt_dict: dict = None,
        model_response: ModelResponse = None,
        print_verbose: Callable = None,
        encoding: Any = None,
        api_key: Any = None,
        logging_obj: Any = None,
        optional_params: dict = None,
        acompletion: Any = None,
        litellm_params: Any = None,
        logger_fn: Any = None,
        headers: Any = None,
        timeout: Any = None,
        client: Any = None,
    ) -> ModelResponse:
        # Create message converter and use it to convert messages
        message_converter = MessageConverter(model, enable_token_counting=True)
        api_messages = message_converter.convert_messages(messages)

        # Prepare request payload with default temperature
        payload = {
            "messages": api_messages,
            "model": model,
            "temperature": 0.0,  # Deterministic, repeatable responses
            **(optional_params or {}),
        }

        # Make the HTTP request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Attempting LLM call (attempt {attempt + 1}/{self.max_retries})"
                )
                response = requests.post(
                    self.api_url, headers=headers, data=json.dumps(payload), timeout=180
                )
                response.raise_for_status()

                resp_json = response.json()
                completion_text = (
                    resp_json.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )

                # Strip thinking tags from the completion text
                self.logger.info("Completion text before cleaning:", completion_text)
                cleaned_completion_text = strip_thinking_tags(completion_text)

                response_data = {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": cleaned_completion_text,
                            }
                        }
                    ]
                }

                return ModelResponse(**response_data)

            except Exception as e:
                self.logger.error(
                    f"LLM call failed on attempt {attempt + 1}/{self.max_retries}: {str(e)}"
                )
                self.logger.error(f"Stack trace:\n{traceback.format_exc()}")

                # Log ALL response data on error
                if hasattr(e, "response") and e.response is not None:
                    self.logger.error(f"HTTP Status Code: {e.response.status_code}")
                    self.logger.error(f"Response Headers: {dict(e.response.headers)}")
                    try:
                        response_text = e.response.text
                        self.logger.error(f"Response Body: {response_text}")
                        # Try to parse as JSON for better formatting
                        try:
                            response_json = e.response.json()
                            self.logger.error(
                                f"Response JSON: {json.dumps(response_json, indent=2)}"
                            )
                        except:
                            pass
                    except:
                        self.logger.error("Could not read response body")

                if attempt < self.max_retries - 1:  # If not the last attempt
                    delay = self.retry_delay * (attempt + 1)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)  # Exponential backoff
                    continue
                else:  # Last attempt failed
                    self.logger.error("All retry attempts failed, raising exception")
                    self.logger.error(
                        f"Final failure stack trace:\n{traceback.format_exc()}"
                    )
                    raise Exception(
                        f"All {self.max_retries} LLM call attempts failed: {str(e)}"
                    )

        # Return empty response if all attempts failed without raising an exception
        return ModelResponse(
            choices=[{"message": {"role": "assistant", "content": ""}}]
        )
