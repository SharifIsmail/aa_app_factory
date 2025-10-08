import json
import os
from typing import Any, Callable

import litellm
import requests
from litellm import CustomLLM, ModelResponse
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel, MessageRole
from smolagents.tools import Tool

from service.dependencies import with_settings


class AALLMProvider(CustomLLM):
    def __init__(self) -> None:
        base_url = os.environ.get("SERVICE_INFERENCE_API_URL", "")
        self.api_url = f"{base_url.rstrip('/')}/chat/completions"
        self.api_key = os.environ.get("SERVICE_AUTHENTICATION_TOKEN", "")
        self.role_mapping = {
            MessageRole.SYSTEM: "system",
            MessageRole.USER: "user",
            MessageRole.ASSISTANT: "assistant",
        }

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

            if isinstance(m["content"], list):
                for item in m["content"]:
                    api_messages.append({"role": role, "content": item["text"]})
            else:
                raise TypeError(
                    "Expected content to be a list, got " + str(type(m["content"]))
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

        response = requests.post(
            self.api_url, headers=headers, data=json.dumps(payload)
        )

        # Process the response
        if response.status_code == 200:
            resp_json = response.json()
            completion_text = (
                resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            response_data = {
                "choices": [
                    {"message": {"role": "assistant", "content": completion_text}}
                ]
            }
            return ModelResponse(**response_data)
        else:
            raise Exception(
                f"API request failed with status code {response.status_code}: {response.text}"
            )


class DummyTool(Tool):
    name = "google_search"
    description = """Search Google for a query"""
    inputs = {"query": {"type": "string", "description": "the query to search for"}}
    output_type = "string"

    def __init__(self, **kwargs) -> None:
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

    # agent = CodeAgent(tools=[DummyTool()], model=model)

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
    # test_dummy_llm_call()
    test_dummy_agent()
    pass
