import traceback

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from service.core.dependencies.authorization import access_permission
from service.models import ApplicationConfig

application_config_router = APIRouter(dependencies=[Depends(access_permission)])


@application_config_router.get("/application-config")
async def get_application_config() -> ApplicationConfig:
    """
    Get the complete application configuration.

    Returns:
        ApplicationConfig object

    Raises:
        HTTPException: If there's an error retrieving the configuration
    """
    try:
        config = ApplicationConfig()
        return config

    except Exception as e:
        logger.error(f"Error retrieving application configuration: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error retrieving application configuration"
        )
