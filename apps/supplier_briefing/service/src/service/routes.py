import traceback
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import JSONResponse
from loguru import logger

from service.agent_core.constants import (
    REPO_AGENT_RESPONSE,
    REPO_INSIGHTS,
    REPO_PANDAS_OBJECTS,
    REPO_RESULTS,
    AgentMode,
)
from service.agent_core.data_management.paths import get_data_dir
from service.agent_core.data_query_orchestration.data_query_service import (
    DataQueryService,
)
from service.agent_core.models import (
    TaskStatus,
    WorkLog,
)
from service.agent_core.persistence.agent_instance_store import agent_instance_store
from service.core.dependencies.authorization import access_permission
from service.data_loading import get_columns_for_path
from service.data_preparation import TRANSACTIONS_PARQUET
from service.data_preparation_state import (
    DataPreparationState,
    DataPreparationStateManager,
    with_data_preperation_state,
)
from service.dependencies import with_settings
from service.models import HealthResponse
from service.quick_actions.fetcher_registry import QuickActionFetcher
from service.quick_actions.models import (
    QuickAction,
    QuickActionFilterRequest,
    QuickActionFilterResponse,
)
from service.settings import Settings
from service.task_execution_manager import TaskExecutionManager
from service.utils import make_json_serializable
from service.work_log_manager import WorkLogManager

public_router: APIRouter = APIRouter()
protected_router: APIRouter = APIRouter(dependencies=[Depends(access_permission)])
Json = dict | list | bool | float | int | str | None


def get_work_log_manager() -> WorkLogManager:
    return WorkLogManager.get_instance()


def get_task_execution_manager() -> TaskExecutionManager:
    return TaskExecutionManager.get_instance()


@public_router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@public_router.get("/data-preparation-status")
async def data_preparation_status(
    data_preparation_state: DataPreparationStateManager = Depends(
        with_data_preperation_state
    ),
) -> DataPreparationState:
    return data_preparation_state.get_state()


@protected_router.post("/query/start")
async def start_query_agent(
    request: Request,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
    task_execution_manager: TaskExecutionManager = Depends(get_task_execution_manager),
    settings: Settings = Depends(with_settings),
) -> Json:
    data = await request.json()

    # Extract query (required)
    query = data.get("query", "")
    if not query:
        logger.warning("Missing required field: query in request")
        raise HTTPException(status_code=400, detail="Missing required field: query")

    # Extract optional parameters
    execution_id = data.get("execution_id", str(uuid.uuid4()))
    flow_name = data.get("flow_name", "")
    params = data.get("params", {})

    # Log the received parameters for debugging
    logger.info(
        "Using execution_id for conversation and task tracking: {}", execution_id
    )
    if flow_name:
        logger.info("Received flow_name: {} with params: {}", flow_name, params)
        # For now, determine mode but don't use it
        mode = AgentMode.DETERMINISTIC
        logger.info("Would use mode: {} (currently ignored)", mode.value)
    else:
        mode = AgentMode.AGENT
        logger.info("Using standard agent mode")

    # Create a wrapper that ignores the result and returns work_log for task_execution_manager
    def query_task() -> WorkLog:
        data_query_service = DataQueryService(settings, work_log_manager)
        # Pass all parameters to data_query_service
        return data_query_service.run(
            query,
            execution_id,
            enable_explainability=True,
            mode=mode,
            flow_name=flow_name if flow_name else None,
            params=params if params else None,
        )

    task_execution_manager.execute_task(
        execution_id,
        query_task,
    )

    return {"status": "OK", "id": execution_id}


@protected_router.get("/query/status/{uuid}")
async def query_agent_status(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    if not work_log_manager.contains(uuid):
        logger.info(
            "Query agent job with ID {} not found in work_log_manager - data not yet ready",
            uuid,
        )

        return {
            "status": "IN_PROGRESS",
            "uuid": uuid,
            "message": "Query task is starting, data not yet ready",
            "tasks": [],
            "tool_logs": [],
            "explained_steps": [],
            "extracted_data": {},
            "final_result": {},
            "pandas_objects_data": {},
            "results_data": {},
        }

    work_log = work_log_manager.get(uuid)

    if work_log:
        extracted_data = {}
        try:
            extracted_data = work_log.data_storage.retrieve_all_from_repo(REPO_INSIGHTS)
        except Exception as e:
            logger.error("Error retrieving INSIGHTS data: {}", str(e))
            logger.error("Traceback: {}", traceback.format_exc())

        # Extract final result/answer
        final_result = work_log.data_storage.retrieve_all_from_repo(REPO_AGENT_RESPONSE)

        # Extract all pandas data fetched during query task
        pandas_objects_data = {}
        try:
            pandas_objects_data = work_log.data_storage.retrieve_all_from_repo(
                REPO_PANDAS_OBJECTS
            )
        except Exception as e:
            logger.error("Error retrieving pandas object data: {}", str(e))
            logger.error("Traceback: {}", traceback.format_exc())

        # Extract results from present_results tool
        results_data = {}
        try:
            results_data = work_log.data_storage.retrieve_all_from_repo(REPO_RESULTS)
        except Exception as e:
            logger.error("Error retrieving results data: {}", str(e))
            logger.error("Traceback: {}", traceback.format_exc())

        return {
            "status": work_log.status.value,
            "uuid": uuid,
            "tasks": make_json_serializable(work_log.tasks),
            "tool_logs": make_json_serializable(work_log.tool_logs),
            "explained_steps": make_json_serializable(work_log.explained_steps),
            "extracted_data": make_json_serializable(extracted_data),
            "final_result": make_json_serializable(final_result),
            "pandas_objects_data": pandas_objects_data,
            "results_data": results_data,
        }

    logger.error("Error fetching work_log for task {}", uuid)
    return {
        "status": "FAILED",
        "uuid": uuid,
        "message": "Failed to retrieve work log",
        "tasks": [],
        "tool_logs": [],
        "explained_steps": [],
        "extracted_data": {},
        "final_result": {},
        "pandas_objects_data": {},
        "results_data": {},
    }


@protected_router.delete("/query/stop/{uuid}")
async def stop_query_agent(
    uuid: str,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
    task_execution_manager: TaskExecutionManager = Depends(get_task_execution_manager),
) -> Json:
    if not work_log_manager.contains(uuid):
        logger.warning("Attempted to stop non-existent query task: {}", uuid)
        raise HTTPException(status_code=404, detail="Query task not found")

    cancelled = task_execution_manager.cancel_task(uuid)
    work_log_manager.update_status(uuid, TaskStatus.CANCELLED)

    work_log_deleted = work_log_manager.delete(uuid)
    agent_deleted = agent_instance_store.delete_agent(uuid)

    return {
        "uuid": uuid,
        "task_cancelled": cancelled,
        "work_log_deleted": work_log_deleted,
        "agent_deleted": agent_deleted,
    }


@protected_router.get("/columns")
async def get_transactions_columns() -> JSONResponse:
    try:
        data_path = get_data_dir() / TRANSACTIONS_PARQUET
        columns_list = get_columns_for_path(data_path)
    except Exception as e:
        logger.error("Failed to load transactions columns: {}", str(e))
        logger.error("Traceback: {}", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to retrieve columns")

    return JSONResponse(content=columns_list)


@protected_router.post(
    "/quick-actions/filter", response_model=QuickActionFilterResponse
)
async def filter_quick_action_data(
    request: QuickActionFilterRequest,
) -> QuickActionFilterResponse:
    """
    Generic endpoint for filtering data for quick action buttons.

    Uses the modular quick action framework to route requests to appropriate data fetchers.

    Args:
        request: A discriminated union of quick action filter parameters.

    Returns:
        QuickActionFilterResponse with filtered data
    """
    try:
        logger.info(
            f"Quick action filter request: flow_name={request.flow_name}, filter_params={request.filter_params.model_dump()}"
        )

        quick_action = QuickAction(request.flow_name)
        data_fetcher = QuickActionFetcher.get_fetcher(quick_action)
        result = data_fetcher.fetch_data(request.filter_params)

        return QuickActionFilterResponse(
            success=result.success,
            data=result.data,
            error=result.error,
        )

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return QuickActionFilterResponse(success=False, data=[], error=str(e))
    except Exception as e:
        logger.error(f"Quick action filter error: {str(e)}")
        return QuickActionFilterResponse(
            success=False, data=[], error="An internal error occurred"
        )


router: APIRouter = APIRouter(tags=["API"])
router.include_router(public_router)
router.include_router(protected_router)
