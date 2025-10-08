import json
import os
import time
from typing import Any, Callable

import requests
from litellm import CustomLLM, ModelResponse
from loguru import logger
from smolagents import MessageRole


class AALLMProvider(CustomLLM):
    def __init__(self) -> None:
        self.api_url = str(self.client_url + "/chat/completions")
        self.role_mapping = {
            MessageRole.SYSTEM: "system",
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
        }
        self.max_retries = 5
        self.retry_delay = 1  # seconds
        self.logger = logger

    @property
    def api_key(self) -> str:
        """Load API key dynamically from environment variables."""
        return os.environ.get("SERVICE_AUTHENTICATION_TOKEN", "")

    @property
    def client_url(self) -> str:
        return os.environ.get("SERVICE_INFERENCE_API_URL", "")

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
        if not self.api_key:
            raise ValueError(
                "SERVICE_AUTHENTICATION_TOKEN environment variable is not set. Please ensure the .env file is loaded or set the environment variable."
            )

        api_messages = []
        for m in messages:
            role = self.role_mapping.get(m["role"])
            content = m["content"]
            if isinstance(content, str):
                api_messages.append({"role": role, "content": content})

            elif isinstance(content, list):
                for chunk in content:
                    api_messages.append({"role": role, "content": chunk["text"]})

            else:
                raise TypeError(
                    f"Expected content to be str or list, got {type(content)}"
                )

        payload = {
            "messages": api_messages,
            "model": model,
            **(optional_params or {}),
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Attempting LLM call (attempt {attempt + 1}/{self.max_retries})"
                )
                self.logger.debug(f"Using API URL: {self.api_url}")
                self.logger.debug(
                    f"API key available: {'Yes' if self.api_key else 'No'}"
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

                response_data = {
                    "choices": [
                        {"message": {"role": "assistant", "content": completion_text}}
                    ]
                }
                self.logger.info("LLM call successful")
                return ModelResponse(**response_data)

            except Exception as e:
                self.logger.error(
                    f"LLM call failed on attempt {attempt + 1}/{self.max_retries}: {str(e)}"
                )
                if attempt < self.max_retries - 1:  # If not the last attempt
                    delay = self.retry_delay * (attempt + 1)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)  # Exponential backoff
                    continue
                else:  # Last attempt failed
                    self.logger.error("All retry attempts failed, raising exception")
                    raise Exception(
                        f"All {self.max_retries} LLM call attempts failed: {str(e)}"
                    )

        # Return empty response if all attempts failed without raising an exception
        return ModelResponse(
            choices=[{"message": {"role": "assistant", "content": ""}}]
        )
