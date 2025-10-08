"""
Deployment settings for the supplier-briefing service.
Manages environment variables required for deployment and Kubernetes operations.
"""

from pathlib import Path

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploySettings(BaseSettings):
    """Settings for deployment operations."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=False,
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    pharia_api_url: HttpUrl = Field(
        default=HttpUrl("https://api.schwarz.cus.customer.pharia.com"),
        validation_alias="PHARIA_API_URL",
        description="Pharia API base URL",
    )
    pharia_api_token: SecretStr = Field(
        validation_alias="PHARIA_API_TOKEN", description="Pharia API auth token"
    )

    kubeconfig_path: Path = Field(
        validation_alias="KUBECONFIG_PATH",
        description="Path to kubeconfig file",
    )
    kubernetes_namespace: str = Field(
        default="schwarz",
        validation_alias="KUBERNETES_NAMESPACE",
        description="Kubernetes namespace for secrets",
    )

    vertex_ai_credentials: SecretStr = Field(
        validation_alias="SERVICE_VERTEX_AI_CREDENTIALS",
        description="Vertex AI credentials JSON",
    )
    vertex_secret_name: str = Field(
        default="supplier-briefing-schwarz-vertex-credentials-secret",
        validation_alias="VERTEX_SECRET_NAME",
        description="Name of the Kubernetes secret for Vertex AI",
    )

    @field_validator("kubeconfig_path")
    @classmethod
    def expand_kubeconfig_path(cls, v: Path) -> Path:
        """Expand user home directory in kubeconfig path."""
        return v.expanduser()

    @property
    def pharia_api_os_usecases_base_url(self) -> str:
        """Get Pharia API base URL with usecases endpoint."""
        return f"{self.pharia_api_url}/v1/os/usecases"

    @property
    def pharia_auth_header(self) -> dict[str, str]:
        """Get authorization header for Pharia API."""
        return {"Authorization": f"Bearer {self.pharia_api_token.get_secret_value()}"}
