import json
import os
import time
from typing import Any, Callable

import litellm
import requests
from litellm import CustomLLM, ModelResponse
from loguru import logger
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel, MessageRole
from smolagents.tools import Tool

from service.dependencies import with_settings


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

        # Prepare request payload
        payload = {
            "messages": api_messages,
            "model": model,
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


class DummyTool(Tool):
    name = "google_search"
    description = """Search Google for a query"""
    inputs = {"query": {"type": "string", "description": "the query to search for"}}
    output_type = "string"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()

    def forward(self, query: str) -> str:
        result = query
        return result


def test_dummy_agent() -> None:
    custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}
    aa_llm_provider = AALLMProvider()
    litellm.custom_provider_map = [
        {"provider": "aleph-alpha", "custom_handler": aa_llm_provider}
    ]
    settings = with_settings()
    model = LiteLLMModel(
        model_id=f"aleph-alpha/{settings.completion_model_name}",
        max_completion_tokens=8192,
        custom_role_conversions=custom_role_conversions,
    )

    agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model)

    data_store: list[str] = []
    agent.run(
        "How many seconds would it take for a leopard at full speed to run through Pont des Arts?",
        additional_args={"data_store": data_store},
    )


def test_dummy_llm_call() -> None:
    aa_llm_provider = AALLMProvider()
    settings = with_settings()
    messages = [
        {
            "role": MessageRole.SYSTEM,
            "content": [{"text": "You are a helpful assistant."}],
        },
        {
            "role": MessageRole.USER,
            "content": [{"text": "What is the capital of the moon?"}],
        },
    ]
    response = aa_llm_provider.completion(settings.completion_model_name, messages)
    print(response)


if __name__ == "__main__":
    test_dummy_agent()
