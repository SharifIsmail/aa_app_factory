"""
Service for fetching and caching LLM model settings from the inference API.
"""

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from service.core.utils.singleton import SingletonMeta
from service.dependencies import with_settings


class ModelSetting(BaseModel):
    """Represents the configuration for a single LLM model."""

    name: str
    max_context_size: int = Field(..., alias="max_context_size")


class ModelSettingsService(metaclass=SingletonMeta):
    """
    Manages fetching and caching of model settings.
    This service is a singleton, initialized once at application startup.
    """

    _model_settings: dict[str, ModelSetting] = {}

    def __init__(self) -> None:
        self._settings = with_settings()
        self._initialized = True
        logger.info("ModelSettingsService initialized.")
        self.load_model_settings()

    def load_model_settings(self) -> None:
        """
        Fetches model settings from the inference API and caches them.
        This method is called once at application startup.
        """
        if self._model_settings:
            logger.info("Model settings already loaded.")
            return

        api_url = f"{self._settings.inference_api_url}v1/model-settings"
        token = self._settings.authentication_token.get_secret_value()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            with httpx.Client() as client:
                response = client.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                for model_data in data:
                    setting = ModelSetting(**model_data)
                    self._model_settings[setting.name] = setting

                logger.success(
                    f"Successfully loaded and cached settings for {len(self._model_settings)} models."
                )

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch model settings from API: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading model settings: {e}"
            )

    def get_max_context_window(self, model_name: str) -> int:
        """
        Retrieves the max_context_window for a given model name.

        Args:
            model_name: The name of the model (e.g., 'llama-3.1-8b-instruct').

        Returns:
            The max context window size.

        Raises:
            ValueError: If the model is not found in the loaded settings.
        """
        model = self._model_settings.get(model_name)
        if model is None:
            raise ValueError(f"Configuration for model '{model_name}' not found.")
        return int(model.max_context_size * 0.9)


model_settings_service = ModelSettingsService()
