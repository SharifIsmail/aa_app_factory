import re
from typing import TypeVar

from pydantic import HttpUrl, PostgresDsn, Secret, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from service.law_core.persistence.storage_backend import StorageBackendType

T = TypeVar("T")


class SecretPostgresDsn(Secret[PostgresDsn]):  # pylint: disable=too-few-public-methods
    def _display(self) -> str:
        return "**********"

    __hash__ = object.__hash__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_ignore_empty=False,  # required since OS does not allow empty env values on deployment
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,  # to avoid leaking secrets in error messages
        env_prefix="SERVICE_",  # to restrict the envs that get injected into the deployment
    )

    # required since OS does not allow non-string env values on deployment
    @field_validator("enable_cors", mode="before")
    def parse_enable_cors(cls, value: T) -> bool | T:
        if isinstance(value, str):
            cleaned_value = value.strip('"').lower()
            if cleaned_value == "true":
                return True
            elif cleaned_value == "false":
                return False
            else:
                raise ValueError(f'Invalid boolean string "{cleaned_value}"')
        return value

    @field_validator("storage_type", mode="before")
    def validate_storage_type(cls, value: T) -> str | T:
        if isinstance(value, str):
            valid_storage_types = [
                storage_type.value for storage_type in StorageBackendType
            ]
            cleaned_value = value.strip('"').lower()

            if cleaned_value not in valid_storage_types:
                raise ValueError(
                    f'Invalid storage type "{cleaned_value}". '
                    f"Valid options are: {', '.join(valid_storage_types)}"
                )
            return cleaned_value
        return value

    @field_validator("tenant_id", mode="before")
    def validate_tenant_id(cls, value: T) -> str | None | T:
        if value is None:
            return value

        if isinstance(value, str):
            # Allow empty string - treat same as None (no tenant)
            if value.strip() == "":
                return None

            # PostgreSQL schema name rules: must start with letter or underscore,
            # can contain letters, digits, and underscores
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", value):
                raise ValueError(
                    "tenant_id must be a valid PostgreSQL identifier (letters, digits, underscores)"
                )

            # PostgreSQL identifier limit is 63 characters
            # But we prefix with "law_monitoring_" (15 chars), so limit tenant_id to 48
            if len(value) > 48:
                raise ValueError("tenant_id must be 48 characters or less")

            return value.lower()  # Normalize to lowercase

        return value

    enable_cors: bool = True
    enable_partner_button: bool = False
    pharia_kernel_url: HttpUrl
    pharia_studio_url: HttpUrl
    pharia_auth_service_url: str
    pharia_iam_issuer_url: HttpUrl
    pharia_data_url: HttpUrl
    pharia_data_stage_name: str
    storage_type: str
    completion_model_name: str
    database_url: SecretPostgresDsn
    tenant_id: str | None = None
