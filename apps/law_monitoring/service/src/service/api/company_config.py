import traceback

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from service.company_config_service import company_config_service
from service.core.dependencies.authorization import access_permission
from service.models import CompanyConfig, TeamDescription

company_config_router = APIRouter(dependencies=[Depends(access_permission)])


class CompanyDescriptionRequest(BaseModel):
    description: str


@company_config_router.get("/company-config")
async def get_company_config() -> CompanyConfig:
    """
    Get the complete company configuration including company description and all teams.

    Returns:
        CompanyConfig object containing company description and team list

    Raises:
        HTTPException: If there's an error retrieving the configuration
    """
    try:
        config = company_config_service.get_company_config()
        logger.info(f"Retrieved company config with {len(config.teams)} teams")
        return config

    except Exception as e:
        logger.error(f"Error retrieving company configuration: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error retrieving company configuration"
        )


@company_config_router.post("/company-config/company-description")
async def update_company_description(
    request: CompanyDescriptionRequest,
) -> CompanyDescriptionRequest:
    """
    Create or update the company description.

    Args:
        request: CompanyDescriptionRequest with the new description

    Returns:
        CompanyDescriptionRequest with the saved description

    Raises:
        HTTPException: If the update operation fails or request body is invalid
    """
    try:
        saved_description = company_config_service.add_or_update_company_description(
            request.description
        )

        logger.info("Successfully updated company description")
        return CompanyDescriptionRequest(description=saved_description)

    except ValueError as e:
        logger.error(f"Invalid company description: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating company description: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error updating company description"
        )


@company_config_router.post("/company-config/team")
async def add_or_update_team(
    team: TeamDescription,
) -> TeamDescription:
    """
    Add a new team or update an existing team (identified by name, case-insensitive).

    Args:
        team: TeamDescription object with team data

    Returns:
        TeamDescription object with the saved team data

    Raises:
        HTTPException: If the operation fails or request body is invalid
    """
    try:
        saved_team = company_config_service.add_or_update_team(team)

        logger.info(f"Successfully added/updated team: {saved_team.name}")
        return saved_team

    except ValueError as e:
        logger.error(f"Invalid team data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding/updating team '{team.name}': {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error adding/updating team '{team.name}'"
        )


@company_config_router.put("/company-config/team/{team_name}")
async def update_team_by_name(
    team_name: str,
    team: TeamDescription,
) -> TeamDescription:
    """
    Update an existing team by name (explicit update operation).

    Args:
        team_name: Name of the team to update
        team: TeamDescription object with updated team data

    Returns:
        TeamDescription object with the updated team data

    Raises:
        HTTPException: If team not found or update operation fails
    """
    try:
        existing_team = company_config_service.get_team_by_name(team_name)
        if not existing_team:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

        saved_team = company_config_service.add_or_update_team(team)

        logger.info(f"Successfully updated team: {saved_team.name}")
        return saved_team

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid team data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating team '{team_name}': {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error updating team '{team_name}'"
        )


@company_config_router.delete("/company-config/team/{team_name}")
async def delete_team(
    team_name: str,
) -> dict[str, str]:
    """
    Delete a team by name.

    Args:
        team_name: Name of the team to delete

    Returns:
        Dictionary with deletion status message

    Raises:
        HTTPException: If team not found or deletion fails
    """
    try:
        deleted = company_config_service.delete_team(team_name)

        if deleted:
            logger.info(f"Successfully deleted team: {team_name}")
            return {"message": f"Team '{team_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team '{team_name}': {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error deleting team '{team_name}'"
        )
