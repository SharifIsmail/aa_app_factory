from enum import Enum
from typing import TypeVar

from pydantic import Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from service.agent_core.model_constants import (
    DEFAULT_MODEL_DATA_ANALYSIS_AGENT,
    DEFAULT_MODEL_EVAL,
    DEFAULT_MODEL_EXPLAINABILITY,
    DEFAULT_MODEL_LLM_COMPLETION,
    DEFAULT_MODEL_QUERY_AGENT,
    DEFAULT_MODEL_WEAK,
)

T = TypeVar("T")


class AgentTelemetry(Enum):
    PHOENIX = "phoenix"
    PHARIA_STUDIO = "pharia_studio"
    DISABLED = "disabled"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_ignore_empty=False,  # required since OS does not allow empty env values on deployment
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,  # to avoid leaking secrets in error messages
        env_prefix="SERVICE_",  # to restrict the envs that get injected into the deployment
    )

    enable_cors: bool = True
    pharia_auth_service_url: str
    pharia_data_url: str
    completion_model_name: str
    inference_api_url: str
    studio_url: HttpUrl | None
    studio_project_name: str | None
    authentication_token: SecretStr = Field(min_length=1)
    vertex_ai_credentials: SecretStr
    target_output_language: str = "german"
    agent_telemetry: AgentTelemetry = AgentTelemetry.DISABLED
    enable_data_preparation: bool = False
    thinking_tag_end: str = "</think>"
    enable_llm_message_saving: bool = False
    enable_llm_caching: bool = True

    model_query_agent: str = DEFAULT_MODEL_QUERY_AGENT
    model_data_analysis_agent: str = DEFAULT_MODEL_DATA_ANALYSIS_AGENT
    model_llm_completion: str = DEFAULT_MODEL_LLM_COMPLETION
    model_evaluation: str = DEFAULT_MODEL_EVAL
    model_explainability: str = DEFAULT_MODEL_EXPLAINABILITY
    model_weak: str = DEFAULT_MODEL_WEAK

    @field_validator(
        "enable_cors",
        "enable_data_preparation",
        "enable_llm_message_saving",
        "enable_llm_caching",
        mode="before",
    )
    def parse_boolean_fields(cls, value: T) -> bool | T:
        if isinstance(value, str):
            cleaned_value = value.strip('"').lower()
            if cleaned_value == "true":
                return True
            elif cleaned_value == "false":
                return False
            else:
                raise ValueError(f'Invalid boolean string "{cleaned_value}"')
        return value

    @model_validator(mode="after")
    def validate_agent_telemetry(self) -> "Settings":
        if self.agent_telemetry == AgentTelemetry.PHARIA_STUDIO:
            if self.studio_url == None:
                raise ValueError(
                    "SERVICE_STUDIO_URL must be set if SERVICE_AGENT_TELEMETRY=pharia_studio"
                )
            if self.studio_project_name == None:
                raise ValueError(
                    "SERVICE_STUDIO_PROJECT_NAME must be set if SERVICE_AGENT_TELEMETRY=pharia_studio"
                )
        return self
