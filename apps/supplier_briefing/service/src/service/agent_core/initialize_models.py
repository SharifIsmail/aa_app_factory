from smolagents import LiteLLMModel

from service.agent_core.litellm_config import configure_litellm
from service.agent_core.llm.llm_logging_wrapper import LoggingLiteLLMModel
from service.agent_core.model_constants import (
    AVAILABLE_AA_MODELS,
    AVAILABLE_VERTEX_AI_MODELS,
)
from service.dependencies import with_settings


def initialize_models() -> dict[str, LiteLLMModel]:
    configure_litellm()
    custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

    models: dict[str, LiteLLMModel] = {}

    for model_id in AVAILABLE_AA_MODELS:
        models[model_id] = LoggingLiteLLMModel(
            model_id,
            custom_role_conversions=custom_role_conversions,
            max_completion_tokens=8192,
            temperature=0,
        )

    for model_id in AVAILABLE_VERTEX_AI_MODELS:
        models[model_id] = LoggingLiteLLMModel(
            model_id,
            max_completion_tokens=8192,
            temperature=0,
            vertex_credentials=with_settings().vertex_ai_credentials.get_secret_value(),
        )

    return models
