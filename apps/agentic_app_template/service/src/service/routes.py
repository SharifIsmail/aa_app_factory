import os
import re
import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import FileResponse, HTMLResponse
from loguru import logger

from service.agent_core.models import (
    TaskStatus,
    WorkLog,
)
from service.agent_core.persistence_service import persistence_service
from service.agent_core.research_agent.research_service import ResearchService
from service.agent_core.research_agent.work_log_manager import create_work_log

# Repository keys
from service.core.dependencies.authorization import access_permission, with_user_profile
from service.core.services.auth_service import UserProfile
from service.dependencies import with_settings
from service.kernel import Json
from service.models import HealthResponse
from service.task_execution_manager import TaskExecutionManager
from service.work_log_manager import WorkLogManager

REPO_INSIGHTS = "INSIGHTS"

public_router: APIRouter = APIRouter()
protected_router: APIRouter = APIRouter(dependencies=[Depends(access_permission)])


class SearchStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Dependency to get the WorkLogManager instance
def get_work_log_manager() -> WorkLogManager:
    return WorkLogManager.get_instance()


# Dependency to get the TaskExecutionManager instance
def get_task_execution_manager() -> TaskExecutionManager:
    return TaskExecutionManager.get_instance()


# Helper function for running research in a separate thread
def run_research_in_thread(
    research_topic: str, execution_id: str, work_log: WorkLog, research_type: str
) -> str:
    try:
        # Check if the task has been cancelled before starting
        if (
            work_log.status == TaskStatus.FAILED
            or work_log.status == TaskStatus.CANCELLED
        ):
            logger.info(f"Task {execution_id} was cancelled before execution began")
            return ""

        settings = with_settings()
        return ResearchService.run_research(
            research_topic, execution_id, settings, research_type, work_log
        )
    except Exception as e:
        logger.error(f"Error in research thread: {str(e)}")
        logger.error(traceback.format_exc())
        work_log.status = TaskStatus.FAILED
        return ""


@public_router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@protected_router.post("/research/start")
async def start_research_agent(
    request: Request,
    background_tasks: BackgroundTasks,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
    task_execution_manager: TaskExecutionManager = Depends(get_task_execution_manager),
) -> Json:
    data = await request.json()
    if "research_topic" not in data:
        logger.warning("Missing required field: research_topic in request")
        raise HTTPException(
            status_code=400, detail="Missing required field: research_topic"
        )

    research_type = data.get("research_type", "comprehensive")
    if research_type not in ["basic", "comprehensive"]:
        logger.warning("Invalid research_type: {}", research_type)
        raise HTTPException(
            status_code=400,
            detail="Invalid research_type. Must be 'basic' or 'comprehensive'",
        )

    execution_id = str(uuid.uuid4())
    logger.info("Starting research task with ID: {}", execution_id)
    work_log = create_work_log(research_type=research_type, work_log_id=execution_id)
    work_log.status = TaskStatus.IN_PROGRESS
    work_log_manager.set(execution_id, work_log)

    task_execution_manager.execute_task(
        execution_id,
        run_research_in_thread,
        data["research_topic"],
        execution_id,
        work_log,
        research_type,
    )

    return {"status": "OK", "id": execution_id}


@protected_router.get("/research/status/{uuid}")
async def research_agent_status(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    if not work_log_manager.contains(uuid):
        logger.warning("Research job with ID {} not found", uuid)
        raise HTTPException(
            status_code=404, detail=f"Research job with ID {uuid} not found"
        )

    work_log = work_log_manager.get(uuid)

    if work_log:
        # Extract insights data with fallback to empty dict if the repository doesn't exist
        extracted_data = {}
        try:
            extracted_data = work_log.data_storage.retrieve_all_from_repo(REPO_INSIGHTS)
        except KeyError:
            # This is expected during early stages of research
            logger.warning(f"INSIGHTS repository not yet available for job {uuid}")
        except Exception as e:
            logger.error("Error retrieving INSIGHTS data: {}", str(e))
            logger.error("Traceback: {}", traceback.format_exc())

        return {
            "status": work_log.status.value,
            "uuid": uuid,
            "tasks": work_log.tasks,
            "tool_logs": work_log.tool_logs,
            "extracted_data": extracted_data,
        }

    logger.error("Error fetching work_log for task {}", uuid)
    return {}


@protected_router.delete("/research/stop/{uuid}")
async def stop_research_agent(
    uuid: str,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
    task_execution_manager: TaskExecutionManager = Depends(get_task_execution_manager),
) -> Json:
    if not work_log_manager.contains(uuid):
        logger.warning("Attempted to stop non-existent research job: {}", uuid)
        raise HTTPException(status_code=404, detail="Research job not found")

    cancelled = task_execution_manager.cancel_task(uuid)
    work_log_manager.update_status(uuid, TaskStatus.CANCELLED)

    return {"uuid": uuid, "task_cancelled": cancelled}


@protected_router.get("/reports/{uuid}")
async def get_agentic_report(
    uuid: str,
    download: bool = False,
) -> Response:
    agentic_data = persistence_service.get_agentic_data_by_uuid(uuid)

    if agentic_data is None:
        logger.warning("Agentic data not found for UUID: {}", uuid)
        raise HTTPException(
            status_code=404, detail=f"Agentic data not found for UUID: {uuid}"
        )

    if not agentic_data["agentic_data_report_path"]:
        logger.warning("Agentic data report not found for UUID: {}", uuid)
        raise HTTPException(status_code=404, detail="Agentic data report not found")

    report_path = agentic_data["agentic_data_report_path"]
    filename = (
        re.sub(r"\W+", "_", agentic_data["name"]).lower() + "_agentic_report.html"
    )

    logger.info("Serving report for UUID: {} (download={})", uuid, download)
    if download:
        return FileResponse(path=report_path, filename=filename, media_type="text/html")
    else:
        return HTMLResponse(content=open(report_path, "r", encoding="utf-8").read())


@protected_router.get("/reports")
async def get_agentic_list() -> Json:
    logger.debug("Retrieving list of agentic reports")
    agentic_data = persistence_service.list_cached_agentic_data()
    response_data = []

    for data in agentic_data:
        response_data.append(
            {
                "uuid": data["uuid"],
                "name": data["name"],
                "hasAgenticDataReport": data["agentic_data_report_path"] is not None,
                "processingDate": os.path.getmtime(data["path"]),
            }
        )

    response_data.sort(key=lambda x: x["processingDate"], reverse=True)
    for item in response_data:
        item["processingDate"] = datetime.fromtimestamp(
            item["processingDate"]
        ).strftime("%Y-%m-%d %H:%M:%S")

    logger.debug("Found {} agentic reports", len(response_data))
    return response_data


@protected_router.get("/user-profile")
async def user_profile(
    user_profile: Annotated[UserProfile, Depends(with_user_profile)],
) -> UserProfile:
    return user_profile


router: APIRouter = APIRouter(tags=["API"])
router.include_router(public_router)
router.include_router(protected_router)
