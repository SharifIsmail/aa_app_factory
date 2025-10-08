from loguru import logger

from service.dependencies import with_settings
from service.settings import AgentTelemetry
from service.tracing.smolagents_instrumentor import SmolagentsStudioInstrumentor


def initialize_tracing() -> None:
    settings = with_settings()

    if settings.agent_telemetry == AgentTelemetry.PHOENIX:
        from openinference.instrumentation.smolagents import SmolagentsInstrumentor
        from phoenix.otel import register

        register(project_name="supplier-briefing-service")
        SmolagentsInstrumentor().instrument()
        logger.info("Smolagents instrumentor initialized for Phoenix telemetry")

    if settings.agent_telemetry == AgentTelemetry.PHARIA_STUDIO:
        assert settings.studio_url is not None
        assert settings.studio_project_name is not None
        SmolagentsStudioInstrumentor(
            studio_url=str(settings.studio_url),
            auth_token=settings.authentication_token.get_secret_value(),
            studio_project_name=settings.studio_project_name,
        ).instrument()
        logger.info("Smolagents instrumentor initialized for Pharia Studio telemetry")
